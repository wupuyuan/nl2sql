from config import SEMANTIC_CONFIG
from dictionary import SEMANTIC_DICT, ENUM_DICT, METRIC_DICT
from models import Filter, SemanticResponse
from time_utils import parse_time


def extract_metrics(query: str):
    """
    metric 解析：核心能力
    """

    metrics = []

    # 复合指标（优先识别）
    if "利润" in query:
        metrics.append("profit")

    if "成本" in query:
        metrics.append("cost")

    # COUNT类
    if any(k in query for k in ["条", "数量", "订单数", "单", "笔"]):
        metrics.append("order_cnt")

    # SUM类（利润/成本本身已是金额类，避免重复）
    if not metrics or not any(m in metrics for m in ["profit", "cost"]):
        if any(k in query for k in ["金额", "销售额", "总额", "GMV"]):
            metrics.append("amount")

    # AVG类（预留）
    if "平均" in query:
        metrics.append("avg_amount")

    return metrics


def parse(query: str):

    warnings = []
    filters = []
    metrics = []
    dimensions = []
    intent = "query"

    # =========================
    # 1. metric 解析（核心修复点）
    # =========================
    metrics = extract_metrics(query)

    # =========================
    # 2. order status（默认只查有效订单）
    # =========================
    if "作废" in query:
        filters.append(Filter(field="order_status", op="=", value=-1))
    elif "全部" in query or "所有" in query or "含作废" in query or "包括作废" in query:
        pass  # 不添加默认过滤
    else:
        # 默认只查有效订单
        filters.append(Filter(field="order_status", op="=", value=1))

    # =========================
    # 3. order type（利润/成本内部已处理 order_type，不再额外过滤）
    # =========================
    if "利润" not in query and "成本" not in query:
        if "采购" in query:
            filters.append(Filter(field="order_type", op="=", value=1))

        if "销售" in query:
            filters.append(Filter(field="order_type", op="=", value=2))

    # =========================
    # 4. time parsing
    # =========================
    start, end = parse_time(query)

    if start:
        filters.append(Filter(field="create_time", op=">=", value=start))
        filters.append(Filter(field="create_time", op="<=", value=end))

    # =========================
    # 5. unknown word warnings
    # =========================
    for word in query.split():

        if word in ["北京", "上海", "广州"]:
            warnings.append(f"字段[{word}]无法映射：当前表无该维度")

    # =========================
    # 6. fallback（非常重要）
    # =========================
    if not metrics:
        metrics.append("order_cnt")

    # =========================
    # 7. return DSL
    # =========================
    return SemanticResponse(
        intent=intent,
        metrics=metrics,
        dimensions=dimensions,
        filters=filters,
        warnings=warnings,
        limit=SEMANTIC_CONFIG["default_limit"]
    )
