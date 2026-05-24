from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.news import DiscoveryPool, DiscoveryStatus
from app.schemas.news import DiscoveryPoolCreate, DiscoveryPool as DiscoverySchema, DiscoveryPoolUpdate
from typing import List, Optional

router = APIRouter()

@router.post("/", response_model=DiscoverySchema)
def add_to_discovery_pool(item: DiscoveryPoolCreate, db: Session = Depends(get_db)):
    # 检查是否已存在
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
def list_discovery_pool(status: Optional[DiscoveryStatus] = None, db: Session = Depends(get_db)):
    query = db.query(DiscoveryPool)
    if status:
        query = query.filter(DiscoveryPool.status == status)
    return query.order_by(DiscoveryPool.created_at.desc()).all()

@router.patch("/{item_id}", response_model=DiscoverySchema)
def update_discovery_item(item_id: int, item_update: DiscoveryPoolUpdate, db: Session = Depends(get_db)):
    db_item = db.query(DiscoveryPool).filter(DiscoveryPool.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Discovery item not found")
    
    update_data = item_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
    
    try:
        db.commit()
        db.refresh(db_item)
        return db_item
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
