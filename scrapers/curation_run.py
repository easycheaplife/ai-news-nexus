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

            # 2. 深度聚合：一次性获取更多近期内容，建立作者映射表
            # 扫描深度增加到 500 条，以覆盖更多冷门账号
            news_res = requests.get(f"{self.api_url}/news/", params={"limit": 500}, timeout=10)
            if news_res.status_code != 200:
                logger.error("Failed to fetch news for curation analysis.")
                return
            
            all_news = news_res.json()
            author_data_map = defaultdict(list)
            
            for n in all_news:
                # 尝试从 metadata 或 title 中识别作者
                author = n.get('metadata_json', {}).get('author')
                if not author:
                    # 尝试从 title 解析 (@username:)
                    if n['title'].startswith('@') and ':' in n['title']:
                        author = n['title'].split(':')[0].strip('@')
                
                if author:
                    author_data_map[author.lower()].append(n)

            # 3. 对每个账号执行性能评估
            logger.info(f"🧐 Evaluating {len(targets)} targets against {len(all_news)} recent items...")
            
            for target in targets:
                self._evaluate_target_performance(target, author_data_map.get(target['handle'].lower(), []))

        except Exception as e:
            logger.error(f"Error in curation phase: {e}")

    def _evaluate_target_performance(self, target: dict, recent_news: list):
        """评价单个账号的表现并决定是否汰换"""
        handle = target['handle']
        target_id = target['id']
        
        if not recent_news:
            # 长期沉默检查
            added_at = datetime.fromisoformat(target['added_at'].replace('Z', '+00:00'))
            days_since_added = (datetime.utcnow().replace(tzinfo=None) - added_at.replace(tzinfo=None)).days
            
            # 如果加入超过 14 天且最近 500 条都没有内容，增加失败计数
            if days_since_added > 14:
                current_fail = target.get('failure_count', 0)
                logger.info(f"⏳ @{handle} has no recent content. Increasing failure count ({current_fail + 1})")
                requests.patch(f"{self.api_url}/targets/{target_id}", json={"failure_count": current_fail + 1}, timeout=5)
            else:
                logger.info(f"💤 @{handle} is silent (no recent posts), skipping.")
            return

        # 计算质量指标
        scores = [n['score'] for n in recent_news if n.get('score') is not None]
        if not scores: 
            logger.info(f"⏩ @{handle} has posts but no AI scores yet. Skipping.")
            return
        
        avg_score = sum(scores) / len(scores)
        high_value_count = len([s for s in scores if s >= 80])
        total_posts = len(scores)
        
        logger.info(f"📊 Stats for @{handle}: Avg={avg_score:.1f}, HighValue={high_value_count}/{total_posts}")

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

        # 执行自动下架
        if avg_score < 40 and total_posts >= 5:
            logger.warning(f"🚨 Deactivating @{handle}: Low average score ({avg_score:.1f})")
            update_payload["is_active"] = False
            update_payload["status"] = "deactivated"
            update_payload["description"] = (target.get('description') or "") + " [Auto-deactivated due to low quality]"
        
        elif update_payload["failure_count"] >= 10: # 沉默或低质容忍度设为 10
            logger.warning(f"🚨 Deactivating @{handle}: Consistent lack of value or active content")
            update_payload["is_active"] = False
            update_payload["status"] = "deactivated"

        # 更新到后端
        requests.patch(f"{self.api_url}/targets/{target_id}", json=update_payload, timeout=5)

if __name__ == "__main__":
    api_url = os.getenv("SCRAPER_API_URL", "http://localhost:8000")
    curator = SourceCurator(api_url)
    curator.run_curation()
