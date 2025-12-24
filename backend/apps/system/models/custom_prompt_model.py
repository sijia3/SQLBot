# backend/apps/system/models/custom_prompt_model.py

from datetime import datetime
from typing import List, Optional, Any
from enum import Enum
from sqlalchemy import Column, BigInteger, DateTime, Identity, String, Text
from sqlalchemy.dialects import postgresql
from sqlmodel import SQLModel, Field
from pydantic import BaseModel

class CustomPromptTypeEnum(str, Enum):
    GENERATE_SQL = "GENERATE_SQL"
    ANALYSIS = "ANALYSIS"
    PREDICT_DATA = "PREDICT_DATA"

class CustomPrompt(SQLModel, table=True):
    __tablename__ = "custom_prompt"

    # --- 新增这一行 ---
    __table_args__ = {'extend_existing': True}

    id: Optional[int] = Field(sa_column=Column(BigInteger, Identity(always=True), primary_key=True))
    oid: Optional[int] = Field(sa_column=Column(BigInteger, nullable=True, index=True))
    name: str = Field(max_length=255, nullable=False)
    type: str = Field(max_length=50, nullable=False)  # 存储 Enum 字符串
    prompt: str = Field(sa_column=Column(Text, nullable=False))
    specific_ds: bool = Field(default=False)
    # 存储数据源 ID 列表 (JSONB)
    datasource_ids: Optional[List[int]] = Field(default=None, sa_column=Column(postgresql.JSONB))
    create_time: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=False), default=datetime.now, nullable=True)
    )

# 用于接收前端参数和返回给前端的 Pydantic 模型
class CustomPromptInfo(BaseModel):
    id: Optional[int] = None
    oid: Optional[int] = None
    name: Optional[str] = None
    type: Optional[str] = None
    prompt: Optional[str] = None
    specific_ds: bool = False
    datasource_ids: Optional[List[int]] = []
    # 前端展示需要名称列表，数据库不存
    datasource_names: Optional[List[str]] = []
    create_time: Optional[datetime] = None

# 分页返回的 Item 结构
class CustomPromptInfoResult(CustomPromptInfo):
    pass