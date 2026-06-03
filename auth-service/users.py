"""
本地用户配置（模拟生产环境用户系统）

用户体系：
- cipher_op: 最高权限，能看到北京和上海的订单
- beijing:   只能看到北京的订单
- shanghai:  只能看到上海的订单
"""

USERS_DB = {
    "cipher_op": {
        "username": "cipher_op",
        "password": "550e8400-e29b-41d4-a716-446655440000",
        "role": "admin",
        "areas": ["beijing", "shanghai"],
        "department": "总部",
    },
    "beijing": {
        "username": "beijing",
        "password": "660e8400-e29b-41d4-a716-446655440001",
        "role": "viewer",
        "areas": ["beijing"],
        "department": "北京分部",
    },
    "shanghai": {
        "username": "shanghai",
        "password": "770e8400-e29b-41d4-a716-446655440002",
        "role": "viewer",
        "areas": ["shanghai"],
        "department": "上海分部",
    },
}

# Token 到用户的映射（模拟 Token 解析）
TOKEN_MAP = {
    "token_cipher_op": "cipher_op",
    "token_beijing": "beijing",
    "token_shanghai": "shanghai",
}


def get_user_by_token(token: str) -> dict:
    """根据 Token 获取用户信息"""
    username = TOKEN_MAP.get(token)
    if username:
        return USERS_DB.get(username)
    return None


def get_user_by_username(username: str) -> dict:
    """根据用户名获取用户信息"""
    return USERS_DB.get(username)


# RBAC 角色权限定义
ROLE_PERMISSIONS = {
    "admin": ["query", "manage_users", "view_audit"],
    "analyst": ["query", "view_audit"],
    "viewer": ["query"],
}


def check_role_permission(role: str, action: str) -> bool:
    """检查角色是否有指定权限"""
    permissions = ROLE_PERMISSIONS.get(role, [])
    return action in permissions
