from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.news import ScrapingTarget
from app.schemas.news import ScrapingTargetCreate, ScrapingTarget as TargetSchema, ScrapingTargetUpdate
from typing import List, Optional
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache

router = APIRouter()

async def clear_targets_cache():
    """清除采集目标相关的缓存"""
    try:
        await FastAPICache.clear(namespace="targets")
    except Exception:
        pass

@router.post("/", response_model=TargetSchema)
async def create_scraping_target(target: ScrapingTargetCreate, db: Session = Depends(get_db)):
    # 🚀 强制清除缓存
    await clear_targets_cache()
    target.handle = target.handle.strip()
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
@cache(expire=600, namespace="targets")
def list_scraping_targets(
    request: Request,
    platform: Optional[str] = None, 
    handle: Optional[str] = None,
    is_active: Optional[bool] = None, 
    status: Optional[str] = None, 
    has_scraped_data: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(ScrapingTarget)
    if is_active is not None:
        query = query.filter(ScrapingTarget.is_active == is_active)
    if status:
        query = query.filter(ScrapingTarget.status == status)
    if platform:
        query = query.filter(ScrapingTarget.platform == platform)
    if handle:
        query = query.filter(ScrapingTarget.handle == handle)
    if has_scraped_data is True:
        query = query.filter(ScrapingTarget.last_scraped_at.isnot(None))
    elif has_scraped_data is False:
        query = query.filter(ScrapingTarget.last_scraped_at.is_(None))
    return query.all()

@router.patch("/{target_id}", response_model=TargetSchema)
async def update_scraping_target(target_id: int, target_update: ScrapingTargetUpdate, db: Session = Depends(get_db)):
    # 🚀 强制清除缓存
    await clear_targets_cache()
    db_target = db.query(ScrapingTarget).filter(ScrapingTarget.id == target_id).first()
    if not db_target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    update_data = target_update.dict(exclude_unset=True)
    if "handle" in update_data:
        update_data["handle"] = update_data["handle"].strip()
        
    for key, value in update_data.items():
        setattr(db_target, key, value)
    
    try:
        db.commit()
        db.refresh(db_target)
        return db_target
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{target_id}")
async def delete_scraping_target(target_id: int, db: Session = Depends(get_db)):
    # 🚀 强制清除缓存
    await clear_targets_cache()
    db_target = db.query(ScrapingTarget).filter(ScrapingTarget.id == target_id).first()
    if not db_target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    try:
        db.delete(db_target)
        db.commit()
        return {"message": "Target deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
