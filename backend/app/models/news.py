from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, UniqueConstraint, Date
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
    created_at = Column(DateTime, default=datetime.utcnow)
