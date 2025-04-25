import os
import sqlite3
from flask import Flask, jsonify, request, g
import xml.etree.ElementTree as ET
import re
import json
from werkzeug.utils import secure_filename
import datetime
import shutil

app = Flask(__name__)

# u6570u636eu5e93u914du7f6e
DATABASE = 'test_reports.sqlite'
UPLOAD_FOLDER = 'uploads'
XML_DIRECTORY = 'testReports'

# u786eu5b9au4e0au4f20u4e09u4e2au76eeu5f55u76eeu5f59
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(XML_DIRECTORY, exist_ok=True)

# APIu72b6u6001u7aefu70b9
@app.route('/api/status', methods=['GET'])
def get_status():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT COUNT(*) FROM test_reports')
    count = cursor.fetchone()[0]
    return jsonify({
        'status': 'u8fd0u884cu4e2d',
        'version': '1.0.0',
        'database': DATABASE,
        'report_count': count
    })

# u83b7u53d6u6240u6709u6d4bu8bd5u62a5u544a
@app.route('/api/reports', methods=['GET'])
def get_reports():
    db = get_db()
    cursor = db.cursor()
    
    # u5904u7406u67e5u8be2u53c2u6570
    limit = request.args.get('limit', default=100, type=int)
    offset = request.args.get('offset', default=0, type=int)
    serial_number = request.args.get('serial_number', default=None, type=str)
    part_number = request.args.get('part_number', default=None, type=str)
    result = request.args.get('result', default=None, type=str)
    
    # u6784u5efaSQLu67e5u8be2
    query = 'SELECT * FROM test_reports WHERE 1=1'
    params = []
    
    if serial_number:
        query += ' AND serial_number LIKE ?'
        params.append(f'%{serial_number}%')
    
    if part_number:
        query += ' AND part_number LIKE ?'
        params.append(f'%{part_number}%')
    
    if result:
        query += ' AND result = ?'
        params.append(result)
    
    query += ' ORDER BY id DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    reports = cursor.fetchall()
    
    # u8f6cu6362u4e3aJSON
    result = []
    for row in reports:
        item = {}
        for idx, col in enumerate(cursor.description):
            item[col[0]] = row[idx]
        result.append(item)
    
    return jsonify(result)

# u83b7u53d6u5355u4e2au62a5u544au8be6u60c5
@app.route('/api/reports/<int:report_id>', methods=['GET'])
def get_report_detail(report_id):
    db = get_db()
    cursor = db.cursor()
    
    # u83b7u53d6u62a5u544au57fau672cu4fe1u606f
    cursor.execute('SELECT * FROM test_reports WHERE id = ?', (report_id,))
    report = cursor.fetchone()
    
    if not report:
        return jsonify({'error': 'u62a5u544au4e0du5b58u5728'}), 404
    
    # u5c06u884cu8f6cu6362u4e3au5b57u5178
    report_dict = {}
    for idx, col in enumerate(cursor.description):
        report_dict[col[0]] = report[idx]
    
    # u83b7u53d6u6d4bu8bd5u4fe1u606f
    cursor.execute('SELECT * FROM test_info WHERE report_id = ?', (report_id,))
    test_info = cursor.fetchone()
    test_info_dict = None
    
    if test_info:
        test_info_dict = {}
        for idx, col in enumerate(cursor.description):
            test_info_dict[col[0]] = test_info[idx]
    
    # u83b7u53d6u6d4bu91cfu6570u636e
    cursor.execute('SELECT * FROM measurements WHERE report_id = ?', (report_id,))
    measurements = cursor.fetchall()
    measurements_list = []
    
    for row in measurements:
        item = {}
        for idx, col in enumerate(cursor.description):
            item[col[0]] = row[idx]
        measurements_list.append(item)
    
    return jsonify({
        'report': report_dict,
        'test_info': test_info_dict,
        'measurements': measurements_list
    })

