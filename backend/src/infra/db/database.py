"""
資料庫連線模組
建立 SQLAlchemy Engine 和 Session
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from core.config import settings


# 建立資料庫引擎
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # 連線前檢查
    pool_recycle=3600,   # 每小時回收連線
    echo=False,          # 不顯示 SQL 語句
)

# 建立 Session 工廠
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 建立 Base 類別
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    取得資料庫 Session (依賴注入用)
    
    Yields:
        Session: 資料庫 Session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
