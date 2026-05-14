import os
import json
import re
from urllib.parse import urlparse
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from models import db, UrlScan
from datetime import datetime
from limiter import limiter

scanner_bp = Blueprint('scanner', __name__)

# Load blocklist
BLOCKLIST_FILE = os.path.join(os.path.dirname(__file__), '..', 'blocklist.json')
WHITELIST = ['google.com', 'github.com', 'microsoft.com', 'apple.com', 'amazon.com']
URL_SHORTENERS = ['bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly']
SUSPICIOUS_KEYWORDS = ['login', 'verify', 'secure', 'update', 'account', 'auth', 'signin', 'support-alert']

def load_blocklist():
    try:
        with open(BLOCKLIST_FILE, 'r') as f:
            data = json.load(f)
            return data.get('phishing_domains', [])
    except Exception:
        return []

def get_base_domain(hostname):
    parts = hostname.split('.')
    if len(parts) > 2:
        return '.'.join(parts[-2:])
    return hostname

@scanner_bp.route('/scanner', methods=['GET'])
@login_required
def scanner_ui():
    history = UrlScan.query.filter_by(user_id=current_user.id).order_by(UrlScan.scanned_at.desc()).limit(10).all()
    # history flags will be handled in UI (parsing JSON)
    return render_template('scanner.html', history=history)

@scanner_bp.route('/api/vault/scan-url', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def scan_url():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "No url provided"}), 400

    raw_url = data['url'].strip()
    
    # Validation
    parsed = urlparse(raw_url)
    if not parsed.scheme or not parsed.netloc:
        if raw_url.startswith('http'):
            return jsonify({"error": "Malformed URL"}), 400
        # Attempt to auto-correct scheme
        raw_url = 'http://' + raw_url
        parsed = urlparse(raw_url)
        if not parsed.netloc:
            return jsonify({"error": "Malformed URL"}), 400

    hostname = parsed.netloc.lower()
    base_domain = get_base_domain(hostname)
    path = parsed.path.lower()
    
    flags = []
    risk_score = 0
    is_safe = True
    
    # 1. Whitelist Check
    if base_domain in WHITELIST or hostname in WHITELIST:
        # Instant safe
        risk_score = 0
        risk_level = "safe"
        is_safe = True
        return save_and_respond(raw_url, is_safe, risk_score, risk_level, ["Whitelisted domain"])
        
    # 2. Blacklist Check
    blocklist = load_blocklist()
    if hostname in blocklist or base_domain in blocklist:
        return save_and_respond(raw_url, False, 100, "dangerous", ["Known phishing domain!"])

    # 3. Heuristics
    
    # IP Address as Hostname
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", hostname):
        flags.append({"icon": "🔴", "text": "IP address used instead of domain"})
        risk_score += 80

    # Excessive subdomains
    if len(hostname.split('.')) > 3:
        flags.append({"icon": "🟡", "text": "Multiple subdomains detected"})
        risk_score += 20
        
    # URL Shorteners
    if base_domain in URL_SHORTENERS:
        flags.append({"icon": "🟡", "text": "URL shortener detected (destination hidden)"})
        risk_score += 40
        
    # Suspicious keywords
    for p in SUSPICIOUS_KEYWORDS:
        if p in path or p in hostname:
            flags.append({"icon": "🟡", "text": f"Suspicious keyword found: '{p}'"})
            risk_score += 30
            break
            
    # Long URL over 100 chars
    if len(raw_url) > 100:
        flags.append({"icon": "🟡", "text": "Extremely long URL"})
        risk_score += 15
        
    # Typosquatting / brand spoofing (basic levenshtein equivalent logic could go here, for now rely on simple match)
    if 'google' in hostname and base_domain != 'google.com':
        flags.append({"icon": "🔴", "text": "Spoofed 'Google' domain"})
        risk_score += 60
    if 'paypal' in hostname and base_domain != 'paypal.com':
        flags.append({"icon": "🔴", "text": "Spoofed 'PayPal' domain"})
        risk_score += 60
        
    # Cap score
    risk_score = min(risk_score, 100)
    
    # Determine level
    if risk_score == 0:
        risk_level = "safe"
        flags.append({"icon": "🟢", "text": "No threats detected"})
    elif risk_score < 50:
        risk_level = "suspicious"
        is_safe = False
    else:
        risk_level = "dangerous"
        is_safe = False
        
    return save_and_respond(raw_url, is_safe, risk_score, risk_level, [f['text'] for f in flags])

@scanner_bp.route('/api/vault/scan-urls-batch', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def scan_urls_batch():
    data = request.get_json()
    urls = data.get('urls', [])
    if not urls:
        return jsonify({"results": {}})
    
    blocklist = load_blocklist()
    results = {}
    
    for url in urls[:100]: # max 100 processed silently
        parsed = urlparse(url)
        hostname = parsed.netloc.lower()
        base_domain = get_base_domain(hostname)
        
        # very lightweight scan for fast passive indicators
        if base_domain in WHITELIST:
            results[url] = "safe"
        elif hostname in blocklist or base_domain in blocklist:
            results[url] = "dangerous"
        elif re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", hostname):
            results[url] = "dangerous"
        elif base_domain in URL_SHORTENERS:
            results[url] = "suspicious"
        else:
            path = parsed.path.lower()
            suspicious = False
            for p in SUSPICIOUS_KEYWORDS:
                if p in path or p in hostname:
                    suspicious = True
                    break
            
            if suspicious:
                results[url] = "suspicious"
            else:
                results[url] = "safe"
                
    return jsonify({"results": results})


def save_and_respond(url, is_safe, risk_score, risk_level, flags):
    scan = UrlScan(
        user_id=current_user.id,
        url=url,
        risk_level=risk_level,
        flags=json.dumps(flags)
    )
    db.session.add(scan)
    db.session.commit()
    
    return jsonify({
        "url": url,
        "is_safe": is_safe,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "flags": flags,
        "scanned_at": scan.scanned_at.isoformat()
    })
