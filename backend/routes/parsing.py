from flask import Blueprint, request, jsonify, session
from flask_login import current_user
from parsing_engine import parse_text, parse_pdf, parse_url, parse_image

parsing_bp = Blueprint('parsing', __name__)

@parsing_bp.route('/parse-text', methods=['POST'])
def api_parse_text():
    if not current_user.is_authenticated:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    text = data.get('text', '')
    result = parse_text(text)
    
    # Store parsed context in temporary secure session memory only (Rule 6)
    session['active_parsed_memory'] = result
    
    return jsonify(result)

@parsing_bp.route('/parse-url', methods=['POST'])
def api_parse_url():
    if not current_user.is_authenticated:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    url = data.get('url', '')
    result = parse_url(url)
    
    # Temporary memory persistence
    session['active_parsed_memory'] = result
    
    return jsonify(result)

@parsing_bp.route('/parse-pdf', methods=['POST'])
def api_parse_pdf():
    if not current_user.is_authenticated:
        return jsonify({"error": "Unauthorized"}), 401
        
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file and file.filename.lower().endswith('.pdf'):
        result = parse_pdf(file.stream)
        session['active_parsed_memory'] = result
        return jsonify(result)
        
    return jsonify({"error": "Invalid file type. Must be PDF."}), 400

@parsing_bp.route('/parse-image', methods=['POST'])
def api_parse_image():
    if not current_user.is_authenticated:
        return jsonify({"error": "Unauthorized"}), 401
        
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.heic')):
        result = parse_image(file.stream)
        if result:
            session['active_parsed_memory'] = result
            return jsonify(result)
        else:
            return jsonify({"error": "OCR extraction failed. Image quality too low."}), 500
            
    return jsonify({"error": "Invalid file type. Must be Image."}), 400

@parsing_bp.route('/update-memory', methods=['POST'])
def api_update_memory():
    """ Allows the frontend to manually overwrite the NLP results before triggering autofill """
    if not current_user.is_authenticated:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    session['active_parsed_memory'] = data
    return jsonify({"status": "success", "memory": data})
