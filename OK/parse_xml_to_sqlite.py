import os
import xml.etree.ElementTree as ET
import sqlite3
import re
import json

def parse_filename(filename):
    """
    Parse filename to extract specific details
    Filename format: 1M243403498-476352A.101-NET07A00003-1-20250122-201937_Pass.xml
    Components:
    - Serial Number: 1M243403498
    - Part Number: 476352A.101
    - Tester ID: NET07A00003
    - Test Sub: 1
    - Date: 20250122
    - Time: 201937
    - Result: Pass
    """
    # Remove .xml extension
    filename_base = filename.replace('.xml', '')
    
    # Split by hyphens
    parts = filename_base.split('-')
    
    # Validate we have enough parts
    if len(parts) < 6:
        raise ValueError(f"Invalid filename format: {filename}")
    
    # Extract serial number (first part)
    serial_number = parts[0]
    
    # Extract part number (second part)
    part_number = parts[1]
    
    # Extract tester ID (third part)
    tester_id = parts[2]
    
    # Extract test sub (fourth part)
    test_sub = parts[3]
    
    # Extract date (fifth part)
    date = parts[4]
    
    # The last part contains time and result
    last_part = parts[5]
    
    # Split the last part by underscore
    time_result = last_part.split('_')
    
    # Extract time (first part of the split)
    time = time_result[0]
    
    # Extract result (last part of the split)
    result = time_result[-1] if len(time_result) > 1 else ''
    
    # Clean up result field
    result = result.strip()
    
    # Normalize result to 'Pass' or 'Fail'
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

def parse_xml_file(xml_path):
    """
    Comprehensively parse XML file and extract all relevant data.
    Returns three dictionaries: filename_info, test_info, and measurements.
    """
    # Extract filename details
    filename = os.path.basename(xml_path)
    try:
        filename_info = parse_filename(filename)
        
        # Parse the XML content
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Extract test info (header information)
        test_info = {}
        if root.find('./RESULT_DATA/HEADER') is not None:
            header = root.find('./RESULT_DATA/HEADER')
            
            # Extract basic header fields
            test_info['file_name'] = get_text_safe(header, './FILE_NAME')
            test_info['swift_version'] = get_text_safe(header, './SWIFT_VERSION')
            test_info['test_spec_id'] = get_text_safe(header, './TEST_SPEC_ID')
            test_info['operator_id'] = get_text_safe(header, './OPERATOR')
            
            # Extract TESTER information
            if header.find('./TESTER') is not None:
                tester = header.find('./TESTER')
                test_info['tester_serial_number'] = get_text_safe(tester, './SERIAL_NUMBER')
                test_info['tester_ot_number'] = get_text_safe(tester, './OT_NUMBER')
                test_info['tester_sw_version'] = get_text_safe(tester, './SW_VERSION')
                test_info['tester_hw_version'] = get_text_safe(tester, './HW_VERSION')
                test_info['tester_site'] = get_text_safe(tester, './SITE')
                test_info['tester_operation'] = get_text_safe(tester, './OPERATION')
            
            # Extract DUT information
            if header.find('./DUT') is not None:
                dut = header.find('./DUT')
                test_info['dut_serial_number'] = get_text_safe(dut, './SERIAL_NUMBER')
                test_info['dut_product_code'] = get_text_safe(dut, './PRODUCT_CODE')
                test_info['dut_product_revision'] = get_text_safe(dut, './PRODUCT_REVISION')
            
            # Extract custom attributes as JSON
            if header.find('./CUSTOM_ATTRIBUTES') is not None:
                custom_attrs = {}
                for field in header.findall('./CUSTOM_ATTRIBUTES/FIELD'):
                    if 'VALUE' in field.attrib:
                        custom_attrs[field.text] = field.attrib['VALUE']
                test_info['custom_attributes'] = json.dumps(custom_attrs)
        
        # Extract times information
        if root.find('./RESULT_DATA/TIMES') is not None:
            times = root.find('./RESULT_DATA/TIMES')
            test_info['setup_time'] = get_text_safe(times, './SETUP_TIME')
            test_info['test_time'] = get_text_safe(times, './TEST_TIME')
            test_info['unload_time'] = get_text_safe(times, './UNLOAD_TIME')
        
        # Extract test start, stop, status and diagnostics
        test_info['test_start'] = get_text_safe(root, './RESULT_DATA/TEST_START')
        test_info['test_stop'] = get_text_safe(root, './RESULT_DATA/TEST_STOP')
        test_info['overall_status'] = get_text_safe(root, './RESULT_DATA/OVERALL_STATUS')
        
        if root.find('./RESULT_DATA/DIAGNOSTICS') is not None:
            diagnostics = root.find('./RESULT_DATA/DIAGNOSTICS')
            test_info['diagnostics_type'] = diagnostics.attrib.get('TYPE', '')
            test_info['diagnostics_value'] = diagnostics.text
        
        # Extract measurements
        measurements = []
        for meas in root.findall('./RESULT_DATA/RESULTS/MEASUREMENT'):
            measurement = {}
            measurement['step_type'] = get_text_safe(meas, './STEP_TYPE')
            measurement['measurement_id'] = get_text_safe(meas, './ID')
            measurement['name'] = get_text_safe(meas, './NAME')
            
            # Extract result details
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
        print(f"Error parsing XML file {filename}: {e}")
        return None

