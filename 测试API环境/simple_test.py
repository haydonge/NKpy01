import requests
import json

# 基本URL
base_url = 'http://localhost:5000'

# 测试1: 指定字段的查询
print('\n===== 测试1: 指定返回字段功能 ======')
response = requests.get(f'{base_url}/api/measurements?limit=1&fields=name,result_value,status')
data = response.json()
print(f'状态码: {response.status_code}')
print('返回数据:')
print(json.dumps(data, indent=2, ensure_ascii=False))

# 测试2: 使用过滤条件
print('\n===== 测试2: 过滤和分页功能 ======')
response = requests.get(f'{base_url}/api/measurements?name=CheckRFSW&limit=2&offset=0')
data = response.json()
print(f'状态码: {response.status_code}')
print(f'总记录数: {data["total"]}')
print(f'返回记录数: {len(data["measurements"])}')

# 测试3: 统计分析功能
print('\n===== 测试3: 统计分析功能 ======')
response = requests.get(f'{base_url}/api/measurements/stats?name=CheckRFSW')
data = response.json()
print(f'状态码: {response.status_code}')
print('统计结果:')
print(json.dumps(data, indent=2, ensure_ascii=False))
