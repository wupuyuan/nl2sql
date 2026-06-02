from datetime import datetime, timedelta
from typing import List, Optional, Any, Dict

from .config import (
    ALL_CUBES,
    CUBE_NAME_MAP,
    METRIC_NAME_MAP,
    DIMENSION_NAME_MAP,
    FILTER_NAME_MAP,
    TIME_KEYWORDS,
    ORDERS_CUBE,
)
from .schema import CubeConfig, Metric, Dimension, Filter


class CubeEngine:
    """Cube 查询引擎"""

    def __init__(self):
        self.cubes = ALL_CUBES
        self._cache: Dict[str, Any] = {}

    def get_cube(self, cube_name: str) -> Optional[CubeConfig]:
        """获取 Cube 配置"""
        return self.cubes.get(cube_name)

    def list_cubes(self) -> List[Dict[str, Any]]:
        """列出所有 Cube"""
        return [
            {
                "name": cube.name,
                "display_name": cube.display_name,
                "description": cube.description,
                "metrics_count": len(cube.metrics),
                "dimensions_count": len(cube.dimensions),
                "filters_count": len(cube.filters),
            }
            for cube in self.cubes.values()
        ]

    def get_cube_details(self, cube_name: str) -> Optional[Dict[str, Any]]:
        """获取 Cube 详细信息"""
        cube = self.get_cube(cube_name)
        if not cube:
            return None

        return {
            "name": cube.name,
            "display_name": cube.display_name,
            "description": cube.description,
            "table": cube.table,
            "primary_key": cube.primary_key,
            "metrics": [
                {
                    "name": m.name,
                    "display_name": m.display_name,
                    "expression": m.expression,
                    "format": m.format,
                }
                for m in cube.metrics
            ],
            "dimensions": [
                {
                    "name": d.name,
                    "display_name": d.display_name,
                    "field": d.field,
                    "type": d.type,
                }
                for d in cube.dimensions
            ],
            "filters": [
                {
                    "name": f.name,
                    "display_name": f.display_name,
                    "field": f.field,
                    "values": f.values,
                }
                for f in cube.filters
            ],
            "time_dimensions": [
                {
                    "name": t.name,
                    "display_name": t.display_name,
                    "field": t.field,
                }
                for t in cube.time_dimensions
            ],
        }

    def resolve_cube(self, query: str) -> Optional[CubeConfig]:
        """从查询中解析 Cube 名称"""
        for keyword, cube_name in CUBE_NAME_MAP.items():
            if keyword in query:
                return self.get_cube(cube_name)
        return ORDERS_CUBE

    def resolve_metrics(self, query: str) -> List[Metric]:
        """从查询中解析指标"""
        metrics = []
        for keyword, metric_name in METRIC_NAME_MAP.items():
            if keyword in query:
                cube = self.resolve_cube(query)
                if cube:
                    for metric in cube.metrics:
                        if metric.name == metric_name:
                            metrics.append(metric)
                            break
        return metrics

    def resolve_dimensions(self, query: str) -> List[Dimension]:
        """从查询中解析维度"""
        dimensions = []
        for keyword, dim_name in DIMENSION_NAME_MAP.items():
            if keyword in query:
                cube = self.resolve_cube(query)
                if cube:
                    for dimension in cube.dimensions:
                        if dimension.name == dim_name:
                            dimensions.append(dimension)
                            break
        return dimensions

    def resolve_filters(self, query: str) -> List[Filter]:
        """从查询中解析过滤器"""
        filters = []
        for keyword, (filter_field, value) in FILTER_NAME_MAP.items():
            if keyword in query:
                cube = self.resolve_cube(query)
                if cube:
                    for filter_item in cube.filters:
                        if filter_item.name == filter_field:
                            filters.append(filter_item)
                            break
        return filters

    def resolve_time_range(self, query: str) -> Optional[Dict[str, Any]]:
        """从查询中解析时间范围"""
        for keyword, time_type in TIME_KEYWORDS.items():
            if keyword in query:
                return self._get_time_range(time_type)
        return None

    def _get_time_range(self, time_type: str) -> Dict[str, Any]:
        """获取时间范围"""
        now = datetime.now()

        time_ranges = {
            "today": {
                "start": now.replace(hour=0, minute=0, second=0).isoformat(),
                "end": now.replace(hour=23, minute=59, second=59).isoformat(),
            },
            "yesterday": {
                "start": (now - timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat(),
                "end": (now - timedelta(days=1)).replace(hour=23, minute=59, second=59).isoformat(),
            },
            "this_week": {
                "start": (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0).isoformat(),
                "end": now.replace(hour=23, minute=59, second=59).isoformat(),
            },
            "last_week": {
                "start": (now - timedelta(days=now.weekday() + 7)).replace(hour=0, minute=0, second=0).isoformat(),
                "end": (now - timedelta(days=now.weekday() + 1)).replace(hour=23, minute=59, second=59).isoformat(),
            },
            "this_month": {
                "start": now.replace(day=1, hour=0, minute=0, second=0).isoformat(),
                "end": now.replace(hour=23, minute=59, second=59).isoformat(),
            },
            "last_month": {
                "start": (now.replace(day=1) - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0).isoformat(),
                "end": (now.replace(day=1) - timedelta(days=1)).replace(hour=23, minute=59, second=59).isoformat(),
            },
            "this_year": {
                "start": now.replace(month=1, day=1, hour=0, minute=0, second=0).isoformat(),
                "end": now.replace(hour=23, minute=59, second=59).isoformat(),
            },
            "last_year": {
                "start": (now.replace(year=now.year - 1, month=1, day=1, hour=0, minute=0, second=0)).isoformat(),
                "end": (now.replace(year=now.year - 1, month=12, day=31, hour=23, minute=59, second=59)).isoformat(),
            },
            "last_7_days": {
                "start": (now - timedelta(days=7)).replace(hour=0, minute=0, second=0).isoformat(),
                "end": now.replace(hour=23, minute=59, second=59).isoformat(),
            },
            "last_30_days": {
                "start": (now - timedelta(days=30)).replace(hour=0, minute=0, second=0).isoformat(),
                "end": now.replace(hour=23, minute=59, second=59).isoformat(),
            },
            "last_90_days": {
                "start": (now - timedelta(days=90)).replace(hour=0, minute=0, second=0).isoformat(),
                "end": now.replace(hour=23, minute=59, second=59).isoformat(),
            },
        }

        return time_ranges.get(time_type, {})

    def build_query(self, query: str) -> Dict[str, Any]:
        """构建查询 DSL"""
        cube = self.resolve_cube(query)
        metrics = self.resolve_metrics(query)
        dimensions = self.resolve_dimensions(query)
        filters = self.resolve_filters(query)
        time_range = self.resolve_time_range(query)

        # 如果没有解析到指标，使用默认指标
        if not metrics:
            metrics = [m for m in cube.metrics if m.name == "order_cnt"][:1]

        # 构建过滤条件
        filter_conditions = []
        for filter_item in filters:
            if filter_item.values:
                # 枚举类型过滤器
                for keyword, value in filter_item.values.items():
                    if keyword in query:
                        filter_conditions.append({
                            "field": filter_item.field,
                            "op": "=",
                            "value": value,
                        })

        # 时间范围过滤
        if time_range and time_range.get("start"):
            filter_conditions.append({
                "field": "create_time",
                "op": ">=",
                "value": time_range["start"],
            })
            filter_conditions.append({
                "field": "create_time",
                "op": "<=",
                "value": time_range["end"],
            })

        return {
            "cube": cube.name,
            "metrics": [m.name for m in metrics],
            "dimensions": [d.name for d in dimensions],
            "filters": filter_conditions,
            "time_range": time_range,
            "limit": cube.default_limit,
            "sql": self._generate_sql(cube, metrics, dimensions, filter_conditions),
        }

    def _generate_sql(
        self,
        cube: CubeConfig,
        metrics: List[Metric],
        dimensions: List[Dimension],
        filters: List[Dict[str, Any]],
    ) -> str:
        """生成 SQL 查询"""
        # SELECT 子句
        select_parts = []
        for metric in metrics:
            select_parts.append(f"    {metric.expression} AS {metric.name}")

        # 如果有维度，添加到 SELECT
        for dimension in dimensions:
            select_parts.append(f"    {dimension.field}")

        select_clause = ",\n".join(select_parts)

        # FROM 子句
        from_clause = f"FROM {cube.table}"

        # WHERE 子句
        where_conditions = []
        for filter_cond in filters:
            field = filter_cond["field"]
            op = filter_cond["op"]
            value = filter_cond["value"]

            if isinstance(value, str):
                where_conditions.append(f"    {field} {op} '{value}'")
            else:
                where_conditions.append(f"    {field} {op} {value}")

        where_clause = ""
        if where_conditions:
            where_clause = "\nWHERE\n    " + "\n    AND ".join(where_conditions)

        # GROUP BY 子句
        group_by_clause = ""
        if dimensions:
            group_by_fields = ", ".join([d.field for d in dimensions])
            group_by_clause = f"\nGROUP BY\n    {group_by_fields}"

        # ORDER BY 子句（默认按第一个指标降序）
        order_by_clause = ""
        if metrics:
            order_by_clause = f"\nORDER BY {metrics[0].name} DESC"

        # LIMIT 子句
        limit_clause = f"\nLIMIT {cube.default_limit}"

        sql = f"SELECT\n{select_clause}\n{from_clause}{where_clause}{group_by_clause}{order_by_clause}{limit_clause}"

        return sql

    def execute(self, query: str) -> Dict[str, Any]:
        """执行查询"""
        dsl = self.build_query(query)

        # 检查缓存
        cache_key = f"{query}:{dsl['limit']}"
        if cache_key in self._cache:
            return {
                "status": "success",
                "semantic": dsl,
                "data": self._cache[cache_key],
                "cached": True,
            }

        # 这里应该调用 metrics-engine 执行查询
        # 暂时返回模拟数据
        result = self._mock_execute(dsl)

        # 缓存结果
        self._cache[cache_key] = result["data"]

        return {
            "status": "success",
            "semantic": dsl,
            "data": result["data"],
            "cached": False,
        }

    def _mock_execute(self, dsl: Dict[str, Any]) -> Dict[str, Any]:
        """模拟执行查询（用于测试）"""
        # 这里应该调用 metrics-engine 执行真实的 SQL
        # 暂时返回模拟数据
        return {
            "data": [
                {
                    "order_cnt": 100,
                    "total_amount": 50000.00,
                    "product_name": "示例产品",
                }
            ],
        }

    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            "cache_size": len(self._cache),
            "cache_ttl": 300,
        }


# 全局引擎实例
cube_engine = CubeEngine()
