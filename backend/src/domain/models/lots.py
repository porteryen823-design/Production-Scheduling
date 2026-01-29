"""
Lots 資料表模型
"""
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from infra.db.database import Base


class Lot(Base):
    """工單基本資訊"""
    __tablename__ = "Lots"
    
    LotId = Column(String(50), primary_key=True)
    Priority = Column(Integer, nullable=False)
    DueDate = Column(DateTime, nullable=False)
    ActualFinishDate = Column(DateTime, nullable=True)
    ProductID = Column(String(50), nullable=True)
    ProductName = Column(String(100), nullable=True)
    CustomerID = Column(String(50), nullable=True)
    CustomerName = Column(String(100), nullable=True)
    LotCreateDate = Column(DateTime, nullable=True)
    
    # 關聯
    operations = relationship("LotOperation", back_populates="lot", cascade="all, delete-orphan")
    completed_operations = relationship("CompletedOperation", back_populates="lot", cascade="all, delete-orphan")
    wip_operations = relationship("WIPOperation", back_populates="lot", cascade="all, delete-orphan")
    frozen_operations = relationship("FrozenOperation", back_populates="lot", cascade="all, delete-orphan")
