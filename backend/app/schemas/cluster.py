from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .news import NewsItem

class ClusterNewsMappingBase(BaseModel):
    news_id: int
    platform_role: Optional[str] = None

class ClusterNewsMappingCreate(ClusterNewsMappingBase):
    pass

class ClusterNewsMapping(ClusterNewsMappingBase):
    id: int
    cluster_id: str
    created_at: datetime
    news: Optional[NewsItem] = None

    class Config:
        from_attributes = True

class TopicClusterBase(BaseModel):
    title: str
    summary: Optional[str] = None
    resonance_score: Optional[int] = 0

class TopicClusterCreate(TopicClusterBase):
    pass

class TopicCluster(TopicClusterBase):
    id: str
    created_at: datetime
    news_items: List[ClusterNewsMapping] = []
    first_mover_news_id: Optional[int] = None
    first_mover_tier: Optional[str] = None
    first_mover_news: Optional[NewsItem] = None

    class Config:
        from_attributes = True

class ClusterBatchItem(BaseModel):
    title: str
    summary: Optional[str] = None
    news_ids: List[int]

class ClusterBatchCreate(BaseModel):
    clusters: List[ClusterBatchItem]