# u83b7u53d6u7edfu8ba1u6570u636e
@app.route('/api/statistics/results', methods=['GET'])
def get_result_statistics():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT result, COUNT(*) as count FROM test_reports GROUP BY result')
    stats = cursor.fetchall()
    
    result = {}
    for row in stats:
        result[row[0]] = row[1]
    
    return jsonify(result)

# u6309u65e5u671fu7edfu8ba1
@app.route('/api/statistics/by-date', methods=['GET'])
def get_date_statistics():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT date, COUNT(*) as count FROM test_reports GROUP BY date ORDER BY date')
    stats = cursor.fetchall()
    
    result = {}
    for row in stats:
        result[row[0]] = row[1]
    
    return jsonify(result)

# u83b7u53d6u6d4bu91cfu6570u636e
@app.route('/api/measurements', methods=['GET'])
def get_measurements():
    """
    u83b7u53d6u6d4bu91cfu6570u636euff0cu652fu6301u6307u5b9au8fd4u56deu5b57u6bb5
    
    u53c2u6570:
    - fields: u9017u53f7u5206u9694u7684u8981u8fd4u56deu7684u5b57u6bb5u5217u8868uff08u4f8bu5982fields=name,result_value,test_timeuff09
    - name: u6839u636eu6d4bu8bd5u9879u76eeu540du79f0u7b5bu9009
    - report_id: u6839u636eu62a5u544aIDu7b5bu9009
    - status: u6839u636eu72b6u6001u7b5bu9009uff08PASSu6216FAILuff09
    - limit: u6bcfu9875u8bb0u5f55u6570uff08u9ed8u8ba4100uff09
    - offset: u5206u9875u504fu79fbu91cfuff08u9ed8u8ba40uff09
    """
    db = get_db()
    cursor = db.cursor()
    
    # u62c9u53d6u67e5u8be2u53c2u6570
    fields = request.args.get('fields', default=None)
    name = request.args.get('name', default=None, type=str)
    report_id = request.args.get('report_id', default=None, type=int)
    status = request.args.get('status', default=None, type=str)
    limit = request.args.get('limit', default=100, type=int)
    offset = request.args.get('offset', default=0, type=int)
    
    # u5904u7406u6307u5b9au7684u5b57u6bb5
    if fields:
        requested_fields = fields.split(',')
        # u786eu4fddu6240u6307u5b9au7684u5b57u6bb5u5408u6cd5
        valid_fields = [
            'id', 'report_id', 'measurement_id', 'step_type', 'name', 'result_type',
            'result_value', 'status', 'unit_of_measure', 'lower_limit', 'upper_limit',
            'test_time', 'comment'
        ]
        # u8fd8u53efu4ee5u8fd4u56deu62a5u544au76f8u5173u5b57u6bb5
        report_fields = ['serial_number', 'part_number', 'date', 'test_result']
        
        # u8fc7u6ee4u51fau540cu65f6u5b58u5728u4eaeu6709u6548u5b57u6bb5u548cu8bf7u6c42u5b57u6bb5u4e2du7684u5b57u6bb5
        select_fields = []
        join_needed = False
        
        for field in requested_fields:
            field = field.strip()
            if field in valid_fields:
                select_fields.append(f'm.{field}')
            elif field in report_fields:
                select_fields.append(f'r.{field}')
                join_needed = True
        
        # u5982u679cu6ca1u6709u6709u6548u5b57u6bb5uff0cu9ed8u8ba4u9009u53d6u6240u6709u5b57u6bb5
        if not select_fields:
            select_fields = ['m.*']
            join_needed = True
    else:
        # u9ed8u8ba4u9009u62e9u6240u6709u5b57u6bb5
        select_fields = ['m.*']
        join_needed = True
    
    # u6784u5efau67e5u8be2
    select_clause = ', '.join(select_fields)
    if join_needed:
        select_clause += ', r.serial_number, r.part_number, r.date, r.result as test_result'
        from_clause = 'FROM measurements m JOIN test_reports r ON m.report_id = r.id'
    else:
        from_clause = 'FROM measurements m'
    
    where_clauses = []
    params = []
    
    if name:
        where_clauses.append('m.name = ?')
        params.append(name)
    
    if report_id:
        where_clauses.append('m.report_id = ?')
        params.append(report_id)
    
    if status:
        where_clauses.append('m.status = ?')
        params.append(status)
    
    # u7ec4u88c5WHERE
    where_clause = ''
    if where_clauses:
        where_clause = 'WHERE ' + ' AND '.join(where_clauses)
    
    # u83b7u53d6u603bu6570
    count_query = f"SELECT COUNT(*) {from_clause} {where_clause}"
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()[0]
    
    # u6784u5efau5b8cu6574u67e5u8be2
    query = f"SELECT {select_clause} {from_clause} {where_clause} ORDER BY m.id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # u6784u5efau7ed3u679c
    result = []
    for row in rows:
        item = {}
        for idx, col in enumerate(cursor.description):
            col_name = col[0]
            # u5982u679cu662fm.u5f00u5934u7684u5217u540duff0cu53bbu6389m.
            if '.' in col_name:
                col_name = col_name.split('.')[1]
            item[col_name] = row[idx]
        result.append(item)
    
    return jsonify({
        'total': total_count,
        'limit': limit,
        'offset': offset,
        'measurements': result
    })

