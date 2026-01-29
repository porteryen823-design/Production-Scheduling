"""
Operations 資料表模型 (Completed, WIP, Frozen)
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from infra.db.database import Base


class CompletedOperation(Base):
    """已完成的作業"""
    __tablename__ = "CompletedOperations"
    
    LotId = Column(String(50), ForeignKey("Lots.LotId"), primary_key=True)
    Step = Column(String(20), primary_key=True)
    MachineId = Column(String(20), ForeignKey("Machines.MachineId"), nullable=False)
    StartTime = Column(DateTime, nullable=False)
    EndTime = Column(DateTime, nullable=False)
    
    # 關聯
    lot = relationship("Lot", back_populates="completed_operations")
    machine = relationship("Machine", back_populates="completed_operations")


class WIPOperation(Base):
    """進行中的作業"""
    __tablename__ = "WIPOperations"
    
    LotId = Column(String(50), ForeignKey("Lots.LotId"), primary_key=True)
    Step = Column(String(20), primary_key=True)
    MachineId = Column(String(20), ForeignKey("Machines.MachineId"), nullable=False)
    StartTime = Column(DateTime, nullable=False)
    ElapsedMinutes = Column(Integer, nullable=False)
    
    # 關聯
    lot = relationship("Lot", back_populates="wip_operations")
    machine = relationship("Machine", back_populates="wip_operations")


class FrozenOperation(Base):
    """凍結的作業"""
    __tablename__ = "FrozenOperations"
    
    LotId = Column(String(50), ForeignKey("Lots.LotId"), primary_key=True)
    Step = Column(String(20), primary_key=True)
    MachineId = Column(String(20), ForeignKey("Machines.MachineId"), nullable=False)
    StartTime = Column(DateTime, nullable=False)
    EndTime = Column(DateTime, nullable=False)
    
    # 關聯
    lot = relationship("Lot", back_populates="frozen_operations")
    machine = relationship("Machine", back_populates="frozen_operations")
