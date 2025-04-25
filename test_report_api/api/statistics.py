from flask import jsonify
from api import api_bp
from db import TestReport, Measurement, db

@api_bp.route('/statistics/results', methods=['GET'])
def get_result_statistics():
    """Gets statistics on test results."""
    results = TestReport.query.group_by(TestReport.result).count()
    return jsonify(results)

@api_bp.route('/statistics/top-fail-measurements', methods=['GET'])
def get_top_fail_measurements():
    """
    获取所有测试中失败（非pass）项目的TOP10。
    统计逻辑：
    - 只统计测量项status字段非'Pass'（不区分大小写）的记录。
    - 按name分组，统计fail数量，按数量降序取前10。
    """
    from sqlalchemy import func
    # 统计所有status非'Pass'的测量项
    results = (
        db.session.query(Measurement.name, func.count().label('fail_count'))
        .filter(func.lower(Measurement.status) != 'pass')
        .group_by(Measurement.name)
        .order_by(func.count().desc())
        .limit(10)
        .all()
    )
    data = [
        {"name": name, "fail_count": count}
        for name, count in results
    ]
    return jsonify(data)