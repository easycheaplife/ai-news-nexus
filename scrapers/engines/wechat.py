import requests
import feedparser
from .base import BaseScraper
from datetime import datetime
import time
from ..utils.ai import evaluator
import os

class WeChatScraper(BaseScraper):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("wechat", api_url)
        # 公众号订阅列表及其 RSS 地址 (使用稳定的公共/私有 RSS 桥接)
        # 这里预设一组稳定的 RSSHub 或 Wechat2RSS 链接
        self.targets = {
            "QbitAI": "https://rsshub.app/wechat/msghistory/Mzg5MTA3MzMyMA==", # 量子位
            "Synced": "https://rsshub.app/wechat/msghistory/MzI0ODUxMjU2Mw==", # 机器之心
            "ZhipuAI": "https://rsshub.app/wechat/msghistory/MzI2NzQ1OTU5MQ==", # 智谱AI
            "deepseek_ai": "https://rsshub.app/wechat/msghistory/Mzk0OTQ5NjY5NQ==", # DeepSeek
            "baoyu_share": "https://rsshub.app/wechat/msghistory/MzI3NDMyNTMzOQ==", # 宝玉的分享
            "guizang_ai": "https://rsshub.app/wechat/msghistory/Mzk0MzA4NzYzOA==", # 归藏的 AI 笔记
            "muyao": "https://rsshub.app/wechat/msghistory/MjM5MTY4OTYyMA==" # 木遥
        }
        # 允许在 .env 中覆盖 RSS 基础 URL，防止公共实例被封
        self.rss_prefix = os.getenv("WECHAT_RSS_PREFIX", "").rstrip('/')
        if self.rss_prefix:
            # 如果配置了前缀，尝试动态替换
            pass

    def _fetch_full_content(self, url: str) -> str:
        """使用 r.jina.ai 穿透抓取公众号全文"""
        jina_url = f"https://r.jina.ai/{url}"
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            res = requests.get(jina_url, headers=headers, timeout=30)
            if res.status_code == 200:
                # 过滤掉一些不必要的导航信息
                content = res.text
                if "Markdown Content:" in content:
                    content = content.split("Markdown Content:")[1]
                return content.strip()[:8000] # 限制 8000 字符，防止过大
        except Exception as e:
            self.logger.warning(f"Failed to fetch full content via Jina: {e}")
        return ""

    def scrape(self):
        self.logger.info("🏮 Starting WeChat Official Account scraping...")
        
        for name, rss_url in self.targets.items():
            last_timestamp = self.get_last_id(name)
            self.logger.info(f"👀 Monitoring: {name}")
            
            try:
                # 礼貌延迟，防止被 RSS 服务封禁
                time.sleep(2)
                feed = feedparser.parse(rss_url)
                
                if feed.bozo:
                    self.logger.warning(f"⚠️ RSS feed error for {name}: {feed.bozo_exception}")
                    # 如果 RSSHub 公共实例挂了，这属于正常现象，记录日志但不崩溃
                
                newest_timestamp = None
                
                # 遍历条目 (RSSHub 默认返回最近 10-20 条)
                for entry in feed.entries:
                    # 获取发布时间戳
                    published_dt = datetime(*entry.published_parsed[:6])
                    published_ts = str(int(published_dt.timestamp()))
                    
                    if last_timestamp and int(published_ts) <= int(last_timestamp):
                        break # 已抓取到最新，停止
                    
                    if newest_timestamp is None:
                        newest_timestamp = published_ts
                    
                    if not self.is_within_window(published_dt):
                        continue

                    self.logger.info(f"📰 Found new article: {entry.title}")
                    
                    # 🧵 穿透抓取全文
                    full_text = self._fetch_full_content(entry.link)
                    
                    # 如果抓取不到全文，则使用 RSS 里的简短描述（通常也是空的或排版混乱）
                    content_to_eval = full_text if len(full_text) > 100 else entry.summary
                    
                    # 🤖 AI 深度评估
                    score, reason, takeaways, cluster_id, mentioned_users, trending_keywords = evaluator.evaluate(
                        f"WeChat Article: {entry.title}", 
                        content_to_eval
                    )

                    # 提取封面图 (通常在媒体标签中)
                    media_urls = []
                    if 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
                        media_urls.append(entry.media_thumbnail[0]['url'])
                    elif 'links' in entry:
                        for link in entry.links:
                            if 'image' in link.get('type', ''):
                                media_urls.append(link.href)

                    item = {
                        "platform": "wechat",
                        "external_id": f"wc_{published_ts}_{name}",
                        "title": entry.title,
                        "content": content_to_eval,
                        "url": entry.link,
                        "published_at": published_dt.isoformat(),
                        "score": score,
                        "reason": reason,
                        "takeaways": takeaways,
                        "cluster_id": cluster_id,
                        "mentioned_users": mentioned_users,
                        "trending_keywords": trending_keywords,
                        "media_urls": media_urls,
                        "metadata_json": {
                            "author": name,
                            "is_full_text": len(full_text) > 100
                        }
                    }
                    self.push_to_backend(item)
                    
                if newest_timestamp:
                    self.update_last_id(name, newest_timestamp)
                    
            except Exception as e:
                self.logger.error(f"Error scraping WeChat {name}: {e}")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    scraper = WeChatScraper()
    scraper.scrape()
