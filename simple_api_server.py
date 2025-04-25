import os
import sqlite3
from flask import Flask, g, jsonify, request, send_from_directory, make_response
import json
from datetime import datetime, timedelta
from flask_cors import CORS

app = Flask(__name__, static_folder='front/dist')
# 添加 CORS 支持，允许所有源访问所有 API 端点
CORS(app)

# Release version 0.3
# 数据库配置
DATABASE = 'test_reports.sqlite'
UPLOAD_FOLDER = 'uploads'
XML_DIRECTORY = 'testReports'

# 确定上传三个目录目录
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(XML_DIRECTORY, exist_ok=True)
# 如果目录不存在，创建目录

# API状态端点
@app.route('/api/status', methods=['GET'])
def get_status():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT COUNT(*) FROM test_reports')
    count = cursor.fetchone()[0]
    return jsonify({
        'status': '运行中',
        'version': '1.0.0',
        'database': DATABASE,
        'report_count': count
    })

# 获取所有测试报告
@app.route('/api/reports', methods=['GET'])
def get_reports():
    db = get_db()
    cursor = db.cursor()
    
    # 处理查询参数
    limit = request.args.get('limit', default=100, type=int)
    offset = request.args.get('offset', default=0, type=int)
    serial_number = request.args.get('serial_number', default=None, type=str)
    part_number = request.args.get('part_number', default=None, type=str)
    result = request.args.get('result', default=None, type=str)
    date = request.args.get('date', default=None, type=str)
    
    # 构造SQL查询
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
    
    if date:
        query += ' AND date = ?'
        params.append(date)
    
    query += ' ORDER BY id DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    reports = cursor.fetchall()
    
    # 转换为JSON
    result = []
    for row in reports:
        item = {}
        for idx, col in enumerate(cursor.description):
            item[col[0]] = row[idx]
        result.append(item)
    
    return jsonify(result)

# 获取单个报告详情
@app.route('/api/reports/<int:report_id>', methods=['GET'])
def get_report_detail(report_id):
    db = get_db()
    cursor = db.cursor()
    
    # 获取报告信息
    cursor.execute('SELECT * FROM test_reports WHERE id = ?', (report_id,))
    report = cursor.fetchone()
    
    if not report:
        return jsonify({'error': '报告不存在'}), 404
    
    # 转换为字典
    report_dict = {}
    for idx, col in enumerate(cursor.description):
        report_dict[col[0]] = report[idx]
    
    # 获取测试信息
    cursor.execute('SELECT * FROM test_info WHERE report_id = ?', (report_id,))
    test_info = cursor.fetchone()
    test_info_dict = None
    
    if test_info:
        # 明确映射前端需要的字段
        columns = [col[0] for col in cursor.description]
        info = dict(zip(columns, test_info))
        test_info_dict = {
            # 这些key与前端ReportDetail.jsx渲染字段一一对应
            'test_id': info.get('test_spec_id', ''),
            'test_type': info.get('tester_operation', ''),
            'software_name': info.get('tester_sw_version', ''),
            'software_version': info.get('swift_version', ''),
            'operator': info.get('operator_id', ''),
            'station_id': info.get('tester_site', '')
        }
    
    # 获取测量数据
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

# 获取统计数据
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

# 按日期统计
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

# 每日良率统计（总数、通过、不良、良率）
@app.route('/api/statistics/daily-yield', methods=['GET'])
def get_daily_yield():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT date,
               COUNT(*) as total,
               SUM(CASE WHEN result = 'Pass' THEN 1 ELSE 0 END) as pass,
               SUM(CASE WHEN result != 'Pass' THEN 1 ELSE 0 END) as fail
        FROM test_reports
        GROUP BY date
        ORDER BY date
    ''')
    stats = cursor.fetchall()
    result = []
    for row in stats:
        date, total, passed, failed = row
        yield_rate = round((passed / total) * 100, 1) if total > 0 else 0.0
        result.append({
            "date": date,
            "total": total,
            "pass": passed,
            "fail": failed,
            "yield": yield_rate
        })
    return jsonify(result)

# 不良项目TOP10统计
@app.route('/api/statistics/top-fail-measurements', methods=['GET'])
def get_top_fail_measurements():
    """
    获取所有测试中失败（非pass）项目的TOP10。
    - 只统计 measurements.status 非 'pass'（不区分大小写）的记录
    - 按 name 分组，统计 fail 数量，按数量降序取前10
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT name, COUNT(*) as fail_count
        FROM measurements
        WHERE LOWER(status) != 'pass'
        GROUP BY name
        ORDER BY fail_count DESC
        LIMIT 10
    ''')
    results = cursor.fetchall()
    data = [{"name": row[0], "fail_count": row[1]} for row in results]
    return jsonify(data)

