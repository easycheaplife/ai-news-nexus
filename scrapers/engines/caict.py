import feedparser
import requests
from datetime import datetime
from .base import BaseScraper
import time

class CAICTScraper(BaseScraper):
    """
    CAICT (中国信通院) 引擎
    国内 AI 政策、标准和权威报告的首发地。
    """
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__(platform="caict", api_url=api_url, region="cn")
        # 信通院“人工智能”关键词 RSS
        self.rss_url = "https://rsshub.app/caict/keyword/人工智能"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

    def scrape(self):
        self.logger.info("Fetching latest AI policy & standards from CAICT...")
        try:
            response = requests.get(self.rss_url, headers=self.headers, timeout=20)
            if response.status_code != 200: return

            feed = feedparser.parse(response.content)
            for entry in feed.entries:
                dt = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))

                if not self.is_within_window(dt): continue

                self.push_to_backend({
                    "platform": "caict",
                    "external_id": entry.id if hasattr(entry, 'id') else entry.link,
                    "title": entry.title,
                    "content": entry.summary if hasattr(entry, 'summary') else entry.title,
                    "url": entry.link,
                    "author": "中国信通院",
                    "published_at": dt.isoformat() if dt else datetime.utcnow().isoformat(),
                    "score": 0
                })
        except Exception as e:
            self.logger.error(f"Error scraping CAICT: {e}")
