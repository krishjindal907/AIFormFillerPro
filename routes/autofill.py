from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Feedback

autofill_bp = Blueprint('autofill', __name__)

@autofill_bp.route('/api/feedback', methods=['POST'])
@login_required
def submit_feedback():
    data = request.get_json()
    analysis_id = data.get('analysis_id')
    is_accurate = data.get('is_accurate', True)
    
    if analysis_id:
        fb = Feedback(user_id=current_user.id, form_analysis_id=analysis_id, is_accurate=is_accurate)
        db.session.add(fb)
        db.session.commit()
        return jsonify({"status": "feedback saved"})
    return jsonify({"error": "missing analysis_id"}), 400
