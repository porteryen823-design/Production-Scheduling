"""
UI Settings Pydantic Schemas
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class UISettingBase(BaseModel):
    """UI 設定基礎 Schema"""
    parameter_name: str
    parameter_value: Optional[str] = None
    remark: Optional[str] = None


class UISettingCreate(UISettingBase):
    """建立 UI 設定 Schema"""
    pass


class UISettingUpdate(BaseModel):
    """更新 UI 設定 Schema"""
    parameter_value: Optional[str] = None
    remark: Optional[str] = None


class UISetting(UISettingBase):
    """UI 設定回應 Schema"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
