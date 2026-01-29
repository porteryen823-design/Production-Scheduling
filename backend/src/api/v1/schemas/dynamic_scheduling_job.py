"""
DynamicSchedulingJob Pydantic Schemas
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Any


class DynamicSchedulingJobBase(BaseModel):
    """動態排程作業基礎 Schema"""
    LotPlanRaw: Optional[str] = None
    CreateUser: Optional[str] = None
    PlanSummary: Optional[str] = None
    LotPlanResult: Optional[Any] = None
    LotStepResult: Optional[Any] = None
    machineTaskSegment: Optional[Any] = None
    simulation_end_time: Optional[datetime] = None


class DynamicSchedulingJobCreate(DynamicSchedulingJobBase):
    """建立動態排程作業 Schema"""
    ScheduleId: str


class DynamicSchedulingJobUpdate(BaseModel):
    """更新動態排程作業 Schema"""
    LotPlanRaw: Optional[str] = None
    CreateUser: Optional[str] = None
    PlanSummary: Optional[str] = None
    LotPlanResult: Optional[Any] = None
    LotStepResult: Optional[Any] = None
    machineTaskSegment: Optional[Any] = None
    simulation_end_time: Optional[datetime] = None


class DynamicSchedulingJobResponse(DynamicSchedulingJobBase):
    """動態排程作業回應 Schema"""
    ScheduleId: str
    CreateDate: datetime
    
    model_config = ConfigDict(from_attributes=True)
