import pytest
from parsing_engine import parse_text, _gemini_enhance
from unittest.mock import patch, MagicMock
import os

def test_parse_text_empty():
    result = parse_text("")
    assert result is None

def test_parse_text_identity_extraction():
    # Testing the RegEx logic core logic inside parsing_engine
    sample_text = """
    Alice Johnson
    alice.johnson@example.com
    +91-9876543210
    Address: 456 Cyber Hub Boulevard
    Education: M.Tech in Artificial Intelligence
    Data Scientist
    Technical Skills: Python, SQL, Machine Learning
    """
    
    # We must patch os.environ locally if we want to bypass Gemini
    with patch.dict(os.environ, clear=True):
        result = parse_text(sample_text)
        
        assert result is not None
        assert result["name"] == "Alice Johnson"
        assert "alice.johnson@example.com" in result["email"]
        assert "+91-9876543210" in result["phone"]
        assert result["address"] == "456 Cyber Hub Boulevard"
        assert result["profession"] == "Data Scientist"
        assert "python" in [s.lower() for s in result["skills"]]

def test_parse_text_stubborn_formatting():
    # Test handling of edge-case labels and formatting
    sample_text = "Name: Bob Smith\nEmail : bob.smith@work.org\nDOB: 15/08/1985\nPincode: 110001"
    
    with patch.dict(os.environ, clear=True):
        result = parse_text(sample_text)
        
        assert result["name"] == "Bob Smith"
        assert result["email"] == "bob.smith@work.org"
        assert result["date_of_birth"] == "15/08/1985"
        assert result["address"] == "110001"

def test_gemini_enhance_fallback():
    # Test that gemini returns basic_result if no API key
    with patch.dict(os.environ, clear=True):
        res = _gemini_enhance("sample text", {"name": "Basic Name"})
        assert res["name"] == "Basic Name"

import sys

@patch('parsing_engine.os.environ.get')
def test_gemini_enhance_mocked(mock_env):
    mock_env.return_value = "fake_key"
    
    mock_genai_module = MagicMock()
    mock_client_class = MagicMock()
    mock_genai_module.Client = mock_client_class
    
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.text = '{"name": "Gemini Name", "skills": ["Python"]}'
    mock_client.models.generate_content.return_value = mock_response
    
    # Mock both google and google.genai
    mock_google = MagicMock()
    mock_google.genai = mock_genai_module
    
    with patch.dict(sys.modules, {'google': mock_google, 'google.genai': mock_genai_module}):
        basic = {"name": "Basic Name", "email": "test@test.com"}
        res = _gemini_enhance("Sample document text", basic)
        
    assert res["name"] == "Gemini Name"
    assert res["skills"] == ["Python"]
    assert res["email"] == "test@test.com"
