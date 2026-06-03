# 语义转 SQL Demo 工程说明

## 1. 项目概述

这是一个从自然语言到 SQL 的演示工程，目标是把用户输入的中文查询语句，逐层转换为结构化语义 DSL，再生成 SQL 并访问数据库，最终返回查询结果。

当前工程的核心链路如下：

```text
自然语言（Web / Agent）
        ↓
MCP Hub（网关，mcp-hub）
        ↓
   Auth Module（认证鉴权）
        ↓
Semantic Layer（定义层，semantic-layer）
        ↓
 Policy Engine（策略引擎，RBAC + ABAC）
        ↓
Metrics Engine（执行层，metrics-engine）
        ↓
DB（MySQL）
```

其中：

- `Web` 提供简单的自然语言输入页面。
- `Agent` 可以作为智能助手入口，调用 `MCP Hub` 的统一接口或工具接口。
- `MCP Hub` 负责聚合调用语义解析和指标执行。
- `Auth Module` 负责身份认证和 RBAC 权限检查，无效请求最早拦截。
- `Semantic Layer` 负责把自然语言转换为语义 DSL。
- `Policy Engine` 负责基于用户属性和语义结果做 ABAC 数据级权限过滤。
- `Metrics Engine` 负责把 DSL 转为 SQL，并执行数据库查询。
- `DB` 保存演示数据。

---

## 2. 工程目录

```text
ai-platform/
├─ auth-service/
│  ├─ main.py
│  ├─ users.py
│  ├─ external_auth.py
│  ├─ schema.py
│  ├─ start.sh
│  └─ start.bat
├─ policy-engine/
│  ├─ main.py
│  ├─ engine.py
│  ├─ config.py
│  ├─ schema.py
│  ├─ start.sh
│  └─ start.bat
├─ web/
│  └─ index.html
├─ mcp-hub/
│  ├─ main.py
│  └─ tools/
│     ├─ auth_tool.py
│     ├─ policy_tool.py
│     ├─ semantic_tool.py
│     └─ metrics_tool.py
├─ semantic-layer/
│  ├─ main.py
│  ├─ parser.py
│  ├─ schema.py
│  └─ models.py
├─ metrics-engine/
│  └─ main.py
└─ doc/
   ├─ create.sql
   ├─ inport.sql
   ├─ project-overview.md
   └─ product-introduction.md
```

---

## 3. 各模块职责

### 3.1 Web

目录：`web/index.html`

职责：

- 提供一个简单输入框，让用户输入自然语言查询。
- 调用网关接口 `/nl2sql?query=...`。
- 展示最终返回的语义结果、SQL 和数据结果。

示例输入：

- `查询总销售额`
- `查询所有销售记录`
- `查询正常销售订单金额`

---

### 3.2 Agent

`Agent` 是本 Demo 中的扩展角色，不一定必须有独立代码实现，但在整体架构中可以承担以下职责：

- 接收用户自然语言问题。
- 选择调用 `MCP Hub` 的统一接口 `/nl2sql`。
- 或者按工具化方式调用：
  - `/tool/semantic_parse`
  - `/tool/metrics_execute`
- 对最终结果进行解释、格式化或继续多轮追问。

适合的使用方式：

- Web 页面作为人工输入入口。
- Agent 作为智能编排入口。
- 两者最终都可以接入 `MCP Hub`。

---

### 3.3 MCP Hub

目录：`mcp-hub/`

职责：

- 作为统一网关，对外暴露查询入口。
- 接收自然语言请求。
- 调用 `Auth Module` 完成身份认证和 RBAC 权限检查。
- 先调用 `Semantic Layer` 完成语义解析。
- 再调用 `Metrics Engine` 执行 DSL 并产出 SQL 和数据。
- 把链路结果统一返回给调用方。

主要接口：

- `GET /`
- `GET /health`
- `GET /nl2sql?query=xxx`
- `POST /tool/semantic_parse`
- `POST /tool/metrics_execute`

返回结构示例：

```json
{
  "query": "查询正常销售订单金额",
  "semantic": {
    "intent": "query",
    "metrics": ["amount"],
    "dimensions": [],
    "filters": [
      {"field": "order_status", "op": "=", "value": 1},
      {"field": "order_type", "op": "=", "value": 2}
    ],
    "warnings": [],
    "limit": 100
  },
  "sql": "SELECT SUM(amount) AS amount FROM demo_orders WHERE order_status = 1 AND order_type = 2",
  "data": [],
  "status": "success"
}
```

---

### 3.4 Auth Module（认证鉴权）

目录：`auth-service/`

职责：

- 身份认证：验证 Token 有效性，确认用户身份。
- RBAC（基于角色的访问控制）：检查用户是否有权限执行查询操作。
- ABAC（基于属性的访问控制）：根据用户属性（部门、区域、角色等）动态生成数据过滤条件。

#### RBAC 模块

控制"谁能做什么操作"：

