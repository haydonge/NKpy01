from flask import jsonify, request
from api import api_bp
from db import TestReport, db

@api_bp.route('/reports', methods=['GET'])
def get_reports():
    """Gets all test reports with optional filtering and pagination.
    支持result筛选，所有非'Pass'都归为'Fail'。"""
    limit = request.args.get('limit', default=100, type=int)
    offset = request.args.get('offset', default=0, type=int)
    result_filter = request.args.get('result', default=None, type=str)

    reports = TestReport.query.offset(offset).limit(limit).all()
    report_list = []
    for report in reports:
        r = report.to_dict()
        # 只要不是'Pass'都归为'Fail'
        normalized_result = 'Pass' if str(r.get('result', '')).strip().lower() == 'pass' else 'Fail'
        r['normalized_result'] = normalized_result
        report_list.append(r)

    # 前端传result=Pass或result=Fail时，后端只返回对应归类
    if result_filter:
        filter_val = result_filter.strip().lower()
        if filter_val == 'pass':
            report_list = [r for r in report_list if r['normalized_result'] == 'Pass']
        elif filter_val == 'fail':
            report_list = [r for r in report_list if r['normalized_result'] == 'Fail']

    return jsonify(report_list)