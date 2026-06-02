# =========================
# 1. 字段语义映射（Dimension / Column）
# =========================

SEMANTIC_DICT = {
    # 金额类
    "订单金额": "amount",
    "金额": "amount",
    "销售额": "amount",

    # 订单基础字段
    "订单类型": "order_type",
    "订单号": "order_id",
    "订单名称": "order_name",
    "名称": "order_name",
    "订单明细": "order_detail",
    "明细": "order_detail",

    # 时间字段
    "创建时间": "create_time",
    "下单时间": "create_time"
}


# =========================
# 2. 枚举值映射（Value Mapping）
# =========================

ENUM_DICT = {
    "order_type": {
        "采购": 1,
        "销售": 2
    },
    "order_status": {
        "正常": 1,
        "作废": -1
    }
}


# =========================
# 3. 指标语义映射（Metric Layer）⭐核心新增
# =========================

METRIC_DICT = {
    # 订单计数类（核心）
    "条": "order_cnt",
    "数量": "order_cnt",
    "订单数": "order_cnt",
    "订单条数": "order_cnt",

    # 金额类指标
    "订单金额": "amount",
    "金额": "amount",
    "销售额": "amount",
    "总金额": "amount",

    # 可扩展指标（以后用）
    "平均金额": "avg_amount",
    "最大金额": "max_amount",

    # 利润/成本
    "成本": "cost",
    "利润": "profit",
}
