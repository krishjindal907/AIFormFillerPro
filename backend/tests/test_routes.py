import pytest

def test_export_profile_unauthorized(client):
    res = client.get('/api/profile/export')
    assert res.status_code == 302 # unauthenticated redirect to login

def test_export_profile_authorized(auth_client):
    res = auth_client.get('/api/profile/export')
    assert res.status_code == 200
    data = res.json
    assert data["name"] == "Test User"
    assert data["phone"] == "1234567890"

def test_edit_profile(auth_client, test_app):
    with test_app.app_context():
        # post to edit profile
        res = auth_client.post('/edit_profile', data={
            'name': 'Updated User',
            'phone': '0000000000',
            'age': '35',
            'gender': 'Male',
            'address': 'Location'
        })
        assert res.status_code == 302 # redirect back to my_profile
        
        # Verify db persistence natively
        from models import User
        user = User.query.filter_by(email="test@example.com").first()
        assert user.name == "Updated User"
        assert user.phone == "0000000000"

def test_cancel_ingestion(auth_client):
    # Set something in mock session simulating a pending upload
    with auth_client.session_transaction() as sess:
        sess['last_scan_temp_file'] = 'fake_path.tmp'
        sess['last_scan_result'] = {'name': 'junk'}
        
    res = auth_client.post('/api/cancel_ingestion')
    assert res.status_code == 200
    assert res.json['status'] == 'success'
    
    # Assert session was purged securely
    with auth_client.session_transaction() as sess:
        assert 'last_scan_temp_file' not in sess
        assert 'last_scan_result' not in sess
