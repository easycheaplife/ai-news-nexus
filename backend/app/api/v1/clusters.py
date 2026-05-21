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
    created_clusters_count = 0
    try:
        for item in batch.clusters:
            # 1. Deduplicate news_ids and check if we have any valid IDs
            # AI sometimes repeats IDs in the list
            unique_news_ids = list(set(item.news_ids))
            if not unique_news_ids:
                continue
                
            cluster_id = str(uuid.uuid4())
            
            # 2. Heuristic resonance score: base 20 + 10 points per item
            score = 10 + (len(unique_news_ids) * 10)
            
            new_cluster = TopicCluster(
                id=cluster_id,
                title=item.title,
                summary=item.summary,
                resonance_score=score
            )
            db.add(new_cluster)
            # Flush to ensure the cluster exists for FK constraints
            db.flush()
            
            # 3. Create mappings
            actual_mapped_count = 0
            for n_id in unique_news_ids:
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
                    # update the news item's cluster_id legacy field
                    news.cluster_id = cluster_id
                    actual_mapped_count += 1
            
            # 4. Only count as created if we actually mapped at least 2 items (true resonance)
            if actual_mapped_count >= 2:
                created_clusters_count += 1
            else:
                # If only 1 or 0 items were actually valid, the AI made a mistake or news were deleted.
                # We could roll back this specific cluster or just keep it. 
                # For now, let's keep it but skip the count.
                pass
                    
        db.commit()
        return {"message": f"Successfully created {created_clusters_count} clusters."}
    except Exception as e:
        db.rollback()
        import logging
        logging.error(f"Error creating cluster batch: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
