from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.news import DiscoveryPool, DiscoveryStatus
from app.schemas.news import DiscoveryPoolCreate, DiscoveryPool as DiscoverySchema

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

@router.get("/", response_model=list[DiscoverySchema])
def list_discovery_pool(status: DiscoveryStatus = DiscoveryStatus.pending, db: Session = Depends(get_db)):
    return db.query(DiscoveryPool).filter(DiscoveryPool.status == status).all()
