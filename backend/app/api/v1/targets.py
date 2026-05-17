from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.news import ScrapingTarget
from app.schemas.news import ScrapingTargetCreate, ScrapingTarget as TargetSchema
from typing import List

router = APIRouter()

@router.post("/", response_model=TargetSchema)
def create_scraping_target(target: ScrapingTargetCreate, db: Session = Depends(get_db)):
    db_target = db.query(ScrapingTarget).filter(
        ScrapingTarget.platform == target.platform,
        ScrapingTarget.handle == target.handle
    ).first()
    if db_target:
        return db_target
    
    try:
        new_target = ScrapingTarget(**target.dict())
        db.add(new_target)
        db.commit()
        db.refresh(new_target)
        return new_target
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[TargetSchema])
def list_scraping_targets(platform: str = None, is_active: bool = True, db: Session = Depends(get_db)):
    query = db.query(ScrapingTarget).filter(ScrapingTarget.is_active == is_active)
    if platform:
        query = query.filter(ScrapingTarget.platform == platform)
    return query.all()
