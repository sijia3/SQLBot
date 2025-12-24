# backend/apps/system/api/custom_prompt.py

from typing import List, Optional
from fastapi import APIRouter, Path, Query, Body, Request
from apps.swagger.i18n import PLACEHOLDER_PREFIX
from common.core.deps import SessionDep, CurrentUser, Trans
from apps.system.models.custom_prompt_model import CustomPromptInfo
from apps.system.crud.custom_prompt import page_custom_prompt, create_prompt, update_prompt, delete_prompt

# 注意：前缀要和前端 api/prompt.ts 中的一致
router = APIRouter(tags=["System Custom Prompt"], prefix="/system/custom_prompt")

# 1. 分页列表接口
# 前端调用: request.get(`/system/custom_prompt/${type}/page/${pageNum}/${pageSize}${params}`)
@router.get("/{type}/page/{current_page}/{page_size}", summary=f"{PLACEHOLDER_PREFIX}get_prompt_page")
async def pager(
    session: SessionDep,
    current_user: CurrentUser,
    type: str,
    current_page: int,
    page_size: int,
    name: Optional[str] = Query(None, description="搜索名称")
):
    current_page, page_size, total_count, total_pages, _list = page_custom_prompt(
        session, current_page, page_size, type, name, current_user.oid
    )

    return {
        "current_page": current_page,
        "page_size": page_size,
        "total_count": total_count,
        "total_pages": total_pages,
        "data": _list
    }

# 2. 创建或更新接口 (PUT)
# 前端调用: request.put(`/system/custom_prompt`, data)
# 前端 saveHandler 逻辑: 如果 data 没有 id，则视为新建；有 id 则视为更新。
@router.put("", response_model=int, summary=f"{PLACEHOLDER_PREFIX}save_prompt")
async def create_or_update(
    session: SessionDep,
    current_user: CurrentUser,
    info: CustomPromptInfo
):
    # 强制将操作限制在当前用户的 OID 下
    if info.id:
        return update_prompt(session, info, current_user.oid)
    else:
        return create_prompt(session, info, current_user.oid)

# 3. 删除接口 (DELETE)
# 前端调用: request.delete('/system/custom_prompt', { data: params }) -> params 是 ID 数组
@router.delete("", summary=f"{PLACEHOLDER_PREFIX}delete_prompt")
async def delete(
    session: SessionDep,
    current_user: CurrentUser,
    id_list: List[int] = Body(...) # 接收 body 中的数组
):
    delete_prompt(session, id_list, current_user.oid)
    return {"message": "Success"}

# 4. 获取单个详情接口 (GET)
# 前端调用: request.get(`/system/custom_prompt/${id}`)
# (虽然列表页已经有数据，但如果需要单独获取可以使用 sqlmodel 直接 get)
@router.get("/{id}", response_model=CustomPromptInfo)
async def get_one(session: SessionDep, current_user: CurrentUser, id: int):
    # 这里可以使用 SQLModel 的 get，但最好加 OID 校验
    from apps.system.models.custom_prompt_model import CustomPrompt
    obj = session.get(CustomPrompt, id)
    if not obj or obj.oid != current_user.oid:
        raise Exception("Not found")
    return obj