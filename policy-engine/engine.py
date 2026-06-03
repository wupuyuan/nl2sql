"""
ABAC 策略引擎

职责：
- 根据用户属性评估数据访问策略
- 动态生成/修改 DSL 过滤条件
- 实现细粒度数据级权限控制
"""

from typing import List, Dict, Any, Optional


def evaluate_abac_policy(
    user: dict,
    semantic_dsl: dict
) -> dict:
    """
    评估 ABAC 策略，返回增强后的 DSL

    参数：
        user: 用户信息（包含 role, areas, department 等属性）
        semantic_dsl: Semantic Layer 解析出的语义 DSL

    返回：
        增强后的 DSL（可能追加 area 过滤条件）

    示例：
        user = {"username": "beijing", "role": "viewer", "areas": ["beijing"]}
        dsl = {"metrics": ["amount"], "filters": []}
        result = evaluate_abac_policy(user, dsl)
        # result["filters"] 会追加 {"field": "area", "op": "in", "value": ["beijing"]}
    """
    role = user.get("role", "viewer")
    areas = user.get("areas", [])

    # 深拷贝 DSL，避免修改原始数据
    enhanced_dsl = semantic_dsl.copy()
    filters = list(enhanced_dsl.get("filters", []))

    # 策略1：管理员且能看到全部区域，不追加过滤
    if role == "admin" and len(areas) >= 2:
        enhanced_dsl["abac_applied"] = False
        enhanced_dsl["abac_reason"] = "管理员权限，无需区域过滤"
        return enhanced_dsl

    # 策略2：根据用户 areas 属性追加过滤条件
    if areas and len(areas) > 0:
        # 检查是否已有 area 过滤条件
        has_area_filter = any(
            f.get("field") == "area" for f in filters
        )

        if not has_area_filter:
            # 追加 area IN (...) 过滤条件
            if len(areas) == 1:
                # 单个区域用 = 操作符
                filters.append({
                    "field": "area",
                    "op": "=",
                    "value": areas[0],
                })
            else:
                # 多个区域用 in 操作符
                filters.append({
                    "field": "area",
                    "op": "in",
                    "value": areas,
                })

    enhanced_dsl["filters"] = filters
    enhanced_dsl["abac_applied"] = True
    enhanced_dsl["abac_reason"] = f"用户 {user.get('username')} 只能访问区域: {areas}"

    return enhanced_dsl


def build_area_sql_condition(
    areas: List[str]
) -> tuple:
    """
    构建 area 过滤的 SQL 条件

    返回：
        (sql_fragment, params)

    示例：
        areas = ["beijing"]
        -> ("area = ?", ["beijing"])

        areas = ["beijing", "shanghai"]
        -> ("area IN (?, ?)", ["beijing", "shanghai"])
    """
    if not areas:
        return ("1=1", [])

    if len(areas) == 1:
        return ("area = %s", [areas[0]])
    else:
        placeholders = ", ".join(["%s"] * len(areas))
        return (f"area IN ({placeholders})", areas)


def get_user_visible_areas(user: dict) -> List[str]:
    """获取用户可见的区域列表"""
    return user.get("areas", [])
