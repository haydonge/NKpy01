from flask import jsonify, request
from api import api_bp
from db import Measurement, db

@api_bp.route('/measurements', methods=['GET'])
def get_measurements():
    """Gets all measurements with optional filtering and pagination."""
    limit = request.args.get('limit', default=100, type=int)
    offset = request.args.get('offset', default=0, type=int)

    measurements = Measurement.query.limit(limit).offset(offset).all()
    measurement_list = [measurement.to_dict() for measurement in measurements]

    return jsonify(measurement_list)