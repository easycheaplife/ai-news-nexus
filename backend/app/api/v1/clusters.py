from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
import uuid

from app.db.session import get_db
from app.models.news import TopicCluster, ClusterNewsMapping, NewsItem
from app.schemas.cluster import TopicCluster as TopicClusterSchema, ClusterBatchCreate

router = APIRouter()

@router.get("/trending", response_model=List[TopicClusterSchema])
def get_trending_clusters(limit: int = 10, db: Session = Depends(get_db)):
    """
    Get top trending topic clusters.
    """
    clusters = db.query(TopicCluster).order_by(desc(TopicCluster.resonance_score), desc(TopicCluster.created_at)).limit(limit).all()
    
    # Pre-fetch news mapping manually or just rely on relationship if it was defined.
    # We didn't define relationship in SQLAlchemy model, so we attach manually for schema
    result = []
    for c in clusters:
        mappings = db.query(ClusterNewsMapping).filter(ClusterNewsMapping.cluster_id == c.id).all()
        # Fetch news items
        for m in mappings:
            m.news = db.query(NewsItem).filter(NewsItem.id == m.news_id).first()
        c.news_items = mappings
        result.append(c)
        
    return result

@router.get("/{cluster_id}", response_model=TopicClusterSchema)
def get_cluster(cluster_id: str, db: Session = Depends(get_db)):
    """
    Get specific cluster by ID.
    """
    c = db.query(TopicCluster).filter(TopicCluster.id == cluster_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cluster not found")
        
    mappings = db.query(ClusterNewsMapping).filter(ClusterNewsMapping.cluster_id == c.id).all()
    for m in mappings:
        m.news = db.query(NewsItem).filter(NewsItem.id == m.news_id).first()
    c.news_items = mappings
    return c

@router.post("/batch")
def create_clusters_batch(batch: ClusterBatchCreate, db: Session = Depends(get_db)):
    """
    Create a batch of clusters from AI clustering engine.
    """
    created_clusters = []
    for item in batch.clusters:
        # Check if we have any valid news_ids
        if not item.news_ids:
            continue
            
        cluster_id = str(uuid.uuid4())
        
        # Calculate resonance score based on number of platforms and items
        # Just simple heuristics: 10 points per item
        score = len(item.news_ids) * 10
        
        new_cluster = TopicCluster(
            id=cluster_id,
            title=item.title,
            summary=item.summary,
            resonance_score=score
        )
        db.add(new_cluster)
        
        # We need to map them
        for n_id in item.news_ids:
            # check if news exists
            news = db.query(NewsItem).filter(NewsItem.id == n_id).first()
            if news:
                platform_role = news.platform
                mapping = ClusterNewsMapping(
                    cluster_id=cluster_id,
                    news_id=n_id,
                    platform_role=platform_role
                )
                db.add(mapping)
                # optionally update the news item's cluster_id legacy field
                news.cluster_id = cluster_id
                
        created_clusters.append(new_cluster)
        
    db.commit()
    return {"message": f"Successfully created {len(created_clusters)} clusters."}
