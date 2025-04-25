import os
import json
import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS

# 导入现有的解析和数据库函数
from 测试API环境.parse_xml_to_sqlite import (
    create_database, 
    insert_test_report, 
    insert_test_info, 
    insert_measurements
)

# 创建一个简单的 Flask 应用，仅用于处理 JSON 上传
app = Flask(__name__)
CORS(app)

# 数据库配置
DATABASE = 'test_reports.sqlite'

@app.route('/api/upload-xml-json', methods=['POST'])
def upload_xml_json():
    """
    接收前端解析后的 XML JSON 数据，写入数据库
    
    JSON 结构应包含:
    - filename_info: 文件名解析信息
    - test_info: 测试信息
    - measurements: 测量数据
    """
    try:
        # 获取 JSON 数据
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '未接收到 JSON 数据'
            }), 400
            
        # 确保数据结构完整
        if 'filename_info' not in data or 'test_info' not in data or 'measurements' not in data:
            return jsonify({
                'success': False,
                'message': 'JSON 数据结构不完整，需要 filename_info, test_info 和 measurements'
            }), 400
        
        # 创建或连接数据库
        create_database(DATABASE)
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # 准备插入数据库的报告对象
        report = {
            'filename': data['filename_info']['filename'],
            'filename_info': data['filename_info']
        }
        
        # 插入测试报告信息
        report_id = insert_test_report(cursor, report)
        if report_id is None:
            conn.close()
            return jsonify({
                'success': False,
                'message': '插入测试报告失败'
            }), 500
        
        # 插入测试信息
        insert_test_info(cursor, report_id, data['test_info'])
        
        # 插入测量数据
        insert_measurements(cursor, report_id, data['measurements'])
        
        # 提交事务并关闭连接
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'JSON 数据已成功写入数据库',
            'report_id': report_id
        })
        
    except Exception as e:
        print(f"处理 JSON 数据出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'处理出错: {str(e)}'
        }), 500

# 仅当直接运行此文件时启动服务器
if __name__ == '__main__':
    # 确保数据库和上传目录存在
    os.makedirs('uploads', exist_ok=True)
    
    # 启动服务器
    print('JSON API 服务将在 http://localhost:5001 运行')
    print('此服务仅处理前端解析后的 XML JSON 数据')
    app.run(debug=True, port=5001)