# 获取测量数据
@app.route('/api/measurements', methods=['GET'])
def get_measurements():
    """
    解释各个参数的含义:
    - fields: 指定要返回的字段，用逗号分隔
    - name: 测试项名称
    - report_id: 测试报告ID
    - status: 测试状态
    - limit: 限制返回的记录数
    - offset: 起始位置
    """
    db = get_db()
    cursor = db.cursor()
    
    # 处理查询参数
    fields = request.args.get('fields', default=None)
    name = request.args.get('name', default=None, type=str)
    report_id = request.args.get('report_id', default=None, type=int)
    status = request.args.get('status', default=None, type=str)
    limit = request.args.get('limit', default=100, type=int)
    offset = request.args.get('offset', default=0, type=int)
    # 新增部件号参数
    part_number = request.args.get('part_number', default=None, type=str)
    
    # 处理字段
    if fields:
        requested_fields = fields.split(',')
        # 确保请求的字段是有效的
        valid_fields = [
            'id', 'report_id', 'measurement_id', 'step_type', 'name', 'result_type',
            'result_value', 'status', 'unit_of_measure', 'lower_limit', 'upper_limit',
            'test_time', 'comment'
        ]
        # 过滤掉无效的字段
        select_fields = []
        join_needed = False
        
        for field in requested_fields:
            field = field.strip()
            if field in valid_fields:
                select_fields.append(f'm.{field}')
            elif field in ['serial_number', 'part_number', 'date', 'test_result']:
                select_fields.append(f'r.{field}')
                join_needed = True
        
        # 如果没有指定字段，则返回所有字段
        if not select_fields:
            select_fields = ['m.*']
            join_needed = True
    else:
        # 默认返回所有字段
        select_fields = ['m.*']
        join_needed = True
    
    # 构造SQL查询
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
    
    # 添加部件号过滤
    if part_number:
        # 确保使用 JOIN
        if not join_needed:
            from_clause = 'FROM measurements m JOIN test_reports r ON m.report_id = r.id'
            join_needed = True
        where_clauses.append('r.part_number = ?')
        params.append(part_number)
    
    # 构造WHERE子句
    where_clause = ''
    if where_clauses:
        where_clause = 'WHERE ' + ' AND '.join(where_clauses)
    
    # 获取记录数
    count_query = f"SELECT COUNT(*) {from_clause} {where_clause}"
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()[0]
    
    # 构造查询
    query = f"SELECT {select_clause} {from_clause} {where_clause} ORDER BY m.id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # 转换为JSON
    result = []
    for row in rows:
        item = {}
        for idx, col in enumerate(cursor.description):
            col_name = col[0]
            # 移除表名前缀
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

# 测量统计分析
@app.route('/api/measurements/stats', methods=['GET'])
def get_measurement_stats():
    """
    获取测试结果统计信息
    
    参数:
    - name: 测试项名称
    """
    db = get_db()
    cursor = db.cursor()
    
    name = request.args.get('name')
    if not name:
        return jsonify({
            'error': '必须指定测试项名称 (name)'
        }), 400
    
    # 获取统计信息
    stats = {}
    
    # 1. 记录数
    cursor.execute('SELECT COUNT(*) FROM measurements WHERE name = ?', (name,))
    stats['total_count'] = cursor.fetchone()[0]
    
    # 2. 通过/失败数
    cursor.execute('''
        SELECT status, COUNT(*) 
        FROM measurements 
        WHERE name = ? 
        GROUP BY status
    ''', (name,))
    status_counts = {row[0]: row[1] for row in cursor.fetchall()}
    stats['pass_count'] = status_counts.get('PASS', 0)
    stats['fail_count'] = status_counts.get('FAIL', 0)
    
    # 计算通过率
    if stats['total_count'] > 0:
        stats['pass_rate'] = round(stats['pass_count'] / stats['total_count'] * 100, 2)
    else:
        stats['pass_rate'] = 0
    
    # 3. 测试时间统计
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
    
    # 4. 测量值统计
    cursor.execute('''
        SELECT result_type 
        FROM measurements 
        WHERE name = ? 
        LIMIT 1
    ''', (name,))
    result_type = cursor.fetchone()
    
    # 如果是数值类型，则计算统计值
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
    
    # 5. 获取下限和上限
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
    
    # 6. 获取最常用的单位
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

