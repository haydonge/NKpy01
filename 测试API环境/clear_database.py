#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
清空数据库中的所有数据，但保留表结构

用法：
    python clear_database.py

可选参数：
    --db DATABASE: 指定数据库文件路径，默认为 'test_reports.sqlite'
    --backup: 在清空前创建数据库备份
"""

import os
import sqlite3
import argparse
import shutil
import datetime

# 默认数据库文件
DEFAULT_DB = 'test_reports.sqlite'

def backup_database(db_file):
    """
    在清空数据库前创建备份
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{os.path.splitext(db_file)[0]}_{timestamp}_backup.sqlite"
    
    if os.path.exists(db_file):
        print(f"创建数据库备份: {backup_file}")
        shutil.copy2(db_file, backup_file)
        return backup_file
    return None

def clear_database(db_file, create_backup=False):
    """
    清空数据库中的所有表，但保留表结构
    """
    # 如果数据库文件不存在，给出提示并退出
    if not os.path.exists(db_file):
        print(f"错误: 数据库文件 '{db_file}' 不存在")
        return False
    
    # 创建备份（如果需要）
    if create_backup:
        backup_file = backup_database(db_file)
        if backup_file:
            print(f"备份已创建: {backup_file}")
    
    try:
        # 连接到数据库
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 启用外键约束
        cursor.execute('PRAGMA foreign_keys = OFF')
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()
        
        # 开始事务
        conn.execute('BEGIN TRANSACTION')
        
        # 清空每个表
        for table in tables:
            table_name = table[0]
            print(f"清空表: {table_name}")
            cursor.execute(f"DELETE FROM {table_name}")
        
        # 重置自增ID
        for table in tables:
            table_name = table[0]
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}'")
        
        # 提交更改
        conn.commit()
        print("所有表已清空，数据库结构保留")
        
        # 重新启用外键约束
        cursor.execute('PRAGMA foreign_keys = ON')
        
        # 运行VACUUM优化数据库文件大小
        print("优化数据库文件大小...")
        cursor.execute('VACUUM')
        
        # 关闭连接
        conn.close()
        return True
        
    except sqlite3.Error as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"清空数据库时出错: {e}")
        return False

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='清空数据库中的所有数据，但保留表结构')
    parser.add_argument('--db', default=DEFAULT_DB, help=f'数据库文件路径（默认: {DEFAULT_DB}）')
    parser.add_argument('--backup', action='store_true', help='在清空前创建数据库备份')
    args = parser.parse_args()
    
    # 显示确认提示
    print(f"警告: 即将清空数据库 '{args.db}' 中的所有数据!")
    confirm = input("确定要继续吗? (y/n): ").strip().lower()
    
    if confirm == 'y':
        if clear_database(args.db, args.backup):
            print("数据库清空完成")
    else:
        print("操作已取消")

if __name__ == '__main__':
    main()
