# backend/apps/system/api/appearance.py

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse
from common.core.deps import SessionDep
# 引入之前写好的 CRUD 和 Utils
from apps.system.crud.parameter_manage import get_groups, save_parameter_args
from common.utils.local_file import LocalFileUtils
import os

router = APIRouter(tags=["system/appearance"], prefix="/system/appearance")

# 1. [原有] 前端获取 UI 配置的接口
@router.get("/ui")
async def get_ui_config(session: SessionDep):
    # 复用之前写的 get_groups，获取 'appearance' 分组的配置
    return await get_groups(session, "appearance")

# 2. [原有] 前端加载 Logo/背景图的接口
@router.get("/picture/{file_id}")
async def get_picture(file_id: str):
    file_path = LocalFileUtils.get_file_path(file_id)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}

# 3. 【新增】 保存配置接口 (修复 Method Not Allowed)
# 前端调用: request.post('/system/appearance', formData)
# 修改 POST 接口的返回值
@router.post("")
async def save_appearance(request: Request, session: SessionDep):
    """
    接收 multipart/form-data，包含文件和配置数据
    """
    await save_parameter_args(session, request)
    # 修改前: return {"message": "Success"}
    # 修改后: 直接返回 True 或 "success"，中间件会自动包装成 {code:0, data: true, ...}
    return True