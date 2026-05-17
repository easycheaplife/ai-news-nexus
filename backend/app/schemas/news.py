from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from enum import Enum

class NewsItemBase(BaseModel):
    platform: str
    external_id: str
    title: str
    content: Optional[str] = None
    url: str
    published_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None
    score: Optional[int] = 0
    reason: Optional[str] = None
    media_urls: Optional[List[str]] = None
    takeaways: Optional[List[str]] = None
    cluster_id: Optional[str] = None
    mentioned_users: Optional[List[str]] = None
    trending_keywords: Optional[List[str]] = None

class NewsItemCreate(NewsItemBase):
    pass

class NewsItem(NewsItemBase):
    id: int
    scraped_at: datetime

    class Config:
        from_attributes = True

class DailyInsightBase(BaseModel):
    date: date
    content: str
    hot_topics: Optional[List[str]] = None
    stats_json: Optional[Dict[str, Any]] = None

class DailyInsightCreate(DailyInsightBase):
    pass

class DailyInsight(DailyInsightBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class DiscoveryType(str, Enum):
    user = "user"
    keyword = "keyword"

class DiscoveryStatus(str, Enum):
    pending = "pending"
    vetted = "vetted"
    rejected = "rejected"

class DiscoveryPoolBase(BaseModel):
    type: DiscoveryType
    value: str
    status: DiscoveryStatus = DiscoveryStatus.pending
    source_id: Optional[int] = None
    discovery_reason: Optional[str] = None

class DiscoveryPoolCreate(DiscoveryPoolBase):
    pass

class DiscoveryPool(DiscoveryPoolBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ScrapingTargetBase(BaseModel):
    platform: str
    handle: str
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True

class ScrapingTargetCreate(ScrapingTargetBase):
    pass

class ScrapingTarget(ScrapingTargetBase):
    id: int
    added_at: datetime

    class Config:
        from_attributes = True
