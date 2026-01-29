"""
MachineUnavailablePeriods 資料表模型
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, JSON, Enum, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from infra.db.database import Base


class UnavailableType(str, enum.Enum):
    """機台不可用類型"""
    PM = "PM"                      # 預防性保養
    CM = "CM"                      # 矯正性維修
    BREAK = "BREAK"                # 休息時間
    SHIFT_CHANGE = "SHIFT_CHANGE"  # 換班時間
    DOWNTIME = "DOWNTIME"          # 故障停機
    COMPLETED = "COMPLETED"        # 已完成作業
    WIP = "WIP"                    # 進行中作業
    FROZEN = "FROZEN"              # 凍結作業
    RESERVED = "RESERVED"          # 預留/保留
    OTHER = "OTHER"                # 其他


class MachineUnavailablePeriod(Base):
    """機台不可用時段"""
    __tablename__ = "machine_unavailable_periods"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    MachineId = Column(String(20), ForeignKey("Machines.MachineId", ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    unavailable_type = Column(Enum(UnavailableType), nullable=False)
    
    # 關聯資訊
    lot_id = Column(String(50), nullable=True)
    operation_step = Column(String(50), nullable=True)
    
    # 其他資訊
    reason = Column(String(255), nullable=True)
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(JSON, nullable=True)
    
    # 管理欄位
    source = Column(String(50), nullable=True)
    is_locked = Column(Boolean, default=False)
    created_by = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 關聯
    machine = relationship("Machine", back_populates="unavailable_periods")
    
    # 約束
    __table_args__ = (
        CheckConstraint('end_time > start_time', name='chk_time_valid'),
    )
