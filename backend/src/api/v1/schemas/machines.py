"""
Machines and MachineGroups Pydantic Schemas
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


# MachineGroup Schemas
class MachineGroupBase(BaseModel):
    """機器群組基礎 Schema"""
    GroupName: str


class MachineGroupCreate(MachineGroupBase):
    """建立機器群組 Schema"""
    GroupId: str


class MachineGroupUpdate(BaseModel):
    """更新機器群組 Schema"""
    GroupName: Optional[str] = None


class MachineGroupResponse(MachineGroupBase):
    """機器群組回應 Schema"""
    GroupId: str
    
    model_config = ConfigDict(from_attributes=True)


# Machine Schemas
class MachineBase(BaseModel):
    """機器基礎 Schema"""
    GroupId: str
    machine_name: Optional[str] = None
    is_active: bool = True


class MachineCreate(MachineBase):
    """建立機器 Schema"""
    MachineId: str


class MachineUpdate(BaseModel):
    """更新機器 Schema"""
    GroupId: Optional[str] = None
    machine_name: Optional[str] = None
    is_active: Optional[bool] = None


class MachineResponse(MachineBase):
    """機器回應 Schema"""
    MachineId: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
