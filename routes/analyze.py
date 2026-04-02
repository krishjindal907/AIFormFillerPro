import re
import json
import requests
from bs4 import BeautifulSoup
from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from models import db, FormAnalysis

analyze_bp = Blueprint('analyze', __name__)


def build_vault_context(user):
    """
    User ke saare profile fields aur documents ko ek rich
    context string mein combine karo Gemini ke liye.
    """
    parts = []
    if user.name:        parts.append(f"Full Name: {user.name}")
    if user.email:       parts.append(f"Email: {user.email}")
    if user.phone:       parts.append(f"Phone: {user.phone}")
    if user.age:         parts.append(f"Age: {user.age}")
    if user.gender:      parts.append(f"Gender: {user.gender}")
    if user.address:     parts.append(f"Address: {user.address}")
    if user.father_name: parts.append(f"Father's Name: {user.father_name}")
    if user.mother_name: parts.append(f"Mother's Name: {user.mother_name}")
    if user.profession:  parts.append(f"Profession/Job Title: {user.profession}")
    if user.education:   parts.append(f"Education: {user.education}")
    if user.skills:      parts.append(f"Skills: {user.skills}")
    if user.preferences: parts.append(f"Additional Context / Documents:\n{user.preferences}")

    return "\n".join(parts) if parts else ""


def match_field_to_profile(field_label, field_name, user):
    """
    Form field ko user profile se match karo (offline fallback).
    Returns (match_key, confidence_score, matched_value).
    """
    text = f"{field_label} {field_name}".lower()

    mappings = {
        'name':       ['name', 'first name', 'last name', 'full name', 'fname', 'lname'],
        'email':      ['email', 'e-mail', 'mail'],
        'phone':      ['phone', 'mobile', 'cell', 'tel', 'contact', 'number'],
        'age':        ['age', 'years old', 'dob', 'date of birth', 'birth'],
        'gender':     ['gender', 'sex'],
        'address':    ['address', 'location', 'street', 'city', 'state', 'pincode', 'zip'],
        'profession': ['profession', 'job', 'occupation', 'role', 'title', 'designation'],
        'education':  ['education', 'degree', 'university', 'college', 'school', 'qualification'],
        'skills':     ['skills', 'technologies', 'expertise', 'competencies'],
        'father_name':['father', 'fathers name', "father's name"],
        'mother_name':['mother', 'mothers name', "mother's name"],
        'preferences':['preferences', 'diet', 'hobbies', 'interests'],
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
            return best_match, best_score, str(val)

    return None, 0, ''


def run_gemini_autofill(fields, vault_context, url=""):
    """
    Gemini ko fields + vault context deke JSON mapping lao.
    Returns dict: { field_name: value }
    """
    import os
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key or not fields or not vault_context.strip():
        return {}

    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=gemini_key)

        summary = [
            {
                "name": f.get("name", ""),
                "id": f.get("id", ""),
                "label": f.get("label") or f.get("placeholder", ""),
                "type": f.get("type", "text"),
                "options": f.get("options", [])
            }
            for f in fields
        ]

        url_context = f"Form URL: {url}\n" if url else ""

        prompt = f"""
You are an expert Auto-Fill AI Agent.
{url_context}
USER'S KNOWLEDGE VAULT (their personal data):
---------------------------------------------
{vault_context}
---------------------------------------------

FORM FIELDS TO FILL:
{json.dumps(summary, indent=2)}

INSTRUCTIONS:
- For each field, find the best matching value from the user's vault.
- For "select" fields, choose from the provided "options" list.
- For date fields, use common formats like DD/MM/YYYY or YYYY-MM-DD.
- If data is unavailable or uncertain, omit the field.
- Keep answers concise and accurate.

Return ONLY a valid JSON object mapping each field's exact `name` (or `id` if name is blank) to its value.
Do NOT include any explanation, markdown, or extra text.
"""

        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)

    except Exception as e:
        print(f"Gemini Autofill Error: {e}")
        return {}