# u6d4bu91cfu7edfu8ba1u5206u6790
@app.route('/api/measurements/stats', methods=['GET'])
def get_measurement_stats():
    """
    u83b7u53d6u7279u5b9au6d4bu91cfu9879u76eeu7684u7edfu8ba1u4fe1u606f
    
    u53c2u6570:
    - name: u6d4bu8bd5u9879u76eeu540du79f0
    """
    db = get_db()
    cursor = db.cursor()
    
    name = request.args.get('name')
    if not name:
        return jsonify({
            'error': 'u5fc5u987bu6307u5b9au6d4bu91cfu9879u76eeu540du79f0 (name)'
        }), 400
    
    # u83b7u53d6u7edfu8ba1u4fe1u606f
    stats = {}
    
    # 1. u603bu6570u91cf
    cursor.execute('SELECT COUNT(*) FROM measurements WHERE name = ?', (name,))
    stats['total_count'] = cursor.fetchone()[0]
    
    # 2. u901au8fc7/u5931u8d25u6570u91cf
    cursor.execute('''
        SELECT status, COUNT(*) 
        FROM measurements 
        WHERE name = ? 
        GROUP BY status
    ''', (name,))
    status_counts = {row[0]: row[1] for row in cursor.fetchall()}
    stats['pass_count'] = status_counts.get('PASS', 0)
    stats['fail_count'] = status_counts.get('FAIL', 0)
    
    # u8ba1u7b97u901au8fc7u7387
    if stats['total_count'] > 0:
        stats['pass_rate'] = round(stats['pass_count'] / stats['total_count'] * 100, 2)
    else:
        stats['pass_rate'] = 0
    
    # 3. u6d4bu8bd5u65f6u95f4u7edfu8ba1
    cursor.execute('''
        SELECT 
            MIN(test_time) as min_time,
            MAX(test_time) as max_time,
            AVG(test_time) as avg_time
        FROM measurements 
        WHERE name = ?
    ''', (name,))
    time_stats = cursor.fetchone()
    if time_stats and time_stats[0] is not None:
        stats['min_test_time'] = time_stats[0]
        stats['max_test_time'] = time_stats[1]
        stats['avg_test_time'] = round(time_stats[2], 2)
    
    # 4. u6839u636eu7ed3u679cu7c7bu578bu4e0du540cu6536u96c6u6570u503cu7edfu8ba1
    cursor.execute('''
        SELECT result_type 
        FROM measurements 
        WHERE name = ? 
        LIMIT 1
    ''', (name,))
    result_type = cursor.fetchone()
    
    # u5982u679cu662fu6570u503cu7c7bu578bu7684u6d4bu91cfuff0cu8ba1u7b97u76f8u5173u7edfu8ba1
    if result_type and result_type[0] in ['FLOAT', 'INTEGER', 'NUMBER']:
        cursor.execute('''
            SELECT 
                MIN(CAST(result_value AS REAL)) as min_value,
                MAX(CAST(result_value AS REAL)) as max_value,
                AVG(CAST(result_value AS REAL)) as avg_value
            FROM measurements 
            WHERE name = ? AND result_value != ''
        ''', (name,))
        value_stats = cursor.fetchone()
        if value_stats and value_stats[0] is not None:
            stats['min_value'] = value_stats[0]
            stats['max_value'] = value_stats[1]
            stats['avg_value'] = round(value_stats[2], 2)
    
    # 5. u83b7u53d6u4e0au4e0bu9650u503c
    cursor.execute('''
        SELECT lower_limit, upper_limit 
        FROM measurements 
        WHERE name = ? AND lower_limit IS NOT NULL AND upper_limit IS NOT NULL
        LIMIT 1
    ''', (name,))
    limits = cursor.fetchone()
    if limits:
        stats['lower_limit'] = limits[0]
        stats['upper_limit'] = limits[1]
    
    # 6. u83b7u53d6u6700u591au4f7fu7528u7684u5355u4f4d
    cursor.execute('''
        SELECT unit_of_measure, COUNT(*) as count
        FROM measurements
        WHERE name = ? AND unit_of_measure IS NOT NULL AND unit_of_measure != ''
        GROUP BY unit_of_measure
        ORDER BY count DESC
        LIMIT 1
    ''', (name,))
    unit = cursor.fetchone()
    if unit:
        stats['unit_of_measure'] = unit[0]
    
    return jsonify({
        'name': name,
        'statistics': stats
    })

