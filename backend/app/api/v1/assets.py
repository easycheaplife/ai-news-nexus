from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from app.db.session import get_db
from app.models.news import KnowledgeTerm, PeriodicReport
from app.schemas.assets import (
    KnowledgeTerm as KnowledgeSchema, 
    KnowledgeTermCreate, 
    KnowledgeTermUpdate,
    PeriodicReport as ReportSchema,
    PeriodicReportCreate
)
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache

router = APIRouter()

async def clear_assets_cache():
    """清除资产相关的缓存"""
    try:
        await FastAPICache.clear(namespace="assets")
    except Exception:
        pass

# --- Knowledge Terms ---

@router.get("/terms", response_model=List[KnowledgeSchema])
@cache(expire=600, namespace="assets")
async def list_knowledge_terms(request: Request, category: Optional[str] = None, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(KnowledgeTerm)
    if category:
        query = query.filter(KnowledgeTerm.category == category)
    return query.order_by(KnowledgeTerm.heat_score.desc()).limit(limit).all()

@router.post("/terms", response_model=KnowledgeSchema)
async def create_knowledge_term(term: KnowledgeTermCreate, db: Session = Depends(get_db)):
    await clear_assets_cache()
    db_term = db.query(KnowledgeTerm).filter(KnowledgeTerm.keyword == term.keyword).first()
    if db_term:
        return db_term
    
    try:
        new_term = KnowledgeTerm(**term.dict())
        db.add(new_term)
        db.commit()
        db.refresh(new_term)
        return new_term
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/terms/{term_id}", response_model=KnowledgeSchema)
async def update_knowledge_term(term_id: int, term_update: KnowledgeTermUpdate, db: Session = Depends(get_db)):
    await clear_assets_cache()
    db_term = db.query(KnowledgeTerm).filter(KnowledgeTerm.id == term_id).first()
    if not db_term:
        raise HTTPException(status_code=404, detail="Term not found")
    
    for key, value in term_update.dict(exclude_unset=True).items():
        setattr(db_term, key, value)
    
    db.commit()
    db.refresh(db_term)
    return db_term

# --- Periodic Reports ---

@router.get("/reports", response_model=List[ReportSchema])
@cache(expire=1800, namespace="assets")
async def list_periodic_reports(request: Request, limit: int = 20, db: Session = Depends(get_db)):
    return db.query(PeriodicReport).order_by(PeriodicReport.end_date.desc()).limit(limit).all()

@router.post("/reports", response_model=ReportSchema)
async def create_periodic_report(report: PeriodicReportCreate, db: Session = Depends(get_db)):
    await clear_assets_cache()
    try:
        new_report = PeriodicReport(**report.dict())
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
        return new_report
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
