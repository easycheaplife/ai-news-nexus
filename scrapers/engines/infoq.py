import feedparser
import requests
from datetime import datetime
from .base import BaseScraper
import time

class InfoQScraper(BaseScraper):
    """
    InfoQ 中国 AI 频道引擎
    采用多节点 RSSHub 冗余方案，并加强 AI 关键词过滤。
    """
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__(platform="infoq", api_url=api_url, region="cn")
        # 多节点备选方案，包含官方和高质量第三方镜像
        self.rss_nodes = [
            "https://www.infoq.cn/public/rss/ai.xml", # 官方
            "https://rsshub.rssforever.com/infoq/topic/AI",
            "https://rsshub.app/infoq/topic/AI",
            "https://rss.feedapi.top/infoq/topic/AI"
        ]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
            "Referer": "https://www.infoq.cn/topic/AI",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        }

    def scrape(self):
        self.logger.info("Fetching latest AI articles from InfoQ (Multi-node RSS)...")
        
        success = False
        for rss_url in self.rss_nodes:
            try:
                self.logger.info(f"Trying RSS node: {rss_url}")
                response = requests.get(rss_url, headers=self.headers, timeout=20)
                
                if response.status_code != 200:
                    self.logger.warning(f"Node {rss_url} failed with status {response.status_code}")
                    continue

                feed = feedparser.parse(response.content)
                if not feed.entries:
                    self.logger.warning(f"No entries found in node {rss_url}")
                    continue

                for entry in feed.entries:
                    title = entry.title
                    summary = entry.summary if hasattr(entry, 'summary') else title
                    
                    # 🛡️ 严格 AI 关键词过滤
                    ai_keywords = ["ai", "大模型", "智能", "agent", "llm", "深度学习", "架构", "机器学习", "transformer"]
                    if not any(k in title.lower() or k in summary.lower() for k in ai_keywords):
                        continue

                    external_id = entry.id if hasattr(entry, 'id') else entry.link
                    dt = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))

                    if not self.is_within_window(dt):
                        continue

                    news_item = {
                        "platform": "infoq",
                        "external_id": external_id,
                        "title": title,
                        "content": summary,
                        "url": entry.link,
                        "author": "InfoQ 中国",
                        "published_at": dt.isoformat() if dt else datetime.utcnow().isoformat(),
                        "score": 0,
                        "raw_data": {"rss_node": rss_url}
                    }
                    self.push_to_backend(news_item)
                
                success = True
                break # 成功抓取一个节点就停止

            except Exception as e:
                self.logger.error(f"Error scraping InfoQ node {rss_url}: {e}")
                continue
        
        if not success:
            self.logger.error("All InfoQ RSS nodes failed.")
