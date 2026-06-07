import feedparser
import requests
from datetime import datetime
from .base import BaseScraper
import time

class QbitAIScraper(BaseScraper):
    """
    QbitAI (量子位) RSS 引擎
    量子位是国内顶尖的 AI 科技媒体，其 RSS 源非常稳定。
    """
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__(platform="qbitai", api_url=api_url, region="cn")
        self.rss_url = "https://www.qbitai.com/feed"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

    def scrape(self):
        self.logger.info("Fetching latest articles from QbitAI RSS...")
        try:
            # 拿到原始 XML 内容，因为 feedparser 有时会被 403
            response = requests.get(self.rss_url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch QbitAI RSS: {response.status_code}")
                return

            # 解析 RSS
            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                self.logger.warning("No entries found in QbitAI RSS.")
                return

            for entry in feed.entries:
                external_id = entry.id if hasattr(entry, 'id') else entry.link
                
                # 时间处理
                dt = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))

                if not self.is_within_window(dt):
                    continue

                news_item = {
                    "platform": "qbitai",
                    "external_id": external_id,
                    "title": entry.title,
                    "content": entry.summary if hasattr(entry, 'summary') else entry.title,
                    "url": entry.link,
                    "author": "量子位",
                    "published_at": dt.isoformat() if dt else datetime.utcnow().isoformat(),
                    "score": 0,
                    "raw_data": {"rss_entry": True}
                }
                
                self.push_to_backend(news_item)

        except Exception as e:
            self.logger.error(f"Error scraping QbitAI RSS: {e}")
