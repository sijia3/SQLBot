# backend/apps/system/crud/custom_prompt.py

from typing import List, Optional
from sqlalchemy import select, func, and_, delete, update, or_
from sqlmodel import Session
from apps.system.models.custom_prompt_model import CustomPrompt, CustomPromptInfo
from apps.datasource.models.datasource import CoreDatasource
from common.core.deps import SessionDep, Trans
from datetime import datetime


def page_custom_prompt(
        session: SessionDep,
        current_page: int,
        page_size: int,
        prompt_type: str,
        name: Optional[str] = None,
        oid: Optional[int] = None
):
    """
    分页查询自定义提示词，并填充数据源名称
    """
    # 1. 构建基础查询条件
    filters = [
        CustomPrompt.oid == oid,
        CustomPrompt.type == prompt_type
    ]
    if name and name.strip():
        filters.append(CustomPrompt.name.ilike(f"%{name.strip()}%"))

    # 2. 计算总数
    count_stmt = select(func.count()).select_from(CustomPrompt).where(and_(*filters))
    total_count = session.execute(count_stmt).scalar()

    # 3. 计算分页
    page_size = max(10, page_size)
    total_pages = (total_count + page_size - 1) // page_size
    current_page = max(1, min(current_page, total_pages)) if total_pages > 0 else 1

    # 4. 查询数据
    stmt = (
        select(CustomPrompt)
        .where(and_(*filters))
        .order_by(CustomPrompt.create_time.desc())
        .offset((current_page - 1) * page_size)
        .limit(page_size)
    )
    # results = session.exec(stmt).all()
    results = session.execute(stmt).scalars().all()

    # 5. 填充 datasource_names (这是前端列表展示必须的)
    _list = []

    # 收集当前页所有用到的 datasource_id
    all_ds_ids = set()
    for row in results:
        if row.specific_ds and row.datasource_ids:
            all_ds_ids.update(row.datasource_ids)

    # 批量查询数据源名称
    ds_map = {}
    if all_ds_ids:
        ds_rows = session.exec(
            select(CoreDatasource.id, CoreDatasource.name)
            .where(CoreDatasource.id.in_(all_ds_ids))
        ).all()
        ds_map = {row.id: row.name for row in ds_rows}

    # 组装返回对象
    for row in results:
        info = CustomPromptInfo(
            id=row.id,
            oid=row.oid,
            name=row.name,
            type=row.type,
            prompt=row.prompt,
            specific_ds=row.specific_ds,
            datasource_ids=row.datasource_ids or [],
            create_time=row.create_time,
            datasource_names=[]
        )
        # 填充名称
        if row.specific_ds and row.datasource_ids:
            info.datasource_names = [ds_map.get(ds_id, str(ds_id)) for ds_id in row.datasource_ids if ds_id in ds_map]

        _list.append(info)

    return current_page, page_size, total_count, total_pages, _list


def create_prompt(session: SessionDep, info: CustomPromptInfo, oid: int):
    # 查重逻辑 (可选)
    # ...

    db_obj = CustomPrompt(
        oid=oid,
        name=info.name,
        type=info.type,
        prompt=info.prompt,
        specific_ds=info.specific_ds,
        datasource_ids=info.datasource_ids,
        create_time=datetime.now()
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj.id


def update_prompt(session: SessionDep, info: CustomPromptInfo, oid: int):
    stmt = (
        update(CustomPrompt)
        .where(and_(CustomPrompt.id == info.id, CustomPrompt.oid == oid))
        .values(
            name=info.name,
            prompt=info.prompt,
            specific_ds=info.specific_ds,
            datasource_ids=info.datasource_ids
        )
    )
    session.execute(stmt)
    session.commit()
    return info.id


def delete_prompt(session: SessionDep, id_list: List[int], oid: int):
    # 只能删除当前 OID 下的数据
    stmt = delete(CustomPrompt).where(
        and_(CustomPrompt.id.in_(id_list), CustomPrompt.oid == oid)
    )
    session.execute(stmt)
    session.commit()


def find_custom_prompts(session: Session, prompt_type: str, oid: int, ds_id: Optional[int] = None) -> List[str]:
    """
    根据类型、OID和数据源ID查找匹配的自定义提示词列表
    """
    # 1. 查出当前空间下该类型的所有启用提示词
    stmt = select(CustomPrompt).where(
        CustomPrompt.oid == oid,
        CustomPrompt.type == prompt_type
    )
    prompts = session.execute(stmt).scalars().all()
    # prompts = session.exec(stmt).all()

    valid_prompts = []
    for prompt in prompts:
        # 逻辑判断：
        # 1. 如果 specific_ds 为 False，说明是通用提示词，直接采纳
        # 2. 如果 specific_ds 为 True，且当前有 ds_id，且 ds_id 在该提示词的 datasource_ids 列表中，则采纳
        if not prompt.specific_ds:
            valid_prompts.append(prompt.prompt)
        elif ds_id and prompt.datasource_ids and ds_id in prompt.datasource_ids:
            valid_prompts.append(prompt.prompt)

    return valid_prompts