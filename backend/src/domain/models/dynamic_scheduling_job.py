"""
DynamicSchedulingJob 資料表模型
"""
from sqlalchemy import Column, String, DateTime, JSON, Text
from sqlalchemy.sql import func
from infra.db.database import Base


class DynamicSchedulingJob(Base):
    """動態排程作業"""
    __tablename__ = "DynamicSchedulingJob"
    
    ScheduleId = Column(String(50), primary_key=True)
    LotPlanRaw = Column(Text, nullable=True)
    CreateDate = Column(DateTime, server_default=func.now())
    CreateUser = Column(String(50), nullable=True)
    PlanSummary = Column(String(2500), nullable=True)
    LotPlanResult = Column(JSON, nullable=True)
    LotStepResult = Column(JSON, nullable=True)
    machineTaskSegment = Column(JSON, nullable=True)
    simulation_end_time = Column(DateTime, nullable=True)
