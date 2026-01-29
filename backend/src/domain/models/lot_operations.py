"""
LotOperations 資料表模型
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from infra.db.database import Base


class LotOperation(Base):
    """工單的作業步驟"""
    __tablename__ = "LotOperations"
    
    LotId = Column(String(50), ForeignKey("Lots.LotId"), primary_key=True)
    Step = Column(String(20), primary_key=True)
    MachineGroup = Column(String(20), nullable=False)
    Duration = Column(Integer, nullable=False)
    Sequence = Column(Integer, nullable=False)
    CheckInTime = Column(DateTime, nullable=True)
    CheckOutTime = Column(DateTime, nullable=True)
    StepStatus = Column(Integer, default=0)
    PlanCheckInTime = Column(DateTime, nullable=True)
    PlanCheckOutTime = Column(DateTime, nullable=True)
    PlanMachineId = Column(String(20), nullable=True)
    PlanHistory = Column(JSON, nullable=True)
    
    # 關聯
    lot = relationship("Lot", back_populates="operations")
