"""
SimulationData Pydantic Schemas
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Any


class SimulationDataBase(BaseModel):
    """模擬資料基礎 Schema"""
    schedule_id: str
    gantt_data: Optional[Any] = None
    kpi_results: Optional[Any] = None


class SimulationDataCreate(SimulationDataBase):
    """建立模擬資料 Schema"""
    pass


class SimulationDataUpdate(BaseModel):
    """更新模擬資料 Schema"""
    gantt_data: Optional[Any] = None
    kpi_results: Optional[Any] = None


class SimulationDataResponse(SimulationDataBase):
    """模擬資料回應 Schema"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
