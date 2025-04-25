from flask import request, jsonify
from api import api_bp
from xml_parser import parse_xml_file
from db import db, TestReport, Measurement
from config import Config
from utils import log_error
import os

@api_bp.route('/upload-xml', methods=['POST'])
def upload_xml():
    """Uploads an XML file and parses it."""
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    if not file.filename.lower().endswith('.xml'):
        return jsonify({'message': 'Invalid file type. Only XML files are allowed.'}), 400

    try:
        filename = file.filename
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)

        parsed_data = parse_xml_file(filepath)

        if parsed_data:
            # Example: Save data to the database
            # test_report = TestReport(**parsed_data['filename_info'])
            # db.session.add(test_report)
            # db.session.commit()

            return jsonify({'message': 'File uploaded and parsed successfully'}), 200
        else:
            return jsonify({'message': 'Error parsing XML file'}), 500

    except Exception as e:
        log_error("Error uploading and parsing XML", e)
        return jsonify({'message': f'An error occurred: {str(e)}'}), 500