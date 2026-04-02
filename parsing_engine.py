import re
import os
import cv2
import numpy as np
import pytesseract
from PIL import Image
import PyPDF2
from bs4 import BeautifulSoup
import requests
# Tesseract path - Windows ke liye
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def _gemini_enhance(raw_text, basic_result):
    """
    Gemini AI se raw text ko deeply parse karo.
    Basic regex result ko fallback ke roop mein use karo.
    """
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key or not raw_text.strip():
        return basic_result

    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=gemini_key)

        prompt = f"""
You are an expert resume and document parser. Extract structured information from the following document text.

Document Text:
--------------
{raw_text[:4000]}
--------------

Return ONLY a valid JSON object with these exact keys (use empty string "" if not found):
{{
  "name": "full name of the person",
  "email": "email address",
  "phone": "phone number",
  "date_of_birth": "date of birth if mentioned",
  "address": "full address or city/location",
  "education": ["list of education entries"],
  "experience": ["list of work experience entries"],
  "skills": ["list of technical and soft skills"],
  "gender": "",
  "profession": "current job title or profession"
}}

Rules:
- For name: Extract the person's full name, usually at the top of the document
- For skills: Extract ALL skills mentioned (programming languages, tools, frameworks, soft skills)
- For education: Include degree, institution, year
- For experience: Include company name, role, duration
- Return ONLY the JSON, no explanation
"""

        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        import json
        parsed = json.loads(response.text)

        # Gemini result ko basic result se merge karo
        # Gemini values ko priority do, lekin empty ho to basic use karo
        final = {
            "name": parsed.get("name") or basic_result.get("name", ""),
            "email": parsed.get("email") or basic_result.get("email", ""),
            "phone": parsed.get("phone") or basic_result.get("phone", ""),
            "date_of_birth": parsed.get("date_of_birth") or basic_result.get("date_of_birth", ""),
            "address": parsed.get("address") or basic_result.get("address", ""),
            "education": parsed.get("education") or basic_result.get("education", []),
            "experience": parsed.get("experience") or basic_result.get("experience", []),
            "skills": parsed.get("skills") or basic_result.get("skills", []),
            "gender": parsed.get("gender") or basic_result.get("gender", ""),
            "profession": parsed.get("profession") or basic_result.get("profession", ""),
        }
        return final

    except Exception as e:
        print(f"Gemini Parse Enhancement Error: {e}")
        return basic_result


