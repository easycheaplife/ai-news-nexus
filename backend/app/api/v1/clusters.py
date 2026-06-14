from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
import uuid
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.news import TopicCluster, ClusterNewsMapping, NewsItem, ScrapingTarget
from app.schemas.cluster import TopicCluster as TopicClusterSchema, ClusterBatchCreate
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache
from sqlalchemy import func

router = APIRouter()

async def clear_clusters_cache():
    """清除聚类相关的缓存"""
    try:
        await FastAPICache.clear(namespace="clusters")
    except Exception:
        pass

def resolve_first_mover(db: Session, news_ids: List[int]):
    """
    🎯 核心算法：识别并标记首发贡献者 (First Mover)
    采用权重加权逻辑：Tier S (15m), Tier A (5m), Tier B (Absolute)
    """
    if not news_ids:
        return None, None

    # 1. 获取所有资讯及其作者的分数
    news_items = db.query(NewsItem).filter(NewsItem.id.in_(news_ids)).all()
    if not news_items:
        return None, None

    # 预加载作者分数以减少查询
    enriched_items = []
    for item in news_items:
        author = item.metadata_json.get('author') if item.metadata_json else None
        avg_score = 50
        if author:
            target = db.query(ScrapingTarget).filter(
                ScrapingTarget.platform == item.platform,
                ScrapingTarget.handle == author
            ).first()
            if target:
                avg_score = target.avg_score or 50
        
        tier = 'B'
        if avg_score >= 90: tier = 'S'
        elif avg_score >= 80: tier = 'A'
        
        enriched_items.append({
            'item': item,
            'published_at': item.published_at,
            'tier': tier,
            'score': avg_score
        })

    # 2. 确定绝对首发基准
    enriched_items.sort(key=lambda x: x['published_at'])
    t_start = enriched_items[0]['published_at']

    # 3. 扫描 Tier S (15分钟宽限)
    s_candidates = [i for i in enriched_items if i['tier'] == 'S' and (i['published_at'] - t_start).total_seconds() <= 900]
    if s_candidates:
        s_candidates.sort(key=lambda x: x['published_at'])
        return s_candidates[0]['item'].id, 'S'

    # 4. 扫描 Tier A (5分钟宽限)
    a_candidates = [i for i in enriched_items if i['tier'] == 'A' and (i['published_at'] - t_start).total_seconds() <= 300]
    if a_candidates:
        a_candidates.sort(key=lambda x: x['published_at'])
        return a_candidates[0]['item'].id, 'A'

    # 5. 返回绝对首发
    return enriched_items[0]['item'].id, enriched_items[0]['tier']

@router.get("/trending", response_model=List[TopicClusterSchema])
@cache(expire=300, namespace="clusters")
async def get_trending_clusters(request: Request, limit: int = 10, db: Session = Depends(get_db)):
    """
    Get top trending topic clusters from the last 48 hours.
    """
    time_window = datetime.now() - timedelta(hours=48)
    
    clusters = db.query(TopicCluster)\
        .filter(TopicCluster.created_at >= time_window)\
        .order_by(desc(TopicCluster.resonance_score), desc(TopicCluster.created_at))\
        .limit(limit).all()
    
    result = []
    for c in clusters:
        mappings = db.query(ClusterNewsMapping).filter(ClusterNewsMapping.cluster_id == c.id).all()
        for m in mappings:
            m.news = db.query(NewsItem).filter(NewsItem.id == m.news_id).first()
        c.news_items = mappings
        
        # 附加 First Mover 详情
        if c.first_mover_news_id:
            c.first_mover_news = db.query(NewsItem).filter(NewsItem.id == c.first_mover_news_id).first()
            
        result.append(c)
        
    return result

@router.get("/{cluster_id}", response_model=TopicClusterSchema)
@cache(expire=600, namespace="clusters")
async def get_cluster(request: Request, cluster_id: str, db: Session = Depends(get_db)):
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

    if c.first_mover_news_id:
        c.first_mover_news = db.query(NewsItem).filter(NewsItem.id == c.first_mover_news_id).first()
        
    return c

@router.post("/batch")
async def create_clusters_batch(batch: ClusterBatchCreate, db: Session = Depends(get_db)):
    """
    Create a batch of clusters from AI clustering engine.
    """
    await clear_clusters_cache()
    
    created_clusters_count = 0
    try:
        for item in batch.clusters:
            unique_news_ids = list(set(item.news_ids))
            if not unique_news_ids:
                continue
                
            cluster_id = str(uuid.uuid4())
            
            # 🚀 计算 First Mover
            fm_id, fm_tier = resolve_first_mover(db, unique_news_ids)
            
            score = 10 + (len(unique_news_ids) * 10)
            
            new_cluster = TopicCluster(
                id=cluster_id,
                title=item.title,
                summary=item.summary,
                resonance_score=score,
                first_mover_news_id=fm_id,
                first_mover_tier=fm_tier
            )
            db.add(new_cluster)
            db.flush()
            
            # 3. Create mappings
            actual_mapped_count = 0
            for n_id in unique_news_ids:
                news = db.query(NewsItem).filter(NewsItem.id == n_id).first()
                if news:
                    mapping = ClusterNewsMapping(
                        cluster_id=cluster_id,
                        news_id=n_id,
                        platform_role=news.platform
                    )
                    db.add(mapping)
                    news.cluster_id = cluster_id
                    actual_mapped_count += 1
            
            if actual_mapped_count >= 2:
                created_clusters_count += 1
                    
        db.commit()
        return {"message": f"Successfully created {created_clusters_count} clusters."}
    except Exception as e:
        db.rollback()
        import logging
        logging.error(f"Error creating cluster batch: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
