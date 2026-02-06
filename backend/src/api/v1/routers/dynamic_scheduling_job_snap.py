"""
DynamicSchedulingJobSnap API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from infra.db.database import get_db
from domain.models import DynamicSchedulingJobSnap, DynamicSchedulingJob
from core.config import settings
from api.v1.schemas.dynamic_scheduling_job_snap import (
    DynamicSchedulingJobSnapCreate,
    DynamicSchedulingJobSnapResponse
)

router = APIRouter(prefix="/dynamic-scheduling-job-snaps", tags=["DynamicSchedulingJobSnaps"])


@router.get("", response_model=List[DynamicSchedulingJobSnapResponse])
def get_simulation_planning_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """取得所有模擬規劃備份"""
    jobs = db.query(DynamicSchedulingJobSnap).order_by(DynamicSchedulingJobSnap.CreateDate.desc()).offset(skip).limit(limit).all()
    return jobs


@router.post("/save", status_code=201)
def save_current_job_to_simulation(
    job_info: DynamicSchedulingJobSnapCreate,
    db: Session = Depends(get_db)
):
    """將現有的所有 DynamicSchedulingJob 存入模擬規劃"""
    # 1. 取得所有資料 (使用原生 SQL 以排除 ORM 問題)
    from sqlalchemy import text
    result = db.execute(text("SELECT * FROM DynamicSchedulingJob"))
    current_jobs = result.fetchall()
    count = len(current_jobs)
    print(f"DEBUG: Found {count} records in DynamicSchedulingJob via RAW SQL")
    
    if count == 0:
        raise HTTPException(status_code=404, detail="目前沒有任何動態排程作業可以儲存")
    
    # 2. 轉換為 dict 列表進行批量插入
    data_to_save = []
    for job in current_jobs:
        # 使用 _mapping 或是直接轉換
        job_dict = dict(job._mapping) if hasattr(job, '_mapping') else dict(job)
        data_to_save.append({
            "key_value": job_info.key_value,
            "remark": job_info.remark,
            "ScheduleId": job_dict.get("ScheduleId"),
            "LotPlanRaw": job_dict.get("LotPlanRaw"),
            "CreateUser": job_dict.get("CreateUser"),
            "PlanSummary": job_dict.get("PlanSummary"),
            "LotPlanResult": job_dict.get("LotPlanResult"),
            "LotStepResult": job_dict.get("LotStepResult"),
            "machineTaskSegment": job_dict.get("machineTaskSegment"),
            "simulation_end_time": job_dict.get("simulation_end_time")
        })
    
    # 3. 執行批量插入
    try:
        db.bulk_insert_mappings(DynamicSchedulingJobSnap, data_to_save)
        db.commit()
        print(f"DEBUG: Successfully bulk inserted {len(data_to_save)} records")
        return {
            "message": f"成功儲存 {len(data_to_save)} 筆記錄", 
            "count": len(data_to_save),
            "db_info": {
                "host": settings.DB_HOST,
                "user": settings.DB_USER,
                "name": settings.DB_NAME
            }
        }
    except Exception as e:
        db.rollback()
        print(f"ERROR during bulk insert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/load/{job_id}", status_code=200)
def load_simulation_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """從模擬規劃還原至 DynamicSchedulingJob (還原當初整批存入的所有記錄)"""
    # 1. 取得指定的備份點資料，並找出其對應的 key_value
    target_backup = db.query(DynamicSchedulingJobSnap).filter(DynamicSchedulingJobSnap.id == job_id).first()
    if not target_backup:
        raise HTTPException(status_code=404, detail=f"找不到 ID 為 {job_id} 的模擬規劃")
    
    # 根據 key_value 找出同一批的所有備份
    all_backups = db.query(DynamicSchedulingJobSnap).filter(DynamicSchedulingJobSnap.key_value == target_backup.key_value).all()
    
    # 2. 刪除現有的 DynamicSchedulingJob
    db.query(DynamicSchedulingJob).delete()
    
    # 3. 插入還原資料
    for backup_job in all_backups:
        new_job = DynamicSchedulingJob(
            ScheduleId=backup_job.ScheduleId,
            LotPlanRaw=backup_job.LotPlanRaw,
            CreateUser=backup_job.CreateUser,
            PlanSummary=backup_job.PlanSummary,
            LotPlanResult=backup_job.LotPlanResult,
            LotStepResult=backup_job.LotStepResult,
            machineTaskSegment=backup_job.machineTaskSegment,
            simulation_end_time=backup_job.simulation_end_time
        )
        db.add(new_job)
    
    db.commit()
    
    return {"message": f"還原成功，共還原 {len(all_backups)} 筆記錄", "key_value": target_backup.key_value}


@router.delete("/{job_id}", status_code=204)
def delete_simulation_job(job_id: int, db: Session = Depends(get_db)):
    """刪除模擬規劃備份 (刪除該 ID 所屬整批 key_value)"""
    target = db.query(DynamicSchedulingJobSnap).filter(DynamicSchedulingJobSnap.id == job_id).first()
    if not target:
        raise HTTPException(status_code=404, detail=f"找不到 ID 為 {job_id} 的模擬規劃")
    
    # 刪除同一批 key_value 的所有記錄
    db.query(DynamicSchedulingJobSnap).filter(DynamicSchedulingJobSnap.key_value == target.key_value).delete()
    db.commit()
    return None
