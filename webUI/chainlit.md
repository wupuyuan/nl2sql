# 📋 数据结构说明

## 数据表：`demo_orders`

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `order_id` | INT | 订单号（主键） |
| `order_name` | VARCHAR(100) | 订单名称 |
| `order_detail` | TEXT | 订单明细 |
| `order_type` | TINYINT | 1=采购，2=销售 |
| `amount` | DECIMAL(12,2) | 金额 |
| `order_status` | TINYINT | 1=正常，-1=作废 |
| `create_time` | DATETIME | 创建时间 |

---

### 可用指标

| 指标 | 含义 |
|------|------|
| `order_cnt` | 订单数量 |
| `amount` | 订单总金额 |
| `avg_amount` | 平均订单金额 |
| `max_amount` | 最大订单金额 |
| `min_amount` | 最小订单金额 |
| `cost` | 成本（有效采购订单总金额） |
| `profit` | 利润（有效销售 - 有效采购） |

---

### 可用维度

- `order_name`（订单名称）
- `order_detail`（订单明细）
- `order_status`（订单状态）
- `order_type`（订单类型）
- `create_time`（创建时间）

---

### 常用查询示例

- 查一下总销售额
- 本月采购订单数
- 利润是多少
- 成本统计
