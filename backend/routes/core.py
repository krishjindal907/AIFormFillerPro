from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import FormAnalysis, Document

core_bp = Blueprint('core', __name__)

@core_bp.route('/')
@login_required
def index():
    latest_analysis = FormAnalysis.query.filter_by(user_id=current_user.id).order_by(FormAnalysis.id.desc()).first()
    
    docs = Document.query.filter_by(user_id=current_user.id).order_by(Document.uploaded_at.desc()).all()
    history = FormAnalysis.query.filter_by(user_id=current_user.id).order_by(FormAnalysis.timestamp.desc()).limit(10).all()
    return render_template('index.html', docs=docs, history=history, latest=latest_analysis)

@core_bp.route('/api/delete_history/<int:history_id>', methods=['POST'])
@login_required
def delete_history(history_id):
    from models import db, FormAnalysis
    from flask import redirect, url_for
    record = FormAnalysis.query.get_or_404(history_id)
    if record.user_id == current_user.id:
        db.session.delete(record)
        db.session.commit()
    return redirect(url_for('core.index'))

@core_bp.route('/mock')
def mock():
    return render_template('mock_application.html')
