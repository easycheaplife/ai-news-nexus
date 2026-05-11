from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.db.session import get_db
from app.models.news import NewsItem
from app.schemas.news import NewsItem as NewsSchema, NewsItemCreate

router = APIRouter()

@router.post("/", response_model=NewsSchema)
def create_news_item(item: NewsItemCreate, db: Session = Depends(get_db)):
    db_item = db.query(NewsItem).filter(
        NewsItem.platform == item.platform,
        NewsItem.external_id == item.external_id
    ).first()
    
    if db_item:
        return db_item
        
    db_item_url = db.query(NewsItem).filter(NewsItem.url == item.url).first()
    if db_item_url:
        return db_item_url

    new_item = NewsItem(**item.dict())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@router.get("/", response_model=List[NewsSchema])
def read_news(
    platform: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    query: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    db_query = db.query(NewsItem)
    
    if platform:
        db_query = db_query.filter(NewsItem.platform == platform)
    if start_date:
        db_query = db_query.filter(NewsItem.published_at >= start_date)
    if end_date:
        db_query = db_query.filter(NewsItem.published_at <= end_date)
    if query:
        db_query = db_query.filter(
            (NewsItem.title.ilike(f"%{query}%")) | 
            (NewsItem.content.ilike(f"%{query}%"))
        )
    
    return db_query.order_by(NewsItem.published_at.desc()).offset(skip).limit(limit).all()
