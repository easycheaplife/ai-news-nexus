from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.db.session import get_db
from app.models.news import DailyInsight
from app.schemas.news import DailyInsight as InsightSchema, DailyInsightCreate, DailyInsightUpdate
from fastapi_cache.decorator import cache

router = APIRouter()

@router.post("/", response_model=InsightSchema)
def create_daily_insight(insight: DailyInsightCreate, db: Session = Depends(get_db)):
    # 检查是否已存在该日期的简报
    db_insight = db.query(DailyInsight).filter(DailyInsight.date == insight.date).first()
    
    if db_insight:
        # 如果存在，则更新内容
        db_insight.content = insight.content
        db_insight.hot_topics = insight.hot_topics
        db_insight.stats_json = insight.stats_json
        if insight.report_url:
            db_insight.report_url = insight.report_url
        db.commit()
        db.refresh(db_insight)
        return db_insight

    try:
        new_insight = DailyInsight(**insight.dict())
        db.add(new_insight)
        db.commit()
        db.refresh(new_insight)
        return new_insight
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{insight_date}", response_model=InsightSchema)
def update_daily_insight(insight_date: date, insight: DailyInsightUpdate, db: Session = Depends(get_db)):
    db_insight = db.query(DailyInsight).filter(DailyInsight.date == insight_date).first()
    if not db_insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    
    update_data = insight.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_insight, key, value)
    
    db.commit()
    db.refresh(db_insight)
    return db_insight

@router.get("/", response_model=List[InsightSchema])
@cache(expire=600)
def list_insights(limit: int = 100, db: Session = Depends(get_db)):
    return db.query(DailyInsight).order_by(DailyInsight.date.desc()).limit(limit).all()

@router.get("/latest", response_model=Optional[InsightSchema])
@cache(expire=600)
def get_latest_insight(db: Session = Depends(get_db)):
    return db.query(DailyInsight).order_by(DailyInsight.date.desc()).first()

@router.get("/{target_date}", response_model=InsightSchema)
@cache(expire=600)
def get_insight_by_date(target_date: date, db: Session = Depends(get_db)):
    db_insight = db.query(DailyInsight).filter(DailyInsight.date == target_date).first()
    if not db_insight:
        raise HTTPException(status_code=404, detail="No insight found for this date")
    return db_insight
