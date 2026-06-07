import requests
import logging
from datetime import datetime
from .base import BaseScraper
import os

class AIHotScraper(BaseScraper):
    """
    AI HOT (aihot.virxact.com) 聚合引擎
    国内 AI 资讯的“元信源”，聚合了公众号、主流媒体等。
    """
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__(platform="aihot", api_url=api_url, region="cn")
        self.ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        self.base_url = "https://aihot.virxact.com/api/public/items"

    def scrape(self):
        self.logger.info("Fetching latest AI HOT items...")
        params = {
            "mode": "selected",
            "take": 50
        }
        headers = {"User-Agent": self.ua}
        
        try:
            response = requests.get(self.base_url, params=params, headers=headers, timeout=10)
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch AI HOT: {response.status_code}")
                return

            data = response.json()
            items = data.get("items", [])
            
            for item in items:
                # 转换格式以匹配后端 schema
                external_id = item.get("id")
                published_at_str = item.get("publishedAt")
                
                dt = None
                if published_at_str:
                    try:
                        dt = datetime.fromisoformat(published_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
                    except Exception as e:
                        self.logger.error(f"Error parsing date {published_at_str}: {e}")

                # 检查时间窗口
                if not self.is_within_window(dt):
                    continue

                news_item = {
                    "platform": "aihot",
                    "external_id": external_id,
                    "title": item.get("title"),
                    "content": item.get("summary") or item.get("title"),
                    "url": item.get("url"),
                    "author": item.get("source"),
                    "published_at": published_at_str,
                    "score": 0,  # AI HOT 已经是精选，后端会重新评估
                    "raw_data": item
                }
                
                self.push_to_backend(news_item)
                
        except Exception as e:
            self.logger.error(f"Error scraping AI HOT: {e}")
