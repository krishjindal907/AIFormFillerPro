<div align="center">
  
# ⚡ NeoVault Intelligence Platform
**An advanced, ultra-secure, AI-driven Personal Document & Autofill Architecture.**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.x-lightgrey.svg)](https://flask.palletsprojects.com/)
[![SQLite3](https://img.shields.io/badge/Database-SQLite3-green.svg)](https://www.sqlite.org/index.html)
[![AI](https://img.shields.io/badge/Engine-Google_Gemini-orange.svg)](https://deepmind.google/technologies/gemini/)

</div>

---

## 🚀 System Architecture Overview

NeoVault is a high-fidelity document storage and intelligence suite engineered to securely hold personal credentials while utilizing Google's advanced **Gemini LLM** to instantaneously scan and auto-fill complex web forms via physical URL extraction.

The platform was built with a fanatical focus on **Premium SaaS Aesthetics**, featuring deep neon-glow glassmorphism, mathematical hardware telemetry algorithms, and enterprise-grade security protocols.

### 🛡️ Core Capabilities

- **Mathematical 2FA Auth Pipeline:** True session security. All standard Logins and new identity Registrations are gated behind dynamic, cryptographically secure 6-digit OTP verification sequences dispatched natively via an asynchronous `smtplib` SSL pipeline to the user's registered email.
- **Biometric Password Recovery:** A comprehensive 3-stage password recovery gateway utilizing OTP tokens and temporary session storage to safely mutate the underlying SHA256 hashed PINs.
- **Isolated Node Storage:** All physical PDF payloads are scrubbed and written directly into dynamically generated, mathematically isolated `/User_{ID}_Vault/` server sub-directories for pristine organizational hierarchy. No more dumping files into generic folders.
- **Neural Data Parsing Engine:** A heavyweight NLP extraction layer capable of stripping structured identity arrays (Name, Phone, Email, Location, Education, Experience) from unstructured plaintext and remote URLs.
- **Computer Vision OCR:** Powered by OpenCV and Tesseract, the platform can physically "see" and extract text characters from uploaded JPG/PNG images in real-time.
- **Intelligence Assessor Modal:** An aggressively styled, dual-pane UI Terminal that renders physical document scans alongside a "Hacker-Themed CRT Matrix" text-dump, exposing exactly what the Gemini Engine has OCR extracted from the payload.
- **Global Form Interceptor:** Via the included **NeoVault Chrome Extension**, the software instantly bridges the local SQLite3 database with any live website (including complex SPA frameworks like React) to seamlessly map profile data into third-party HTML schemas.

---

## 💻 Elite Tech Stack

*   **Backend Engine:** Python 3, Flask, Werkzeug
*   **Database Matrix:** SQLAlchemy, SQLite3 (Local persistence)
*   **Vision & OCR:** OpenCV (Image Preprocessing), Tesseract OCR, PyPDF2
*   **Security Layers:** Flask-Login, Werkzeug Password Hashing (`pbkdf2:sha256`), SMTP-SSL Mail Delivery
*   **Intelligence:** `google-genai` (Gemini Flash Vectors), `BeautifulSoup4` (URL Scraping)
*   **Frontend UI:** Pure HTML5, Vanilla JavaScript, Advanced CSS3 (Glassmorphism, CSS Grid/Flexbox, Radial Gradients)
*   **Progressive Web App:** Fully installable mobile PWA architecture (`sw.js`, `manifest.json`)

---

## ⚙️ Initializing the Node (Local Deployment)

To boot up the NeoVault local testing environment, execute the following protocols:

### 1. External OCR Engine (Required for Image Scanning)
You MUST install the physical Tesseract binary on your host machine:
1. Download from: [UB-Mannheim Tesseract Releases](https://github.com/UB-Mannheim/tesseract/wiki)
2. Ensure it is installed at: `C:\Program Files\Tesseract-OCR\tesseract.exe`

### 2. Dependency Initialization
Ensure you have Python installed, then build your virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment Vectors
Create a `.env` file in the root directory and inject your highly sensitive API configurations:
```ini
# Google Gemini API Matrix Key
GEMINI_API_KEY=your_gemini_api_key_here

# Required for 2FA / Password Recovery Live Email Dispatch
MAIL_USERNAME=your_gmail_address@gmail.com
MAIL_PASSWORD=your_16_digit_google_app_password
```

### 4. Ignition
Using the custom-built Windows Bootloader:
Double click `Start_NeoVault.bat` 
*This will automatically resolve directory contexts, spin up the backend WSGI instance, and aggressively pop open your default browser to intercept the `0.0.0.0:5000` payload.*

Alternatively, run manually:
```bash
python app.py
```

---

*Engineered with precision.*
