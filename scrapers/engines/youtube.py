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
            "UCfzlCWGWYyIQ0aLC5GQIIyw": "Yannic Kilcher",
            "UCX84O3K-Z9E8N9B9-6uN1pA": "Wes Roth",
            "UCZ9th96L0XNToUv84_f-8A": "Matthew Berman",
            "UCvYpB3Z6-uX7X0f0S1V0-Lg": "Lex Fridman (AI Focus)",
            "UC8uT9cgJdzSGeG67Sfcv7pA": "The AI Grid",
            "UCRixvX07y3D-fXo575R-tDw": "ColdTake AI"
        }
        self.rss_base = "https://www.youtube.com/feeds/videos.xml?channel_id="

    def _get_transcript(self, video_id: str) -> str:
        """获取视频的字幕文本"""
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            # 尝试获取中文或英文字幕
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # 优先顺序：中文 -> 英文
            try:
                transcript = transcript_list.find_transcript(['zh-Hans', 'zh-CN', 'zh-TW', 'zh', 'en'])
            except:
                # 都没有的话取第一个可用的
                transcript = next(iter(transcript_list))
                
            data = transcript.fetch()
            # 拼接文本并限制长度 (前 3000 字符)
            full_text = " ".join([t['text'] for t in data])
            return full_text[:3000]
        except Exception:
            # 很多视频（如 Short 或未开启字幕的视频）会失败，静默处理
            return ""

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
                    self.logger.info(f"🔗 Processing Item ID: {entry.yt_videoid}")
                    # 获取发布时间戳
                    published_ts = str(int(datetime(*entry.published_parsed[:6]).timestamp()))
                    
                    if last_timestamp and int(published_ts) <= int(last_timestamp):
                        self.logger.info(f"⏱️ Reached last seen video for {channel_name}, stopping.")
                        break
                    
                    if newest_timestamp is None:
                        newest_timestamp = published_ts
                        
                    # YouTube RSS content is in summary or media_description
                    description = ""
                    if 'summary' in entry:
                        description = entry.summary
                    elif 'media_description' in entry:
                        description = entry.media_description
                        
                    # 🧵 获取视频字幕深度内容
                    transcript_text = self._get_transcript(entry.yt_videoid)
                    full_content = f"{description}\n\n[视频字幕摘要]:\n{transcript_text}".strip()

                    # 提取封面图 (最大分辨率)
                    media_urls = []
                    if 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
                        # Find the highest resolution thumbnail (usually the last one or max width)
                        best_thumb = max(entry.media_thumbnail, key=lambda x: int(x.get('width', 0)))
                        media_urls.append(best_thumb['url'])

                    # 🤖 AI 评分与理由
                    score, reason, takeaways, cluster_id, mentioned_users, trending_keywords = evaluator.evaluate(f"YouTube Video: {entry.title}", full_content)

                    item = {
                        "platform": "youtube",
                        "external_id": entry.yt_videoid,
                        "title": entry.title,
                        "content": full_content,
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
                            "author": channel_name,
                            "channel_id": channel_id
                        }
                    }
                    self.push_to_backend(item)
                    
                if newest_timestamp:
                    self.update_last_id(channel_id, newest_timestamp)
                    
            except Exception as e:
                self.logger.error(f"Error scraping YouTube channel {channel_name}: {e}")
