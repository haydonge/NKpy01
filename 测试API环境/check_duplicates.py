import sqlite3
import os

# 自动查找数据库文件
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'test_reports.sqlite')

def check_duplicates():
    if not os.path.exists(DB_PATH):
        print(f'数据库文件不存在: {DB_PATH}')
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # 查找重复的filename
    sql = '''
    SELECT filename, COUNT(*) as cnt
    FROM test_reports
    GROUP BY filename
    HAVING cnt > 1
    '''
    cur.execute(sql)
    rows = cur.fetchall()
    if not rows:
        print('未发现重复的filename。')
    else:
        print('发现重复的filename如下：')
        for filename, cnt in rows:
            print(f'\n文件名: {filename} 出现 {cnt} 次')
            # 查询所有该filename的记录
            cur.execute('SELECT id, filename, serial_number, part_number, tester_id, date, time, result FROM test_reports WHERE filename = ?', (filename,))
            all_rows = cur.fetchall()
            for r in all_rows:
                print(f'  id={r[0]}, serial={r[2]}, part={r[3]}, tester={r[4]}, date={r[5]}, time={r[6]}, result={r[7]}')
                # 关联展示test_info
                cur.execute('SELECT * FROM test_info WHERE report_id=?', (r[0],))
                infos = cur.fetchall()
                for info in infos:
                    print(f'    [test_info] {info}')
                # 关联展示measurements
                cur.execute('SELECT * FROM measurements WHERE report_id=? LIMIT 3', (r[0],))
                meas = cur.fetchall()
                if meas:
                    print(f'    [measurements] 前3条:')
                    for m in meas:
                        print(f'      {m}')
                else:
                    print(f'    [measurements] 无')
            # 提示是否仅保留一条
            ans = input(f'是否仅保留一条，删除其它 {cnt-1} 条，并同步删除相关 test_info 和 measurements？(y/n)：').strip().lower()
            if ans == 'y':
                # 按id升序保留最早一条，其余删除
                ids = [r[0] for r in all_rows]
                keep_id = ids[0]
                del_ids = ids[1:]
                if del_ids:
                    # 先删子表
                    cur.executemany('DELETE FROM test_info WHERE report_id=?', [(i,) for i in del_ids])
                    cur.executemany('DELETE FROM measurements WHERE report_id=?', [(i,) for i in del_ids])
                    cur.executemany('DELETE FROM test_reports WHERE id=?', [(i,) for i in del_ids])
                    conn.commit()
                    print(f'已删除 {len(del_ids)} 条，仅保留 id={keep_id}，相关 test_info 和 measurements 也已删除')
                else:
                    print('无需删除。')
            else:
                print('未做删除。')
    conn.close()

if __name__ == '__main__':
    check_duplicates()
