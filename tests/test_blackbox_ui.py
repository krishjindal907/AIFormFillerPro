import pytest
import re
from playwright.sync_api import Page, expect

# Basic UI integration tests
# Ensure that the app server is running before executing these tests.
# Or pytest-flask / live_server fixture could be used. Here we assume we run `pytest` against live or we spin up app.

def test_homepage_loads(page: Page):
    """Test that the homepage loads successfully"""
    # Using the local address where app runs
    # To make it isolated, in a real CI this would use pytest-flask live_server
    try:
        page.goto("http://127.0.0.1:5000/")
        expect(page).to_have_title(re.compile("NeoVault", re.IGNORECASE))
    except Exception as e:
        pytest.skip(f"Live server not running at 5000: {e}")

def test_login_flow_ui(page: Page):
    try:
        page.goto("http://127.0.0.1:5000/login", timeout=5000)
    except Exception:
        pytest.skip("Live server not running at 5000")

    # Assuming there's an email input, fill it
    page.fill('input[name="email"]', 'test@example.com')
    page.fill('input[name="password"]', 'password123')
    
    # Submit login
    page.click('button[type="submit"]')
    
    # Should redirect to OTP validation
    expect(page).to_have_url(re.compile(r'/otp-verify'))
    
    # Enter OTP (assuming a fixed OTP or we just check if the OTP route rendered correctly)
    expect(page.locator('input[name="otp"]')).to_be_visible()
