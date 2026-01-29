"""
Lots Pydantic Schemas
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class LotBase(BaseModel):
    """工單基礎 Schema"""
    Priority: int
    DueDate: datetime
    ActualFinishDate: Optional[datetime] = None
    ProductID: Optional[str] = None
    ProductName: Optional[str] = None
    CustomerID: Optional[str] = None
    CustomerName: Optional[str] = None
    LotCreateDate: Optional[datetime] = None


class LotCreate(LotBase):
    """建立工單 Schema"""
    LotId: str


class LotUpdate(BaseModel):
    """更新工單 Schema"""
    Priority: Optional[int] = None
    DueDate: Optional[datetime] = None
    ActualFinishDate: Optional[datetime] = None
    ProductID: Optional[str] = None
    ProductName: Optional[str] = None
    CustomerID: Optional[str] = None
    CustomerName: Optional[str] = None
    LotCreateDate: Optional[datetime] = None


class LotResponse(LotBase):
    """工單回應 Schema"""
    LotId: str
    
    model_config = ConfigDict(from_attributes=True)
