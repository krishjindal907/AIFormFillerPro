import re
import cv2
import numpy as np
import pytesseract
from PIL import Image
import PyPDF2
from bs4 import BeautifulSoup
import requests
import io

# Instruct Python binding on the absolute Windows trajectory of the winged Tesseract Engine
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def parse_text(text):
    """
    Core parsing logic utilizing regex combinations and basic string extraction
    to pull structural entities from raw unstructured inputs.
    """
    if not text:
        return None
        
    # High-precision RegEx Patterns
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
    dob_pattern = r'\b(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2})\b'
    
    # Extraction Maps
    emails = re.findall(email_pattern, text)
    phones = re.findall(phone_pattern, text)
    dobs = re.findall(dob_pattern, text)
    
    # NLP keyword matching (Lightweight)
    address = None
    education = []
    experience = []
    name = None
    
    # Heuristic for Name (First 2-3 capitalized words at start of line)
    name_match = re.search(r'^([A-Z][a-z]+)\s([A-Z][a-z]+)', text, re.MULTILINE)
    if name_match:
        name = name_match.group(0)
        
    lines = text.split('\n')
    for line in lines:
        l_lower = line.lower()
        
        # Address Heuristic
        if 'address:' in l_lower or 'residence:' in l_lower or 'location:' in l_lower:
            address = line.split(':', 1)[-1].strip()
            
        # Education Heuristic
        if any(kw in l_lower for kw in ['education', 'university', 'college', 'degree', 'b.tech', 'school']):
            # Filter single word false-positives
            if len(line.split()) > 2:
                education.append(line.strip())
                
        # Experience Heuristic
        if any(kw in l_lower for kw in ['experience', 'worked at', 'engineer', 'developer', 'intern']):
            if len(line.split()) > 2:
                experience.append(line.strip())
            
    return {
        "name": name if name else None,
        "email": emails[0] if emails else None,
        "phone": phones[0] if phones else None,
        "date_of_birth": dobs[0] if dobs else None,
        "address": address,
        "education": list(set(education)), # Remove duplicates
        "experience": list(set(experience))
    }

def parse_image(file_stream):
    """ Extract text from physical image file via OpenCV preprocessing & Tesseract OCR """
    try:
        image = Image.open(file_stream)
        open_cv_image = np.array(image) 
        
        # Binarize memory buffer down to Grayscale format for Engine parsing
        if len(open_cv_image.shape) == 3 and open_cv_image.shape[2] == 3:
            gray = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2GRAY)
        elif len(open_cv_image.shape) == 3 and open_cv_image.shape[2] == 4:
            gray = cv2.cvtColor(open_cv_image, cv2.COLOR_RGBA2GRAY)
        else:
            gray = open_cv_image
            
        # Super-resolution upscale for superior OCR hit rate
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        
        # Gaussian Blur payload
        blur = cv2.GaussianBlur(gray, (5,5), 0)
        
        # Otsu's computational thresholding
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Tesseract execution over threshold bounds
        custom_config = r'--oem 3 --psm 6'
        raw_text = pytesseract.image_to_string(thresh, config=custom_config)
        
        if not raw_text.strip():
            print("OCR Vision Engine Warning: Low-fidelity image resulted in blank extraction.")
            
        return parse_text(raw_text)
    except Exception as e:
        print(f"OCR Vision Engine Fatal Error: {e}")
        return None

def parse_pdf(file_stream):
    """ Extract text layer from physical PDF binary stream and forward to parser. """
    try:
        reader = PyPDF2.PdfReader(file_stream)
        raw_text = ""
        for page in reader.pages:
            raw_text += (page.extract_text() or "") + "\n"
        return parse_text(raw_text)
    except Exception as e:
        print(f"PDF Parse Error: {e}")
        return None

def parse_url(url):
    """ Traverse a URL, scrape raw HTML text content, and forward to parser. """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Kill noise
        for script in soup(["script", "style"]):
            script.extract()
            
        text = soup.get_text(separator='\n')
        return parse_text(text)
    except Exception as e:
        print(f"URL Parse Error: {e}")
        return None