# u83b7u53d6u6240u6709u6d4bu8bd5u9879u76eeu540du79f0
@app.route('/api/measurements/names', methods=['GET'])
def get_measurement_names():
    """
    u83b7u53d6measurementsu8868u4e2du6240u6709u4e0du540cu7684u6d4bu8bd5u9879u76eeu540du79f0
    """
    db = get_db()
    cursor = db.cursor()
    
    # u4f7fu7528DISTINCTu83b7u53d6u6240u6709u4e0du540cu7684nameu503c
    cursor.execute('SELECT DISTINCT name FROM measurements ORDER BY name')
    names = cursor.fetchall()
    
    # u83b7u53d6u6bcfu4e2au6d4bu8bd5u540du79f0u51fau73b0u7684u6b21u6570
    cursor.execute('''
    SELECT name, COUNT(*) as count 
    FROM measurements 
    GROUP BY name 
    ORDER BY name
    ''')
    name_counts = {row[0]: row[1] for row in cursor.fetchall()}
    
    # u6784u9020u8fd4u56deu7ed3u679c
    result = []
    for row in names:
        name = row[0]
        if name:  # u786eu4fddu6d4bu8bd5u540du79f0u4e0du4e3au7a7a
            result.append({
                'name': name,
                'count': name_counts.get(name, 0)
            })
    
    return jsonify({
        'total': len(result),
        'names': result
    })

