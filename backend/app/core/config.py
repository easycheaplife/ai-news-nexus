import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI News Nexus"
    API_V1_STR: str = "/api/v1"
    
    # Database
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: str = os.getenv("MYSQL_PORT", "3306")
    MYSQL_DB: str = os.getenv("MYSQL_DB", "ai_news")
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if not self.MYSQL_PASSWORD and os.getenv("ENV") != "production":
            return "sqlite:///./ai_news.db"
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4"

    class Config:
        case_sensitive = True

settings = Settings()
