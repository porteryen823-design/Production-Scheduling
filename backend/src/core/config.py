"""
核心配置模組
使用 Pydantic Settings 管理環境變數
"""
from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    """應用程式設定"""
    
    # 資料庫配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "1234"
    DB_NAME: str = "Scheduling"
    
    # API 配置
    API_TITLE: str = "生產排程系統 API"
    API_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    
    # CORS 配置
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5500,http://localhost:5500,http://localhost:8080"
    
    class Config:
        # 使用絕對路徑定位 .env 檔案（backend/.env）
        env_file = Path(__file__).parent.parent.parent / ".env"
        case_sensitive = True
    
    @property
    def database_url(self) -> str:
        """取得資料庫連線 URL"""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """取得 CORS 來源清單"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# 建立全域設定實例
settings = Settings()
