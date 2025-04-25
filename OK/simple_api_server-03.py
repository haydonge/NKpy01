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
        test_info_dict = {}
        for idx, col in enumerate(cursor.description):
            test_info_dict[col[0]] = test_info[idx]
    
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
    """
    db = get_db()
    cursor = db.cursor()
    
    # 使用DISTINCT获取所有的name值
    cursor.execute('SELECT DISTINCT name FROM measurements ORDER BY name')
    names = cursor.fetchall()
    
    # 获取每个测试项的记录数
    cursor.execute('''
    SELECT name, COUNT(*) as count 
    FROM measurements 
    GROUP BY name 
    ORDER BY name
    ''')
    name_counts = {row[0]: row[1] for row in cursor.fetchall()}
    
    # 构造返回结果
    result = []
    for row in names:
        name = row[0]
        if name:  # 确保测试项名称不为空
            result.append({
                'name': name,
                'count': name_counts.get(name, 0)
            })
    
    return jsonify({
        'total': len(result),
        'names': result
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
