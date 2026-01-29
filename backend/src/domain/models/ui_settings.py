"""
UI 設定資料表模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from infra.db.database import Base


class UISetting(Base):
    """UI 設定"""
    __tablename__ = "ui_settings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    parameter_name = Column(String(255), unique=True, nullable=False, comment="參數名稱")
    parameter_value = Column(Text, nullable=True, comment="參數值")
    remark = Column(Text, nullable=True, comment="備註")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
