from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.news import DiscoveryPool, DiscoveryStatus
from app.schemas.news import DiscoveryPoolCreate, DiscoveryPool as DiscoverySchema, DiscoveryPoolUpdate
from typing import List, Optional
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache

router = APIRouter()

async def clear_discovery_cache():
    """清除发现池相关的缓存"""
    try:
        await FastAPICache.clear(namespace="discovery")
    except Exception:
        pass

@router.post("/", response_model=DiscoverySchema)
async def create_discovery_item(item: DiscoveryPoolCreate, db: Session = Depends(get_db)):
    # 🚀 强制清除缓存
    await clear_discovery_cache()
    # 检查是否已存在 (根据类型和值)
    db_item = db.query(DiscoveryPool).filter(
        DiscoveryPool.type == item.type,
        DiscoveryPool.value == item.value
    ).first()
    
    if db_item:
        return db_item
        
    try:
        new_item = DiscoveryPool(**item.dict())
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        return new_item
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[DiscoverySchema])
@cache(expire=600, namespace="discovery")
def list_discovery_pool(request: Request, status: Optional[DiscoveryStatus] = None, db: Session = Depends(get_db)):
    query = db.query(DiscoveryPool)
    if status:
        query = query.filter(DiscoveryPool.status == status)
    return query.order_by(DiscoveryPool.created_at.desc()).all()

@router.patch("/{item_id}", response_model=DiscoverySchema)
async def update_discovery_item(item_id: int, item_update: DiscoveryPoolUpdate, db: Session = Depends(get_db)):
    # 🚀 强制清除缓存
    await clear_discovery_cache()
    db_item = db.query(DiscoveryPool).filter(DiscoveryPool.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    for key, value in item_update.dict(exclude_unset=True).items():
        setattr(db_item, key, value)
    
    try:
        db.commit()
        db.refresh(db_item)
        return db_item
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
