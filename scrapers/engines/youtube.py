import requests
import feedparser
from .base import BaseScraper
from datetime import datetime
import time
from ..utils.ai import evaluator

class YouTubeScraper(BaseScraper):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("youtube", api_url)
        # 顶级 AI 相关频道的 ID
        self.channels = {
            "UCv83tO5cePwHMt1952IVBgA": "Two Minute Papers",
            "UCl59L8xY7h-pI5x58v9_L1Q": "Andrej Karpathy",
            "UCOjD18EJYcsBog4IozkF_7w": "DeepLearning.AI",
            "UCfzlCWGWYyIQ0aLC5GQIIyw": "Yannic Kilcher"
        }
        self.rss_base = "https://www.youtube.com/feeds/videos.xml?channel_id="

    def scrape(self):
        self.logger.info("▶️ Starting YouTube scraping...")
        
        for channel_id, channel_name in self.channels.items():
            last_timestamp = self.get_last_id(channel_id)
            url = f"{self.rss_base}{channel_id}"
            
            try:
                time.sleep(1) # 礼貌延迟
                feed = feedparser.parse(url)
                newest_timestamp = None
                
                for entry in feed.entries:
                    # 获取发布时间戳
                    published_ts = str(int(datetime(*entry.published_parsed[:6]).timestamp()))
                    
                    if last_timestamp and int(published_ts) <= int(last_timestamp):
                        self.logger.info(f"⏱️ Reached last seen video for {channel_name}, stopping.")
                        break
                    
                    if newest_timestamp is None:
                        newest_timestamp = published_ts
                        
                    # YouTube RSS content is in summary or media_description
                    description = ""
                    if 'media_content' in entry and len(entry.media_content) > 0:
                        # Extract thumbnail from media_content if needed, though usually media_thumbnail is better
                        pass
                    
                    if 'summary' in entry:
                        description = entry.summary
                    elif 'media_description' in entry:
                        description = entry.media_description
                        
                    # 提取封面图 (最大分辨率)
                    media_urls = []
                    if 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
                        # Find the highest resolution thumbnail (usually the last one or max width)
                        best_thumb = max(entry.media_thumbnail, key=lambda x: int(x.get('width', 0)))
                        media_urls.append(best_thumb['url'])

                    # 🤖 AI 评分与理由
                    score, reason = evaluator.evaluate(f"YouTube Video: {entry.title}", description)

                    item = {
                        "platform": "youtube",
                        "external_id": entry.yt_videoid,
                        "title": entry.title,
                        "content": description,
                        "url": entry.link,
                        "published_at": datetime.fromtimestamp(int(published_ts)).isoformat(),
                        "score": score,
                        "reason": reason,
                        "media_urls": media_urls,
                        "metadata_json": {
                            "author": channel_name,
                            "channel_id": channel_id
                        }
                    }
                    self.push_to_backend(item)
                    
                if newest_timestamp:
                    self.update_last_id(channel_id, newest_timestamp)
                    
            except Exception as e:
                self.logger.error(f"Error scraping YouTube channel {channel_name}: {e}")
