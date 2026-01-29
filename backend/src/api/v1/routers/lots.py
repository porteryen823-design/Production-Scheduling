"""
Lots API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from infra.db.database import get_db
from domain.models import Lot
from api.v1.schemas.lots import LotCreate, LotUpdate, LotResponse

router = APIRouter(prefix="/lots", tags=["Lots"])


@router.get("", response_model=List[LotResponse])
def get_lots(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    customer_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """取得所有工單 (支援分頁和篩選)"""
    query = db.query(Lot)
    
    if customer_id:
        query = query.filter(Lot.CustomerID == customer_id)
    
    lots = query.offset(skip).limit(limit).all()
    return lots


@router.get("/{lot_id}", response_model=LotResponse)
def get_lot(lot_id: str, db: Session = Depends(get_db)):
    """取得單一工單"""
    lot = db.query(Lot).filter(Lot.LotId == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail=f"工單 {lot_id} 不存在")
    return lot


@router.post("", response_model=LotResponse, status_code=201)
def create_lot(lot: LotCreate, db: Session = Depends(get_db)):
    """建立工單"""
    # 檢查是否已存在
    existing = db.query(Lot).filter(Lot.LotId == lot.LotId).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"工單 {lot.LotId} 已存在")
    
    db_lot = Lot(**lot.model_dump())
    db.add(db_lot)
    db.commit()
    db.refresh(db_lot)
    return db_lot


@router.put("/{lot_id}", response_model=LotResponse)
def update_lot(lot_id: str, lot: LotUpdate, db: Session = Depends(get_db)):
    """更新工單"""
    db_lot = db.query(Lot).filter(Lot.LotId == lot_id).first()
    if not db_lot:
        raise HTTPException(status_code=404, detail=f"工單 {lot_id} 不存在")
    
    # 更新欄位
    update_data = lot.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_lot, field, value)
    
    db.commit()
    db.refresh(db_lot)
    return db_lot


@router.delete("/{lot_id}", status_code=204)
def delete_lot(lot_id: str, db: Session = Depends(get_db)):
    """刪除工單"""
    db_lot = db.query(Lot).filter(Lot.LotId == lot_id).first()
    if not db_lot:
        raise HTTPException(status_code=404, detail=f"工單 {lot_id} 不存在")
    
    db.delete(db_lot)
    db.commit()
    return None


@router.get("/by-priority/sorted", response_model=List[LotResponse])
def get_lots_by_priority(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """依優先權排序取得工單"""
    lots = db.query(Lot).order_by(Lot.Priority.desc()).offset(skip).limit(limit).all()
    return lots
