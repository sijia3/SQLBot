from typing import Optional
from sqlmodel import Field, SQLModel


class SysParameter(SQLModel, table=True):
    __tablename__ = "sys_parameter"

    pkey: str = Field(primary_key=True, max_length=255, description="配置键")
    pval: Optional[str] = Field(default=None, description="配置值")
    group_name: str = Field(index=True, max_length=50, description="分组(login/appearance/chat)")
    description: Optional[str] = Field(default=None, description="描述")


# 用于前端交互的 Pydantic 模型（保持与原 xpack 兼容）
class SysArgModel(SQLModel):
    pkey: str
    pval: Optional[str] = None
    label: Optional[str] = None
    type: Optional[str] = None  # text, image, boolean...
    options: Optional[str] = None
    show: Optional[bool] = True