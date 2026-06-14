from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date

class KnowledgeTermBase(BaseModel):
    keyword: str
    category: Optional[str] = "general"
    description: Optional[str] = None
    heat_score: Optional[int] = 1
    trend_json: Optional[Dict[str, Any]] = None
    related_news_ids: Optional[List[int]] = []

class KnowledgeTermCreate(KnowledgeTermBase):
    pass

class KnowledgeTermUpdate(BaseModel):
    category: Optional[str] = None
    description: Optional[str] = None
    heat_score: Optional[int] = None
    trend_json: Optional[Dict[str, Any]] = None
    related_news_ids: Optional[List[int]] = None

class KnowledgeTerm(KnowledgeTermBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PeriodicReportBase(BaseModel):
    title: str
    content: str
    start_date: date
    end_date: date
    stats_json: Optional[Dict[str, Any]] = None

class PeriodicReportCreate(PeriodicReportBase):
    pass

class PeriodicReport(PeriodicReportBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
