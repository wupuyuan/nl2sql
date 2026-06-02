from typing import Optional, List, Any, Dict

from cube.engine import cube_engine
from cube.config import SEMANTIC_CONFIG
from models import SemanticResponse, Filter


class CubeParser:
    """基于 Cube 的语义解析器"""

    def __init__(self):
        self.engine = cube_engine

    def parse(self, query: str) -> SemanticResponse:
        """解析查询，返回语义 DSL"""
        # 执行 Cube 查询引擎
        result = self.engine.execute(query)

        if result["status"] != "success":
            return SemanticResponse(
                intent="error",
                metrics=[],
                dimensions=[],
                filters=[],
                warnings=[result.get("message", "查询失败")],
                limit=SEMANTIC_CONFIG["default_limit"],
            )

        semantic = result["semantic"]

        # 转换为 Filter 对象
        filters = []
        for filter_cond in semantic.get("filters", []):
            filters.append(Filter(
                field=filter_cond["field"],
                op=filter_cond["op"],
                value=filter_cond["value"],
            ))

        return SemanticResponse(
            intent="query",
            metrics=semantic.get("metrics", []),
            dimensions=semantic.get("dimensions", []),
            filters=filters,
            warnings=[],
            limit=semantic.get("limit", SEMANTIC_CONFIG["default_limit"]),
            sql=semantic.get("sql"),
            cube=semantic.get("cube"),
            time_range=semantic.get("time_range"),
            cached=not result.get("cached", False),
        )

    def build_query(self, query: str) -> Dict[str, Any]:
        """构建查询 DSL（不执行）"""
        return self.engine.build_query(query)

    def get_cube(self, cube_name: str) -> Optional[Dict[str, Any]]:
        """获取 Cube 详细信息"""
        return self.engine.get_cube_details(cube_name)

    def list_cubes(self) -> List[Dict[str, Any]]:
        """列出所有 Cube"""
        return self.engine.list_cubes()

    def clear_cache(self):
        """清除缓存"""
        self.engine.clear_cache()

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return self.engine.get_cache_stats()


# 全局解析器实例
cube_parser = CubeParser()
