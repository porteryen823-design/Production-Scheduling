"""
Machines 和 MachineGroups 資料表模型
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from infra.db.database import Base


class MachineGroup(Base):
    """機器群組"""
    __tablename__ = "MachineGroups"
    
    GroupId = Column(String(20), primary_key=True)
    GroupName = Column(String(100), nullable=False)
    
    # 關聯
    machines = relationship("Machine", back_populates="group", cascade="all, delete-orphan")


class Machine(Base):
    """機器"""
    __tablename__ = "Machines"
    
    MachineId = Column(String(20), primary_key=True)
    GroupId = Column(String(20), ForeignKey("MachineGroups.GroupId"), nullable=False)
    machine_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 關聯
    group = relationship("MachineGroup", back_populates="machines")
    unavailable_periods = relationship("MachineUnavailablePeriod", back_populates="machine", cascade="all, delete-orphan")
    completed_operations = relationship("CompletedOperation", back_populates="machine")
    wip_operations = relationship("WIPOperation", back_populates="machine")
    frozen_operations = relationship("FrozenOperation", back_populates="machine")
