from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, Text, BigInteger, String


class DsPermission(SQLModel, table=True):
    __tablename__ = "ds_permission"

    __table_args__ = {'extend_existing': True}

    # [030] 修复：ID 类型改为 BigInteger，匹配迁移脚本
    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))

    enable: bool = Field(default=True)

    # [027] 修复：增加 name 字段
    name: Optional[str] = Field(default=None, max_length=128)

    # [027] 修复：auth_target_type 变为 nullable
    auth_target_type: Optional[str] = Field(default="user", max_length=128)
    auth_target_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger))

    type: str = Field(max_length=64)
    ds_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    table_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger))

    expression_tree: Optional[str] = Field(default=None, sa_column=Column(Text))
    permissions: Optional[str] = Field(default=None, sa_column=Column(Text))
    white_list_user: Optional[str] = Field(default=None, sa_column=Column(Text))
    create_time: Optional[datetime] = Field(default_factory=datetime.now)


class DsRules(SQLModel, table=True):
    __tablename__ = "ds_rules"

    __table_args__ = {'extend_existing': True}

    id: Optional[int] = Field(default=None, primary_key=True)

    # [030] 修复：增加 oid 字段
    oid: Optional[int] = Field(default=None, sa_column=Column(BigInteger))

    enable: bool = Field(default=True)
    name: str = Field(max_length=128)
    description: Optional[str] = Field(default=None, max_length=512)
    permission_list: Optional[str] = Field(default=None, sa_column=Column(Text))
    user_list: Optional[str] = Field(default=None, sa_column=Column(Text))
    white_list_user: Optional[str] = Field(default=None, sa_column=Column(Text))
    create_time: Optional[datetime] = Field(default_factory=datetime.now)


# 用于内部逻辑传输的 DTO
class PermissionDTO:
    def __init__(self, tree=None):
        self.tree = tree
