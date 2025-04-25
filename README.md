# 测试报告 API 服务器

## 概述

这是一个基于Flask的API服务器，用于管理和查询XML测试报告数据。服务器将XML测试报告解析并存储在SQLite数据库中，并提供多个API端点用于数据检索和分析。

## 功能特点

- XML测试报告的解析和导入
- 测试报告的基本信息查询
- 详细的测量数据查询（支持字段选择和过滤）
- 测量数据的统计分析
- 全文件上传和目录批量处理

## 数据库结构

本系统采用SQLite数据库，主要有三张核心表：

### 1. test_reports（测试报告主表）
| 字段名         | 类型      | 说明              |
| -------------- | --------- | ----------------- |
| id             | INTEGER   | 主键，自增        |
| filename       | TEXT      | 文件名，唯一      |
| serial_number  | TEXT      | 序列号            |
| part_number    | TEXT      | 部件号            |
| tester_id      | TEXT      | 测试工位/设备ID   |
| test_sub       | TEXT      | 子测试编号        |
| date           | TEXT      | 测试日期（YYYYMMDD）|
| time           | TEXT      | 测试时间（HHMMSS）|
| result         | TEXT      | 测试结果（Pass/Fail）|

### 2. test_info（测试信息表）
| 字段名                | 类型      | 说明                |
| --------------------- | --------- | ------------------- |
| id                    | INTEGER   | 主键，自增          |
| report_id             | INTEGER   | 外键，关联test_reports(id) |
| file_name             | TEXT      | 文件名              |
| swift_version         | TEXT      | 测试脚本版本        |
| test_spec_id          | TEXT      | 测试规范ID          |
| operator_id           | TEXT      | 操作员ID            |
| tester_serial_number  | TEXT      | 测试仪序列号        |
| tester_ot_number      | TEXT      | 测试仪OT号          |
| tester_sw_version     | TEXT      | 测试仪软件版本      |
| tester_hw_version     | TEXT      | 测试仪硬件版本      |
| tester_site           | TEXT      | 测试站点            |
| tester_operation      | TEXT      | 测试操作            |
| dut_serial_number     | TEXT      | DUT序列号           |
| dut_product_code      | TEXT      | DUT产品编码         |
| dut_product_revision  | TEXT      | DUT产品版本         |
| custom_attributes     | TEXT      | 自定义属性          |
| setup_time            | TEXT      | 上架时间            |
| test_time             | TEXT      | 测试时间            |
| unload_time           | TEXT      | 下架时间            |
| test_start            | TEXT      | 测试开始时间        |
| test_stop             | TEXT      | 测试结束时间        |
| overall_status        | TEXT      | 总体状态            |
| diagnostics_type      | TEXT      | 诊断类型            |
| diagnostics_value     | TEXT      | 诊断值              |

### 3. measurements（测量数据表）
| 字段名           | 类型      | 说明                |
| ---------------- | --------- | ------------------- |
| id               | INTEGER   | 主键，自增          |
| report_id        | INTEGER   | 外键，关联test_reports(id) |
| measurement_id   | TEXT      | 测量项ID            |
| step_type        | TEXT      | 步骤类型            |
| name             | TEXT      | 测量项名称          |
| result_type      | TEXT      | 结果类型            |
| result_value     | TEXT      | 结果值              |
| status           | TEXT      | 状态（PASS/FAIL）   |
| unit_of_measure  | TEXT      | 单位                |
| lower_limit      | TEXT      | 下限                |
| upper_limit      | TEXT      | 上限                |
| test_time        | TEXT      | 测试时间            |
| comment          | TEXT      | 备注                |
| qm_meas_id       | TEXT      | 质量管理测量ID      |

> 说明：
> - test_reports 为所有测试的主索引。
> - test_info 存储每个报告的详细测试信息。
> - measurements 存储与报告相关的所有测量数据。

---

## 安装

### 依赖项

```
pip install flask
```

### 设置

1. 克隆或下载本仓库
2. 确保您有正确的XML测试报告文件在 `testReports`目录中，或创建此目录
3. 运行服务器：

```bash
python simple_api_server.py
```

服务器将在 http://localhost:5000 上启动。

## API 端点

### 状态检查

```
GET /api/status
```

返回服务器状态和基本信息。

### 测试报告

#### 获取所有测试报告

```
GET /api/reports
```

查询参数：

- `limit`: 返回结果数量上限（默认100）
- `offset`: 分页偏移量（默认0）
- `serial_number`: 按序列号筛选（支持模糊匹配）
- `part_number`: 按部件号筛选（支持模糊匹配）
- `result`: 按测试结果筛选（Pass/Fail）

#### 获取单个测试报告详情

```
GET /api/reports/<report_id>
```

返回指定ID的测试报告详细信息，包括基本信息、测试信息和测量数据。

