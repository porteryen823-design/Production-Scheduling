"""
Simulation Data API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from infra.db.database import get_db
from domain.models.simulation_data import SimulationData
from api.v1.schemas.simulation_data import (
    SimulationDataCreate,
    SimulationDataUpdate,
    SimulationDataResponse
)

router = APIRouter(prefix="/simulation-data", tags=["SimulationData"])


@router.get("", response_model=List[SimulationDataResponse])
def get_simulation_data_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """取得所有模擬資料"""
    return db.query(SimulationData).offset(skip).limit(limit).all()


@router.get("/{schedule_id}", response_model=SimulationDataResponse)
def get_simulation_data_by_schedule(schedule_id: str, db: Session = Depends(get_db)):
    """依 Schedule ID 取得模擬資料"""
    data = db.query(SimulationData).filter(SimulationData.schedule_id == schedule_id).first()
    if not data:
        raise HTTPException(status_code=404, detail=f"找不到排程 {schedule_id} 的模擬資料")
    return data


@router.post("", response_model=SimulationDataResponse, status_code=201)
def create_simulation_data(data: SimulationDataCreate, db: Session = Depends(get_db)):
    """建立模擬資料"""
    existing = db.query(SimulationData).filter(SimulationData.schedule_id == data.schedule_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"排程 {data.schedule_id} 的模擬資料已存在")
    
    db_data = SimulationData(**data.model_dump())
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    return db_data


@router.put("/{schedule_id}", response_model=SimulationDataResponse)
def update_simulation_data(
    schedule_id: str,
    data_update: SimulationDataUpdate,
    db: Session = Depends(get_db)
):
    """更新模擬資料"""
    db_data = db.query(SimulationData).filter(SimulationData.schedule_id == schedule_id).first()
    if not db_data:
        raise HTTPException(status_code=404, detail=f"找不到排程 {schedule_id} 的模擬資料")
    
    update_data = data_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_data, field, value)
    
    db.commit()
    db.refresh(db_data)
    return db_data


@router.delete("/{schedule_id}", status_code=204)
def delete_simulation_data(schedule_id: str, db: Session = Depends(get_db)):
    """刪除模擬資料"""
    db_data = db.query(SimulationData).filter(SimulationData.schedule_id == schedule_id).first()
    if not db_data:
        raise HTTPException(status_code=404, detail=f"找不到排程 {schedule_id} 的模擬資料")
    
    db.delete(db_data)
    db.commit()
    return None