# ─────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────

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
            res = requests.get(url, headers=headers, timeout=8)
            html = res.text
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    elif html_content:
        html = html_content
    else:
        return jsonify({"error": "No URL or HTML provided"}), 400

    soup = BeautifulSoup(html, 'html.parser')
    forms = soup.find_all('form')

    # Lenient Mode: agar <form> tag nahi mila to poori body use karo
    target_form = forms[0] if forms else (soup.body if soup.body else soup)

    fields = []
    for el in target_form.find_all(['input', 'select', 'textarea']):
        el_type = el.name if el.name != 'input' else el.get('type', 'text')
        name = el.get('name', '')

        is_google_form = "docs.google.com/forms" in (url or "")
        is_google_entry = is_google_form and el_type == 'hidden' and name.startswith('entry.')

        if el_type in ['hidden', 'submit', 'button', 'reset', 'file', 'image'] and not is_google_entry:
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
                label_text = parent_lbl.get_text(separator=' ', strip=True)

        if not label_text:
            heading = el.find_previous(attrs={"role": "heading"})
            if heading:
                label_text = heading.get_text(separator=' ', strip=True)

        match_key, confidence, prefill_val = match_field_to_profile(
            label_text or placeholder, name, current_user
        )

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

    # Vault context build karo
    vault_context = build_vault_context(current_user)

    # Session parsed memory ko override ke roop mein inject karo
    parsed_memory = session.get('active_parsed_memory')
    if parsed_memory:
        vault_context += f"\n\n--- HIGH PRIORITY: Recently Parsed Document Data (OVERRIDE) ---\n{json.dumps(parsed_memory, indent=2)}"

    # Gemini se AI mapping lao
    ai_mapping = run_gemini_autofill(fields, vault_context, url=url or "")

    # AI mapping apply karo fields pe
    for f in fields:
        key = f["name"] or f["id"]
        if key and key in ai_mapping and ai_mapping[key]:
            f["match_key"] = "GEMINI_AI"
            f["confidence"] = 99
            f["prefill_value"] = str(ai_mapping[key])

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
        "metrics": {"total": len(fields), "matched": matched_count}
    })


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

        if '<head>' in html:
            html = html.replace('<head>', f'<head><base href="{url}">', 1)
        elif re.search(r'<head\s', html):
            html = re.sub(r'(<head[^>]*>)', r'\1<base href="' + url + '">', html, count=1)
        else:
            html = f'<head><base href="{url}"></head>' + html

        from flask import Response
        return Response(html, mimetype='text/html')
    except Exception as e:
        return str(e), 500


@analyze_bp.route('/api/extension/analyze', methods=['POST', 'OPTIONS'])
def extension_analyze():
    """
    Chrome Extension endpoint.
    Session cookie cross-origin nahi milti, isliye
    fallback: database ka pehla user use karo (local single-user setup).
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    # Auth check
    user = current_user
    if not getattr(user, 'is_authenticated', False):
        from models import User
        # Local single-user fallback
        user = User.query.first()
        if not user:
            return jsonify({
                "status": "error",
                "error": "No user found! Please open http://127.0.0.1:5000 and sign up first."
            }), 401

    data = request.json or {}
    fields = data.get('fields', [])
    url = data.get('url', '')

    vault_context = build_vault_context(user)

    # Session parsed memory (extension ke liye usually empty hogi, but try karo)
    parsed_memory = session.get('active_parsed_memory')
    if parsed_memory:
        vault_context += f"\n\n--- HIGH PRIORITY: Recently Parsed Document Data (OVERRIDE) ---\n{json.dumps(parsed_memory, indent=2)}"

    # Gemini autofill
    ai_mapping = run_gemini_autofill(fields, vault_context, url=url)

    # Agar Gemini fail ho to offline dictionary fallback
    if not ai_mapping:
        for f in fields:
            label = f.get('label', '') or f.get('placeholder', '')
            name = f.get('name', '')
            match_key, conf, prefill_val = match_field_to_profile(label, name, user)
            if prefill_val:
                key = name if name else f.get('id', '')
                if key:
                    ai_mapping[key] = prefill_val

    return jsonify({
        "status": "success",
        "ai_mapping": ai_mapping
    })
