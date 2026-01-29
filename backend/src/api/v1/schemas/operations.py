"""
Operations Pydantic Schemas (Completed, WIP, Frozen)
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


# CompletedOperation Schemas
class CompletedOperationBase(BaseModel):
    """已完成作業基礎 Schema"""
    MachineId: str
    StartTime: datetime
    EndTime: datetime


class CompletedOperationCreate(CompletedOperationBase):
    """建立已完成作業 Schema"""
    LotId: str
    Step: str


class CompletedOperationUpdate(BaseModel):
    """更新已完成作業 Schema"""
    MachineId: Optional[str] = None
    StartTime: Optional[datetime] = None
    EndTime: Optional[datetime] = None


class CompletedOperationResponse(CompletedOperationBase):
    """已完成作業回應 Schema"""
    LotId: str
    Step: str
    
    model_config = ConfigDict(from_attributes=True)


# WIPOperation Schemas
class WIPOperationBase(BaseModel):
    """進行中作業基礎 Schema"""
    MachineId: str
    StartTime: datetime
    ElapsedMinutes: int


class WIPOperationCreate(WIPOperationBase):
    """建立進行中作業 Schema"""
    LotId: str
    Step: str


class WIPOperationUpdate(BaseModel):
    """更新進行中作業 Schema"""
    MachineId: Optional[str] = None
    StartTime: Optional[datetime] = None
    ElapsedMinutes: Optional[int] = None


class WIPOperationResponse(WIPOperationBase):
    """進行中作業回應 Schema"""
    LotId: str
    Step: str
    
    model_config = ConfigDict(from_attributes=True)


# FrozenOperation Schemas
class FrozenOperationBase(BaseModel):
    """凍結作業基礎 Schema"""
    MachineId: str
    StartTime: datetime
    EndTime: datetime


class FrozenOperationCreate(FrozenOperationBase):
    """建立凍結作業 Schema"""
    LotId: str
    Step: str


class FrozenOperationUpdate(BaseModel):
    """更新凍結作業 Schema"""
    MachineId: Optional[str] = None
    StartTime: Optional[datetime] = None
    EndTime: Optional[datetime] = None


class FrozenOperationResponse(FrozenOperationBase):
    """凍結作業回應 Schema"""
    LotId: str
    Step: str
    
    model_config = ConfigDict(from_attributes=True)