# 获取所有测试项名称
@app.route('/api/measurements/names', methods=['GET'])
def get_measurement_names():
    """
    获取measurements表中所有的测试项名称
    
    参数:
    - q: 模糊搜索测试项名称
    - part_number: 按部件号过滤
    """
    db = get_db()
    cursor = db.cursor()
    
    # 支持 q（项目名称模糊）、part_number、name 三种参数的双向筛查
    # 兼容 q=xxx 和 q[q]=xxx 两种写法
    q = request.args.get('q', default=None, type=str)
    if not q:
        # 兼容 q[q]=xxx
        q = request.args.get('q[q]', default=None, type=str)
    part_number = request.args.get('part_number', default=None, type=str)
    name = request.args.get('name', default=None, type=str)

    # 1. 获取项目名称列表
    name_query = 'SELECT DISTINCT m.name FROM measurements m JOIN test_reports r ON m.report_id = r.id WHERE 1=1'
    name_params = []
    if part_number:
        name_query += ' AND r.part_number = ?'
        name_params.append(part_number)
    if name:
        name_query += ' AND m.name = ?'
        name_params.append(name)
    if q:
        name_query += ' AND m.name LIKE ?'
        name_params.append(f'%{q}%')
    name_query += ' ORDER BY m.name'
    cursor.execute(name_query, tuple(name_params))
    names = cursor.fetchall()

    # 2. 获取部件号列表
    part_query = 'SELECT DISTINCT r.part_number FROM measurements m JOIN test_reports r ON m.report_id = r.id WHERE r.part_number IS NOT NULL'
    part_params = []
    if name:
        part_query += ' AND m.name = ?'
        part_params.append(name)
    if part_number:
        part_query += ' AND r.part_number = ?'
        part_params.append(part_number)
    if q:
        part_query += ' AND m.name LIKE ?'
        part_params.append(f'%{q}%')
    part_query += ' ORDER BY r.part_number'
    cursor.execute(part_query, tuple(part_params))
    part_numbers = [row[0] for row in cursor.fetchall() if row[0]]

    # 3. 获取每个测试项的记录数（在当前筛选下）
    count_query = 'SELECT m.name, COUNT(*) as count FROM measurements m JOIN test_reports r ON m.report_id = r.id WHERE 1=1'
    count_params = []
    if part_number:
        count_query += ' AND r.part_number = ?'
        count_params.append(part_number)
    if name:
        count_query += ' AND m.name = ?'
        count_params.append(name)
    if q:
        count_query += ' AND m.name LIKE ?'
        count_params.append(f'%{q}%')
    count_query += ' GROUP BY m.name ORDER BY m.name'
    cursor.execute(count_query, tuple(count_params))
    name_counts = {row[0]: row[1] for row in cursor.fetchall()}

    # 4. 构造返回结果
    result = []
    for row in names:
        n = row[0]
        if n:
            result.append({'name': n, 'count': name_counts.get(n, 0)})

    return jsonify({
        'total': len(result),
        'names': result,
        'part_numbers': part_numbers
    })

# 按测试项名称获取测量数据
@app.route('/api/measurements/by-name/<string:name>', methods=['GET'])
def get_measurements_by_name(name):
    """
    按测试项名称获取测量数据
    
    参数:
    - name: 测试项名称
    - limit: 限制返回的记录数
    - offset: 起始位置
    """
    db = get_db()
    cursor = db.cursor()
    
    # 处理查询参数
    limit = request.args.get('limit', default=100, type=int)
    offset = request.args.get('offset', default=0, type=int)
    
    # 获取记录数
    cursor.execute(
        'SELECT COUNT(*) FROM measurements WHERE name = ?',
        (name,)
    )
    total_count = cursor.fetchone()[0]
    
    # 获取测量数据
    cursor.execute('''
    SELECT m.*, r.serial_number, r.part_number, r.date, r.result as test_result
    FROM measurements m
    JOIN test_reports r ON m.report_id = r.id
    WHERE m.name = ?
    ORDER BY r.date DESC, r.id DESC
    LIMIT ? OFFSET ?
    ''', (name, limit, offset))
    
    measurements = cursor.fetchall()
    
    # 转换为JSON
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

# XML文件处理相关函数
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

