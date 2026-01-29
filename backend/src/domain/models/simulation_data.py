"""
SimulationData 資料表模型
"""
from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.sql import func
from infra.db.database import Base


class SimulationData(Base):
    """模擬結果追蹤資料"""
    __tablename__ = "simulation_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    schedule_id = Column(String(50), nullable=False, unique=True, comment="對應的排程 ID")
    gantt_data = Column(JSON, nullable=True, comment="甘特圖專用 JSON 資料")
    kpi_results = Column(JSON, nullable=True, comment="KPI 指標結果資料")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
