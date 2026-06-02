from .schema import Metric, Dimension, Filter, CubeConfig

ORDERS_METRIC = Metric(
    name="order_cnt",
    display_name="订单数量",
    expression="COUNT(*)",
    description="订单总数",
    table="demo_orders",
    format="int",
)

TOTAL_AMOUNT_METRIC = Metric(
    name="total_amount",
    display_name="订单总金额",
    expression="SUM(amount)",
    description="订单金额总和",
    table="demo_orders",
    format="decimal",
)

AVG_AMOUNT_METRIC = Metric(
    name="avg_amount",
    display_name="平均订单金额",
    expression="AVG(amount)",
    description="平均订单金额",
    table="demo_orders",
    format="decimal",
)

MAX_AMOUNT_METRIC = Metric(
    name="max_amount",
    display_name="最大订单金额",
    expression="MAX(amount)",
    description="最大订单金额",
    table="demo_orders",
    format="decimal",
)

MIN_AMOUNT_METRIC = Metric(
    name="min_amount",
    display_name="最小订单金额",
    expression="MIN(amount)",
    description="最小订单金额",
    table="demo_orders",
    format="decimal",
)

COST_METRIC = Metric(
    name="cost",
    display_name="成本",
    expression="SUM(CASE WHEN order_type = 1 THEN amount ELSE 0 END)",
    description="有效的采购订单总金额",
    table="demo_orders",
    format="decimal",
)

PROFIT_METRIC = Metric(
    name="profit",
    display_name="利润",
    expression="SUM(CASE WHEN order_type = 2 THEN amount ELSE 0 END) - SUM(CASE WHEN order_type = 1 THEN amount ELSE 0 END)",
    description="有效的销售订单总金额 - 有效的采购订单总金额",
    table="demo_orders",
    format="decimal",
)

ORDER_STATUS_FILTER = Filter(
    name="order_status",
    display_name="订单状态",
    field="order_status",
    type="enum",
    table="demo_orders",
    values={"正常": 1, "作废": -1},
    description="订单状态筛选",
)

ORDER_TYPE_FILTER = Filter(
    name="order_type",
    display_name="订单类型",
    field="order_type",
    type="enum",
    table="demo_orders",
    values={"采购": 1, "销售": 2},
    description="订单类型筛选",
)

CREATE_TIME_DIMENSION = Dimension(
    name="create_time",
    display_name="创建时间",
    field="create_time",
    type="datetime",
    table="demo_orders",
    is_time=True,
    time_format="%Y-%m-%d %H:%M:%S",
)

ORDER_NAME_DIMENSION = Dimension(
    name="order_name",
    display_name="订单名称",
    field="order_name",
    type="string",
    table="demo_orders",
    is_time=False,
)

ORDER_DETAIL_DIMENSION = Dimension(
    name="order_detail",
    display_name="订单明细",
    field="order_detail",
    type="string",
    table="demo_orders",
    is_time=False,
)

ORDER_STATUS_DIMENSION = Dimension(
    name="order_status",
    display_name="订单状态",
    field="order_status",
    type="enum",
    table="demo_orders",
    is_time=False,
)

ORDER_TYPE_DIMENSION = Dimension(
    name="order_type",
    display_name="订单类型",
    field="order_type",
    type="enum",
    table="demo_orders",
    is_time=False,
)

ORDERS_CUBE = CubeConfig(
    name="orders",
    display_name="订单数据",
    description="订单数据立方体，包含订单数量、金额等指标",
    table="demo_orders",
    primary_key="order_id",
    metrics=[
        ORDERS_METRIC,
        TOTAL_AMOUNT_METRIC,
        AVG_AMOUNT_METRIC,
        MAX_AMOUNT_METRIC,
        MIN_AMOUNT_METRIC,
        COST_METRIC,
        PROFIT_METRIC,
    ],
    dimensions=[
        ORDER_STATUS_DIMENSION,
        ORDER_TYPE_DIMENSION,
        ORDER_NAME_DIMENSION,
    ],
    filters=[
        ORDER_STATUS_FILTER,
        ORDER_TYPE_FILTER,
    ],
    time_dimensions=[
        CREATE_TIME_DIMENSION,
    ],
    default_limit=100,
    cache_ttl=300,
)

ALL_CUBES = {
    ORDERS_CUBE.name: ORDERS_CUBE,
}

CUBE_NAME_MAP = {
    "订单": "orders",
    "orders": "orders",
    "销售": "orders",
    "采购": "orders",
    "交易": "orders",
}

METRIC_NAME_MAP = {
    "订单数量": "order_cnt",
    "订单数": "order_cnt",
    "订单条数": "order_cnt",
    "条数": "order_cnt",
    "数量": "order_cnt",
    "条": "order_cnt",
    "总金额": "total_amount",
    "总额": "total_amount",
    "销售额": "total_amount",
    "金额": "total_amount",
    "平均金额": "avg_amount",
    "平均值": "avg_amount",
    "最大金额": "max_amount",
    "最大值": "max_amount",
    "最小金额": "min_amount",
    "最小值": "min_amount",
    "成本": "cost",
    "利润": "profit",
}

DIMENSION_NAME_MAP = {
    "订单名称": "order_name",
    "名称": "order_name",
    "订单明细": "order_detail",
    "明细": "order_detail",
    "订单状态": "order_status",
    "状态": "order_status",
    "订单类型": "order_type",
    "类型": "order_type",
    "创建时间": "create_time",
    "下单时间": "create_time",
    "下单日期": "create_time",
}

FILTER_NAME_MAP = {
    "正常": ("order_status", 1),
    "作废": ("order_status", -1),
    "采购": ("order_type", 1),
    "销售": ("order_type", 2),
}

TIME_KEYWORDS = {
    "今天": "today",
    "昨天": "yesterday",
    "本周": "this_week",
    "上周": "last_week",
    "本月": "this_month",
    "上月": "last_month",
    "今年": "this_year",
    "去年": "last_year",
    "近7天": "last_7_days",
    "近30天": "last_30_days",
    "近90天": "last_90_days",
}

SEMANTIC_CONFIG = {
    "default_limit": 100,
    "max_limit": 10000,
    "cache_ttl": 300,
    "supported_cubes": list(ALL_CUBES.keys()),
}
