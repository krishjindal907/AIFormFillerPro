import re
import json
import requests
from bs4 import BeautifulSoup
from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from models import db, FormAnalysis

analyze_bp = Blueprint('analyze', __name__)

def match_field_to_profile(field_label, field_name, user):
    """
    Tries to match a form field (based on label/name) with the User Profile.
    Returns (match_key, confidence_score, matched_value).
    """
    text = f"{field_label} {field_name}".lower()
    
    mappings = {
        'name': ['name', 'first name', 'last name', 'full name'],
        'email': ['email', 'e-mail'],
        'phone': ['phone', 'mobile', 'cell', 'tel', 'contact number'],
        'age': ['age', 'years old'],
        'gender': ['gender', 'sex'],
        'address': ['address', 'location', 'street', 'city'],
        'profession': ['profession', 'job', 'occupation', 'role', 'title'],
        'education': ['education', 'degree', 'university', 'college', 'school'],
        'skills': ['skills', 'technologies', 'expertise'],
        'preferences': ['preferences', 'diet', 'hobbies']
    }
    
    best_match = None
    best_score = 0
    
    for key, keywords in mappings.items():
        for kw in keywords:
            if kw in text:
                score = 100 if kw == text.strip() else 80
                if score > best_score:
                    best_score = score
                    best_match = key
                    
    if best_match:
        val = getattr(user, best_match, '')
        if val:
            return best_match, best_score, val
            
    return None, 0, ''

@analyze_bp.route('/analyze', methods=['GET'])
@login_required
def analyze_view():
    return render_template('analyze.html')

@analyze_bp.route('/api/fetch_form', methods=['POST'])
@login_required
def fetch_form():
    url = request.form.get('url')
    html_content = request.form.get('html_content')
    
    if url:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url, headers=headers, timeout=5)
            html = res.text
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    elif html_content:
        html = html_content
    else:
        return jsonify({"error": "No URL or HTML provided"}), 400
        
    soup = BeautifulSoup(html, 'html.parser')
    forms = soup.find_all('form')
    
    # Lenient Mode: If no <form> tag is found, treat the whole body as a form
    if forms:
        target_form = forms[0]
    else:
        target_form = soup.body if soup.body else soup
        
    fields = []
    
    for el in target_form.find_all(['input', 'select', 'textarea']):
        el_type = el.name if el.name != 'input' else el.get('type', 'text')
        name = el.get('name', '')
        
        # Bypass hidden filter for Google Forms 'entry.' inputs
        is_google_form = "docs.google.com/forms" in (url or "")
        is_google_entry = is_google_form and el_type == 'hidden' and name.startswith('entry.')
        
        if el_type in ['hidden', 'submit', 'button', 'reset', 'file'] and not is_google_entry:
            continue
            
        id_ = el.get('id', '')
        placeholder = el.get('placeholder', '')
        
        label_text = ''
        if id_:
            lbl = soup.find('label', attrs={'for': id_})
            if lbl:
                label_text = lbl.get_text(separator=' ', strip=True)
                
        if not label_text:
            parent_lbl = el.find_parent('label')
            if parent_lbl:
                label_text = parent_lbl.get_text(separator=' ', strip=True).replace(el.get_text(), '')
                
        # Google Forms Fallback
        if not label_text:
            heading = el.find_previous(attrs={"role": "heading"})
            if heading:
                label_text = heading.get_text(separator=' ', strip=True)
                
        match_key, confidence, prefill_val = match_field_to_profile(label_text or placeholder, name, current_user)
        
        fields.append({
            "tag": el.name,
            "type": el_type,
            "name": name,
            "id": id_,
            "label": label_text,
            "placeholder": placeholder,
            "match_key": match_key,
            "confidence": confidence,
            "prefill_value": prefill_val,
            "options": [opt.get_text(strip=True) for opt in el.find_all('option')] if el.name == 'select' else []
        })
        
    import os
    gemini_key = os.environ.get("GEMINI_API_KEY")
    ai_mapping = {}
    vault_context = getattr(current_user, 'preferences', '') or f"Name: {getattr(current_user, 'name', '')}, Profession: {getattr(current_user, 'profession', '')}, Skills: {getattr(current_user, 'skills', '')}"
    
    parsed_memory = session.get('active_parsed_memory')
    if parsed_memory:
        vault_context += f"\n\n--- HIGH PRIORITY TEMPORARY PARSED DATA ---\nThe following data was just parsed from a Resume/Document by the user and should OVERRIDE permanent vault data:\n{json.dumps(parsed_memory, indent=2)}"

    if gemini_key and fields and vault_context.strip():
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=gemini_key)
            
            summary = [{"name": f["name"], "label": f["label"] or f["placeholder"], "type": f["type"]} for f in fields]
            
            prompt = f"""
You are an expert Auto-Fill AI Agent.
I will provide you with a user's entire 'Knowledge Vault' (all their resume info, history, skills) and a JSON array representing the input fields of an external HTML form.

For each field in the form, intelligently deduce the best possible answer from the user's Vault. Keep answers concise but accurate. If the information does not exist or you cannot guess it with high confidence, leave it entirely out of the output.

User Context Vault:
-----------------------
{vault_context}
-----------------------

Form Fields:
{json.dumps(summary, indent=2)}

Return ONLY a valid JSON object mapping the exact field `name` to the extracted `value`.
            """
            
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            ai_mapping = json.loads(response.text)
        except Exception as e:
            print(f"Gemini API Error: {e}")
            
    # Apply mapping
    for f in fields:
        if f["name"] in ai_mapping and ai_mapping[f["name"]]:
            f["match_key"] = "GEMINI_AI"
            f["confidence"] = 99
            f["prefill_value"] = str(ai_mapping[f["name"]])
        
    matched_count = sum(1 for f in fields if f['match_key'])
    new_analysis = FormAnalysis(
        user_id=current_user.id,
        target_url=url if url else 'custom_html',
        form_html_snapshot=json.dumps(fields),
        fields_detected=len(fields),
        matched_fields=matched_count
    )
    db.session.add(new_analysis)
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "analysis_id": new_analysis.id,
        "fields": fields,
        "metrics": {
            "total": len(fields),
            "matched": matched_count
        }
    })