```python
ROLES = {
    "admin": ["query", "manage_users", "view_audit"],
    "analyst": ["query", "view_audit"],
    "viewer": ["query"],
}
```

#### ABAC 模块

控制"谁能看到什么数据"：

```python
POLICIES = {
    "sales_data": {
        "condition": "user.department == 'sales' OR user.role == 'admin'",
        "data_filter": {"region": "user.allowed_regions"},
    },
}
```

#### 权限检查点

| 阶段 | 权限类型 | 检查内容 | 拦截时机 |
|------|---------|---------|---------|
| **MCP Hub 入口** | 认证 + RBAC | 用户身份是否合法？是否有查询权限？ | 最早拦截，无效请求直接拒绝 |
| **Semantic Layer 后** | ABAC | 用户能查哪些数据？需要追加什么过滤条件？ | 语义解析后，SQL 生成前 |

---

### 3.5 Semantic Layer

目录：`semantic-layer/`

职责：

- 把自然语言解析为统一的语义 DSL。
- 识别指标、过滤条件、时间范围和告警信息。
- 作为“定义层”，屏蔽前端和执行层之间的语义差异。

当前已实现的语义能力：

#### 指标识别

- 包含 `条`、`数量`、`订单数`、`单`、`笔` 时，映射为 `order_cnt`
- 包含 `金额`、`销售额`、`总额`、`GMV` 时，映射为 `amount`
- 包含 `平均` 时，映射为 `avg_amount`（目前执行层未完全支持）

#### 条件识别

- `正常` -> `order_status = 1`
- `作废` -> `order_status = -1`
- `采购` -> `order_type = 1`
- `销售` -> `order_type = 2`

#### 时间解析

- 调用时间处理逻辑解析开始时间和结束时间
- 生成：
  - `create_time >= start`
  - `create_time <= end`

#### 回退策略

- 如果没有识别到指标，默认使用 `order_cnt`

语义 DSL 示例：

```json
{
  "intent": "query",
  "metrics": ["amount"],
  "dimensions": [],
  "filters": [
    {"field": "order_status", "op": "=", "value": 1},
    {"field": "order_type", "op": "=", "value": 2}
  ],
  "warnings": [],
  "limit": 100
}
```

---

### 3.6 Metrics Engine

目录：`metrics-engine/`

职责：

- 接收 `Semantic Layer` 输出的 DSL。
- 把指标名映射为真实 SQL 聚合表达式。
- 拼接 `SELECT / WHERE / GROUP BY`。
- 执行 SQL 并返回结果。

当前已实现的指标映射：

```python
METRIC_DEFS = {
    "amount": "SUM(amount)",
    "order_cnt": "COUNT(*)"
}
```

说明：

- `amount` 对应金额汇总。
- `order_cnt` 对应记录数统计。
- 如果传入未知指标，会返回 `unknown metric` 错误。

---

## 4. 数据库设计

数据库：`ai_platform`

数据表：`demo_orders`

建表脚本见：`doc/create.sql`

表结构如下：

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `order_id` | `INT UNSIGNED` | 订单号 |
| `order_name` | `VARCHAR(100)` | 订单名称 |
| `order_detail` | `TEXT` | 订单明细 |
| `order_type` | `TINYINT` | `1=采购，2=销售` |
| `amount` | `DECIMAL(12,2)` | 金额 |
| `order_status` | `TINYINT` | `-1=作废，1=正常` |
| `area` | `VARCHAR(50)` | 地区：`beijing`、`shanghai` |
| `create_time` | `DATETIME` | 创建时间 |

**测试用户与数据权限：**

| 用户 | Token | 角色 | 可见区域 |
|------|-------|------|---------|
| `cipher_op` | `token_cipher_op` | admin | 北京 + 上海 |
| `beijing` | `token_beijing` | viewer | 仅北京 |
| `shanghai` | `token_shanghai` | viewer | 仅上海 |

---

## 5. 请求处理流程

### 5.1 统一调用流程

1. 用户在 `web/index.html` 输入自然语言。
2. 页面调用 `MCP Hub` 的 `/nl2sql` 接口。
3. `MCP Hub` 调用 `Auth Module` 完成身份认证和 RBAC 权限检查。
   - 如果认证失败或无权限，直接返回 403。
4. `MCP Hub` 调用 `Semantic Layer` 的 `/semantic/parse`。
5. `Semantic Layer` 输出 DSL。
6. `MCP Hub` 调用 `Policy Engine` 完成 ABAC 数据级权限过滤。
   - 根据用户属性（部门、区域等）动态追加过滤条件到 DSL。
7. `MCP Hub` 再调用 `Metrics Engine` 的 `/execute`。
8. `Metrics Engine` 生成 SQL，并执行查询。
9. 结果返回给 `MCP Hub`。
10. `MCP Hub` 把语义结果、SQL 和数据统一返回前端或 Agent。

### 5.2 工具化调用流程

如果由 `Agent` 接入，也可以拆成两步：

1. 调用 `/tool/semantic_parse` 获取语义 DSL。
2. 调用 `/tool/metrics_execute` 获取 SQL 与数据结果。

