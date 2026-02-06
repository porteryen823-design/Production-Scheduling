"""
Schedule API 路由 (專為甘特圖設計)
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from infra.db.database import get_db
from domain.models import DynamicSchedulingJob, DynamicSchedulingJobHist
from api.v1.schemas.dynamic_scheduling_job import DynamicSchedulingJobResponse
from typing import Any, Dict, Optional

router = APIRouter(tags=["Schedule"])


@router.get("/schedule")
def get_schedule_for_gantt(
    offset: int = Query(0, ge=0, description="偏移量 (0 是最新一筆)"),
    limit: int = Query(1, ge=1, le=10, description="限制數量"),
    source: str = Query("current", description="資料來源: current (目前), history (歷史)"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    取得排程資料 (專為甘特圖設計)
    
    - offset: 偏移量,0 是最新一筆,1 是第二新,依此類推
    - limit: 限制數量,預設 1
    - source: 資料來源
    
    返回格式:
    {
        "ScheduleId": "SCH_xxx",
        "CreateDate": "2026-01-23T19:48:45.000Z",
        "CreateUser": "user",
        "PlanSummary": "summary",
        "machineTaskSegment": [...],
        "total": 30
    }
    """
    # 決定使用的 Model
    model = DynamicSchedulingJobHist if source == "history" else DynamicSchedulingJob
    
    # 計算總數
    total = db.query(func.count(model.ScheduleId)).scalar()
    
    # 查詢排程資料 (按 CreateDate DESC 排序)
    jobs = db.query(model)\
        .order_by(model.CreateDate.desc())\
        .offset(offset)\
        .limit(limit)\
        .all()
    
    if not jobs:
        return {
            "ScheduleId": None,
            "CreateDate": None,
            "CreateUser": None,
            "PlanSummary": None,
            "machineTaskSegment": [],
            "total": total,
            "source": source
        }
    
    # 取第一筆 (因為 limit 通常是 1)
    job = jobs[0]
    
    return {
        "ScheduleId": job.ScheduleId,
        "CreateDate": job.CreateDate.isoformat() if job.CreateDate else None,
        "CreateUser": job.CreateUser,
        "PlanSummary": job.PlanSummary,
        "machineTaskSegment": job.machineTaskSegment if job.machineTaskSegment else [],
        "LotPlanResult": job.LotPlanResult if job.LotPlanResult else {},
        "LotStepResult": job.LotStepResult if job.LotStepResult else {},
        "simulation_end_time": job.simulation_end_time.isoformat() if job.simulation_end_time else None,
        "total": total,
        "source": source
    }
