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
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "1234"
    MYSQL_DATABASE: str = "Scheduling"
    
    @property
    def DB_HOST(self) -> str: return self.MYSQL_HOST
    @property
    def DB_PORT(self) -> int: return self.MYSQL_PORT
    @property
    def DB_USER(self) -> str: return self.MYSQL_USER
    @property
    def DB_PASSWORD(self) -> str: return self.MYSQL_PASSWORD
    @property
    def DB_NAME(self) -> str: return self.MYSQL_DATABASE
    
    # API 配置
    API_TITLE: str = "生產排程系統 API"
    API_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    
    # CORS 配置
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5500,http://localhost:5500,http://127.0.0.1:5501,http://localhost:5501,http://localhost:8080"
    
    class Config:
        # 使用絕對路徑定位 .env 檔案（專案根目錄）
        env_file = Path(__file__).parent.parent.parent.parent / ".env"
        case_sensitive = True
        extra = "ignore"
    
    @property
    def database_url(self) -> str:
        """取得資料庫連線 URL"""
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """取得 CORS 來源清單"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# 建立全域設定實例
settings = Settings()
