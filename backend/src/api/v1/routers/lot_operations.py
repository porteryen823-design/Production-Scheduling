"""
LotOperations API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from infra.db.database import get_db
from domain.models import LotOperation
from api.v1.schemas.lot_operations import LotOperationCreate, LotOperationUpdate, LotOperationResponse

router = APIRouter(prefix="/lot-operations", tags=["LotOperations"])


@router.get("", response_model=List[LotOperationResponse])
def get_lot_operations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """取得所有工單作業"""
    operations = db.query(LotOperation).offset(skip).limit(limit).all()
    return operations


@router.get("/lot/{lot_id}", response_model=List[LotOperationResponse])
def get_lot_operations_by_lot(lot_id: str, db: Session = Depends(get_db)):
    """取得指定工單的所有作業"""
    operations = db.query(LotOperation).filter(LotOperation.LotId == lot_id).order_by(LotOperation.Sequence).all()
    return operations


@router.get("/{lot_id}/{step}", response_model=LotOperationResponse)
def get_lot_operation(lot_id: str, step: str, db: Session = Depends(get_db)):
    """取得單一工單作業"""
    operation = db.query(LotOperation).filter(
        LotOperation.LotId == lot_id,
        LotOperation.Step == step
    ).first()
    if not operation:
        raise HTTPException(status_code=404, detail=f"工單作業 {lot_id}/{step} 不存在")
    return operation


@router.post("", response_model=LotOperationResponse, status_code=201)
def create_lot_operation(operation: LotOperationCreate, db: Session = Depends(get_db)):
    """建立工單作業"""
    # 檢查是否已存在
    existing = db.query(LotOperation).filter(
        LotOperation.LotId == operation.LotId,
        LotOperation.Step == operation.Step
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"工單作業 {operation.LotId}/{operation.Step} 已存在")
    
    db_operation = LotOperation(**operation.model_dump())
    db.add(db_operation)
    db.commit()
    db.refresh(db_operation)
    return db_operation


@router.put("/{lot_id}/{step}", response_model=LotOperationResponse)
def update_lot_operation(
    lot_id: str,
    step: str,
    operation: LotOperationUpdate,
    db: Session = Depends(get_db)
):
    """更新工單作業"""
    db_operation = db.query(LotOperation).filter(
        LotOperation.LotId == lot_id,
        LotOperation.Step == step
    ).first()
    if not db_operation:
        raise HTTPException(status_code=404, detail=f"工單作業 {lot_id}/{step} 不存在")
    
    update_data = operation.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_operation, field, value)
    
    db.commit()
    db.refresh(db_operation)
    return db_operation


@router.delete("/{lot_id}/{step}", status_code=204)
def delete_lot_operation(lot_id: str, step: str, db: Session = Depends(get_db)):
    """刪除工單作業"""
    db_operation = db.query(LotOperation).filter(
        LotOperation.LotId == lot_id,
        LotOperation.Step == step
    ).first()
    if not db_operation:
        raise HTTPException(status_code=404, detail=f"工單作業 {lot_id}/{step} 不存在")
    
    db.delete(db_operation)
    db.commit()
    return None


@router.put("/{lot_id}/{step}/check-in", response_model=LotOperationResponse)
def check_in_operation(lot_id: str, step: str, db: Session = Depends(get_db)):
    """作業 CheckIn"""
    db_operation = db.query(LotOperation).filter(
        LotOperation.LotId == lot_id,
        LotOperation.Step == step
    ).first()
    if not db_operation:
        raise HTTPException(status_code=404, detail=f"工單作業 {lot_id}/{step} 不存在")
    
    db_operation.CheckInTime = datetime.now()
    db_operation.StepStatus = 1
    
    db.commit()
    db.refresh(db_operation)
    return db_operation


@router.put("/{lot_id}/{step}/check-out", response_model=LotOperationResponse)
def check_out_operation(lot_id: str, step: str, db: Session = Depends(get_db)):
    """作業 CheckOut"""
    db_operation = db.query(LotOperation).filter(
        LotOperation.LotId == lot_id,
        LotOperation.Step == step
    ).first()
    if not db_operation:
        raise HTTPException(status_code=404, detail=f"工單作業 {lot_id}/{step} 不存在")
    
    db_operation.CheckOutTime = datetime.now()
    db_operation.StepStatus = 2
    
    db.commit()
    db.refresh(db_operation)
    return db_operation
