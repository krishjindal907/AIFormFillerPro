import pytest
import os
from werkzeug.security import generate_password_hash
import sys

# Ensure the root project directory is in the sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app import create_app
from models import db, User

@pytest.fixture
def test_app():
    # Set environment variables for testing if necessary
    os.environ['TESTING'] = 'true'
    
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test_secret_key"
    })
    
    with app.app_context():
        db.create_all()
        
        # Seed a test user
        test_user = User(
            email="test@example.com",
            password=generate_password_hash("password123", method="pbkdf2:sha256"),
            name="Test User",
            phone="1234567890",
            age="30"
        )
        db.session.add(test_user)
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(test_app):
    """A test client for the app."""
    return test_app.test_client()

@pytest.fixture
def runner(test_app):
    """A test CLI runner for the app."""
    return test_app.test_cli_runner()

@pytest.fixture
def auth_client(client, test_app):
    """Returns a test client that is already logged in as the test user."""
    # We login as the seeded user
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    })
    # Handle the OTP verification step
    with client.session_transaction() as sess:
        otp = sess.get('login_otp')
    
    client.post('/otp-verify', data={'otp': otp})
    return client
