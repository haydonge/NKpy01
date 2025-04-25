import requests
import json

# 测试基本URL
base_url = 'http://localhost:5000'

# 测试1: 测试支持字段筛选的通用查询端点
print("=== 测试1: 字段筛选的通用查询 ===")
response = requests.get(f"{base_url}/api/measurements?limit=2&fields=name,result_value,status")
print(f"状态码: {response.status_code}")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
print()

# 测试2: 测试字段筛选和多条件过滤
print("=== 测试2: 多条件过滤 ===")
response = requests.get(f"{base_url}/api/measurements?name=CheckRFSW&status=PASS&fields=name,result_value,status&limit=3")
print(f"状态码: {response.status_code}")
data = response.json()
print(f"总记录数: {data['total']}")
print(f"返回记录数: {len(data['measurements'])}")
print(json.dumps(data['measurements'][0], indent=2, ensure_ascii=False))  # 只显示第一条记录
print()

# 测试3: 测试统计分析功能
print("=== 测试3: 统计分析功能 ===")
response = requests.get(f"{base_url}/api/measurements/stats?name=CheckRFSW")
print(f"状态码: {response.status_code}")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