### 统计数据

#### 按结果统计

```
GET /api/statistics/results
```

返回按测试结果（Pass/Fail）分组的统计数据。

#### 按日期统计

```
GET /api/statistics/by-date
```

返回按日期分组的测试报告统计数据。

#### 每日良率统计（推荐前端使用）

```
GET /api/statistics/daily-yield
```

返回每一天的测试总数、通过数、不良数和良率（百分比），结构如下：

```json
[
  { "date": "2025-04-23", "total": 100, "pass": 95, "fail": 5, "yield": 95.0 },
  ...
]
```

此接口用于前端仪表盘直接展示最近N天的测试良率，无需前端自行聚合。
### 测量数据

#### 获取测量数据（支持字段选择）

```
GET /api/measurements
```

查询参数：

- `fields`: 要返回的字段列表，用逗号分隔（例如：`fields=name,result_value,test_time`）
- `name`: 按测试项目名称筛选
- `report_id`: 按报告ID筛选
- `status`: 按状态筛选（PASS或FAIL）
- `limit`: 返回结果数量上限（默认100）
- `offset`: 分页偏移量（默认0）

#### 获取所有测量项目名称

```
GET /api/measurements/names
```

返回数据库中所有唯一的测量项目名称及其计数。

#### 按名称获取测量结果

```
GET /api/measurements/by-name/<name>
```

查询参数：

- `limit`: 返回结果数量上限（默认100）
- `offset`: 分页偏移量（默认0）

#### 获取测量统计数据

```
GET /api/measurements/stats
```

查询参数：

- `name`: 测试项目名称（必填）

返回指定测量项目的统计信息，包括：

- 总计数
- 通过/失败计数和通过率
- 测试时间统计（最小值、最大值、平均值）
- 数值类型测量的值统计（最小值、最大值、平均值）
- 上下限值
- 使用的单位

### XML文件处理

本系统支持三种XML导入方式，适应不同场景：

#### 1. 批量导入目录（后端解析）

```
POST /api/import-xml
```
- 适用：后端直接扫描指定目录（如 testReports），批量解析所有XML文件。
- 请求体（JSON）：
  - `directory`: 要处理的XML文件目录（默认为'testReports'）

#### 2. 单文件上传（后端解析）

```
POST /api/upload-xml
```
- 适用：通过表单上传单个XML文件，由后端解析。
- 请求体（multipart/form-data）：
  - `file`: 要上传的XML文件

#### 3. 前端解析XML为JSON后上传

```
POST /api/upload-xml-json
```
- 适用：前端解析XML，转为结构化JSON后上传（适合浏览器环境、可自定义解析逻辑）。
- 请求体（application/json）：
  - `filename_info`: 文件名解析信息
  - `test_info`: 测试信息
  - `measurements`: 测量数据数组

建议：
- 批量历史导入建议用“批量导入目录”。
- 网页交互/单文件上传可用“单文件上传”或“前端解析后上传JSON”。

## 示例

### 获取带字段选择的测量数据

请求：

```
GET /api/measurements?fields=name,result_value,status&limit=2
```

响应：

```json
{
  "limit": 2,
  "measurements": [
    {
      "name": "CheckRFSW",
      "result_value": "BuildName:rfsw-package-fru6_0x620AD0DC",
      "status": "PASS"
    },
    {
      "name": "CheckRFSW",
      "result_value": "BuildVersion:rfsw-package-fru6_0x620AD0DC",
      "status": "PASS"
    }
  ],
  "offset": 0,
  "total": 7720
}
```

### 获取测量统计数据

请求：

```
GET /api/measurements/stats?name=CheckRFSW
```

响应：

```json
{
  "name": "CheckRFSW",
  "statistics": {
    "avg_test_time": 12.14,
    "fail_count": 0,
    "lower_limit": "BuildName:rfsw-package-fru6_0x620AD0DC",
    "max_test_time": 17,
    "min_test_time": 10,
    "pass_count": 35,
    "pass_rate": 100.0,
    "total_count": 35,
    "unit_of_measure": "NA",
    "upper_limit": "BuildName:rfsw-package-fru6_0x620AD0DC"
  }
}
```

## 数据库结构

该API使用SQLite数据库，主要包含以下表：

- `test_reports`: 存储测试报告基本信息
- `test_info`: 存储测试设备和环境信息
- `measurements`: 存储测量数据

## 故障排除

- 确保 `test_reports.sqlite`数据库文件存在并可访问
- 检查XML文件格式是否符合预期
- 检查API调用的URL和参数格式是否正确

## 使用提示

- 使用 `fields`参数可以减少返回数据量，提高API性能
- 使用 `limit`和 `offset`参数进行分页请求，避免一次性返回过多数据
- 使用统计API可以快速获取测量数据的概览信息，而无需获取全部详细记录