# u6309u6d4bu8bd5u540du79f0u83b7u53d6u6d4bu8bd5u7ed3u679c
@app.route('/api/measurements/by-name/<string:name>', methods=['GET'])
def get_measurements_by_name(name):
    """
    u6839u636eu6d4bu8bd5u540du79f0u83b7u53d6u7279u5b9au7684u6d4bu8bd5u7ed3u679c
    
    u53c2u6570:
    - name: u6d4bu8bd5u9879u76eeu540du79f0uff08URLu7f16u7801uff09
    - limit: u6bcfu9875u8bb0u5f55u6570uff08u9ed8u8ba4100uff09
    - offset: u5206u9875u504fu79fbu91cfuff08u9ed8u8ba40uff09
    """
    db = get_db()
    cursor = db.cursor()
    
    # u5904u7406u67e5u8be2u53c2u6570
    limit = request.args.get('limit', default=100, type=int)
    offset = request.args.get('offset', default=0, type=int)
    
    # u83b7u53d6u603bu8bb0u5f55u6570
    cursor.execute(
        'SELECT COUNT(*) FROM measurements WHERE name = ?',
        (name,)
    )
    total_count = cursor.fetchone()[0]
    
    # u83b7u53d6u7279u5b9au540du79f0u7684u6d4bu91cfu6570u636e
    cursor.execute('''
    SELECT m.*, r.serial_number, r.part_number, r.date, r.result as test_result
    FROM measurements m
    JOIN test_reports r ON m.report_id = r.id
    WHERE m.name = ?
    ORDER BY r.date DESC, r.id DESC
    LIMIT ? OFFSET ?
    ''', (name, limit, offset))
    
    measurements = cursor.fetchall()
    
    # u8f6cu6362u4e3aJSON
    result = []
    for row in measurements:
        item = {}
        for idx, col in enumerate(cursor.description):
            item[col[0]] = row[idx]
        result.append(item)
    
    return jsonify({
        'name': name,
        'total': total_count,
        'limit': limit,
        'offset': offset,
        'measurements': result
    })

