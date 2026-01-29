"""
Machines and MachineGroups API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from infra.db.database import get_db
from domain.models import Machine, MachineGroup
from api.v1.schemas.machines import (
    MachineCreate, MachineUpdate, MachineResponse,
    MachineGroupCreate, MachineGroupUpdate, MachineGroupResponse
)

router = APIRouter(tags=["Machines"])


# MachineGroup 路由
@router.get("/machine-groups", response_model=List[MachineGroupResponse])
def get_machine_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """取得所有機器群組"""
    groups = db.query(MachineGroup).offset(skip).limit(limit).all()
    return groups


@router.get("/machine-groups/{group_id}", response_model=MachineGroupResponse)
def get_machine_group(group_id: str, db: Session = Depends(get_db)):
    """取得單一機器群組"""
    group = db.query(MachineGroup).filter(MachineGroup.GroupId == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail=f"機器群組 {group_id} 不存在")
    return group


@router.post("/machine-groups", response_model=MachineGroupResponse, status_code=201)
def create_machine_group(group: MachineGroupCreate, db: Session = Depends(get_db)):
    """建立機器群組"""
    existing = db.query(MachineGroup).filter(MachineGroup.GroupId == group.GroupId).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"機器群組 {group.GroupId} 已存在")
    
    db_group = MachineGroup(**group.model_dump())
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group


@router.put("/machine-groups/{group_id}", response_model=MachineGroupResponse)
def update_machine_group(group_id: str, group: MachineGroupUpdate, db: Session = Depends(get_db)):
    """更新機器群組"""
    db_group = db.query(MachineGroup).filter(MachineGroup.GroupId == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail=f"機器群組 {group_id} 不存在")
    
    update_data = group.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_group, field, value)
    
    db.commit()
    db.refresh(db_group)
    return db_group


@router.delete("/machine-groups/{group_id}", status_code=204)
def delete_machine_group(group_id: str, db: Session = Depends(get_db)):
    """刪除機器群組"""
    db_group = db.query(MachineGroup).filter(MachineGroup.GroupId == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail=f"機器群組 {group_id} 不存在")
    
    db.delete(db_group)
    db.commit()
    return None


# Machine 路由
@router.get("/machines", response_model=List[MachineResponse])
def get_machines(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    group_id: str = None,
    is_active: bool = None,
    db: Session = Depends(get_db)
):
    """取得所有機器 (支援依群組和啟用狀態篩選)"""
    query = db.query(Machine)
    
    if group_id:
        query = query.filter(Machine.GroupId == group_id)
    if is_active is not None:
        query = query.filter(Machine.is_active == is_active)
    
    machines = query.offset(skip).limit(limit).all()
    return machines


@router.get("/machines/{machine_id}", response_model=MachineResponse)
def get_machine(machine_id: str, db: Session = Depends(get_db)):
    """取得單一機器"""
    machine = db.query(Machine).filter(Machine.MachineId == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail=f"機器 {machine_id} 不存在")
    return machine


@router.post("/machines", response_model=MachineResponse, status_code=201)
def create_machine(machine: MachineCreate, db: Session = Depends(get_db)):
    """建立機器"""
    existing = db.query(Machine).filter(Machine.MachineId == machine.MachineId).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"機器 {machine.MachineId} 已存在")
    
    db_machine = Machine(**machine.model_dump())
    db.add(db_machine)
    db.commit()
    db.refresh(db_machine)
    return db_machine


@router.put("/machines/{machine_id}", response_model=MachineResponse)
def update_machine(machine_id: str, machine: MachineUpdate, db: Session = Depends(get_db)):
    """更新機器"""
    db_machine = db.query(Machine).filter(Machine.MachineId == machine_id).first()
    if not db_machine:
        raise HTTPException(status_code=404, detail=f"機器 {machine_id} 不存在")
    
    update_data = machine.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_machine, field, value)
    
    db.commit()
    db.refresh(db_machine)
    return db_machine


@router.delete("/machines/{machine_id}", status_code=204)
def delete_machine(machine_id: str, db: Session = Depends(get_db)):
    """刪除機器"""
    db_machine = db.query(Machine).filter(Machine.MachineId == machine_id).first()
    if not db_machine:
        raise HTTPException(status_code=404, detail=f"機器 {machine_id} 不存在")
    
    db.delete(db_machine)
    db.commit()
    return None
