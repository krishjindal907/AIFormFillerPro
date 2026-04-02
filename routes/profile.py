from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from models import db

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/my_profile')
@login_required
def my_profile():
    return render_template('my_profile.html')

@profile_bp.route('/edit_profile', methods=['POST'])
@login_required
def edit_profile():
    import os
    from werkzeug.utils import secure_filename

    current_user.name = request.form.get('name', current_user.name)
    current_user.phone = request.form.get('phone', current_user.phone)
    current_user.age = request.form.get('age', current_user.age)
    current_user.gender = request.form.get('gender', current_user.gender)
    current_user.address = request.form.get('address', current_user.address)
    current_user.father_name = request.form.get('father_name', current_user.father_name)
    current_user.mother_name = request.form.get('mother_name', current_user.mother_name)
    current_user.profession = request.form.get('profession', current_user.profession)
    current_user.education = request.form.get('education', current_user.education)
    current_user.skills = request.form.get('skills', current_user.skills)
    
    if 'profile_pic' in request.files:
        file = request.files['profile_pic']
        if file.filename != '':
            filename = secure_filename(f"user_{current_user.id}_{file.filename}")
            filepath = os.path.join('static', 'uploads', 'profiles', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            file.save(filepath)
            current_user.profile_pic = filename
            
    from models import db
    db.session.commit()
    flash('Identity Demographics successfully updated and secured.', 'success')
    return redirect(url_for('profile.my_profile'))

@profile_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.name = request.form.get('name', '')
        current_user.phone = request.form.get('phone', '')
        current_user.age = request.form.get('age', '')
        current_user.gender = request.form.get('gender', '')
        current_user.address = request.form.get('address', '')
        current_user.profession = request.form.get('profession', '')
        current_user.education = request.form.get('education', '')
        current_user.skills = request.form.get('skills', '')
        current_user.preferences = request.form.get('preferences', '')
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile.profile'))
    return render_template('profile.html')

@profile_bp.route('/api/profile/export', methods=['GET'])
@login_required
def export_profile():
    data = {
        "name": current_user.name,
        "email": current_user.email,
        "phone": current_user.phone,
        "age": current_user.age,
        "gender": current_user.gender,
        "address": current_user.address,
        "profession": current_user.profession,
        "education": current_user.education,
        "skills": current_user.skills,
        "preferences": current_user.preferences
    }
    return jsonify(data)

@profile_bp.route('/api/upload_doc', methods=['POST'])
@login_required
def upload_doc():
    """ 
    Scan-Before-Store Stage 1: In-Memory Ingestion 
    Performs parsing FIRST without touching the disk.
    """
    if 'document' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400
        
    file = request.files['document']
    
    if file.filename == '':
        return jsonify({"status": "error", "message": "No file selected"}), 400
        
    try:
        from parsing_engine import parse_pdf, parse_image, parse_text
        from werkzeug.utils import secure_filename
        import os
        
        # 0. Secure Temp Storage
        temp_dir = os.path.join('static', 'uploads', 'temp_hold')
        os.makedirs(temp_dir, exist_ok=True)
        temp_filename = secure_filename(f"temp_{current_user.id}_{file.filename}")
        temp_path = os.path.join(temp_dir, temp_filename)
        file.save(temp_path)
        
        # 1. Parsing FIRST (From temp file)
        result = None
        text_content = ""
        
        if file.filename.lower().endswith('.pdf'):
            with open(temp_path, 'rb') as f:
                result = parse_pdf(f)
                f.seek(0)
                import PyPDF2
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text_content += (page.extract_text() or "") + "\n"
        elif file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            with open(temp_path, 'rb') as f:
                result = parse_image(f)
        else:
            with open(temp_path, 'r', encoding='utf-8', errors='ignore') as f:
                text_content = f.read()
                result = parse_text(text_content)
            
        if not result:
            if os.path.exists(temp_path): os.remove(temp_path)
            # Use 422 Unprocessable Entity for parsing failures (standardized)
            return jsonify({"status": "error", "message": "Neural Engine could not decipher this payload. Please ensure the document is clear and high-resolution."}), 422

        # Stage in session
        session['last_scan_result'] = result
        session['last_scan_text'] = text_content
        session['last_scan_temp_file'] = temp_path
        
        return jsonify({
            "status": "success",
            "data": result,
            "message": "Intelligence extracted successfully. Enter Review Portal."
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": f"Ingestion Failure: {str(e)}"}), 500

@profile_bp.route('/api/confirm_save_doc', methods=['POST'])
@login_required
def confirm_save_doc():
    """ 
    Scan-Before-Store Stage 2: Controlled Persistence
    Saves verified data and (optionally) the physical file.
    """
    data = request.json
    save_file = data.get('save_file', False)
    verified_data = data.get('verified_data', {})
    doc_type = data.get('doc_type', 'Generic Document')
    
    if not verified_data:
        return jsonify({"status": "error", "message": "No data found for confirmation."}), 400

    try:
        from models import db, Document
        import os
        
        # Update User Demographics if fields were edited in preview
        current_user.name = verified_data.get('name', current_user.name)
        current_user.phone = verified_data.get('phone', current_user.phone)
        current_user.address = verified_data.get('address', current_user.address)
        # Handle DOB if existing (may need model update if not exists, but assuming it's in preferences for now)
        
        # 2. Store structured data in preferences for Gemini context
        text_payload = session.get('last_scan_text', '')
        current_user.preferences = (current_user.preferences or "") + f"\n\n--- [{doc_type} Context] ---\n{text_payload}"
        
        filename_for_db = None
        temp_path = session.get('last_scan_temp_file')

        # Handle optional file saving
        if save_file and temp_path and os.path.exists(temp_path):
            user_vault = f"User_{current_user.id}_Vault"
            vault_dir = os.path.join('static', 'uploads', 'documents', user_vault)
            os.makedirs(vault_dir, exist_ok=True)
            
            final_filename = os.path.basename(temp_path).replace('temp_', '')
            final_path = os.path.join(vault_dir, final_filename)
            
            import shutil
            shutil.move(temp_path, final_path)
            filename_for_db = f"{user_vault}/{final_filename}"
        elif temp_path and os.path.exists(temp_path):
            # User opted NOT to save physical file, purge it
            os.remove(temp_path)

        # Save structured document entity
        new_doc = Document(
            user_id=current_user.id,
            doc_type=doc_type,
            filename=filename_for_db if filename_for_db else "[LINKED_DATA_ONLY]",
            extracted_text=text_payload
        )
        db.session.add(new_doc)
        db.session.commit()
        
        # Clear Memory
        session.pop('last_scan_result', None)
        session.pop('last_scan_text', None)
        session.pop('last_scan_temp_file', None)
        
        return jsonify({"status": "success", "message": "Intelligence archived in secure vault."})
        
    except Exception as e:
        return jsonify({"status": "error", "message": f"Persistence Failure: {str(e)}"}), 500

@profile_bp.route('/api/cancel_ingestion', methods=['POST'])
@login_required
def cancel_ingestion():
    """ Wipes session memory and deletes temp buffered files """
    import os
    temp_path = session.get('last_scan_temp_file')
    if temp_path and os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except:
            pass
            
    session.pop('last_scan_result', None)
    session.pop('last_scan_text', None)
    session.pop('last_scan_temp_file', None)
    
    return jsonify({"status": "success", "message": "Memory purged."})


@profile_bp.route('/api/delete_doc/<int:doc_id>', methods=['POST'])
@login_required
def delete_doc(doc_id):
    from models import db, Document
    import os
    
    doc = Document.query.get_or_404(doc_id)
    if doc.user_id != current_user.id:
        flash("Unauthorized modification request.", "danger")
        return redirect(url_for('core.index'))
        
    # Wipe the physical binary file off the host system disk securely
    if doc.filename:
        filepath = os.path.join('static', 'uploads', 'documents', doc.filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"File teardown warning: {e}")
                
    # Destruct the SQL entity
    db.session.delete(doc)
    db.session.commit()
    
    # Surgically scrub the deleted document's extracted intelligence out of the user's AI vault prompt
    remaining_docs = Document.query.filter_by(user_id=current_user.id).all()
    scrubbed_context = ""
    for r_doc in remaining_docs:
        scrubbed_context += f"\n\n--- [{r_doc.doc_type} Context] ---\n{r_doc.extracted_text}"
        
    current_user.preferences = scrubbed_context.strip()
    db.session.commit()
    
    flash("Identity document completely wiped from secure vault.", "success")
    return redirect(url_for('core.index'))

