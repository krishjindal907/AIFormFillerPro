from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models import db, FormAnalysis, Feedback, Document

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
    return """
    <html>
    <body>
    <h1>External Job Application</h1>
    <form>
        <label for="fname">Full Name</label><br><input type="text" id="fname" name="fname"><br><br>
        <label>Contact Mobile</label><br><input type="tel" name="mobile"><br><br>
        <label>Years Old</label><br><input type="number" name="age"><br><br>
        <label>Job Title / Profession</label><br><input type="text" name="job">
    </form>
    </body>
    </html>
    """