def parse_text(text):
    """
    Core parsing — regex + heuristics se basic extraction,
    phir Gemini AI se enhance karo.
    """
    if not text:
        return None

    # --- RegEx Patterns ---
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}'
    dob_pattern = r'\b(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2})\b'

    emails = re.findall(email_pattern, text)
    phones = re.findall(phone_pattern, text)
    dobs = re.findall(dob_pattern, text)

    # --- Name Extraction (Improved) ---
    # Strategy 1: Pehli non-empty line jo sirf capitalized words ho
    name = None
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    for line in lines[:8]:  # pehli 8 lines mein dhundho
        # Skip karo agar line mein email ya phone ho
        if '@' in line or re.search(phone_pattern, line):
            continue
        # Skip karo agar line bahut lambi ho (heading nahi hogi)
        if len(line) > 60:
            continue
        # 2-4 capitalized words match karo
        name_match = re.match(r'^([A-Z][a-zA-Z]+)(?:\s+[A-Z][a-zA-Z]+){1,3}$', line)
        if name_match:
            name = line
            break

    # Strategy 2: "Name:" ke baad dhundho
    if not name:
        name_colon = re.search(r'(?:name|full name)\s*[:\-]\s*(.+)', text, re.IGNORECASE)
        if name_colon:
            name = name_colon.group(1).strip()

    # Strategy 3: Original regex fallback
    if not name:
        name_match = re.search(r'^([A-Z][a-z]+)\s([A-Z][a-z]+)', text, re.MULTILINE)
        if name_match:
            name = name_match.group(0)

    # --- Skills Extraction (NEW - pehle missing tha) ---
    skills = []
    skill_keywords = [
        'python', 'java', 'javascript', 'js', 'react', 'node', 'flask', 'django',
        'html', 'css', 'sql', 'mysql', 'postgresql', 'mongodb', 'redis',
        'git', 'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'linux',
        'machine learning', 'deep learning', 'ai', 'nlp', 'tensorflow', 'pytorch',
        'c++', 'c#', 'php', 'ruby', 'swift', 'kotlin', 'typescript',
        'rest', 'api', 'graphql', 'microservices', 'agile', 'scrum',
        'communication', 'leadership', 'teamwork', 'problem solving'
    ]

    # Skills section dhundho
    in_skills_section = False
    skill_section_lines = []
    for line in lines:
        l_lower = line.lower()
        # Skills section ki beginning detect karo
        if re.search(r'^skills?\s*[:\-]?$|^technical skills?\s*[:\-]?$|^core competencies', l_lower):
            in_skills_section = True
            continue
        # Nayi section shuru ho gayi to skills section band karo
        if in_skills_section and re.search(r'^(experience|education|projects|work history|employment)', l_lower):
            in_skills_section = False
        if in_skills_section and line:
            skill_section_lines.append(line)

    # Skills section se extract karo
    if skill_section_lines:
        skills_text = ' '.join(skill_section_lines)
        # Comma/bullet separated skills
        extracted = re.split(r'[,•|/\n]+', skills_text)
        skills = [s.strip() for s in extracted if 2 < len(s.strip()) < 50]

    # Agar section nahi mila to pure text mein keywords dhundho
    if not skills:
        for kw in skill_keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text, re.IGNORECASE):
                skills.append(kw)

    # --- Address Extraction (Improved) ---
    address = None
    for line in lines:
        l_lower = line.lower()
        if any(kw in l_lower for kw in ['address:', 'residence:', 'location:', 'city:', 'pincode']):
            address = line.split(':', 1)[-1].strip()
            break
        # Indian address patterns (Pincode 6 digits)
        if re.search(r'\b\d{6}\b', line):
            address = line.strip()
            break

    # --- Education Extraction ---
    education = []
    for line in lines:
        l_lower = line.lower()
        if any(kw in l_lower for kw in [
            'education', 'university', 'college', 'degree', 'b.tech', 'b.e',
            'b.sc', 'm.tech', 'mba', 'school', 'institute', 'batch', 'cgpa', 'gpa'
        ]):
            if len(line.split()) > 2:
                education.append(line.strip())

    # --- Experience Extraction ---
    experience = []
    for line in lines:
        l_lower = line.lower()
        if any(kw in l_lower for kw in [
            'experience', 'worked at', 'engineer', 'developer', 'intern',
            'manager', 'analyst', 'designer', 'architect', 'consultant',
            'present', 'jan', 'feb', 'mar', 'apr', 'may', 'jun',
            'jul', 'aug', 'sep', 'oct', 'nov', 'dec'
        ]):
            if len(line.split()) > 2:
                experience.append(line.strip())

    # --- Profession Extraction ---
    profession = ""
    profession_patterns = [
        r'(?:profession|designation|title|role|position)\s*[:\-]\s*(.+)',
        r'^\s*(Software Engineer|Web Developer|Data Scientist|Full Stack|Frontend|Backend|DevOps|ML Engineer|Product Manager).*',
    ]
    for pattern in profession_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            profession = match.group(1).strip()
            break

    basic_result = {
        "name": name if name else "",
        "email": emails[0] if emails else "",
        "phone": phones[0] if phones else "",
        "date_of_birth": dobs[0] if dobs else "",
        "address": address if address else "",
        "education": list(dict.fromkeys(education)) if education else [],
        "experience": list(dict.fromkeys(experience)) if experience else [],
        "skills": list(dict.fromkeys(skills)) if skills else [],
        "gender": "",
        "profession": profession,
    }

    # Gemini band hai — seedha basic result return karo
    return basic_result


def parse_image(file_stream):
    """
    OpenCV preprocessing + Tesseract OCR se image parse karo.
    Multiple preprocessing strategies try karo better accuracy ke liye.
    """
    try:
        image = Image.open(file_stream)

        # RGBA to RGB convert karo agar zaroorat ho
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')

        open_cv_image = np.array(image)
        gray = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2GRAY)

        # Super-resolution upscale
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

        # Strategy 1: Otsu's thresholding
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh1 = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Strategy 2: Adaptive thresholding (handwritten text ke liye better)
        thresh2 = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

        custom_config = r'--oem 3 --psm 6'

        # Dono strategies try karo, jyada text wala use karo
        text1 = pytesseract.image_to_string(thresh1, config=custom_config)
        text2 = pytesseract.image_to_string(thresh2, config=custom_config)

        raw_text = text1 if len(text1) >= len(text2) else text2

        if not raw_text.strip():
            print("OCR Warning: Low-fidelity image. Trying original grayscale...")
            raw_text = pytesseract.image_to_string(gray, config=custom_config)

        if not raw_text.strip():
            return None

        return parse_text(raw_text)

    except Exception as e:
        print(f"OCR Vision Engine Fatal Error: {e}")
        return None


def parse_pdf(file_stream):
    """
    PDF se text extract karo. Pehle text layer try karo,
    agar blank ho to error return karo (scanned PDF image-based hogi).
    """
    try:
        reader = PyPDF2.PdfReader(file_stream)
        raw_text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                raw_text += extracted + "\n"

        if not raw_text.strip():
            print("PDF Parse Warning: No text layer found. PDF might be scanned/image-based.")
            return {
                "name": "", "email": "", "phone": "", "date_of_birth": "",
                "address": "", "education": [], "experience": [],
                "skills": [], "gender": "", "profession": "",
                "_warning": "Scanned PDF detected. Please upload as image for OCR."
            }

        return parse_text(raw_text)

    except Exception as e:
        print(f"PDF Parse Error: {e}")
        return None


def parse_url(url):
    """URL scrape karo aur text parse karo."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Noise remove karo
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.extract()

        text = soup.get_text(separator='\n')
        # Multiple spaces/newlines clean karo
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)

        return parse_text(text)

    except Exception as e:
        print(f"URL Parse Error: {e}")
        return None