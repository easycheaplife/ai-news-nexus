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
                resp_json = news_res.json()
                all_news = resp_json.get("items", []) if isinstance(resp_json, dict) else resp_json
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
                            s_json = spec_res.json()
                            recent_news = s_json.get("items", []) if isinstance(s_json, dict) else s_json
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
            
            # 🚨 沉默期强制下线逻辑
            if days_since_added >= self.max_silence_days:
                logger.warning(f"🚨 Deactivating @{handle}: No content found for {self.max_silence_days}+ days")
                requests.patch(f"{self.api_url}/targets/{target_id}", json={
                    "is_active": False,
                    "status": "deactivated",
                    "description": f"Auto-deactivated: No content found for {self.max_silence_days}+ days"
                }, timeout=5)
            else:
                logger.info(f"💤 @{handle} is silent but still within observation window ({days_since_added}/{self.max_silence_days} days).")
            return

        # 计算质量指标：剔除 0 分内容
        valid_scores = [n['score'] for n in recent_news if n.get('score') and n['score'] > 0]
        unscored_count = len([n for n in recent_news if not n.get('score') or n['score'] == 0])
        
        if not valid_scores:
            logger.info(f"⏩ @{handle} has {unscored_count} posts but none are AI-scored yet. skipping quality update.")
            requests.patch(f"{self.api_url}/targets/{target_id}", json={
                "last_scraped_at": datetime.utcnow().isoformat(),
                "failure_count": 0 
            }, timeout=5)
            return
        
        avg_score = sum(valid_scores) / len(valid_scores)
        high_value_count = len([s for s in valid_scores if s >= 80])
        total_posts = len(recent_news)
        
        # 核心比例指标
        high_value_ratio = high_value_count / len(valid_scores) if valid_scores else 0
        
        logger.info(f"📊 Stats for @{handle}: Avg={avg_score:.1f}, HV-Ratio={high_value_ratio:.1%}, Total={total_posts}")

        # 决策逻辑
        update_payload = {
            "avg_score": int(avg_score),
            "total_posts": total_posts,
            "high_value_posts": high_value_count,
            "last_scraped_at": datetime.utcnow().isoformat()
        }
        
        if high_value_count > 0:
            update_payload["last_high_score_at"] = datetime.utcnow().isoformat()
            update_payload["failure_count"] = 0
        else:
            current_fail = target.get('failure_count', 0)
            update_payload["failure_count"] = current_fail + 1

        # --- 精英化淘汰逻辑 ---
        # 1. 评分过低 (门槛由 30 提升至 60)
        is_low_quality = avg_score < 60
        # 2. 信息密度过低 (高分干货占比必须 >= 20%)
        is_low_density = high_value_ratio < 0.20
        # 3. 话多但没干货 (总数多但高分少)
        is_verbose_noise = total_posts >= 15 and high_value_count < 2

        if (is_low_quality or is_low_density or is_verbose_noise) and total_posts >= 10:
            logger.warning(f"🚨 Deactivating @{handle}: Elite-tier check failed (Avg:{avg_score:.1f}, HV-Ratio:{high_value_ratio:.1%})")
            update_payload["is_active"] = False
            update_payload["status"] = "deactivated"
        
        elif update_payload["failure_count"] >= 10: # 沉默惩罚阈值从 15 缩短至 10
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
