from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Any
import pymysql

app = FastAPI()


# =========================
# MySQL连接
# =========================

conn = pymysql.connect(
    host="127.0.0.1",
    user="ai",
    password="IryovBxgn$",
    database="ai_platform",
    charset="utf8mb4",
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=True
)


# =========================
# DSL定义
# =========================

class Filter(BaseModel):
    field: str
    op: str
    value: Any


class QueryDSL(BaseModel):
    metrics: List[str]
    dimensions: List[str] = []
    filters: List[Filter] = []


# =========================
# 指标仓库
# =========================

METRIC_DEFS = {
    "amount": "SUM(amount)",
    "order_cnt": "COUNT(*)",
    "cost": "SUM(CASE WHEN order_type = 1 THEN amount ELSE 0 END)",
    "profit": "SUM(CASE WHEN order_type = 2 THEN amount ELSE 0 END) - SUM(CASE WHEN order_type = 1 THEN amount ELSE 0 END)",
}


# =========================
# 健康检查
# =========================

@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# =========================
# 执行DSL
# =========================

@app.post("/execute")
def execute(dsl: QueryDSL):

    # -------------------------
    # SELECT
    # -------------------------

    select_parts = []

    if dsl.dimensions:
        select_parts.extend(dsl.dimensions)

    for metric in dsl.metrics:

        if metric not in METRIC_DEFS:
            return {
                "error": f"unknown metric: {metric}"
            }

        select_parts.append(
            f"{METRIC_DEFS[metric]} AS {metric}"
        )

    select_sql = ", ".join(select_parts)

    # -------------------------
    # WHERE
    # -------------------------

    where_parts = []

    # 默认过滤有效订单（除非 DSL 已指定 order_status）
    has_status_filter = any(f.field == "order_status" for f in dsl.filters)
    if not has_status_filter:
        where_parts.append("order_status = 1")

    for f in dsl.filters:

        if f.op == "in" and isinstance(f.value, list):
            # 处理 IN 操作符
            values = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in f.value])
            where_parts.append(f"{f.field} IN ({values})")
        elif isinstance(f.value, str):
            where_parts.append(
                f"{f.field} {f.op} '{f.value}'"
            )
        else:
            where_parts.append(
                f"{f.field} {f.op} {f.value}"
            )

    where_sql = ""

    if where_parts:
        where_sql = " WHERE " + " AND ".join(where_parts)

    # -------------------------
    # GROUP BY
    # -------------------------

    group_sql = ""

    if dsl.dimensions:
        group_sql = (
            " GROUP BY "
            + ", ".join(dsl.dimensions)
        )

    # -------------------------
    # 最终SQL
    # -------------------------

    sql = f"""
SELECT
    {select_sql}
FROM demo_orders
{where_sql}
{group_sql}
"""

    # -------------------------
    # 执行SQL
    # -------------------------

    try:

        with conn.cursor() as cursor:

            cursor.execute(sql)

            rows = cursor.fetchall()

        return {
            "status": "success",
            "sql": sql.strip(),
            "data": rows
        }

    except Exception as e:

        return {
            "status": "error",
            "sql": sql.strip(),
            "message": str(e)
        }
