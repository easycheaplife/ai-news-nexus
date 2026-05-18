import requests
import json
from .base import BaseScraper
from datetime import datetime
from ..utils.ai import evaluator

class ProductHuntScraper(BaseScraper):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("ph", api_url)
        self.rss_url = "https://www.producthunt.com/feed"

    def scrape(self):
        try:
            import feedparser
            self.logger.info("📦 Scraping Product Hunt RSS feed...")
            last_timestamp = self.get_last_id("ph_main")
            feed = feedparser.parse(self.rss_url)
            
            newest_timestamp = None
            for entry in feed.entries:
                date_str = entry.get('published', 'N/A')
                self.logger.info(f"🔗 Processing Item ID: {entry.id} | Date: {date_str}")
                # 获取时间戳字符串用于比较
                published_ts = str(int(datetime(*entry.published_parsed[:6]).timestamp()))
                
                if last_timestamp and int(published_ts) <= int(last_timestamp):
                    self.logger.info("⏱️ Reached last seen Product Hunt post, stopping.")
                    break
                
                if newest_timestamp is None:
                    newest_timestamp = published_ts

                if any(k in (entry.title + entry.get('summary', '')).lower() for k in ["ai ", "gpt", "llm", "bot"]):
                    # 🖼️ 提取多媒体
                    media_urls = []
                    for link in entry.get('links', []):
                        if link.get('type') == 'image/jpeg' or link.get('type') == 'image/png':
                            media_urls.append(link.get('href'))
                    
                    # 🧩 提取更详细的内容 (RSS feed 可能包含 summary 和 content)
                    rich_content = entry.get('summary', '')
                    if entry.get('content'):
                        # 如果有 content_list，通常包含更详细的描述
                        rich_content = entry.get('content')[0].value
                    
                    # 🤖 AI 评分与理由
                    score, reason, takeaways, cluster_id, mentioned_users, trending_keywords = evaluator.evaluate(entry.title, rich_content)

                    item = {
                        "platform": "ph",
                        "external_id": entry.id.split('/')[-1],
                        "title": entry.title,
                        "content": rich_content,
                        "url": entry.link,
                        "published_at": datetime.fromtimestamp(int(published_ts)).isoformat(),
                        "score": score,
                        "reason": reason,
                        "takeaways": takeaways,
                            "cluster_id": cluster_id,
                            "mentioned_users": mentioned_users,
                            "trending_keywords": trending_keywords,
                        "media_urls": media_urls,
                        "metadata_json": {
                            "author": entry.get("author", "Unknown")
                        }
                    }
                    self.push_to_backend(item)
            
            if newest_timestamp:
                self.update_last_id("ph_main", newest_timestamp)
                
        except Exception as e:
            self.logger.error(f"Error scraping Product Hunt: {e}")
