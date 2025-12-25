# backend/apps/system/api/third_party_login.py

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from datetime import timedelta
import uuid
from sqlmodel import select

# [关键修复 1] 补全缺少的引用
from apps.system.models.user import UserModel, UserPlatformModel
from apps.system.models.system_model import UserWsModel
from apps.system.schemas.system_schema import BaseUserDTO
from common.core.security import create_access_token, get_password_hash
from common.core.config import settings
from common.core.deps import SessionDep
from apps.system.api.login import Token
from common.utils.time import get_timestamp  # 引入时间工具

router = APIRouter(tags=["login"], prefix="/login")


# --- 定义请求参数模型 ---
class ThirdPartyLoginSchema(BaseModel):
    code: str
    source: Optional[str] = "generic"


# --- 模拟校验函数 ---
async def verify_third_party_code(code: str, source: str):
    if code:
        return {
            "username": f"user_{code}",
            "nickname": f"第三方用户_{code}",
            "email": f"{code}@example.com"
        }
    return None


# --- 接口: 第三方登录回调 ---
@router.post("/oauth/callback", response_model=Token)
async def login_by_oauth_code(
        body: ThirdPartyLoginSchema,
        session: SessionDep
):
    # 1. 校验 Code
    third_user = await verify_third_party_code(body.code, body.source)
    if not third_user:
        raise HTTPException(status_code=400, detail="Invalid authorization code")

    # 2. 查找用户
    stmt = select(UserModel).where(UserModel.account == third_user["username"])
    user = session.exec(stmt).first()

    # 3. 用户不存在则自动创建 (完整且原子性的事务)
    if not user:
        default_oid = 1  # 默认空间ID，请确保 sys_workspace 表中有 id=1 的记录
        current_time = get_timestamp()  # [关键] 获取当前时间

        # 3.1 创建基础用户
        user = UserModel(
            account=third_user["username"],
            name=third_user["nickname"],
            email=third_user.get("email"),
            password=get_password_hash(str(uuid.uuid4())),
            status=1,
            origin=1,
            oid=default_oid,
            create_time=current_time
        )
        session.add(user)

        # [关键修复 2] 使用 flush() 而不是 commit()
        # flush 会将 SQL 发送到数据库并生成 ID (如果需要)，但仍处于同一事务中。
        # 这样如果后面报错，整个用户创建过程会回滚，避免产生脏数据。
        session.flush()
        session.refresh(user)  # 刷新以获取数据库生成的 user.id

        # 3.2 创建用户与工作空间的关联
        user_ws = UserWsModel(
            uid=user.id,  # 这里已经可以拿到正确的 user.id
            oid=default_oid,
            weight=0,
            create_time=current_time
        )
        session.add(user_ws)

        # 3.3 创建第三方来源关联
        user_platform = UserPlatformModel(
            uid=user.id,
            origin=1,
            platform_uid=body.code,
            create_time=current_time
        )
        session.add(user_platform)

        # [关键修复 3] 最后统一提交，确保数据完整性
        session.commit()

    # 4. 校验状态
    if not user.oid or user.oid == 0:
        raise HTTPException(status_code=400, detail="No associated workspace")
    if user.status != 1:
        raise HTTPException(status_code=400, detail="User is inactive")

    # 5. 生成 Token
    # 使用 model_dump() 确保 Pydantic V2 兼容性
    user_dto = BaseUserDTO.model_validate(user.model_dump())

    # 构造 payload
    user_dict = {
        "id": user_dto.id,
        "account": user_dto.account,
        "oid": user_dto.oid
    }

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data=user_dict,
        expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")