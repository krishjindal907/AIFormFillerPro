import pytest
from flask import session
import json
from models import FormAnalysis

def test_analyze_view_unauthorized(client):
    res = client.get('/analyze')
    assert res.status_code == 302 # unauthenticated redirect
    
def test_analyze_view_authorized(auth_client):
    res = auth_client.get('/analyze')
    assert res.status_code == 200

def test_fetch_form_html_content(auth_client, test_app):
    with test_app.app_context():
        html_content = """
        <form>
            <label for="name">Full Name</label>
            <input type="text" id="name" name="name" />
        </form>
        """
        res = auth_client.post('/api/fetch_form', data={'html_content': html_content})
        assert res.status_code == 200
        data = res.json
        assert data["status"] == "success"
        assert len(data["fields"]) == 1
        assert data["fields"][0]["name"] == "name"
        assert data["fields"][0]["match_key"] == "name"

def test_fetch_form_no_data(auth_client):
    res = auth_client.post('/api/fetch_form', data={})
    assert res.status_code == 400

def test_extension_analyze_valid(auth_client):
    # test extension api
    req_data = {
        "fields": [{"name": "phone", "label": "Phone Number", "type": "text"}],
        "url": "http://example.com"
    }
    res = auth_client.post('/api/extension/analyze', json=req_data)
    assert res.status_code == 200
    data = res.json
    assert data["status"] == "success"
    # phone belongs to test_user from conftest
    assert "phone" in data["ai_mapping"]
    assert data["ai_mapping"]["phone"] == "1234567890"

def test_extension_analyze_options(client):
    res = client.options('/api/extension/analyze')
    assert res.status_code == 200
