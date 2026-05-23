from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, UniqueConstraint, Date, Enum, Boolean, ForeignKey
import enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class NewsItem(Base):
    __tablename__ = "news_items"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), index=True)
    external_id = Column(String(255), index=True)
    title = Column(String(500))
    content = Column(Text)
    url = Column(String(768), index=True)
    published_at = Column(DateTime, index=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(JSON)
    score = Column(Integer, default=0)
    reason = Column(Text)
    media_urls = Column(JSON)
    takeaways = Column(JSON)
    cluster_id = Column(String(100), index=True)
    mentioned_users = Column(JSON)
    trending_keywords = Column(JSON)

    __table_args__ = (
        UniqueConstraint('platform', 'external_id', name='_platform_external_id_uc'),
    )

class DailyInsight(Base):
    __tablename__ = "daily_insights"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True, nullable=False)
    content = Column(Text, nullable=False)
    hot_topics = Column(JSON)
    stats_json = Column(JSON)
    report_url = Column(String(500)) # 新增：指向生成的日报图片 URL
    created_at = Column(DateTime, default=datetime.utcnow)

class DiscoveryType(enum.Enum):
    user = "user"
    keyword = "keyword"

class DiscoveryStatus(enum.Enum):
    pending = "pending"
    vetted = "vetted"
    rejected = "rejected"

class DiscoveryPool(Base):
    __tablename__ = "discovery_pool"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(DiscoveryType), nullable=False)
    value = Column(String(255), nullable=False)
    status = Column(Enum(DiscoveryStatus), default=DiscoveryStatus.pending, index=True)
    source_id = Column(Integer)
    discovery_reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('type', 'value', name='_type_value_uc'),
    )

class TargetStatus(enum.Enum):
    active = "active"
    probation = "probation"
    deactivated = "deactivated"
    blacklisted = "blacklisted"

class ScrapingTarget(Base):
    __tablename__ = "scraping_targets"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), nullable=False)
    handle = Column(String(255), nullable=False)
    name = Column(String(255))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # 质量评价维度
    avg_score = Column(Integer, default=50)
    total_posts = Column(Integer, default=0)
    high_value_posts = Column(Integer, default=0) # 评分 > 80 的数量
    status = Column(Enum(TargetStatus), default=TargetStatus.active)
    last_scraped_at = Column(DateTime)
    last_high_score_at = Column(DateTime)
    failure_count = Column(Integer, default=0) # 连续低分或抓取失败计数

    __table_args__ = (
        UniqueConstraint('platform', 'handle', name='_platform_handle_uc'),
    )

class TopicCluster(Base):
    __tablename__ = "topic_clusters"

    id = Column(String(36), primary_key=True, index=True) # UUID string
    title = Column(String(500), nullable=False)
    summary = Column(Text)
    resonance_score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class ClusterNewsMapping(Base):
    __tablename__ = "cluster_news_mapping"

    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(String(36), ForeignKey('topic_clusters.id', ondelete="CASCADE"), index=True, nullable=False)
    news_id = Column(Integer, ForeignKey('news_items.id', ondelete="CASCADE"), index=True, nullable=False)
    platform_role = Column(String(50)) # e.g., 'origin_repo', 'paper', 'discussion'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('cluster_id', 'news_id', name='_cluster_news_uc'),
    )
