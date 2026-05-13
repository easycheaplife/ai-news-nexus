import requests
from datetime import datetime
import logging

class BaseScraper:
    def __init__(self, platform: str, api_url: str = "http://localhost:8000"):
        self.platform = platform
        self.api_url = api_url
        self.logger = logging.getLogger(f"scraper.{platform}")
        # 本地去重缓存（仅限本次运行）
        self.seen_ids = set()

    def push_to_backend(self, item: dict):
        # 1. 采集端本地去重
        item_key = f"{item['platform']}:{item['external_id']}"
        if item_key in self.seen_ids:
            return
        
        try:
            # 2. 推送到后端
            response = requests.post(f"{self.api_url}/news/", json=item)
            if response.status_code == 200:
                self.logger.info(f"✅ Successfully pushed: {item['title'][:50]}...")
                self.seen_ids.add(item_key)
            elif response.status_code == 409: # 假设我们用 409 表示已存在
                self.seen_ids.add(item_key)
            else:
                self.logger.error(f"❌ Failed to push: {response.text}")
        except Exception as e:
            self.logger.error(f"Error pushing to backend: {e}")

    def scrape(self):
        raise NotImplementedError("Subclasses must implement scrape()")