这种方式更适合：

- 调试单独的语义解析能力
- 将 `Semantic Layer` 与 `Metrics Engine` 解耦调用
- 让 Agent 做更复杂的编排

### 5.3 权限检查流程

```
用户请求 → MCP Hub
              ↓
         Auth Module 检查
              ↓
         ❌ 无权限 → 返回 403
         ✅ 有权限 → 继续
              ↓
         Semantic Layer 解析
              ↓
         Policy Engine（ABAC）
              ↓
         根据用户属性追加数据过滤条件
              ↓
         Metrics Engine 执行
```

---

## 6. 示例演示

### 示例 1：查询正常销售订单金额

自然语言：

```text
查询正常销售订单金额
```

语义解析结果：

```json
{
  "intent": "query",
  "metrics": ["amount"],
  "dimensions": [],
  "filters": [
    {"field": "order_status", "op": "=", "value": 1},
    {"field": "order_type", "op": "=", "value": 2}
  ],
  "warnings": [],
  "limit": 100
}
```

生成 SQL：

```sql
SELECT
    SUM(amount) AS amount
FROM demo_orders
WHERE order_status = 1 AND order_type = 2
```

---

### 示例 2：查询订单数

自然语言：

```text
查询订单数
```

语义解析结果：

```json
{
  "intent": "query",
  "metrics": ["order_cnt"],
  "dimensions": [],
  "filters": [],
  "warnings": [],
  "limit": 100
}
```

生成 SQL：

```sql
SELECT
    COUNT(*) AS order_cnt
FROM demo_orders
```

---

### 示例 3：输入无法映射的维度

自然语言：

```text
查询北京销售金额
```

处理结果：

- 语义层会识别 `金额` -> `amount`
- 如果发现 `北京` 当前无法映射到表字段，会写入 `warnings`
- 执行层仍可能继续执行，但结果不包含城市过滤条件

---

## 7. 启动说明

### 7.1 准备数据库

1. 创建数据库：

```sql
CREATE DATABASE IF NOT EXISTS ai_platform DEFAULT CHARSET utf8mb4;
```

2. 执行建表脚本：

```sql
USE ai_platform;
SOURCE doc/create.sql;
```

### 7.2 启动服务

建议直接分别启动 3 个 FastAPI 服务。

#### 启动 Auth Service

```bash
cd auth-service
python -m uvicorn main:app --host 0.0.0.0 --port 8004
```

#### 启动 Policy Engine

```bash
cd policy-engine
python -m uvicorn main:app --host 0.0.0.0 --port 8005
```

#### 启动 Semantic Layer

```bash
cd semantic-layer
python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

#### 启动 Metrics Engine

```bash
cd metrics-engine
python -m uvicorn main:app --host 0.0.0.0 --port 8002
```

#### 启动 MCP Hub

```bash
cd mcp-hub
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 7.3 访问方式

- 前端页面：直接打开 `web/index.html`
- 网关健康检查：`http://127.0.0.1:8000/health`
- 认证服务：`http://127.0.0.1:8004`
- 策略引擎：`http://127.0.0.1:8005`
- 语义解析服务：`http://127.0.0.1:8001/semantic/parse`
- 执行引擎服务：`http://127.0.0.1:8002/execute`

说明：

- `web/index.html` 中的 `API_BASE` 当前为空字符串，默认请求同源地址。
- 如果前端与后端分开部署，需要把 `API_BASE` 改成 `MCP Hub` 的实际地址。
- MCP Hub `/nl2sql` 接口需要在请求头中携带 `X-Auth-Token`。

---

## 8. Demo 价值

这个 Demo 适合用于演示以下能力：

- 自然语言查询到 SQL 的转换链路
- 语义层与执行层解耦
- 指标定义与 SQL 执行分离
- Agent + MCP Hub 的可扩展架构
- 后续接入大模型、知识库、权限控制和多表语义建模

---

## 9. 后续可扩展方向

建议后续逐步补充以下能力：

- 支持更多指标，如平均值、最大值、最小值
- 支持维度分组，如按类型、按日期统计
- 支持排序、分页、TopN
- 支持多表 Join
- 支持语义字典配置化
- 支持基于 Agent 的多轮问答与自动补全条件
- 支持 SQL 安全控制与权限隔离
- **权限管理**：RBAC 角色权限 + ABAC 属性权限，实现细粒度数据访问控制
- **审计日志**：记录所有查询操作和权限决策，支持合规审计

---

## 10. 总结

本工程已经具备一个最小可运行的语义转 SQL Demo 的核心骨架：

- `web` 负责自然语言输入
- `mcp-hub` 负责网关编排
- `semantic-layer` 负责语义定义
- `metrics-engine` 负责 SQL 执行
- `db` 负责数据存储
- `agent` 可作为智能入口进行统一调用与增强编排

该结构适合作为后续扩展企业级 NL2SQL、语义分析平台或 Agent 查询助手的基础版本。
