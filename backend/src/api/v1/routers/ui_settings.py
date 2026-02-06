"""
UI Settings API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from infra.db.database import get_db
from domain.models import UISetting
from api.v1.schemas.ui_settings import UISetting as UISettingSchema, UISettingCreate, UISettingUpdate

router = APIRouter(tags=["UI Settings"])

@router.get("/ui-settings", response_model=List[UISettingSchema])
def get_ui_settings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    parameter_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """取得所有 UI 設定 (支援按名稱篩選)"""
    query = db.query(UISetting)
    if parameter_name:
        query = query.filter(UISetting.parameter_name.ilike(f"%{parameter_name}%"))
    return query.offset(skip).limit(limit).all()

@router.get("/ui-settings/{parameter_name}", response_model=UISettingSchema)
def get_ui_setting_by_name(parameter_name: str, db: Session = Depends(get_db)):
    """依名稱取得單一 UI 設定"""
    setting = db.query(UISetting).filter(UISetting.parameter_name == parameter_name).first()
    if not setting:
        raise HTTPException(status_code=404, detail=f"設定 {parameter_name} 不存在")
    return setting

@router.post("/ui-settings", response_model=UISettingSchema, status_code=201)
def create_ui_setting(setting: UISettingCreate, db: Session = Depends(get_db)):
    """建立 UI 設定"""
    existing = db.query(UISetting).filter(UISetting.parameter_name == setting.parameter_name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"設定 {setting.parameter_name} 已存在")
    
    db_setting = UISetting(**setting.model_dump())
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting

@router.put("/ui-settings/{parameter_name}", response_model=UISettingSchema)
def update_ui_setting(parameter_name: str, setting_update: UISettingUpdate, db: Session = Depends(get_db)):
    """更新 UI 設定 (依名稱)"""
    db_setting = db.query(UISetting).filter(UISetting.parameter_name == parameter_name).first()
    if not db_setting:
        # 如果不存在，也可以考慮自動建立 (Upsert)
        raise HTTPException(status_code=404, detail=f"設定 {parameter_name} 不存在")
    
    update_data = setting_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_setting, field, value)
    
    db.commit()
    db.refresh(db_setting)
    return db_setting

@router.delete("/ui-settings/{parameter_name}", status_code=204)
def delete_ui_setting(parameter_name: str, db: Session = Depends(get_db)):
    """刪除 UI 設定"""
    db_setting = db.query(UISetting).filter(UISetting.parameter_name == parameter_name).first()
    if not db_setting:
        raise HTTPException(status_code=404, detail=f"設定 {parameter_name} 不存在")
    
    db.delete(db_setting)
    db.commit()
    return None

@router.post("/ui-settings/upsert", response_model=UISettingSchema)
def upsert_ui_setting(setting: UISettingCreate, db: Session = Depends(get_db)):
    """新增或更新 UI 設定"""
    db_setting = db.query(UISetting).filter(UISetting.parameter_name == setting.parameter_name).first()
    
    if db_setting:
        update_data = setting.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_setting, field, value)
    else:
        db_setting = UISetting(**setting.model_dump())
        db.add(db_setting)
    
    db.commit()
    db.refresh(db_setting)
    return db_setting
