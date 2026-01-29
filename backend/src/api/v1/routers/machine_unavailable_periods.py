"""
MachineUnavailablePeriods API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from infra.db.database import get_db
from domain.models import MachineUnavailablePeriod
from domain.models.machine_unavailable_periods import UnavailableType
from api.v1.schemas.machine_unavailable_periods import (
    MachineUnavailablePeriodCreate,
    MachineUnavailablePeriodUpdate,
    MachineUnavailablePeriodResponse
)

router = APIRouter(prefix="/machine-unavailable-periods", tags=["MachineUnavailablePeriods"])


@router.get("", response_model=List[MachineUnavailablePeriodResponse])
def get_unavailable_periods(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    machine_id: Optional[str] = None,
    unavailable_type: Optional[UnavailableType] = None,
    db: Session = Depends(get_db)
):
    """取得所有機台不可用時段 (支援依機台和類型篩選)"""
    query = db.query(MachineUnavailablePeriod)
    
    if machine_id:
        query = query.filter(MachineUnavailablePeriod.MachineId == machine_id)
    if unavailable_type:
        query = query.filter(MachineUnavailablePeriod.unavailable_type == unavailable_type)
    
    periods = query.offset(skip).limit(limit).all()
    return periods


@router.get("/{period_id}", response_model=MachineUnavailablePeriodResponse)
def get_unavailable_period(period_id: int, db: Session = Depends(get_db)):
    """取得單一機台不可用時段"""
    period = db.query(MachineUnavailablePeriod).filter(MachineUnavailablePeriod.id == period_id).first()
    if not period:
        raise HTTPException(status_code=404, detail=f"機台不可用時段 {period_id} 不存在")
    return period


@router.post("", response_model=MachineUnavailablePeriodResponse, status_code=201)
def create_unavailable_period(period: MachineUnavailablePeriodCreate, db: Session = Depends(get_db)):
    """建立機台不可用時段"""
    # 驗證時間範圍
    if period.end_time <= period.start_time:
        raise HTTPException(status_code=400, detail="結束時間必須大於開始時間")
    
    db_period = MachineUnavailablePeriod(**period.model_dump())
    db.add(db_period)
    db.commit()
    db.refresh(db_period)
    return db_period


@router.put("/{period_id}", response_model=MachineUnavailablePeriodResponse)
def update_unavailable_period(
    period_id: int,
    period: MachineUnavailablePeriodUpdate,
    db: Session = Depends(get_db)
):
    """更新機台不可用時段"""
    db_period = db.query(MachineUnavailablePeriod).filter(MachineUnavailablePeriod.id == period_id).first()
    if not db_period:
        raise HTTPException(status_code=404, detail=f"機台不可用時段 {period_id} 不存在")
    
    # 檢查是否鎖定
    if db_period.is_locked:
        raise HTTPException(status_code=400, detail="此時段已鎖定,無法修改")
    
    update_data = period.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_period, field, value)
    
    db.commit()
    db.refresh(db_period)
    return db_period


@router.delete("/{period_id}", status_code=204)
def delete_unavailable_period(period_id: int, db: Session = Depends(get_db)):
    """刪除機台不可用時段"""
    db_period = db.query(MachineUnavailablePeriod).filter(MachineUnavailablePeriod.id == period_id).first()
    if not db_period:
        raise HTTPException(status_code=404, detail=f"機台不可用時段 {period_id} 不存在")
    
    # 檢查是否鎖定
    if db_period.is_locked:
        raise HTTPException(status_code=400, detail="此時段已鎖定,無法刪除")
    
    db.delete(db_period)
    db.commit()
    return None