from flask import Response

@analyze_bp.route('/proxy', methods=['GET'])
@login_required
def proxy():
    url = request.args.get('url')
    if not url:
        return "No URL provided", 400
        
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers, timeout=10)
        html = res.text
        
        # Inject base tag to resolve relative URLs (css, js, images)
        if '<head>' in html:
            html = html.replace('<head>', f'<head><base href="{url}">')
        elif '<head ' in html:
            import re
            html = re.sub(r'(<head[^>]*>)', r'\1<base href="' + url + '">', html, count=1)
        else:
            html = f'<head><base href="{url}"></head>' + html
            
        return Response(html, mimetype='text/html')
        return Response(html, mimetype='text/html')
    except Exception as e:
        return str(e), 500

@analyze_bp.route('/api/extension/analyze', methods=['POST', 'OPTIONS'])
def extension_analyze():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    # User authentication check for extension (Fallback to local db if SameSite strips cookie)
    user = current_user
    if not getattr(user, 'is_authenticated', False):
        from models import User
        user = User.query.first()
        if not user:
            return jsonify({"status": "error", "error": "No user found! Please open http://127.0.0.1:5000 and sign up first to attach your Knowledge Vault."}), 401

    data = request.json
    fields = data.get('fields', [])
    url = data.get('url', '')
    
    import os
    import json
    gemini_key = os.environ.get("GEMINI_API_KEY")
    ai_mapping = {}
    vault_context = getattr(user, 'preferences', '') or f"Name: {getattr(user, 'name', '')}, Profession: {getattr(user, 'profession', '')}, Skills: {getattr(user, 'skills', '')}"

    parsed_memory = session.get('active_parsed_memory')
    if parsed_memory:
        vault_context += f"\n\n--- HIGH PRIORITY TEMPORARY PARSED DATA ---\nThe following data was just parsed from a Resume/Document by the user and should OVERRIDE permanent vault data:\n{json.dumps(parsed_memory, indent=2)}"

    if gemini_key and fields and vault_context.strip():
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=gemini_key)
            
            summary = [{"name": f["name"], "id": f["id"], "label": f["label"], "type": f["type"]} for f in fields]
            
            prompt = f"""
You are an expert Auto-Fill AI Agent running as a Chrome Extension.
I will provide you with a user's entire 'Knowledge Vault' (all their resume info, history, skills) and a JSON array representing the input fields of an external HTML form located at {url}.

For each field in the form, intelligently deduce the best possible answer from the user's Vault. Keep answers concise but accurate. If the information does not exist or you cannot guess it with high confidence, leave it entirely out of the output.

User Context Vault:
-----------------------
{vault_context}
-----------------------

Form Fields (IMPORTANT: Use the exact 'name' OR 'id' as the key):
{json.dumps(summary, indent=2)}

Return ONLY a valid JSON object mapping the exact field `name` (or `id` if name is blank) to the extracted `value`. Do not include any other text!
            """
            
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            ai_mapping = json.loads(response.text)
        except Exception as e:
            print(f"Gemini API Error: {str(e)}")
            
    # Fallback to local offline dictionary matching if Gemini is inactive or failed
    if not ai_mapping:
        for f in fields:
            label = f.get('label', '')
            name = f.get('name', '')
            if not label and not name:
                continue
            match_key, conf, prefill_val = match_field_to_profile(label, name, user)
            if prefill_val:
                key = name if name else f.get('id', '')
                if key:
                    ai_mapping[key] = prefill_val

    return jsonify({
        "status": "success",
        "ai_mapping": ai_mapping
    })
