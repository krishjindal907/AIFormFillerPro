from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
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
    if 'document' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400
        
    file = request.files['document']
    doc_type = request.form.get('doc_type', 'Generic Document')
    
    if file.filename == '':
        return jsonify({"status": "error", "message": "No file selected"}), 400
        
    text = ""
    try:
        import os
        from werkzeug.utils import secure_filename
        
        user_folder = f"User_{current_user.id}_Vault"
        secure_name = secure_filename(file.filename)
        relative_path = f"{user_folder}/{secure_name}"
        
        filepath = os.path.join('static', 'uploads', 'documents', user_folder, secure_name)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        if file.filename.lower().endswith('.pdf'):
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + " "
        else:
            text = file.read().decode('utf-8', errors='ignore')
            
        # Secure the physical file into the local OS Document Drive
        file.seek(0)
        file.save(filepath)
            
        from models import db, Document
        new_doc = Document(
            user_id=current_user.id,
            doc_type=doc_type,
            filename=relative_path,
            extracted_text=text.strip()
        )
        db.session.add(new_doc)
        
        current_user.preferences = (current_user.preferences or "") + f"\n\n--- [{doc_type} Context] ---\n{text.strip()}"
        db.session.commit()
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
        
    return jsonify({"status": "success"})


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

