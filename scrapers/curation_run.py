import logging
import requests
import os
from datetime import datetime
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("source_curator")

class SourceCurator:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url

    def run_curation(self):
        """执行信源汰换逻辑"""
        logger.info("🧹 Starting Source Curation phase...")
        
        try:
            # 1. 获取所有活跃的抓取目标
            response = requests.get(f"{self.api_url}/targets/", params={"is_active": True}, timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to fetch targets: {response.text}")
                return
            
            targets = response.json()
            if not targets:
                logger.info("No active targets found to curate.")
                return

            # 2. 第一阶段：高效批处理 (扫描最近 1000 条内容)
            logger.info(f"🧐 Phase 1: Batch scanning {len(targets)} targets against 1000 recent items...")
            news_res = requests.get(f"{self.api_url}/news/", params={"limit": 1000}, timeout=15)
            if news_res.status_code == 200:
                all_news = news_res.json()
                author_data_map = defaultdict(list)
                for n in all_news:
                    author = n.get('metadata_json', {}).get('author')
                    if not author and n['title'].startswith('@') and ':' in n['title']:
                        author = n['title'].split(':')[0].strip('@')
                    if author:
                        author_data_map[author.lower()].append(n)
            else:
                author_data_map = {}

            # 3. 第二阶段：针对性核查
            processed_count = 0
            for target in targets:
                handle = target['handle']
                recent_news = author_data_map.get(handle.lower(), [])
                
                # 如果第一阶段没找到，执行专项核查 (确保冷门账号不被误伤)
                if not recent_news:
                    logger.info(f"🔎 Phase 2: Targeted check for @{handle}...")
                    try:
                        # 请求后端：获取该作者最新的 10 条数据
                        spec_res = requests.get(f"{self.api_url}/news/", params={"author": handle, "limit": 10}, timeout=10)
                        if spec_res.status_code == 200:
                            recent_news = spec_res.json()
                    except Exception as e:
                        logger.warning(f"Targeted check failed for @{handle}: {e}")

                self._evaluate_target_performance(target, recent_news)
                processed_count += 1

        except Exception as e:
            logger.error(f"Error in curation phase: {e}")

    def _evaluate_target_performance(self, target: dict, recent_news: list):
        """评价单个账号的表现并决定是否汰换"""
        handle = target['handle']
        target_id = target['id']
        
        if not recent_news:
            # 只有在专项核查后依然没内容，且加入时间超过 21 天，才增加失败计数
            added_at_str = target['added_at'].replace('Z', '+00:00')
            try:
                added_at = datetime.fromisoformat(added_at_str)
            except:
                added_at = datetime.utcnow() # fallback

            days_since_added = (datetime.utcnow().replace(tzinfo=None) - added_at.replace(tzinfo=None)).days
            
            if days_since_added > 21: # 给冷门账号更多耐心 (3周)
                current_fail = target.get('failure_count', 0)
                logger.info(f"⏳ @{handle} has ZERO content in history. Increasing failure count ({current_fail + 1})")
                requests.patch(f"{self.api_url}/targets/{target_id}", json={"failure_count": current_fail + 1}, timeout=5)
            else:
                logger.info(f"💤 @{handle} is silent but new ({days_since_added} days), skipping.")
            return

        # 计算质量指标：剔除 0 分内容（0分通常代表 AI 额度超限或解析失败，不代表内容差）
        valid_scores = [n['score'] for n in recent_news if n.get('score') and n['score'] > 0]
        unscored_count = len([n for n in recent_news if not n.get('score') or n['score'] == 0])
        
        if not valid_scores:
            # 如果有内容但全都没评分，不应该降级账号，但需要记录
            logger.info(f"⏩ @{handle} has {unscored_count} posts but none are AI-scored yet. skipping quality update.")
            # 仅更新最后抓取时间，重置失败计数（因为确实有产出）
            requests.patch(f"{self.api_url}/targets/{target_id}", json={
                "last_scraped_at": datetime.utcnow().isoformat(),
                "failure_count": 0 
            }, timeout=5)
            return
        
        avg_score = sum(valid_scores) / len(valid_scores)
        high_value_count = len([s for s in valid_scores if s >= 80])
        total_posts = len(recent_news) # 总数包含未评分的，用于观察活跃度
        
        logger.info(f"📊 Stats for @{handle}: Avg={avg_score:.1f} (based on {len(valid_scores)} items), Unscored={unscored_count}, HighValue={high_value_count}")

        # 决策逻辑
        update_payload = {
            "avg_score": int(avg_score),
            "total_posts": total_posts,
            "high_value_posts": high_value_count,
            "last_scraped_at": datetime.utcnow().isoformat()
        }
        
        if high_value_count > 0:
            update_payload["last_high_score_at"] = datetime.utcnow().isoformat()
            update_payload["failure_count"] = 0 # 哪怕只有一条高质量内容，也重置失败计数
        else:
            current_fail = target.get('failure_count', 0)
            update_payload["failure_count"] = current_fail + 1

        # 执行自动下架
        if avg_score < 30 and total_posts >= 5: # 调低阈值到 30，避免误伤
            logger.warning(f"🚨 Deactivating @{handle}: Extremely low average score ({avg_score:.1f})")
            update_payload["is_active"] = False
            update_payload["status"] = "deactivated"
        
        elif update_payload["failure_count"] >= 15: # 增加容忍度到 15 次循环
            logger.warning(f"🚨 Deactivating @{handle}: Long-term silence or zero value")
            update_payload["is_active"] = False
            update_payload["status"] = "deactivated"

        # 更新到后端
        requests.patch(f"{self.api_url}/targets/{target_id}", json=update_payload, timeout=5)

from scrapers.utils.clustering import ClusteringEngine

if __name__ == "__main__":
    api_url = os.getenv("SCRAPER_API_URL", "http://localhost:8000")
    curator = SourceCurator(api_url)
    curator.run_curation()
    
    # Run the clustering phase
    clustering_engine = ClusteringEngine(api_url)
    clustering_engine.run_clustering()
