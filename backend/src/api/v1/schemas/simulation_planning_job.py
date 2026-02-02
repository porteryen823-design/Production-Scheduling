from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Any


class SimulationPlanningJobBase(BaseModel):
    key_value: str
    remark: Optional[str] = None


class SimulationPlanningJobCreate(SimulationPlanningJobBase):
    pass


class SimulationPlanningJobResponse(SimulationPlanningJobBase):
    id: int
    ScheduleId: Optional[str] = None
    LotPlanRaw: Optional[str] = None
    CreateDate: datetime
    CreateUser: Optional[str] = None
    PlanSummary: Optional[str] = None
    LotPlanResult: Optional[Any] = None
    LotStepResult: Optional[Any] = None
    machineTaskSegment: Optional[Any] = None
    simulation_end_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