# XML文件处理API端点
@app.route('/api/import-xml', methods=['POST'])
def import_xml_files():
    """
    处理指定目录中的XML文件并将其导入到数据库中
    
    请求参数:
    - directory: 可选参数，要处理的XML文件目录，默认为'testReports'
    """
    try:
        # 获取请求数据
        data = request.get_json() or {}
        directory = data.get('directory', XML_DIRECTORY)
        
        # 确保目录存在
        if not os.path.exists(directory):
            return jsonify({
                'success': False,
                'message': f"目录 '{directory}' 不存在"
            }), 400
        
        # 使用parse_xml_to_sqlite脚本处理XML文件
        import subprocess
        cmd = ['python', 'parse_xml_to_sqlite.py', '--dir', directory]
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        # 检查处理是否成功
        if process.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'XML文件处理成功',
                'details': process.stdout
            })
        else:
            return jsonify({
                'success': False,
                'message': 'XML文件处理失败',
                'error': process.stderr
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 处理 xmlimport 文件夹中的所有 XML 文件
@app.route('/api/import-folder-xml', methods=['GET'])
def import_folder_xml():
    """
    处理 xmlimport 文件夹中的所有 XML 文件，逐个解析并导入数据库
    """
    import os
    import glob
    import xml.etree.ElementTree as ET
    from datetime import datetime
    
    # 获取 xmlimport 文件夹中的所有 XML 文件
    xml_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'xmlimport')
    xml_files = glob.glob(os.path.join(xml_folder, '*.xml'))
    
    if not xml_files:
        return jsonify({
            'success': False,
            'message': 'xmlimport 文件夹中没有找到 XML 文件'
        }), 404
    
    results = {
        'total': len(xml_files),
        'success': 0,
        'skipped': 0,
        'failed': 0,
        'files': []
    }
    
    # 逐个处理 XML 文件
    for xml_file in xml_files:
        file_name = os.path.basename(xml_file)
        file_result = {
            'file': file_name,
            'status': 'processing'
        }
        
        try:
            # 解析 XML 文件
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # 将 XML 转换为 JSON 格式
            # 这里需要实现与前端 xmlToReportJson.js 类似的解析逻辑
            # 由于后端解析逻辑可能与前端不同，这里简化处理
            
            # 1. 解析文件名，提取 filename_info
            base_name = file_name.replace('.xml', '')
            parts = base_name.split('-')
            
            filename_info = {}
            if len(parts) >= 6:
                last_part = parts[5].split('_')
                result = last_part[1] if len(last_part) > 1 else ''
                result = result.strip()
                if result.lower() in ['pass', 'passed', 'passted']:
                    result = 'Pass'
                elif result.lower() in ['fail', 'failed']:
                    result = 'Fail'
                
                filename_info = {
                    'filename': base_name,
                    'serial_number': parts[0],
                    'part_number': parts[1],
                    'tester_id': parts[2],
                    'test_sub': parts[3],
                    'date': parts[4],
                    'time': last_part[0] if last_part else '',
                    'result': result
                }
            
            # 2. 提取测试信息
            test_info = {}
            
            # 尝试从 HEADER 获取信息
            header = root.find('.//HEADER')
            if header is not None:
                for child in header:
                    test_info[child.tag.lower()] = child.text.strip() if child.text else ''
            
            # 尝试从 TIMES 获取信息
            times = root.find('.//TIMES')
            if times is not None:
                for child in times:
                    test_info[f'time_{child.tag.lower()}'] = child.text.strip() if child.text else ''
            
            # 3. 提取测量数据
            measurements = []
            for measurement in root.findall('.//MEASUREMENT'):
                m_data = {}
                
                # 获取测量项的名称和值
                name_elem = measurement.find('.//NAME')
                value_elem = measurement.find('.//VALUE')
                
                if name_elem is not None and name_elem.text:
                    m_data['name'] = name_elem.text.strip()
                else:
                    continue  # 跳过没有名称的测量项
                
                if value_elem is not None and value_elem.text:
                    m_data['value'] = value_elem.text.strip()
                else:
                    m_data['value'] = ''
                
                # 获取其他属性
                for child in measurement:
                    if child.tag not in ['NAME', 'VALUE']:
                        m_data[child.tag.lower()] = child.text.strip() if child.text else ''
                
                # 添加状态信息
                limit_low = measurement.find('.//LIMIT_LOW')
                limit_high = measurement.find('.//LIMIT_HIGH')
                
                try:
                    if value_elem is not None and value_elem.text and limit_low is not None and limit_high is not None:
                        value = float(value_elem.text.strip())
                        low = float(limit_low.text.strip()) if limit_low.text else float('-inf')
                        high = float(limit_high.text.strip()) if limit_high.text else float('inf')
                        
                        if low <= value <= high:
                            m_data['status'] = 'Pass'
                        else:
                            m_data['status'] = 'Fail'
                    else:
                        m_data['status'] = 'Unknown'
                except (ValueError, TypeError):
                    m_data['status'] = 'Unknown'
                
                measurements.append(m_data)
            
            # 构建完整的 JSON 数据
            json_data = {
                'filename_info': filename_info,
                'test_info': test_info,
                'measurements': measurements
            }
            
            # 将数据插入数据库
            db = get_db()
            
            # 1. 查重：如已存在同名文件则跳过
            cursor = db.cursor()
            cursor.execute('SELECT id FROM test_reports WHERE filename = ?', (filename_info.get('filename', ''),))
            if cursor.fetchone():
                file_result['status'] = 'skipped'
                file_result['reason'] = '同名文件已存在'
                results['skipped'] += 1
                results['files'].append(file_result)
                continue
            # 插入 test_reports 表
            cursor.execute('''
            INSERT INTO test_reports 
            (filename, serial_number, part_number, tester_id, test_sub, date, time, result) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                filename_info.get('filename', ''),
                filename_info.get('serial_number', ''),
                filename_info.get('part_number', ''),
                filename_info.get('tester_id', ''),
                filename_info.get('test_sub', ''),
                filename_info.get('date', ''),
                filename_info.get('time', ''),
                filename_info.get('result', '')
            ))
            
            report_id = cursor.lastrowid
            
            # 2. 插入 test_info 表
            if test_info:
                # 获取表结构中的所有列名
                cursor.execute('PRAGMA table_info(test_info)')
                columns = [row[1] for row in cursor.fetchall()]
                
                # 过滤出存在于表结构中的字段
                valid_columns = ['report_id']
                valid_values = [report_id]
                
                for key, value in test_info.items():
                    if key in columns:
                        valid_columns.append(key)
                        valid_values.append(value)
                
                # 构建动态 SQL 语句
                placeholders = ', '.join(['?'] * len(valid_values))
                columns_str = ', '.join(valid_columns)
                
                cursor.execute(f'''
                INSERT INTO test_info 
                ({columns_str}) 
                VALUES ({placeholders})
                ''', valid_values)
            
            # 3. 插入 measurements 表
            for measurement in measurements:
                # 获取表结构中的所有列名
                cursor.execute('PRAGMA table_info(measurements)')
                columns = [row[1] for row in cursor.fetchall()]
                
                # 过滤出存在于表结构中的字段
                valid_columns = ['report_id']
                valid_values = [report_id]
                
                for key, value in measurement.items():
                    if key in columns:
                        valid_columns.append(key)
                        valid_values.append(value)
                
                # 构建动态 SQL 语句
                placeholders = ', '.join(['?'] * len(valid_values))
                columns_str = ', '.join(valid_columns)
                
                cursor.execute(f'''
                INSERT INTO measurements 
                ({columns_str}) 
                VALUES ({placeholders})
                ''', valid_values)
            
            db.commit()
            
            # 处理成功后移动文件到已处理文件夹
            processed_folder = os.path.join(xml_folder, 'processed')
            if not os.path.exists(processed_folder):
                os.makedirs(processed_folder)
            
            file_result['status'] = 'success'
            results['success'] += 1
        except Exception as e:
            # 事务出错，回滚
            db.rollback()
            file_result['status'] = 'failed'
            file_result['error'] = str(e)
            results['failed'] += 1
        
        results['files'].append(file_result)
    
    return jsonify(results)

# 上传XML文件解析后的JSON数据
@app.route('/api/upload-xml-json', methods=['POST', 'OPTIONS'])
def upload_xml_json():
    """
    接收前端解析后的XML JSON数据并存入数据库
    """
    # 处理 OPTIONS 请求（CORS 预检请求）
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response
    
    try:
        # 获取JSON数据
        json_data = request.get_json()
        if not json_data:
            return jsonify({
                'success': False,
                'message': '无效的JSON数据'
            }), 400
        
        # 提取数据
        filename_info = json_data.get('filename_info', {})
        test_info = json_data.get('test_info', {})
        measurements = json_data.get('measurements', [])
        
        # 插入数据库
        db = get_db()
        
        # 1. 查重：如已存在同名文件则跳过
        cursor = db.cursor()
        cursor.execute('SELECT id FROM test_reports WHERE filename = ?', (filename_info.get('filename', ''),))
        if cursor.fetchone():
            return jsonify({
                'success': False,
                'message': f"数据库中已存在同名文件: {filename_info.get('filename', '')}，本次跳过导入。"
            }), 200
        # 插入 test_reports 表
        cursor.execute('''
        INSERT INTO test_reports 
        (filename, serial_number, part_number, tester_id, test_sub, date, time, result) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            filename_info.get('filename', ''),
            filename_info.get('serial_number', ''),
            filename_info.get('part_number', ''),
            filename_info.get('tester_id', ''),
            filename_info.get('test_sub', ''),
            filename_info.get('date', ''),
            filename_info.get('time', ''),
            filename_info.get('result', '')
        ))
        
        report_id = cursor.lastrowid
        
        # 2. 插入 test_info 表
        if test_info:
            # 获取表结构中的所有列名
            cursor.execute('PRAGMA table_info(test_info)')
            columns = [row[1] for row in cursor.fetchall()]
            
            # 过滤出存在于表结构中的字段
            valid_columns = ['report_id']
            valid_values = [report_id]
            
            for key, value in test_info.items():
                if key in columns:
                    valid_columns.append(key)
                    valid_values.append(value)
            
            # 构建动态 SQL 语句
            placeholders = ', '.join(['?'] * len(valid_values))
            columns_str = ', '.join(valid_columns)
            
            cursor.execute(f'''
            INSERT INTO test_info 
            ({columns_str}) 
            VALUES ({placeholders})
            ''', valid_values)
        
        # 3. 插入 measurements 表
        for measurement in measurements:
            # 获取表结构中的所有列名
            cursor.execute('PRAGMA table_info(measurements)')
            columns = [row[1] for row in cursor.fetchall()]
            
            # 过滤出存在于表结构中的字段
            valid_columns = ['report_id']
            valid_values = [report_id]
            
            for key, value in measurement.items():
                if key in columns:
                    valid_columns.append(key)
                    valid_values.append(value)
            
            # 构建动态 SQL 语句
            placeholders = ', '.join(['?'] * len(valid_values))
            columns_str = ', '.join(valid_columns)
            
            cursor.execute(f'''
            INSERT INTO measurements 
            ({columns_str}) 
            VALUES ({placeholders})
            ''', valid_values)
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': '数据已成功导入',
            'report_id': report_id,
            'measurements_count': len(measurements)
        })
        
    except Exception as e:
        print(f'处理XML JSON数据错误: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 上传XML文件API端点
@app.route('/api/upload-xml', methods=['POST'])
def upload_xml():
    """
    上传XML文件并处理
    
    要求:
    - 请求必须包含名为'file'的文件字段
    """
    try:
        # 检查是否有文件在请求中
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '请求中没有文件'
            }), 400
        
        file = request.files['file']
        
        # 检查文件名是否为空
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '未选择文件'
            }), 400
        
        # 检查是否为XML文件
        if not file.filename.lower().endswith('.xml'):
            return jsonify({
                'success': False,
                'message': '只支持XML文件'
            }), 400
        
        # 确保上传目录存在
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # 保存文件
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        # 查重：如数据库已存在同名文件则跳过
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id FROM test_reports WHERE filename = ?', (filename,))
        if cursor.fetchone():
            return jsonify({
                'success': False,
                'message': f"数据库中已存在同名文件: {filename}，本次跳过导入。"
            }), 200

        file.save(file_path)
        
        # 使用parse_xml_to_sqlite脚本处理上传的文件
        import subprocess
        cmd = ['python', 'parse_xml_to_sqlite.py', '--file', file_path]
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        # 检查处理是否成功
        if process.returncode == 0:
            return jsonify({
                'success': True,
                'message': f"文件 {filename} 上传并处理成功",
                'details': process.stdout
            })
        else:
            return jsonify({
                'success': False,
                'message': f"文件 {filename} 处理失败",
                'error': process.stderr
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

if __name__ == '__main__':
    # 运行应用
    print('应用将在 http://localhost:5000 运行')
    print('根据需要添加 --host=0.0.0.0 参数以允许外部访问')
    app.run(debug=True, port=5000)
