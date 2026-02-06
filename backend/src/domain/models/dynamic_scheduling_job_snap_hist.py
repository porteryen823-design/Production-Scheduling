"""
DynamicSchedulingJob_Snap_Hist 資料表模型
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.sql import func
from infra.db.database import Base


class DynamicSchedulingJob_Snap_Hist(Base):
    """模擬規劃歷史紀錄"""
    __tablename__ = "DynamicSchedulingJob_Snap_Hist"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key_value = Column(String(100), nullable=False)
    remark = Column(Text, nullable=True)
    
    # 複製自 DynamicSchedulingJob 的欄位
    ScheduleId = Column(String(50), nullable=True)
    LotPlanRaw = Column(Text, nullable=True)
    CreateDate = Column(DateTime, server_default=func.now())
    CreateUser = Column(String(50), nullable=True)
    PlanSummary = Column(String(2500), nullable=True)
    LotPlanResult = Column(JSON, nullable=True)
    LotStepResult = Column(JSON, nullable=True)
    machineTaskSegment = Column(JSON, nullable=True)
    simulation_end_time = Column(DateTime, nullable=True)
