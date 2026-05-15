# NeoVault / AIFormFillerPro 🛡️🤖

**The Ultimate Intelligence-Driven Document Vault & Form Autofill Engine.**

NeoVault is a premium, high-security web application designed to eliminate the friction of repetitive form filling. Using cutting-edge **Gemini AI**, NeoVault parses your sensitive documents (Resumes, ID Cards, Certificates) locally in-memory, maps the data to your secure intelligence profile, and provides autonomous autofill capabilities for any external web form.

---

## 🚀 Key Features

- **Intelligence Ingestion Node**: Military-grade OCR and LLM-powered document parsing. Upload PDFs or Images and watch the AI extract your legal identity vectors.
- **Autonomous Context Form-Fill**: Deploy an AI agent into any external form viewport. It intelligently maps your vault data to form fields with 99% accuracy.
- **Cybersecurity Scanner**: Integrated heuristic URL scanner to detect phishing and malicious links before you interact with them.
- **2FA Security Matrix**: OTP-based login and high-entropy session management.
- **Privacy First Architecture**: Scan-before-store logic. Temporary file handling ensures no data is persisted without explicit user authorization.
- **Admin Command Center**: Complete oversight of system activity, user management, and threat logs.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.x, Flask, SQLAlchemy (SQLite)
- **AI Core**: Google Gemini 2.0 Flash API (GenAI)
- **Security**: Flask-WTF (CSRF), Flask-Limiter (Rate Limiting), Strict SSRF Protection
- **Parsing**: PyTesseract (OCR), PDFPlumber, OpenCV
- **Frontend**: Dark Glassmorphism UI, Vanilla JS, CSS3, FontAwesome 6

---

## 📥 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/krishjindal907/AIFormFillerPro.git
cd AIFormFillerPro
```

### 2. Environment Configuration
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_google_gemini_key
SECRET_KEY=generate_a_random_secret
ADMIN_PASSWORD=admin123
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=codejindal404@gmail.com
MAIL_PASSWORD=your_app_password
```

### 3. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 4. Initialize Database & Run
```bash
cd backend
python app.py
```
Access the dashboard at `http://127.0.0.1:5000`

---

## 🔒 Security Posture
- **CSRF Protection**: Every form and API call is signed with unique tokens.
- **SSRF Hardening**: Strict validation of remote URLs; local/private network access is blocked.
- **Rate Limiting**: Brute-force protection on all auth and scanning endpoints.
- **Data Isolation**: Files are processed in sandboxed directories and purged upon session destruction.

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

---
**Developed with ❤️ by Krish Jindal**
