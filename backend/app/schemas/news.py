from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class NewsItemBase(BaseModel):
    platform: str
    external_id: str
    title: str
    content: Optional[str] = None
    url: str
    published_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None

class NewsItemCreate(NewsItemBase):
    pass

class NewsItem(NewsItemBase):
    id: int
    scraped_at: datetime

    class Config:
        from_attributes = True
