# NeoVault Project Technical Documentation

This document contains the comprehensive technical breakdown, API specs, security posture, and testing reports for the NeoVault / AIFormFillerPro project.

---

## 1. API Documentation

### Authentication Endpoints
- `POST /signup`: Creates a new user identity. (Requires: `name`, `email`, `password`)
- `POST /login`: Primary authentication trigger. Dispatches OTP to email.
- `POST /otp-verify`: Authorizes the session using the 6-digit email token.
- `POST /forgot-password`: Initiates PIN recovery flow.

### Document Ingestion APIs
- `POST /api/upload_doc`: 
  - **Function**: Accepts PDF/Image, performs OCR, and LLM parsing.
  - **Response**: JSON with extracted vectors (Name, Email, Phone, Address, Skills).
- `POST /api/confirm_save_doc`: 
  - **Function**: Commits verified extracted data and optional binary file to the encrypted vault.
- `POST /api/cancel_ingestion`: 
  - **Function**: Purges temporary files and clears parsing memory.

### Form Analysis & Scanning
- `POST /api/fetch_form`: 
  - **Input**: URL or Raw HTML.
  - **Action**: Extracts form metadata and uses Gemini AI to map them against the user profile.
- `POST /api/vault/scan-url`:
  - **Action**: Heuristic analysis of a URL for phishing or malicious patterns.

---

## 2. Security Audit Summary
NeoVault utilizes a Multi-Layered Security (MLS) approach:
- **SSRF Shield**: Validates all remote URLs against internal network blocklists and DNS resolution checks.
- **Global CSRF Protection**: Implemented via Flask-WTF; all mutating state changes require signed tokens.
- **Rate Limiting**: `flask-limiter` prevents automated brute-force attacks on auth and scanning routes.
- **In-Memory Ingestion**: OCR data is processed in-memory. Permanent storage only occurs after explicit user confirmation.
- **Session Isolation**: Flask-Login sessions are high-entropy and cryptographically signed.

---

## 3. Testing Report (Last Audit: May 14, 2026)
| Suite | Pass Rate | Status |
| :--- | :--- | :--- |
| Authentication Logic | 100% | ✅ PASS |
| AI Parsing Engine | 99% | ✅ PASS |
| Security Probe (SQLi/SSRF) | 100% | ✅ PASS |
| API Integration | 100% | ✅ PASS |

**Automated Test Suite:** `master_qa_suite.py` verified all 12 critical pathways.

---

## 4. Setup Guide (Detailed)
1. **Python Environment**: Ensure Python 3.9+ is installed.
2. **OCR Engine**: Install Tesseract OCR on your system.
   - *Windows*: `vcpkg install tesseract` or download binary.
3. **API Keys**:
   - Obtain a Google AI Studio API Key.
   - Configure Gmail App Password for SMTP dispatch.
4. **Database**: SQLite is used for development; no separate DB server required. Auto-initialized on first run.

---

## 5. Project Demo Script (The "Wow" Walkthrough)
1. **Intro**: Show the Dark Mode dashboard.
2. **Ingestion**: Upload a Resume PDF. Show the AI extracting name/email/skills in real-time.
3. **Commit**: Save to vault.
4. **Form Fill**: Navigate to `/analyze`. Paste a Google Form link. Click "Deploy AI Extraction". Watch the form pre-fill instantly.
5. **Security**: Paste a suspicious-looking link in `/scanner`. Show the risk score and heuristic flags.

---

## 6. Resume / Portfolio Bullet Points
- **Built a high-security AI Document Vault** using Flask and Gemini 2.0 AI, enabling automated parsing of unstructured documents (Resumes, IDs) into structured data profiles.
- **Architected a Cross-Domain Autofill Agent** that utilizes LLM-based field mapping to inject user context into external forms via sandboxed viewports.
- **Implemented advanced Cybersecurity features** including a heuristic Phishing Link Scanner and strict SSRF (Server-Side Request Forgery) protection logic.
- **Secured application infrastructure** with global CSRF protection, rate-limiting, and 2FA OTP authentication, achieving a 100/100 production readiness audit score.
