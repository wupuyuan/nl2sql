"""
Auth Service - 认证鉴权服务

职责：
- 用户身份认证（Token 验证）
- RBAC 角色权限检查
- 用户信息查询

说明：
- 当前使用本地模拟用户数据
- 外部认证接口保留代码框架（external_auth.py）
- 生产环境可对接企业 IAM / SSO / OAuth2
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from schema import AuthResponse, User
from users import get_user_by_token, check_role_permission
from external_auth import call_external_auth

app = FastAPI(
    title="Auth Service",
    description="Authentication & Authorization Service (RBAC)",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"service": "auth-service", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/auth/verify", response_model=AuthResponse)
async def verify_token(token: Optional[str] = Header(None, alias="X-Auth-Token")):
    """
    验证用户 Token，返回用户信息

    请求头：X-Auth-Token: token_cipher_op
    """
    if not token:
        return AuthResponse(success=False, message="缺少 Token")

    # 步骤1：尝试外部认证（生产环境）
    external_user = await call_external_auth(token)
    if external_user:
        return AuthResponse(
            success=True,
            user=User(**external_user),
            message="外部认证成功"
        )

    # 步骤2：回退到本地模拟认证
    user_data = get_user_by_token(token)
    if not user_data:
        return AuthResponse(success=False, message="无效的 Token")

    return AuthResponse(
        success=True,
        user=User(**user_data),
        message="本地认证成功"
    )


@app.get("/auth/user")
async def get_current_user(token: Optional[str] = Header(None, alias="X-Auth-Token")):
    """获取当前登录用户信息"""
    if not token:
        raise HTTPException(status_code=401, detail="缺少 Token")

    # 尝试外部认证
    external_user = await call_external_auth(token)
    if external_user:
        return external_user

    # 回退本地
    user_data = get_user_by_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="无效的 Token")

    return user_data


@app.post("/auth/check")
async def check_permission(
    action: str = "query",
    token: Optional[str] = Header(None, alias="X-Auth-Token")
):
    """
    RBAC 权限检查

    参数：
        action: 操作类型（query / manage_users / view_audit）
    """
    if not token:
        return {"allowed": False, "reason": "缺少 Token"}

    # 获取用户信息
    user_data = get_user_by_token(token)
    if not user_data:
        # 尝试外部认证
        external_user = await call_external_auth(token)
        if external_user:
            user_data = external_user
        else:
            return {"allowed": False, "reason": "无效的 Token"}

    role = user_data.get("role", "viewer")
    allowed = check_role_permission(role, action)

    return {
        "allowed": allowed,
        "username": user_data.get("username"),
        "role": role,
        "action": action,
    }


@app.get("/users/list")
async def list_users():
    """列出所有本地用户（仅用于开发和调试）"""
    from users import USERS_DB
    return {
        "users": list(USERS_DB.values()),
        "count": len(USERS_DB),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
