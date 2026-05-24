import requests
import feedparser
from .base import BaseScraper
from datetime import datetime
import time
from ..utils.ai import evaluator
from ..utils.wechat_utils import extract_wechat_full_text
import os

class WeChatScraper(BaseScraper):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("wechat", api_url)
        # 公众号订阅列表及其 biz ID
        self.biz_ids = {
            "QbitAI": "Mzg5MTA3MzMyMA==", # 量子位
            "Synced": "MzI0ODUxMjU2Mw==", # 机器之心
            "ZhipuAI": "MzI2NzQ1OTU5MQ==", # 智谱AI
            "deepseek_ai": "Mzk0OTQ5NjY5NQ==", # DeepSeek
            "baoyu_share": "MzI3NDMyNTMzOQ==", # 宝玉的分享
            "guizang_ai": "Mzk0MzA4NzYzOA==", # 归藏的 AI 笔记
            "muyao": "MjM5MTY4OTYyMA==" # 木遥
        }
        
        # 预设多个 RSSHub 实例进行轮询，增加稳定性
        default_instances = [
            "https://rsshub.rssforever.com",
            "https://rsshub.moeyy.cn",
            "https://rsshub.pseudoyu.com",
            "https://rsshub.app"
        ]
        
        env_prefix = os.getenv("WECHAT_RSS_PREFIX")
        self.rss_instances = [env_prefix] if env_prefix else default_instances

    def _fetch_full_content(self, url: str) -> str:
        """使用 r.jina.ai 穿透抓取公众号全文"""
        return extract_wechat_full_text(url)


    def scrape(self):
        self.logger.info("🏮 Starting WeChat Official Account scraping with multi-instance fallback...")
        
        for name, biz_id in self.biz_ids.items():
            last_timestamp = self.get_last_id(name)
            self.logger.info(f"👀 Monitoring: {name}")
            
            success = False
            # 轮询所有可用的 RSS 实例
            for instance in self.rss_instances:
                rss_url = f"{instance.rstrip('/')}/wechat/ce/{biz_id}"
                self.logger.info(f"  trying instance: {instance}")
                try:
                    time.sleep(1) # 基础延迟
                    res = requests.get(rss_url, timeout=15)
                    if res.status_code != 200:
                        self.logger.warning(f"  ⚠️ Instance {instance} returned {res.status_code}")
                        continue

                    feed = feedparser.parse(res.text)
                    if feed.bozo:
                        # 如果解析失败，可能是被拦截了返回了 HTML
                        self.logger.warning(f"  ⚠️ RSS parse error on {instance}")
                        continue
                    
                    if not feed.entries:
                        self.logger.warning(f"  ⚠️ No entries found on {instance}")
                        continue

                    newest_timestamp = None
                    for entry in feed.entries:
                        published_dt = datetime(*entry.published_parsed[:6])
                        published_ts = str(int(published_dt.timestamp()))
                        
                        if last_timestamp and int(published_ts) <= int(last_timestamp):
                            break
                        
                        if newest_timestamp is None:
                            newest_timestamp = published_ts
                        
                        if not self.is_within_window(published_dt):
                            continue

                        self.logger.info(f"  📰 Found new article: {entry.title}")
                        full_text = self._fetch_full_content(entry.link)
                        content_to_eval = full_text if len(full_text) > 100 else entry.summary
                        
                        score, reason, takeaways, cluster_id, mentioned_users, trending_keywords = evaluator.evaluate(
                            f"WeChat Article: {entry.title}", 
                            content_to_eval
                        )

                        media_urls = []
                        if 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
                            media_urls.append(entry.media_thumbnail[0]['url'])

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
                    
                    success = True
                    break # 抓取成功，跳出实例轮询
                    
                except Exception as e:
                    self.logger.warning(f"  ❌ Failed to scrape via {instance}: {e}")
            
            if not success:
                self.logger.error(f"🚫 All RSS instances failed for {name}.")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    scraper = WeChatScraper()
    scraper.scrape()