def get_text_safe(element, xpath):
    """
    Safely get text from an XML element, returning empty string if element is None.
    """
    sub_elem = element.find(xpath)
    if sub_elem is not None and sub_elem.text is not None:
        return sub_elem.text.strip()
    return ''

def create_database(db_path):
    """
    Create SQLite database with all necessary tables:
    - test_reports: for filename information
    - test_info: for test header and time information
    - measurements: for all test measurements
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 注释掉删除表的操作，避免每次运行都重置数据
        # cursor.execute('DROP TABLE IF EXISTS measurements')
        # cursor.execute('DROP TABLE IF EXISTS test_info')
        # cursor.execute('DROP TABLE IF EXISTS test_details')
        # cursor.execute('DROP TABLE IF EXISTS test_additional_info')
        
        # Create test reports table if not exists
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            serial_number TEXT,
            part_number TEXT,
            tester_id TEXT,
            test_sub TEXT,
            date TEXT,
            time TEXT,
            result TEXT
        )''')
        
        # Create test info table if not exists
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER,
            file_name TEXT,
            swift_version TEXT,
            test_spec_id TEXT,
            operator_id TEXT,
            tester_serial_number TEXT,
            tester_ot_number TEXT,
            tester_sw_version TEXT,
            tester_hw_version TEXT,
            tester_site TEXT,
            tester_operation TEXT,
            dut_serial_number TEXT,
            dut_product_code TEXT,
            dut_product_revision TEXT,
            custom_attributes TEXT,
            setup_time TEXT,
            test_time TEXT,
            unload_time TEXT,
            test_start TEXT,
            test_stop TEXT,
            overall_status TEXT,
            diagnostics_type TEXT,
            diagnostics_value TEXT,
            FOREIGN KEY (report_id) REFERENCES test_reports(id)
        )''')
        
        # Create measurements table if not exists
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER,
            measurement_id TEXT,
            step_type TEXT,
            name TEXT,
            result_type TEXT,
            result_value TEXT,
            status TEXT,
            unit_of_measure TEXT,
            lower_limit TEXT,
            upper_limit TEXT,
            test_time TEXT,
            comment TEXT,
            qm_meas_id TEXT,
            FOREIGN KEY (report_id) REFERENCES test_reports(id)
        )''')
        
        return conn, cursor
    except Exception as e:
        print(f"Error creating database: {e}")
        return None, None

def check_file_exists(cursor, filename_base):
    """
    Check if a file already exists in the database.
    
    Returns True if the file exists, False otherwise.
    """
    cursor.execute('''
    SELECT COUNT(*) FROM test_reports 
    WHERE filename = ?
    ''', (filename_base,))
    
    return cursor.fetchone()[0] > 0

def insert_test_report(cursor, report):
    """
    Insert a test report into the database, avoiding duplicate entries.
    
    Check if a record with the same filename (without .xml extension) already exists.
    If it does, skip insertion to prevent duplicates.
    
    Returns the report_id if inserted or found, None if error.
    """
    try:
        # Skip if report is None
        if report is None:
            return None
        
        # Extract report details
        filename = report['filename']
        filename_base = filename.replace('.xml', '')
        filename_info = report['filename_info']
        
        # Check if file already exists
        if check_file_exists(cursor, filename_base):
            print(f"找到已存在的文件: {filename_base}")
            # Get the report_id
            cursor.execute('''
            SELECT id FROM test_reports 
            WHERE filename = ?
            ''', (filename_base,))
            return cursor.fetchone()[0]
        
        # Insert the new record
        cursor.execute('''
        INSERT INTO test_reports 
        (filename, serial_number, part_number, tester_id, test_sub, date, time, result) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            filename_base, 
            filename_info['serial_number'],
            filename_info['part_number'],
            filename_info['tester_id'],
            filename_info['test_sub'],
            filename_info['date'],
            filename_info['time'],
            filename_info['result']
        ))
        
        # Get the report_id
        cursor.execute('SELECT last_insert_rowid()')
        report_id = cursor.fetchone()[0]
        
        print(f"插入新记录: {filename_base}")
        return report_id
    except Exception as e:
        print(f"插入测试报告出错: {e}")
        return None

def insert_test_info(cursor, report_id, test_info):
    """
    Insert test information into the test_info table.
    """
    try:
        # Skip if report_id is None
        if report_id is None or test_info is None:
            return False
        
        # Check if test_info for this report already exists
        cursor.execute('''
        SELECT COUNT(*) FROM test_info 
        WHERE report_id = ?
        ''', (report_id,))
        
        if cursor.fetchone()[0] > 0:
            print(f"测试信息已存在于报告ID: {report_id}")
            return False
        
        # Insert the test info
        cursor.execute('''
        INSERT INTO test_info (
            report_id, file_name, swift_version, test_spec_id, operator_id,
            tester_serial_number, tester_ot_number, tester_sw_version, tester_hw_version,
            tester_site, tester_operation, dut_serial_number, dut_product_code,
            dut_product_revision, custom_attributes, setup_time, test_time, unload_time,
            test_start, test_stop, overall_status, diagnostics_type, diagnostics_value
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            report_id,
            test_info.get('file_name', ''),
            test_info.get('swift_version', ''),
            test_info.get('test_spec_id', ''),
            test_info.get('operator_id', ''),
            test_info.get('tester_serial_number', ''),
            test_info.get('tester_ot_number', ''),
            test_info.get('tester_sw_version', ''),
            test_info.get('tester_hw_version', ''),
            test_info.get('tester_site', ''),
            test_info.get('tester_operation', ''),
            test_info.get('dut_serial_number', ''),
            test_info.get('dut_product_code', ''),
            test_info.get('dut_product_revision', ''),
            test_info.get('custom_attributes', ''),
            test_info.get('setup_time', ''),
            test_info.get('test_time', ''),
            test_info.get('unload_time', ''),
            test_info.get('test_start', ''),
            test_info.get('test_stop', ''),
            test_info.get('overall_status', ''),
            test_info.get('diagnostics_type', ''),
            test_info.get('diagnostics_value', '')
        ))
        
        print(f"插入测试信息: 报告ID {report_id}")
        return True
    except Exception as e:
        print(f"插入测试信息出错: {e}")
        return False

def insert_measurements(cursor, report_id, measurements):
    """
    Insert measurement data into the measurements table.
    """
    try:
        # Skip if report_id is None or measurements is empty
        if report_id is None or not measurements:
            return False
        
        # Check if measurements for this report already exists
        cursor.execute('''
        SELECT COUNT(*) FROM measurements 
        WHERE report_id = ?
        ''', (report_id,))
        
        if cursor.fetchone()[0] > 0:
            print(f"测量数据已存在于报告ID: {report_id}")
            return False
        
        # Insert each measurement
        for measurement in measurements:
            cursor.execute('''
            INSERT INTO measurements (
                report_id, measurement_id, step_type, name, result_type,
                result_value, status, unit_of_measure, lower_limit, upper_limit,
                test_time, comment, qm_meas_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                report_id,
                measurement.get('measurement_id', ''),
                measurement.get('step_type', ''),
                measurement.get('name', ''),
                measurement.get('result_type', ''),
                measurement.get('result_value', ''),
                measurement.get('status', ''),
                measurement.get('unit_of_measure', ''),
                measurement.get('lower_limit', ''),
                measurement.get('upper_limit', ''),
                measurement.get('test_time', ''),
                measurement.get('comment', ''),
                measurement.get('qm_meas_id', '')
            ))
        
        print(f"插入 {len(measurements)} 条测量数据: 报告ID {report_id}")
        return True
    except Exception as e:
        print(f"插入测量数据出错: {e}")
        return False

def main():
    """
    主函数，处理XML文件并存储到SQLite数据库中。
    """
    try:
        xml_directory = "testReports"
        db_path = "test_reports.sqlite"
        
        # 确保目录存在
        if not os.path.exists(xml_directory):
            print(f"目录不存在: {xml_directory}")
            return
            
        # 创建或连接数据库
        conn, cursor = create_database(db_path)
        
        if conn is None or cursor is None:
            return
        
        # 跟踪统计信息
        total_files = 0
        new_files = 0         # 新增文件数
        existing_files = 0     # 已存在文件数
        skipped_files = 0      # 跳过的文件数（由于错误或已存在数据）
        
        # 获取目录中的XML文件列表
        xml_files = [f for f in os.listdir(xml_directory) if f.endswith('.xml')]
        total_files = len(xml_files)
        
        print(f"开始处理 {total_files} 个XML文件...")
        
        # 处理每个XML文件
        for filename in xml_files:
            # XML文件的完整路径
            xml_path = os.path.join(xml_directory, filename)
            filename_base = filename.replace('.xml', '')
            
            # 开始数据库事务
            conn.execute('BEGIN TRANSACTION')
            
            try:
                # 首先检查文件是否已存在
                is_existing = check_file_exists(cursor, filename_base)
                
                if is_existing:
                    # 文件已存在，获取报告ID
                    print(f"找到已存在的文件: {filename_base}")
                    cursor.execute('''
                    SELECT id FROM test_reports 
                    WHERE filename = ?
                    ''', (filename_base,))
                    report_id = cursor.fetchone()[0]
                    existing_files += 1
                    
                    # 检查是否需要添加相关表数据
                    cursor.execute('SELECT COUNT(*) FROM test_info WHERE report_id = ?', (report_id,))
                    has_test_info = cursor.fetchone()[0] > 0
                    
                    cursor.execute('SELECT COUNT(*) FROM measurements WHERE report_id = ?', (report_id,))
                    has_measurements = cursor.fetchone()[0] > 0
                    
                    # 如果已有完整数据，则跳过
                    if has_test_info and has_measurements:
                        print(f"文件 {filename_base} 已有完整数据，跳过处理")
                        conn.commit()
                        skipped_files += 1  # 计入跳过计数
                        continue
                    
                    # 如果缺少关联表数据，解析XML并只插入缺少的部分
                    parsed_data = parse_xml_file(xml_path)
                    if parsed_data is None:
                        conn.rollback()
                        skipped_files += 1
                        continue
                    
                    # 插入缺少的test_info
                    if not has_test_info:
                        insert_test_info(cursor, report_id, parsed_data['test_info'])
                    
                    # 插入缺少的measurements
                    if not has_measurements:
                        insert_measurements(cursor, report_id, parsed_data['measurements'])
                    
                else:
                    # 新文件，完整处理
                    parsed_data = parse_xml_file(xml_path)
                    if parsed_data is None:
                        conn.rollback()
                        skipped_files += 1
                        continue
                    
                    # 插入测试报告基本信息
                    report_id = insert_test_report(cursor, parsed_data)
                    
                    if report_id is not None:
                        # 插入测试详细信息
                        insert_test_info(cursor, report_id, parsed_data['test_info'])
                        
                        # 插入测量数据
                        insert_measurements(cursor, report_id, parsed_data['measurements'])
                        
                        new_files += 1
                    else:
                        skipped_files += 1
                
                # 提交事务
                conn.commit()
            except Exception as e:
                # 事务出错，回滚
                conn.rollback()
                print(f"处理文件出错，回滚事务: {filename}, 错误: {e}")
                skipped_files += 1
        
        # 关闭数据库连接
        conn.close()
        
        print(f"处理完成！总共 {total_files} 个文件:")
        print(f"  - 新增: {new_files} 个")
        print(f"  - 已存在: {existing_files} 个")
        print(f"  - 跳过: {skipped_files} 个")
        
    except Exception as e:
        print(f"主程序出错: {e}")

if __name__ == '__main__':
    main()
