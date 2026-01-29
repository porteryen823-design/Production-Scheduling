"""
LotOperations Pydantic Schemas
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Any


class LotOperationBase(BaseModel):
    """工單作業基礎 Schema"""
    MachineGroup: str
    Duration: int
    Sequence: int
    CheckInTime: Optional[datetime] = None
    CheckOutTime: Optional[datetime] = None
    StepStatus: int = 0
    PlanCheckInTime: Optional[datetime] = None
    PlanCheckOutTime: Optional[datetime] = None
    PlanMachineId: Optional[str] = None
    PlanHistory: Optional[Any] = None


class LotOperationCreate(LotOperationBase):
    """建立工單作業 Schema"""
    LotId: str
    Step: str


class LotOperationUpdate(BaseModel):
    """更新工單作業 Schema"""
    MachineGroup: Optional[str] = None
    Duration: Optional[int] = None
    Sequence: Optional[int] = None
    CheckInTime: Optional[datetime] = None
    CheckOutTime: Optional[datetime] = None
    StepStatus: Optional[int] = None
    PlanCheckInTime: Optional[datetime] = None
    PlanCheckOutTime: Optional[datetime] = None
    PlanMachineId: Optional[str] = None
    PlanHistory: Optional[Any] = None


class LotOperationResponse(LotOperationBase):
    """工單作業回應 Schema"""
    LotId: str
    Step: str
    
    model_config = ConfigDict(from_attributes=True)
