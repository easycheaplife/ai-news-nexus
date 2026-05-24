import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI News Nexus"
    API_V1_STR: str = "/api/v1"
    
    # App Startup
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    
    # Database
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: str = "3306"
    MYSQL_DB: str = "ai_news"
    ENV: str = "development"
    MIN_SCORE: int = 60
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        # 强制使用 MySQL (云端生产环境)
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4"

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }

settings = Settings()
