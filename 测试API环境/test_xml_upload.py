import requests
import json

# 测试 POST /api/import-xml 端点
def test_import_xml():
    url = "http://localhost:5000/api/import-xml"
    
    # 请求体 - 指定要处理的目录
    payload = {
        "directory": "testReports"  # 默认目录
    }
    
    # 发送请求
    response = requests.post(url, json=payload)
    
    # 打印响应状态和内容
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.status_code == 200

if __name__ == "__main__":
    print("测试 POST /api/import-xml 端点")
    success = test_import_xml()
    print(f"测试结果: {'成功' if success else '失败'}")