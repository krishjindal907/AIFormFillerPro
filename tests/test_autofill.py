import pytest
from models import FormAnalysis, Feedback, db

def test_submit_feedback_valid(auth_client, test_app):
    with test_app.app_context():
        from models import User
        user = User.query.filter_by(email="test@example.com").first()
        
        # Create dummy analysis
        analysis = FormAnalysis(user_id=user.id, target_url="test", form_html_snapshot="[]", fields_detected=1, matched_fields=1)
        db.session.add(analysis)
        db.session.commit()
        analysis_id = analysis.id
        
    res = auth_client.post('/api/feedback', json={"analysis_id": analysis_id, "is_accurate": True})
    assert res.status_code == 200
    
    with test_app.app_context():
        fb = Feedback.query.filter_by(form_analysis_id=analysis_id).first()
        assert fb is not None
        assert fb.is_accurate == True

def test_submit_feedback_missing_id(auth_client):
    res = auth_client.post('/api/feedback', json={"is_accurate": True})
    assert res.status_code == 400
