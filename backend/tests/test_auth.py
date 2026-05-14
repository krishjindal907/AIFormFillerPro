import pytest

def test_login_flow(client, test_app):
    # 1. Initiate login
    res = client.post('/login', data={'email': 'test@example.com', 'password': 'password123'})
    assert res.status_code == 302
    assert '/otp-verify' in res.location

    # 2. Extract OTP from session
    with client.session_transaction() as sess:
        otp = sess.get('login_otp')
        assert otp is not None
        
    # 3. Verify OTP
    res_otp = client.post('/otp-verify', data={'otp': otp})
    assert res_otp.status_code == 302
    # Should redirect to index or core dashboard
    assert '/' in res_otp.location

def test_login_invalid(client):
    res = client.post('/login', data={'email': 'test@example.com', 'password': 'wrong'})
    assert res.status_code == 200 # rerenders page with flash
    assert b'unsuccessful' in res.data.lower() or b'invalid' in res.data.lower()

def test_signup_flow(client, test_app):
    res = client.post('/signup', data={
        'name': 'New User',
        'email': 'new2@test.com',
        'password': 'newpassword123'
    })
    
    assert res.status_code == 302
    assert '/otp-verify' in res.location
    
    with client.session_transaction() as sess:
        otp = sess.get('login_otp')
    
    res_otp = client.post('/otp-verify', data={'otp': otp})
    assert res_otp.status_code == 302

def test_logout(auth_client):
    res = auth_client.get('/logout')
    assert res.status_code == 302
    assert '/login' in res.location
