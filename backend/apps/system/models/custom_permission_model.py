from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, Text, BigInteger


class DsPermission(SQLModel, table=True):
    __tablename__ = "ds_permission"
    # --- 新增这一行 ---
    __table_args__ = {'extend_existing': True}

    id: Optional[int] = Field(default=None, primary_key=True)
    enable: bool = Field(default=True)
    auth_target_type: str = Field(default="user", max_length=128)

    # 修复：使用 sa_column=Column(BigInteger) 替代 sa_type="BigInteger"
    auth_target_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger))

    type: str = Field(max_length=64)  # 'row' or 'column'

    # 修复：同上
    ds_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    table_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger))

    # 存储 JSON 字符串
    expression_tree: Optional[str] = Field(default=None, sa_column=Column(Text))
    permissions: Optional[str] = Field(default=None, sa_column=Column(Text))
    white_list_user: Optional[str] = Field(default=None, sa_column=Column(Text))
    create_time: Optional[datetime] = Field(default_factory=datetime.now)


class DsRules(SQLModel, table=True):
    __tablename__ = "ds_rules"
    # --- 新增这一行 ---
    __table_args__ = {'extend_existing': True}

    id: Optional[int] = Field(default=None, primary_key=True)
    enable: bool = Field(default=True)
    name: str = Field(max_length=128)
    description: Optional[str] = Field(default=None, max_length=512)
    # 存储 JSON 字符串：权限ID列表 [1, 2, 3]
    permission_list: Optional[str] = Field(default=None, sa_column=Column(Text))
    # 存储 JSON 字符串：用户ID列表 [1001, 1002]
    user_list: Optional[str] = Field(default=None, sa_column=Column(Text))
    white_list_user: Optional[str] = Field(default=None, sa_column=Column(Text))
    create_time: Optional[datetime] = Field(default_factory=datetime.now)


# 用于内部逻辑传输的 DTO
class PermissionDTO:
    def __init__(self, tree=None):
        self.tree = tree