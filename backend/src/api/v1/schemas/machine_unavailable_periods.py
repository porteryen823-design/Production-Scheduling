"""
MachineUnavailablePeriods Pydantic Schemas
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Any
from domain.models.machine_unavailable_periods import UnavailableType


class MachineUnavailablePeriodBase(BaseModel):
    """機台不可用時段基礎 Schema"""
    MachineId: str
    start_time: datetime
    end_time: datetime
    unavailable_type: UnavailableType
    lot_id: Optional[str] = None
    operation_step: Optional[str] = None
    reason: Optional[str] = None
    is_recurring: bool = False
    recurrence_rule: Optional[Any] = None
    source: Optional[str] = None
    is_locked: bool = False
    created_by: Optional[str] = None


class MachineUnavailablePeriodCreate(MachineUnavailablePeriodBase):
    """建立機台不可用時段 Schema"""
    pass


class MachineUnavailablePeriodUpdate(BaseModel):
    """更新機台不可用時段 Schema"""
    MachineId: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    unavailable_type: Optional[UnavailableType] = None
    lot_id: Optional[str] = None
    operation_step: Optional[str] = None
    reason: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence_rule: Optional[Any] = None
    source: Optional[str] = None
    is_locked: Optional[bool] = None
    created_by: Optional[str] = None


class MachineUnavailablePeriodResponse(MachineUnavailablePeriodBase):
    """機台不可用時段回應 Schema"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
