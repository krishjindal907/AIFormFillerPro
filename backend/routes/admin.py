import os
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from models import db, User, Document, FormAnalysis, Feedback, UrlScan

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/', methods=['GET', 'POST'])
def index():
    is_admin = session.get('is_admin', False)
    
    if request.method == 'POST':
        if 'login' in request.form:
            password = request.form.get('password')
            admin_pass = os.environ.get('ADMIN_PASSWORD', 'admin123')
            if password == admin_pass:
                session['is_admin'] = True
                flash("Admin Access Granted.", "success")
            else:
                flash("Invalid admin password.", "danger")
            return redirect(url_for('admin.index'))
            
    if not is_admin:
        return render_template('admin.html', is_admin=False)
        
    users = User.query.all()
    users_data = []
    
    global_stats = {
        'docs': Document.query.count(),
        'forms': FormAnalysis.query.count(),
        'scans': UrlScan.query.count()
    }
    
    for u in users:
        doc_count = Document.query.filter_by(user_id=u.id).count()
        analysis_count = FormAnalysis.query.filter_by(user_id=u.id).count()
        users_data.append({
            'user': u,
            'doc_count': doc_count,
            'analysis_count': analysis_count
        })
        
    return render_template('admin.html', is_admin=True, users_data=users_data, total_users=len(users), global_stats=global_stats)

@admin_bp.route('/logout')
def logout():
    session.pop('is_admin', None)
    flash("Admin logged out.", "success")
    return redirect(url_for('admin.index'))

@admin_bp.route('/logs')
def logs():
    if not session.get('is_admin'):
        return redirect(url_for('admin.index'))
    
    scans = UrlScan.query.order_by(UrlScan.scanned_at.desc()).limit(20).all()
    forms = FormAnalysis.query.order_by(FormAnalysis.timestamp.desc()).limit(20).all()
    
    return render_template('admin_logs.html', is_admin=True, scans=scans, forms=forms)

@admin_bp.route('/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin.index'))
        
    user = User.query.get_or_404(user_id)
    
    UrlScan.query.filter_by(user_id=user.id).delete()
    Feedback.query.filter_by(user_id=user.id).delete()
    FormAnalysis.query.filter_by(user_id=user.id).delete()
    Document.query.filter_by(user_id=user.id).delete()
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f"User {user.email} aur unka sabhi data successfully delete ho gaya hai.", "success")
    return redirect(url_for('admin.index'))
