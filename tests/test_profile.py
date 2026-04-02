import pytest
import io
import json
from models import Document, db

def test_upload_doc_no_file(auth_client):
    res = auth_client.post('/api/upload_doc')
    assert res.status_code == 400

def test_upload_doc_text_file(auth_client):
    # Simulate a text document upload
    data = {'document': (io.BytesIO(b"Name: Alice Johnson\nEmail: alice@example.com\nDOB: 01/01/1990"), 'test.txt')}
    res = auth_client.post('/api/upload_doc', data=data, content_type='multipart/form-data')
    assert res.status_code == 200
    assert res.json['status'] == 'success'
    
    with auth_client.session_transaction() as sess:
        assert 'last_scan_result' in sess
        assert sess['last_scan_result']['name'] == 'Alice Johnson'

def test_confirm_save_doc(auth_client, test_app):
    # First, stage a file
    with auth_client.session_transaction() as sess:
        sess['last_scan_text'] = "Dummy Scanned Text"
        sess['last_scan_result'] = {"name": "Bob"}
        sess['last_scan_temp_file'] = "dummy_temp.txt"
        
    res = auth_client.post('/api/confirm_save_doc', json={
        "save_file": False,
        "verified_data": {"name": "Bob", "phone": "9999999999"},
        "doc_type": "Resume"
    })
    
    assert res.status_code == 200
    
    with test_app.app_context():
        from models import User, Document
        user = User.query.filter_by(email="test@example.com").first()
        assert user.phone == "9999999999"
        
        doc = Document.query.filter_by(user_id=user.id).first()
        assert doc is not None
        assert doc.doc_type == "Resume"

def test_delete_doc(auth_client, test_app):
    with test_app.app_context():
        from models import User, Document
        user = User.query.filter_by(email="test@example.com").first()
        doc = Document(user_id=user.id, doc_type="ID", filename=None, extracted_text="test")
        db.session.add(doc)
        db.session.commit()
        doc_id = doc.id
        
    res = auth_client.post(f'/api/delete_doc/{doc_id}')
    assert res.status_code == 302 # Redirect back to dashboard
    
    with test_app.app_context():
        from models import Document
        assert Document.query.get(doc_id) is None
