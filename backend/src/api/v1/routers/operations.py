"""
Operations API 路由 (Completed, WIP, Frozen)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from infra.db.database import get_db
from domain.models import CompletedOperation, WIPOperation, FrozenOperation
from api.v1.schemas.operations import (
    CompletedOperationCreate, CompletedOperationUpdate, CompletedOperationResponse,
    WIPOperationCreate, WIPOperationUpdate, WIPOperationResponse,
    FrozenOperationCreate, FrozenOperationUpdate, FrozenOperationResponse
)

router = APIRouter(tags=["Operations"])


# CompletedOperations 路由
@router.get("/completed-operations", response_model=List[CompletedOperationResponse])
def get_completed_operations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """取得所有已完成作業"""
    operations = db.query(CompletedOperation).offset(skip).limit(limit).all()
    return operations


@router.get("/completed-operations/{lot_id}/{step}", response_model=CompletedOperationResponse)
def get_completed_operation(lot_id: str, step: str, db: Session = Depends(get_db)):
    """取得單一已完成作業"""
    operation = db.query(CompletedOperation).filter(
        CompletedOperation.LotId == lot_id,
        CompletedOperation.Step == step
    ).first()
    if not operation:
        raise HTTPException(status_code=404, detail=f"已完成作業 {lot_id}/{step} 不存在")
    return operation


@router.post("/completed-operations", response_model=CompletedOperationResponse, status_code=201)
def create_completed_operation(operation: CompletedOperationCreate, db: Session = Depends(get_db)):
    """建立已完成作業"""
    db_operation = CompletedOperation(**operation.model_dump())
    db.add(db_operation)
    db.commit()
    db.refresh(db_operation)
    return db_operation


@router.delete("/completed-operations/{lot_id}/{step}", status_code=204)
def delete_completed_operation(lot_id: str, step: str, db: Session = Depends(get_db)):
    """刪除已完成作業"""
    db_operation = db.query(CompletedOperation).filter(
        CompletedOperation.LotId == lot_id,
        CompletedOperation.Step == step
    ).first()
    if not db_operation:
        raise HTTPException(status_code=404, detail=f"已完成作業 {lot_id}/{step} 不存在")
    
    db.delete(db_operation)
    db.commit()
    return None


# WIPOperations 路由
@router.get("/wip-operations", response_model=List[WIPOperationResponse])
def get_wip_operations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """取得所有進行中作業"""
    operations = db.query(WIPOperation).offset(skip).limit(limit).all()
    return operations


@router.get("/wip-operations/{lot_id}/{step}", response_model=WIPOperationResponse)
def get_wip_operation(lot_id: str, step: str, db: Session = Depends(get_db)):
    """取得單一進行中作業"""
    operation = db.query(WIPOperation).filter(
        WIPOperation.LotId == lot_id,
        WIPOperation.Step == step
    ).first()
    if not operation:
        raise HTTPException(status_code=404, detail=f"進行中作業 {lot_id}/{step} 不存在")
    return operation


@router.post("/wip-operations", response_model=WIPOperationResponse, status_code=201)
def create_wip_operation(operation: WIPOperationCreate, db: Session = Depends(get_db)):
    """建立進行中作業"""
    db_operation = WIPOperation(**operation.model_dump())
    db.add(db_operation)
    db.commit()
    db.refresh(db_operation)
    return db_operation


@router.put("/wip-operations/{lot_id}/{step}", response_model=WIPOperationResponse)
def update_wip_operation(
    lot_id: str,
    step: str,
    operation: WIPOperationUpdate,
    db: Session = Depends(get_db)
):
    """更新進行中作業"""
    db_operation = db.query(WIPOperation).filter(
        WIPOperation.LotId == lot_id,
        WIPOperation.Step == step
    ).first()
    if not db_operation:
        raise HTTPException(status_code=404, detail=f"進行中作業 {lot_id}/{step} 不存在")
    
    update_data = operation.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_operation, field, value)
    
    db.commit()
    db.refresh(db_operation)
    return db_operation


@router.delete("/wip-operations/{lot_id}/{step}", status_code=204)
def delete_wip_operation(lot_id: str, step: str, db: Session = Depends(get_db)):
    """刪除進行中作業"""
    db_operation = db.query(WIPOperation).filter(
        WIPOperation.LotId == lot_id,
        WIPOperation.Step == step
    ).first()
    if not db_operation:
        raise HTTPException(status_code=404, detail=f"進行中作業 {lot_id}/{step} 不存在")
    
    db.delete(db_operation)
    db.commit()
    return None


# FrozenOperations 路由
@router.get("/frozen-operations", response_model=List[FrozenOperationResponse])
def get_frozen_operations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """取得所有凍結作業"""
    operations = db.query(FrozenOperation).offset(skip).limit(limit).all()
    return operations


@router.get("/frozen-operations/{lot_id}/{step}", response_model=FrozenOperationResponse)
def get_frozen_operation(lot_id: str, step: str, db: Session = Depends(get_db)):
    """取得單一凍結作業"""
    operation = db.query(FrozenOperation).filter(
        FrozenOperation.LotId == lot_id,
        FrozenOperation.Step == step
    ).first()
    if not operation:
        raise HTTPException(status_code=404, detail=f"凍結作業 {lot_id}/{step} 不存在")
    return operation


@router.post("/frozen-operations", response_model=FrozenOperationResponse, status_code=201)
def create_frozen_operation(operation: FrozenOperationCreate, db: Session = Depends(get_db)):
    """建立凍結作業"""
    db_operation = FrozenOperation(**operation.model_dump())
    db.add(db_operation)
    db.commit()
    db.refresh(db_operation)
    return db_operation


@router.delete("/frozen-operations/{lot_id}/{step}", status_code=204)
def delete_frozen_operation(lot_id: str, step: str, db: Session = Depends(get_db)):
    """刪除凍結作業"""
    db_operation = db.query(FrozenOperation).filter(
        FrozenOperation.LotId == lot_id,
        FrozenOperation.Step == step
    ).first()
    if not db_operation:
        raise HTTPException(status_code=404, detail=f"凍結作業 {lot_id}/{step} 不存在")
    
    db.delete(db_operation)
    db.commit()
    return None