# XMLu6587u4ef6u5904u7406APIu7aefu70b9
@app.route('/api/import-xml', methods=['POST'])
def import_xml_files():
    """
    u5904u7406u6307u5b9au76eeu5f55u4e2du7684XMLu6587u4ef6u5e76u5c06u5176u5bfcu5165u5230u6570u636eu5e93u4e2d
    
    u8bf7u6c42u53c2u6570:
    - directory: u53efu9009u53c2u6570uff0cu8981u5904u7406u7684XMLu6587u4ef6u76eeu5f55uff0cu9ed8u8ba4u4e3a'testReports'
    """
    try:
        # u83b7u53d6u8bf7u6c42u6570u636e
        data = request.get_json() or {}
        directory = data.get('directory', XML_DIRECTORY)
        
        # u786eu4fddu76eeu5f55u5b58u5728
        if not os.path.exists(directory):
            return jsonify({
                'success': False,
                'message': f"u76eeu5f55 '{directory}' u4e0du5b58u5728"
            }), 400
        
        # u4f7fu7528parse_xml_to_sqliteu811au672cu5904u7406XMLu6587u4ef6
        import subprocess
        cmd = ['python', 'parse_xml_to_sqlite.py', '--dir', directory]
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        # u68c0u67e5u5904u7406u662fu5426u6210u529f
        if process.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'XMLu6587u4ef6u5904u7406u6210u529f',
                'details': process.stdout
            })
        else:
            return jsonify({
                'success': False,
                'message': 'XMLu6587u4ef6u5904u7406u5931u8d25',
                'error': process.stderr
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# u4e0au4f20XMLu6587u4ef6u4e0au4f20APIu7aefu70b9
@app.route('/api/upload-xml', methods=['POST'])
def upload_xml():
    """
    u4e0au4f20XMLu6587u4ef6u5e76u5904u7406
    
    u8981u6c42:
    - u8bf7u6c42u5fc5u987bu5305u542bu540du4e3a'file'u7684u6587u4ef6u5b57u6bb5
    """
    try:
        # u68c0u67e5u662fu5426u6709u6587u4ef6u5728u8bf7u6c42u4e2d
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'u8bf7u6c42u4e2du6ca1u6709u6587u4ef6'
            }), 400
        
        file = request.files['file']
        
        # u68c0u67e5u6587u4ef6u540du662fu5426u4e3au7a7a
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'u672au9009u62e9u6587u4ef6'
            }), 400
        
        # u68c0u67e5u662fu5426u4e3aXMLu6587u4ef6
        if not file.filename.lower().endswith('.xml'):
            return jsonify({
                'success': False,
                'message': 'u53eau652fu6301XMLu6587u4ef6'
            }), 400
        
        # u786eu4fddu4e0au4f20u76eeu5f55u5b58u5728
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # u4fddu5b58u6587u4ef6
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # u4f7fu7528parse_xml_to_sqliteu811au672cu5904u7406u4e0au4f20u7684u6587u4ef6
        import subprocess
        cmd = ['python', 'parse_xml_to_sqlite.py', '--file', file_path]
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        # u68c0u67e5u5904u7406u662fu5426u6210u529f
        if process.returncode == 0:
            return jsonify({
                'success': True,
                'message': f"u6587u4ef6 {filename} u4e0au4f20u5e76u5904u7406u6210u529f",
                'details': process.stdout
            })
        else:
            return jsonify({
                'success': False,
                'message': f"u6587u4ef6 {filename} u5904u7406u5931u8d25",
                'error': process.stderr
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# XML处理相关函数
def parse_filename(filename):
    """
    解析文件名以提取特定详细信息
    文件名格式: 1M243403498-476352A.101-NET07A00003-1-20250122-201937_Pass.xml
    """
    # 移除.xml扩展名
    filename_base = filename.replace('.xml', '')
    
    # 按连字符分割
    parts = filename_base.split('-')
    
    # 验证我们有足够的部分
    if len(parts) < 6:
        raise ValueError(f"无效的文件名格式: {filename}")
    
    # 提取序列号（第一部分）
    serial_number = parts[0]
    
    # 提取零件号（第二部分）
    part_number = parts[1]
    
    # 提取测试仪ID（第三部分）
    tester_id = parts[2]
    
    # 提取测试子项（第四部分）
    test_sub = parts[3]
    
    # 提取日期（第五部分）
    date = parts[4]
    
    # 最后一部分包含时间和结果
    last_part = parts[5]
    
    # 通过下划线分割最后一部分
    time_result = last_part.split('_')
    
    # 提取时间（分割的第一部分）
    time = time_result[0]
    
    # 提取结果（分割的最后一部分）
    result = time_result[-1] if len(time_result) > 1 else ''
    
    # 清理结果字段
    result = result.strip()
    
    # 规范化结果为'Pass'或'Fail'
    if result.lower() in ['pass', 'passed', 'passted']:
        result = 'Pass'
    elif result.lower() in ['fail', 'failed']:
        result = 'Fail'
    
    return {
        'serial_number': serial_number,
        'part_number': part_number,
        'tester_id': tester_id,
        'test_sub': test_sub,
        'date': date,
        'time': time,
        'result': result
    }

def get_text_safe(element, xpath):
    """
    安全地从XML元素获取文本，如果元素为None则返回空字符串。
    """
    sub_elem = element.find(xpath)
    if sub_elem is not None and sub_elem.text is not None:
        return sub_elem.text.strip()
    return ''

def parse_xml_file(xml_path):
    """
    全面解析XML文件并提取所有相关数据。
    返回三个字典: filename_info, test_info和measurements。
    """
    # 提取文件名详细信息
    filename = os.path.basename(xml_path)
    try:
        filename_info = parse_filename(filename)
        
        # 解析XML内容
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # 提取测试信息（标题信息）
        test_info = {}
        if root.find('./RESULT_DATA/HEADER') is not None:
            header = root.find('./RESULT_DATA/HEADER')
            
            # 提取基本标题字段
            test_info['file_name'] = get_text_safe(header, './FILE_NAME')
            test_info['swift_version'] = get_text_safe(header, './SWIFT_VERSION')
            test_info['test_spec_id'] = get_text_safe(header, './TEST_SPEC_ID')
            test_info['operator_id'] = get_text_safe(header, './OPERATOR')
            
            # 提取TESTER信息
            if header.find('./TESTER') is not None:
                tester = header.find('./TESTER')
                test_info['tester_serial_number'] = get_text_safe(tester, './SERIAL_NUMBER')
                test_info['tester_ot_number'] = get_text_safe(tester, './OT_NUMBER')
                test_info['tester_sw_version'] = get_text_safe(tester, './SW_VERSION')
                test_info['tester_hw_version'] = get_text_safe(tester, './HW_VERSION')
                test_info['tester_site'] = get_text_safe(tester, './SITE')
                test_info['tester_operation'] = get_text_safe(tester, './OPERATION')
            
            # 提取DUT信息
            if header.find('./DUT') is not None:
                dut = header.find('./DUT')
                test_info['dut_serial_number'] = get_text_safe(dut, './SERIAL_NUMBER')
                test_info['dut_product_code'] = get_text_safe(dut, './PRODUCT_CODE')
                test_info['dut_product_revision'] = get_text_safe(dut, './PRODUCT_REVISION')
            
            # 提取自定义属性为JSON
            if header.find('./CUSTOM_ATTRIBUTES') is not None:
                custom_attrs = {}
                for field in header.findall('./CUSTOM_ATTRIBUTES/FIELD'):
                    if 'VALUE' in field.attrib:
                        custom_attrs[field.text] = field.attrib['VALUE']
                test_info['custom_attributes'] = json.dumps(custom_attrs)
        
        # 提取时间信息
        if root.find('./RESULT_DATA/TIMES') is not None:
            times = root.find('./RESULT_DATA/TIMES')
            test_info['setup_time'] = get_text_safe(times, './SETUP_TIME')
            test_info['test_time'] = get_text_safe(times, './TEST_TIME')
            test_info['unload_time'] = get_text_safe(times, './UNLOAD_TIME')
        
        # 提取测试开始、停止、状态和诊断
        test_info['test_start'] = get_text_safe(root, './RESULT_DATA/TEST_START')
        test_info['test_stop'] = get_text_safe(root, './RESULT_DATA/TEST_STOP')
        test_info['overall_status'] = get_text_safe(root, './RESULT_DATA/OVERALL_STATUS')
        
        if root.find('./RESULT_DATA/DIAGNOSTICS') is not None:
            diagnostics = root.find('./RESULT_DATA/DIAGNOSTICS')
            test_info['diagnostics_type'] = diagnostics.attrib.get('TYPE', '')
            test_info['diagnostics_value'] = diagnostics.text
        
        # 提取测量
        measurements = []
        for meas in root.findall('./RESULT_DATA/RESULTS/MEASUREMENT'):
            measurement = {}
            measurement['step_type'] = get_text_safe(meas, './STEP_TYPE')
            measurement['measurement_id'] = get_text_safe(meas, './ID')
            measurement['name'] = get_text_safe(meas, './n')
            
            # 提取结果详情
            result_elem = meas.find('./RESULT')
            if result_elem is not None:
                measurement['result_type'] = result_elem.attrib.get('TYPE', '')
                measurement['result_value'] = result_elem.text
            
            measurement['status'] = get_text_safe(meas, './STATUS')
            measurement['unit_of_measure'] = get_text_safe(meas, './UNIT_OF_MEAS')
            measurement['lower_limit'] = get_text_safe(meas, './ACC_LOW')
            measurement['upper_limit'] = get_text_safe(meas, './ACC_HIGH')
            measurement['test_time'] = get_text_safe(meas, './TEST_TIME')
            measurement['comment'] = get_text_safe(meas, './COMMENT')
            measurement['qm_meas_id'] = get_text_safe(meas, './QM_MEAS_ID')
            
            measurements.append(measurement)
        
        return {
            'filename': filename,
            'filename_info': filename_info,
            'test_info': test_info,
            'measurements': measurements
        }
    except Exception as e:
        print(f"解析XML文件 {filename} 时出错: {e}")
        return None

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

if __name__ == '__main__':
    # u8fd0u884cu670du52a1u5668
    print('u670du52a1u5668u5c06u5728 http://localhost:5000 u542fu52a8')
    print('u6839u636eu9700u8981u6dfbu52a0 --host=0.0.0.0 u53c2u6570u6765u5141u8bb8u5916u90e8u8bbfu95ee')
    app.run(debug=True, port=5000)
