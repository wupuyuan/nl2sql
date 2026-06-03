"""
ABAC 策略配置（本地模拟）

策略说明：
- 数据级权限控制，根据用户属性动态生成过滤条件
- 策略作用于 Semantic Layer 解析后的 DSL

用户属性说明：
- cipher_op: role=admin, areas=[beijing, shanghai]
- beijing:    role=viewer, areas=[beijing]
- shanghai:   role=viewer, areas=[shanghai]
"""

# ABAC 策略规则
# 规则：根据用户的 areas 属性，自动追加 area IN (...) 过滤条件
ABAC_POLICIES = {
    "area_filter": {
        "description": "根据用户可见区域过滤数据",
        "condition": "areas is not None and len(areas) > 0",
        "action": "append_filter",
        "filter": {
            "field": "area",
            "op": "in",
            "value_source": "user.areas",
        },
    },
    "admin_bypass": {
        "description": "管理员不追加区域过滤（已包含全部区域）",
        "condition": "role == 'admin' and len(areas) >= 2",
        "action": "bypass",
    },
}

# Casbin 模型配置（可选，生产环境可启用 Casbin）
CASBIN_MODEL = """
[request_definition]
r = sub, dom, obj, act

[policy_definition]
p = sub, dom, obj, act

[role_definition]
g = _, _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub, r.dom) && r.dom == p.dom && r.obj == p.obj && r.act == p.act
"""

# Casbin 策略配置（可选）
CASBIN_POLICIES = """
p, cipher_op, default, data, query
p, beijing, default, data, query
p, shanghai, default, data, query
"""
