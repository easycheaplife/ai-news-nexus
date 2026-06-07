from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, String
from typing import List, Optional
import json
from datetime import datetime
from app.db.session import get_db
from app.core.config import settings
from app.models.news import NewsItem
from app.schemas.news import NewsItem as NewsSchema, NewsItemCreate, NewsListResponse, NewsItemUpdate
from fastapi_cache.decorator import cache

router = APIRouter()

@router.post("/", response_model=NewsSchema)
def create_news_item(item: NewsItemCreate, db: Session = Depends(get_db)):
    # 1. 严格查重：平台 + 外部ID
    db_item = db.query(NewsItem).filter(
        NewsItem.platform == item.platform,
        NewsItem.external_id == item.external_id
    ).first()
    
    if db_item:
        # 如果已存在，直接返回
        return db_item
        
    # 2. 备选查重：URL (针对 github 等允许每日上榜的平台，放宽限制)
    if item.platform != 'github':
        db_item_url = db.query(NewsItem).filter(NewsItem.url == item.url).first()
        if db_item_url:
            return db_item_url

    # 3. 只有不存在时才执行插入
    try:
        new_item = NewsItem(**item.dict())
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        return new_item
    except Exception as e:
        db.rollback()
        # 处理可能的并发冲突
        existing = db.query(NewsItem).filter(NewsItem.url == item.url).first()
        if existing:
            return existing
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=NewsListResponse)
@cache(expire=300) # 缓存 5 分钟
async def read_news(
    request: Request,
    platform: Optional[str] = None,
    platforms: Optional[str] = Query(None, description="Comma-separated list of platforms"),
    author: Optional[str] = None,
    cluster_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    query: Optional[str] = None,
    min_score: int = Query(settings.MIN_SCORE, description="Minimum AI score to include"),
    include_pending: bool = Query(True, description="Whether to include items with score 0 (pending analysis)"),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    db_query = db.query(NewsItem)
    
    if platform:
        db_query = db_query.filter(NewsItem.platform == platform)
    elif platforms:
        p_list = [p.strip() for p in platforms.split(",") if p.strip()]
        if p_list:
            db_query = db_query.filter(NewsItem.platform.in_(p_list))
    
    if author:
        # 在 metadata_json JSON 字段中搜索作者名 (兼容 MySQL JSON 处理)
        db_query = db_query.filter(func.json_extract(NewsItem.metadata_json, "$.author") == author)

    if cluster_id:
        db_query = db_query.filter(NewsItem.cluster_id == cluster_id)

    if start_date:
        db_query = db_query.filter(NewsItem.published_at >= start_date)
    if end_date:
        db_query = db_query.filter(NewsItem.published_at <= end_date)
    
    # 评分过滤逻辑
    if include_pending:
        # 包含 0 分 (待处理) 或者 达到最小分数的内容
        db_query = db_query.filter((NewsItem.score >= min_score) | (NewsItem.score == 0))
    else:
        db_query = db_query.filter(NewsItem.score >= min_score)

    if query and query.strip():
        query = query.strip().lower()
        # If the user searches "@Handle", strip the "@" for the metadata search but keep it for title/content
        clean_query = query[1:] if query.startswith('@') and len(query) > 1 else query
        
        from sqlalchemy import or_, func
        db_query = db_query.filter(or_(
            func.lower(NewsItem.title).like(f"%{query}%"),
            (NewsItem.content.isnot(None)) & (func.lower(NewsItem.content).like(f"%{query}%")),
            (NewsItem.trending_keywords.isnot(None)) & (func.lower(cast(NewsItem.trending_keywords, String)).like(f"%{query}%")),
            (NewsItem.metadata_json.isnot(None)) & (func.lower(cast(NewsItem.metadata_json, String)).like(f"%{clean_query}%"))
        ))
    
    total_count = db_query.count()
    items = db_query.order_by(NewsItem.published_at.desc(), NewsItem.id.desc()).offset(skip).limit(limit).all()
    
    return {
        "items": items,
        "total": total_count
    }

@router.patch("/{item_id}", response_model=NewsSchema)
def update_news_item(item_id: int, item: NewsItemUpdate, db: Session = Depends(get_db)):
    db_item = db.query(NewsItem).filter(NewsItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="News item not found")
    
    update_data = item.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
    
    try:
        db.commit()
        db.refresh(db_item)
        return db_item
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
