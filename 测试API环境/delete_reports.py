import sqlite3
import os

# 数据库文件路径
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_reports.sqlite')

def delete_reports(start_id, end_id):
    """删除指定ID范围内的报告及其相关数据"""
    print(f"准备删除ID从 {start_id} 到 {end_id} 的报告数据...")
    
    try:
        # 连接到数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 开始事务
        conn.execute("BEGIN TRANSACTION")
        
        # 1. 获取要删除的report_ids
        cursor.execute(f"SELECT id FROM test_reports WHERE id BETWEEN {start_id} AND {end_id}")
        report_ids = [row[0] for row in cursor.fetchall()]
        
        if not report_ids:
            print(f"没有找到ID在 {start_id} 到 {end_id} 范围内的报告")
            conn.rollback()
            return
        
        print(f"找到 {len(report_ids)} 个报告需要删除: {report_ids}")
        
        # 2. 删除 measurements 表中的相关数据
        for report_id in report_ids:
            cursor.execute(f"DELETE FROM measurements WHERE report_id = {report_id}")
            deleted = cursor.rowcount
            print(f"删除了 {deleted} 条与报告 {report_id} 相关的测量数据")
        
        # 3. 删除 test_info 表中的相关数据
        for report_id in report_ids:
            cursor.execute(f"DELETE FROM test_info WHERE report_id = {report_id}")
            deleted = cursor.rowcount
            print(f"删除了 {deleted} 条与报告 {report_id} 相关的测试信息")
        
        # 4. 删除 test_reports 表中的数据
        cursor.execute(f"DELETE FROM test_reports WHERE id BETWEEN {start_id} AND {end_id}")
        deleted = cursor.rowcount
        print(f"删除了 {deleted} 条报告数据")
        
        # 提交事务
        conn.commit()
        print("所有数据已成功删除")
        
    except Exception as e:
        # 发生错误时回滚事务
        if conn:
            conn.rollback()
        print(f"删除过程中发生错误: {e}")
    finally:
        # 关闭连接
        if conn:
            conn.close()

if __name__ == "__main__":
    # 删除ID从37到47的报告数据
    delete_reports(37, 47)
