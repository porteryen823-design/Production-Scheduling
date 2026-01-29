"""
DynamicSchedulingJob API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from infra.db.database import get_db
from domain.models import DynamicSchedulingJob
from api.v1.schemas.dynamic_scheduling_job import (
    DynamicSchedulingJobCreate,
    DynamicSchedulingJobUpdate,
    DynamicSchedulingJobResponse
)

router = APIRouter(prefix="/dynamic-scheduling-jobs", tags=["DynamicSchedulingJobs"])


@router.get("", response_model=List[DynamicSchedulingJobResponse])
def get_scheduling_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """取得所有動態排程作業"""
    jobs = db.query(DynamicSchedulingJob).order_by(DynamicSchedulingJob.CreateDate.desc()).offset(skip).limit(limit).all()
    return jobs


@router.get("/{schedule_id}", response_model=DynamicSchedulingJobResponse)
def get_scheduling_job(schedule_id: str, db: Session = Depends(get_db)):
    """取得單一動態排程作業"""
    job = db.query(DynamicSchedulingJob).filter(DynamicSchedulingJob.ScheduleId == schedule_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"動態排程作業 {schedule_id} 不存在")
    return job


@router.post("", response_model=DynamicSchedulingJobResponse, status_code=201)
def create_scheduling_job(job: DynamicSchedulingJobCreate, db: Session = Depends(get_db)):
    """建立動態排程作業"""
    existing = db.query(DynamicSchedulingJob).filter(DynamicSchedulingJob.ScheduleId == job.ScheduleId).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"動態排程作業 {job.ScheduleId} 已存在")
    
    db_job = DynamicSchedulingJob(**job.model_dump())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


@router.put("/{schedule_id}", response_model=DynamicSchedulingJobResponse)
def update_scheduling_job(
    schedule_id: str,
    job: DynamicSchedulingJobUpdate,
    db: Session = Depends(get_db)
):
    """更新動態排程作業"""
    db_job = db.query(DynamicSchedulingJob).filter(DynamicSchedulingJob.ScheduleId == schedule_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail=f"動態排程作業 {schedule_id} 不存在")
    
    update_data = job.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_job, field, value)
    
    db.commit()
    db.refresh(db_job)
    return db_job


@router.delete("/{schedule_id}", status_code=204)
def delete_scheduling_job(schedule_id: str, db: Session = Depends(get_db)):
    """刪除動態排程作業"""
    db_job = db.query(DynamicSchedulingJob).filter(DynamicSchedulingJob.ScheduleId == schedule_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail=f"動態排程作業 {schedule_id} 不存在")
    
    db.delete(db_job)
    db.commit()
    return None
