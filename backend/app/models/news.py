from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, UniqueConstraint
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
    url = Column(String(768), unique=True, index=True)
    published_at = Column(DateTime, index=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(JSON)

    __table_args__ = (
        UniqueConstraint('platform', 'external_id', name='_platform_external_id_uc'),
    )
