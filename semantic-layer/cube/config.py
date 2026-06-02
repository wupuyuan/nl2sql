from .schema import Metric, Dimension, Filter, CubeConfig

ORDERS_METRIC = Metric(
    name="order_cnt",
    display_name="订单数量",
    expression="COUNT(*)",
    description="订单总数",
    table="orders",
    format="int",
)

TOTAL_AMOUNT_METRIC = Metric(
    name="total_amount",
    display_name="订单总金额",
    expression="SUM(amount)",
    description="订单金额总和",
    table="orders",
    format="decimal",
)

AVG_AMOUNT_METRIC = Metric(
    name="avg_amount",
    display_name="平均订单金额",
    expression="AVG(amount)",
    description="平均订单金额",
    table="orders",
    format="decimal",
)

MAX_AMOUNT_METRIC = Metric(
    name="max_amount",
    display_name="最大订单金额",
    expression="MAX(amount)",
    description="最大订单金额",
    table="orders",
    format="decimal",
)

MIN_AMOUNT_METRIC = Metric(
    name="min_amount",
    display_name="最小订单金额",
    expression="MIN(amount)",
    description="最小订单金额",
    table="orders",
    format="decimal",
)

PRODUCT_SALES_METRIC = Metric(
    name="product_sales",
    display_name="产品销售额",
    expression="SUM(amount)",
    description="按产品分组的销售额",
    table="orders",
    format="decimal",
)

PRODUCT_COUNT_METRIC = Metric(
    name="product_count",
    display_name="产品订单数",
    expression="COUNT(*)",
    description="按产品分组的订单数",
    table="orders",
    format="int",
)

ORDER_STATUS_FILTER = Filter(
    name="order_status",
    display_name="订单状态",
    field="order_status",
    type="enum",
    table="orders",
    values={"正常": 1, "作废": -1, "待处理": 0},
    description="订单状态筛选",
)

ORDER_TYPE_FILTER = Filter(
    name="order_type",
    display_name="订单类型",
    field="order_type",
    type="enum",
    table="orders",
    values={"采购": 1, "销售": 2, "退货": 3},
    description="订单类型筛选",
)

CATEGORY_FILTER = Filter(
    name="category",
    display_name="产品类别",
    field="category",
    type="string",
    table="orders",
    values={"电子产品": "electronics", "服装": "clothing", "食品": "food", "其他": "other"},
    description="产品类别筛选",
)

REGION_FILTER = Filter(
    name="region",
    display_name="地区",
    field="region",
    type="string",
    table="orders",
    values={"北京": "beijing", "上海": "shanghai", "广州": "guangzhou", "深圳": "shenzhen"},
    description="地区筛选",
)

PRODUCT_FILTER = Filter(
    name="product",
    display_name="产品",
    field="product_name",
    type="string",
    table="orders",
    values=None,
    description="产品名称筛选",
)

CREATE_TIME_DIMENSION = Dimension(
    name="create_time",
    display_name="创建时间",
    field="create_time",
    type="datetime",
    table="orders",
    is_time=True,
    time_format="%Y-%m-%d %H:%M:%S",
)

UPDATE_TIME_DIMENSION = Dimension(
    name="update_time",
    display_name="更新时间",
    field="update_time",
    type="datetime",
    table="orders",
    is_time=True,
    time_format="%Y-%m-%d %H:%M:%S",
)

PRODUCT_DIMENSION = Dimension(
    name="product",
    display_name="产品",
    field="product_name",
    type="string",
    table="orders",
    is_time=False,
)

CATEGORY_DIMENSION = Dimension(
    name="category",
    display_name="产品类别",
    field="category",
    type="string",
    table="orders",
    is_time=False,
)

REGION_DIMENSION = Dimension(
    name="region",
    display_name="地区",
    field="region",
    type="string",
    table="orders",
    is_time=False,
)

ORDER_STATUS_DIMENSION = Dimension(
    name="order_status",
    display_name="订单状态",
    field="order_status",
    type="enum",
    table="orders",
    is_time=False,
)

ORDER_TYPE_DIMENSION = Dimension(
    name="order_type",
    display_name="订单类型",
    field="order_type",
    type="enum",
    table="orders",
    is_time=False,
)

ORDERS_CUBE = CubeConfig(
    name="orders",
    display_name="订单数据",
    description="订单数据立方体，包含订单数量、金额等指标",
    table="orders",
    primary_key="order_id",
    metrics=[
        ORDERS_METRIC,
        TOTAL_AMOUNT_METRIC,
        AVG_AMOUNT_METRIC,
        MAX_AMOUNT_METRIC,
        MIN_AMOUNT_METRIC,
        PRODUCT_SALES_METRIC,
        PRODUCT_COUNT_METRIC,
    ],
    dimensions=[
        PRODUCT_DIMENSION,
        CATEGORY_DIMENSION,
        REGION_DIMENSION,
        ORDER_STATUS_DIMENSION,
        ORDER_TYPE_DIMENSION,
    ],
    filters=[
        ORDER_STATUS_FILTER,
        ORDER_TYPE_FILTER,
        CATEGORY_FILTER,
        REGION_FILTER,
        PRODUCT_FILTER,
    ],
    time_dimensions=[
        CREATE_TIME_DIMENSION,
        UPDATE_TIME_DIMENSION,
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
    "产品销售额": "product_sales",
    "产品订单数": "product_count",
}

DIMENSION_NAME_MAP = {
    "产品": "product",
    "产品名称": "product",
    "商品": "product",
    "类别": "category",
    "分类": "category",
    "产品类别": "category",
    "地区": "region",
    "区域": "region",
    "城市": "region",
    "订单状态": "order_status",
    "状态": "order_status",
    "订单类型": "order_type",
    "类型": "order_type",
    "创建时间": "create_time",
    "下单时间": "create_time",
    "下单日期": "create_time",
    "更新时间": "update_time",
}

FILTER_NAME_MAP = {
    "正常": ("order_status", 1),
    "作废": ("order_status", -1),
    "待处理": ("order_status", 0),
    "采购": ("order_type", 1),
    "销售": ("order_type", 2),
    "退货": ("order_type", 3),
    "电子产品": ("category", "electronics"),
    "服装": ("category", "clothing"),
    "食品": ("category", "food"),
    "其他": ("category", "other"),
    "北京": ("region", "beijing"),
    "上海": ("region", "shanghai"),
    "广州": ("region", "guangzhou"),
    "深圳": ("region", "shenzhen"),
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
