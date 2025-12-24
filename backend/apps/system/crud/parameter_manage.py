from fastapi import Request
from sqlbot_xpack.config.arg_manage import get_group_args, save_group_args
# from sqlbot_xpack.config.model import SysArgModel
from sqlmodel import select, delete
import json
from common.core.deps import SessionDep
# from sqlbot_xpack.file_utils import SQLBotFileUtils
from apps.system.models.parameter_model import SysParameter, SysArgModel
from common.utils.local_file import LocalFileUtils


# 1. 获取参数列表
async def get_groups(session: SessionDep, flag: str) -> list[SysArgModel]:
    # 从数据库查
    stmt = select(SysParameter).where(SysParameter.group_name == flag)
    db_params = session.exec(stmt).all()

    # 转换为前端需要的格式 (这里可以根据需求补全默认值，防止数据库为空时报错)
    result = []
    for p in db_params:
        result.append(SysArgModel(pkey=p.pkey, pval=p.pval))
    return result


async def get_parameter_args(session: SessionDep) -> list[SysArgModel]:
    # 获取非外观类的所有参数
    stmt = select(SysParameter).where(SysParameter.group_name != "appearance")
    db_params = session.exec(stmt).all()
    return [SysArgModel(pkey=p.pkey, pval=p.pval) for p in db_params]


# 2. 保存参数
async def save_parameter_args(session: SessionDep, request: Request):
    form_data = await request.form()
    files = form_data.getlist("files")
    json_text = form_data.get("data")

    # 解析前端传来的参数列表
    sys_args_data = json.loads(json_text) if json_text else []

    # 1. 处理文件上传
    file_mapping = {}
    if files:
        for file in files:
            # 简单处理：假设前端传来的 filename 包含 key 信息，或者根据业务逻辑对应
            # 这里简化为直接上传并获取 ID
            file_id = await LocalFileUtils.upload(file)
            # 注意：实际业务中需解析 file.filename 获取对应的配置 key (如 'logo')
            # 假设文件名格式为 "logo_timestamp.png"，取 "logo"
            key = file.filename.split('_')[0] if '_' in file.filename else "unknown"
            file_mapping[key] = file_id

    # 2. 保存到数据库
    for item in sys_args_data:
        key = item.get("pkey")
        val = item.get("pval")

        # 如果该 key 对应了新上传的文件，更新 val 为文件 ID
        if key in file_mapping:
            val = file_mapping[key]

        # Upsert 逻辑 (存在则更新，不存在则插入)
        db_obj = session.get(SysParameter, key)
        if not db_obj:
            # group_name 需要从 item 中获取，或者根据 key 前缀判断
            group = "system"
            if key.startswith("login."):
                group = "login"
            elif key.startswith("chat."):
                group = "chat"
            # 【新增】明确指定这些字段属于 appearance 组
            elif key in ["name", "pc_welcome", "pc_welcome_desc", "foot", "footContent"]:
                group = "appearance"

            db_obj = SysParameter(pkey=key, pval=val, group_name=group)
            session.add(db_obj)
        else:
            db_obj.pval = val
            session.add(db_obj)

    session.commit()