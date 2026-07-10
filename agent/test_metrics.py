"""快速验证 metrics.yaml 中 SQL 模板是否能正确执行"""
import pymysql
import yaml
import os

# 用相对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

conn = pymysql.connect(
    host='127.0.0.1', port=3307,
    user='tr_user', password='tr_pass_2025',
    database='teacher_research', charset='utf8mb4'
)
c = conn.cursor()

# 读取指标
metrics_path = os.path.join(BASE_DIR, 'metrics.yaml')
with open(metrics_path, 'r', encoding='utf-8') as f:
    metrics = yaml.safe_load(f)

# 取第一个教师
c.execute('SELECT gh, xm, zc, dw_mc FROM t_jzg_jbxx LIMIT 1')
t = c.fetchone()
tid, name, title, dept = t
print(f'测试教师: {name} ({tid}), {dept}, {title}')
print()

# 参数
params = {
    ':teacher_id': f"'{tid}'",
    ':start_date': "'2022-01-01'",
    ':end_date': "'2025-12-31'",
    ':start_year': "'2022'",
    ':end_year': "'2025'",
}

# 测试关键指标
test_ids = [
    'project_count_leader', 'project_by_level', 
    'fund_total_arrived', 'fund_monthly_trend',
    'paper_first_author_count', 'paper_by_level',
    'patent_count', 'patent_by_type',
    'book_count', 'software_count',
    'award_count', 'award_by_level',
    'conference_hosted',
]

passed = 0
failed = 0

for m in metrics['metrics']:
    if m['id'] in test_ids:
        sql = m['sql_template']
        for k, v in params.items():
            sql = sql.replace(k, v)
        try:
            c.execute(sql)
            rows = c.fetchall()
            row_count = len(rows)
            if row_count == 1 and len(rows[0]) == 1 and rows[0][0] is not None:
                result = rows[0][0]
                print(f'  ✅ {m["id"]:30s} → {result}')
            elif m['chart_type'] == 'kpi_card':
                result = rows[0][0] if rows else 0
                print(f'  ✅ {m["id"]:30s} → {result}')
            else:
                print(f'  ✅ {m["id"]:30s} → {row_count} rows')
            passed += 1
        except Exception as e:
            print(f'  ❌ {m["id"]:30s} → {str(e)[:70]}')
            failed += 1

print()
print(f'通过: {passed}/{passed+failed}')
conn.close()
