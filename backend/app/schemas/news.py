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
    report_url: Optional[str] = None

class DailyInsightCreate(DailyInsightBase):
    pass

class DailyInsightUpdate(BaseModel):
    content: Optional[str] = None
    hot_topics: Optional[List[str]] = None
    stats_json: Optional[Dict[str, Any]] = None
    report_url: Optional[str] = None

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

class DiscoveryPoolUpdate(BaseModel):
    status: Optional[DiscoveryStatus] = None
    discovery_reason: Optional[str] = None

class DiscoveryPool(DiscoveryPoolBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class TargetStatus(str, Enum):
    active = "active"
    probation = "probation"
    deactivated = "deactivated"
    blacklisted = "blacklisted"

class ScrapingTargetBase(BaseModel):
    platform: str
    handle: str
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    status: TargetStatus = TargetStatus.active

class ScrapingTargetCreate(ScrapingTargetBase):
    pass

class ScrapingTargetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    status: Optional[TargetStatus] = None
    avg_score: Optional[int] = None
    total_posts: Optional[int] = None
    high_value_posts: Optional[int] = None
    failure_count: Optional[int] = None
    last_scraped_at: Optional[datetime] = None
    last_high_score_at: Optional[datetime] = None

class ScrapingTarget(ScrapingTargetBase):
    id: int
    added_at: datetime
    avg_score: int
    total_posts: int
    high_value_posts: int
    failure_count: int
    last_scraped_at: Optional[datetime] = None
    last_high_score_at: Optional[datetime] = None

    class Config:
        from_attributes = True
