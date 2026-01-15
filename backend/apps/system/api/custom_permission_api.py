import json
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, Body
from sqlmodel import select, Session
from common.core.db import get_session
from apps.system.models.custom_permission_model import DsPermission, DsRules
from apps.system.models.user import UserModel  # 修正：导入 UserModel

router = APIRouter()


@router.post("/list")
def get_permission_list(session: Session = Depends(get_session)):
    """获取权限规则组列表，并组装前端需要的嵌套结构"""
    rules = session.exec(select(DsRules)).all()
    result = []

    for rule in rules:
        # 解析 permission_list (存储的是 DsPermission 的 ID 列表)
        perm_ids = json.loads(rule.permission_list) if rule.permission_list else []
        permissions = []
        if perm_ids:
            perms = session.exec(select(DsPermission).where(DsPermission.id.in_(perm_ids))).all()
            for p in perms:
                # 转换回前端需要的对象格式
                p_dict = p.model_dump()
                # 针对不同类型解析 JSON 字符串
                if p.type == 'row' and p.expression_tree:
                    try:
                        p_dict['tree'] = json.loads(p.expression_tree)
                        p_dict['expression_tree'] = json.loads(p.expression_tree)
                    except:
                        p_dict['tree'] = {}

                elif p.type == 'column' and p.permissions:
                    try:
                        p_dict['permission_list'] = json.loads(p.permissions)
                        p_dict['permissions'] = json.loads(p.permissions)
                    except:
                        p_dict['permission_list'] = []

                # 补充前端展示需要的额外字段
                from apps.datasource.models.datasource import CoreDatasource, CoreTable
                if p.ds_id:
                    ds = session.get(CoreDatasource, p.ds_id)
                    p_dict['ds_name'] = ds.name if ds else ''
                if p.table_id:
                    tb = session.get(CoreTable, p.table_id)
                    p_dict['table_name'] = tb.table_name if tb else ''

                permissions.append(p_dict)

        # 解析 user_list 并获取用户信息
        user_ids = json.loads(rule.user_list) if rule.user_list else []
        users = []
        if user_ids:
            # 兼容 user_list 可能存的是 string 或 int
            u_ids = [int(uid) for uid in user_ids]
            # 修正：使用 UserModel
            db_users = session.exec(select(UserModel).where(UserModel.id.in_(u_ids))).all()
            users = [u.model_dump() for u in db_users]

        result.append({
            **rule.model_dump(),
            "permissions": permissions,
            "users": users
        })

    return result  # 中间件会自动包装为 {code: 0, data: result}


@router.post("/save")
def save_permissions(data: dict = Body(...), session: Session = Depends(get_session)):
    """保存权限规则组及其包含的权限详情"""
    rule_id = data.get("id")
    name = data.get("name")
    user_ids = data.get("users", [])  # 前端传过来的是 user id list
    permissions_data = data.get("permissions", [])  # 前端传过来的是 permission 对象 list

    # 1. 保存/更新具体的 Permission 条目
    saved_perm_ids = []
    for p_data in permissions_data:
        # 处理 expression_tree 和 permissions 字段，前端传的是对象，存库需转字符串
        expression_tree_str = None
        if p_data.get("expression_tree"):
            expression_tree_str = json.dumps(p_data["expression_tree"]) if isinstance(p_data["expression_tree"],
                                                                                      (dict, list)) else p_data[
                "expression_tree"]

        permissions_str = None
        if p_data.get("permissions"):
            permissions_str = json.dumps(p_data["permissions"]) if isinstance(p_data["permissions"], (dict, list)) else \
            p_data["permissions"]

        # 处理 id，前端新建的临时 id 通常很大或者非 int，需要置空以触发自增
        p_id = p_data.get("id")
        if p_id and isinstance(p_id, int) and p_id > 2147483647:  # 假设前端临时ID很大
            p_id = None
        elif p_id == 0:
            p_id = None

        perm_model = DsPermission(
            id=p_id,
            type=p_data.get("type"),
            ds_id=p_data.get("ds_id"),
            table_id=p_data.get("table_id"),
            expression_tree=expression_tree_str,
            permissions=permissions_str,
            enable=True
        )

        # 保存 Permission
        # 如果有ID则合并，否则新增
        if perm_model.id:
            perm_db = session.merge(perm_model)
        else:
            perm_db = perm_model
            session.add(perm_db)

        session.flush()  # 以此获取 id
        session.refresh(perm_db)
        saved_perm_ids.append(perm_db.id)

    # 2. 保存/更新 Rule Group
    rule = None
    if rule_id:
        rule = session.get(DsRules, rule_id)

    if not rule:
        rule = DsRules(name=name)
        session.add(rule)
    else:
        rule.name = name

    rule.user_list = json.dumps(user_ids)
    rule.permission_list = json.dumps(saved_perm_ids)

    session.commit()
    return True


@router.post("/delete/{id}")
def delete_permissions(id: int, session: Session = Depends(get_session)):
    """删除规则组"""
    rule = session.get(DsRules, id)
    if rule:
        # 实际业务中可能还需要删除关联的 DsPermission
        session.delete(rule)
        session.commit()
    return True