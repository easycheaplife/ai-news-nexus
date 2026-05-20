import logging
import requests
import os
from datetime import datetime

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
            for target in targets:
                self._evaluate_target_performance(target)

        except Exception as e:
            logger.error(f"Error in curation phase: {e}")

    def _evaluate_target_performance(self, target: dict):
        """评价单个账号的表现并决定是否汰换"""
        handle = target['handle']
        platform = target['platform']
        target_id = target['id']
        
        # 1. 获取该账号最近的内容表现
        # 假设后端支持按作者/handle 过滤新闻 (目前需要后端支持，或者我们在采集端统计)
        # 为了演示，我们通过搜索接口模拟
        try:
            # 实际生产中建议后端提供聚合统计接口
            news_res = requests.get(f"{self.api_url}/news/", params={"limit": 50}, timeout=10)
            if news_res.status_code != 200: return
            
            all_news = news_res.json()
            # 过滤出该作者的内容
            author_news = [n for n in all_news if n.get('metadata_json', {}).get('author') == handle or f"@{handle}" in n['title']]
            
            if not author_news:
                # 检查是否长期沉默 (例如 30 天没发新东西)
                # 这里简单处理：如果 post 数量为 0 且加入时间很久，则增加 failure_count
                return

            # 2. 计算质量指标
            scores = [n['score'] for n in author_news if n.get('score') is not None]
            if not scores: return
            
            avg_score = sum(scores) / len(scores)
            high_value_count = len([s for s in scores if s >= 80])
            total_posts = len(scores)
            
            logger.info(f"📊 Stats for @{handle}: Avg={avg_score:.1f}, HighValue={high_value_count}/{total_posts}")

            # 3. 决策逻辑 (末位淘汰)
            update_payload = {
                "avg_score": int(avg_score),
                "total_posts": total_posts,
                "high_value_posts": high_value_count,
                "last_scraped_at": datetime.utcnow().isoformat()
            }
            
            if high_value_count > 0:
                update_payload["last_high_score_at"] = datetime.utcnow().isoformat()
                update_payload["failure_count"] = 0 # 重置失败计数
            else:
                # 如果没有高价值产出，增加失败计数
                current_fail = target.get('failure_count', 0)
                update_payload["failure_count"] = current_fail + 1

            # 4. 执行自动下架
            if avg_score < 40 and total_posts >= 5:
                logger.warning(f"🚨 Deactivating @{handle}: Low average score ({avg_score:.1f})")
                update_payload["is_active"] = False
                update_payload["status"] = "deactivated"
                update_payload["description"] = (target.get('description') or "") + " [Auto-deactivated due to low quality]"
            
            elif update_payload["failure_count"] >= 5:
                logger.warning(f"🚨 Deactivating @{handle}: Consistent lack of high-quality content")
                update_payload["is_active"] = False
                update_payload["status"] = "deactivated"

            # 5. 更新到后端
            requests.patch(f"{self.api_url}/targets/{target_id}", json=update_payload, timeout=5)

        except Exception as e:
            logger.error(f"Failed to evaluate @{handle}: {e}")

if __name__ == "__main__":
    api_url = os.getenv("SCRAPER_API_URL", "http://localhost:8000")
    curator = SourceCurator(api_url)
    curator.run_curation()
