import json
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, Body
from sqlmodel import select, Session
from common.core.db import get_session
from apps.system.models.custom_permission_model import DsPermission, DsRules
from apps.system.models.user import UserModel

router = APIRouter()


@router.post("/list")
def get_permission_list(session: Session = Depends(get_session)):
    """获取权限规则组列表"""
    rules = session.exec(select(DsRules)).all()
    result = []

    for rule in rules:
        # 1. 解析 permission_list
        perm_ids = json.loads(rule.permission_list) if rule.permission_list else []
        permissions = []
        if perm_ids:
            perms = session.exec(select(DsPermission).where(DsPermission.id.in_(perm_ids))).all()
            for p in perms:
                p_dict = p.model_dump()
                # 容错处理 JSON 解析
                if p.type == 'row' and p.expression_tree:
                    try:
                        p_dict['tree'] = json.loads(p.expression_tree)
                        p_dict['expression_tree'] = json.loads(p.expression_tree)
                    except:
                        p_dict['tree'] = {}
                elif p.type == 'column' and p.permissions:
                    try:
                        p_str = p.permissions
                        if isinstance(p_str, str):
                            p_dict['permission_list'] = json.loads(p_str)
                            p_dict['permissions'] = json.loads(p_str)
                        else:
                            p_dict['permission_list'] = p_str
                    except:
                        p_dict['permission_list'] = []

                # 补充 table_name/ds_name
                from apps.datasource.models.datasource import CoreDatasource, CoreTable
                if p.ds_id:
                    ds = session.get(CoreDatasource, p.ds_id)
                    p_dict['ds_name'] = ds.name if ds else ''
                if p.table_id:
                    tb = session.get(CoreTable, p.table_id)
                    p_dict['table_name'] = tb.table_name if tb else ''

                permissions.append(p_dict)

        # 2. 解析 user_list 并返回字符串类型的 ID 列表
        raw_user_list = []
        if rule.user_list:
            try:
                raw_user_list = json.loads(rule.user_list)
            except:
                raw_user_list = []

        u_ids_str = []
        for item in raw_user_list:
            if isinstance(item, dict):
                if item.get("id"):
                    u_ids_str.append(str(item["id"]))
            elif isinstance(item, (int, str)):
                try:
                    u_ids_str.append(str(item))
                except:
                    pass

        # 3. 准备返回数据
        user_details = []
        if u_ids_str:
            u_ids_int = [int(uid) for uid in u_ids_str]
            db_users = session.exec(select(UserModel).where(UserModel.id.in_(u_ids_int))).all()
            user_details = [u.model_dump() for u in db_users]

        result.append({
            **rule.model_dump(),
            "permissions": permissions,
            "users": u_ids_str,
            "user_details": user_details,
            "user_list": u_ids_str
        })

    return result


@router.post("/save")
def save_permissions(data: dict = Body(...), session: Session = Depends(get_session)):
    """保存权限规则组"""
    try:
        rule_id = int(data.get("id")) if data.get("id") else None
    except ValueError:
        rule_id = None

    name = data.get("name")
    description = data.get("description")
    # 如果请求包含 oid，也一并保存
    oid = data.get("oid")

    # 清洗 user 数据
    raw_users = data.get("users")
    if not raw_users:
        raw_users = data.get("user_list", [])

    user_ids = []
    for u in raw_users:
        if isinstance(u, dict):
            if u.get("id"):
                user_ids.append(int(u["id"]))
        elif isinstance(u, (int, str)):
            try:
                user_ids.append(int(u))
            except:
                pass

    user_ids = list(set(user_ids))
    permissions_data = data.get("permissions", [])

    saved_perm_ids = []
    for p_data in permissions_data:
        expression_tree_str = None
        tree_data = p_data.get("expression_tree") or p_data.get("tree")
        if tree_data:
            expression_tree_str = json.dumps(tree_data) if isinstance(tree_data, (dict, list)) else tree_data

        permissions_str = None
        perm_detail = p_data.get("permissions") or p_data.get("permission_list")
        if perm_detail:
            permissions_str = json.dumps(perm_detail) if isinstance(perm_detail, (dict, list)) else perm_detail

        p_id = p_data.get("id")
        if p_id and isinstance(p_id, int) and p_id > 2147483647:
            p_id = None
        elif p_id == 0:
            p_id = None

        perm_model = DsPermission(
            id=p_id,
            # === [核心修复] 保存明细名称 ===
            name=p_data.get("name"),
            # ==========================
            type=p_data.get("type"),
            ds_id=p_data.get("ds_id"),
            table_id=p_data.get("table_id"),
            expression_tree=expression_tree_str,
            permissions=permissions_str,
            enable=True
        )

        if perm_model.id:
            perm_db = session.merge(perm_model)
        else:
            perm_db = perm_model
            session.add(perm_db)

        session.flush()
        session.refresh(perm_db)
        saved_perm_ids.append(perm_db.id)

    rule = None
    if rule_id:
        rule = session.get(DsRules, rule_id)

    if not rule:
        rule = DsRules(name=name, description=description)
        if oid: rule.oid = oid  # 新建时设置 oid
        session.add(rule)
    else:
        if name is not None:
            rule.name = name
        if description is not None:
            rule.description = description
        if oid is not None:
            rule.oid = oid  # 更新时设置 oid
        session.add(rule)

    rule.user_list = json.dumps(user_ids)
    rule.permission_list = json.dumps(saved_perm_ids)

    session.commit()
    return True


@router.post("/delete/{id}")
def delete_permissions(id: int, session: Session = Depends(get_session)):
    rule = session.get(DsRules, id)
    if rule:
        session.delete(rule)
        session.commit()
    return True
