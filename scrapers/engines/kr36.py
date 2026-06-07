import feedparser
import requests
from datetime import datetime
from .base import BaseScraper
import time

class Kr36Scraper(BaseScraper):
    """
    36Kr AI 频道引擎 (RSS 稳定版)
    36Kr 的 RSS 接口比动态 API 更稳定，适合长期运行。
    """
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__(platform="36kr", api_url=api_url, region="cn")
        self.rss_url = "https://36kr.com/feed"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

    def scrape(self):
        self.logger.info("Fetching latest articles from 36Kr RSS...")
        try:
            # 拿到原始 XML
            response = requests.get(self.rss_url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch 36Kr RSS: {response.status_code}")
                return

            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                self.logger.warning("No entries found in 36Kr RSS.")
                return

            for entry in feed.entries:
                title = entry.title
                summary = entry.summary if hasattr(entry, 'summary') else title
                
                # 🛡️ 严格 AI 关键词过滤
                ai_keywords = ["ai", "大模型", "智算", "算力", "机器人", "gpt", "claude", "deepseek", "智能体", "agent"]
                if not any(k in title.lower() or k in summary.lower() for k in ai_keywords):
                    continue

                external_id = entry.id if hasattr(entry, 'id') else entry.link
                
                # 时间处理
                dt = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))

                if not self.is_within_window(dt):
                    continue

                news_item = {
                    "platform": "36kr",
                    "external_id": external_id,
                    "title": title,
                    "content": summary,
                    "url": entry.link,
                    "author": "36氪",
                    "published_at": dt.isoformat() if dt else datetime.utcnow().isoformat(),
                    "score": 0,
                    "raw_data": {"rss_entry": True}
                }
                self.push_to_backend(news_item)

        except Exception as e:
            self.logger.error(f"Error scraping 36Kr RSS: {e}")
