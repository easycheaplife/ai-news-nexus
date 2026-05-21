import requests
import feedparser
import logging
from datetime import datetime
from .base import BaseScraper
from ..utils.ai import evaluator

class LabsScraper(BaseScraper):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("labs", api_url)
        # 官方实验室 RSS/Atom 配置表 (优先使用官方，无官方则使用可靠的第三方聚合)
        self.feeds = {
            "OpenAI": "https://openai.com/news/rss.xml",
            "Anthropic": "https://rsshub.app/anthropic/news", 
            "Google DeepMind": "https://deepmind.google/blog/rss.xml",
            "Mistral AI": "https://raw.githubusercontent.com/alan-turing-institute/ai-rss-feeds/main/feeds/mistral-news.xml",
            "DeepSeek": "https://rsshub.app/deepseek/news",
            "Meta AI": "https://ai.meta.com/blog/rss/"
        }
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        }

    def scrape(self):
        self.logger.info(f"🧪 Starting Official Labs scraping ({len(self.feeds)} sources)...")
        
        for lab_name, feed_url in self.feeds.items():
            try:
                self.logger.info(f"📡 Fetching Feed: {lab_name} ({feed_url})...")
                last_id = self.get_last_id(lab_name)
                
                # 方案 1: 让 feedparser 直接处理 (它有自己的 User-Agent 和重试逻辑)
                feed = feedparser.parse(feed_url)
                
                # 方案 2: 如果方案 1 没抓到，尝试用 requests 强行获取
                if not feed.entries:
                    self.logger.info(f"🔄 Feedparser empty for {lab_name}, trying with requests...")
                    try:
                        response = requests.get(feed_url, headers=self.headers, timeout=15)
                        if response.status_code == 200:
                            feed = feedparser.parse(response.text)
                    except Exception as e:
                        self.logger.debug(f"Requests fallback failed for {lab_name}: {e}")

                if not feed.entries:
                    self.logger.warning(f"⚠️ No entries found in the feed for {lab_name}")
                    continue

                self.logger.info(f"📂 Found {len(feed.entries)} entries for {lab_name}")
                newest_id = None
                
                # RSS 通常是按时间倒序排列的
                for entry in feed.entries:
                    # 获取唯一标识符 (优先使用 link，因为 link 通常是永久的)
                    item_id = entry.link
                    
                    if last_id and item_id == last_id:
                        self.logger.info(f"⏱️ Reached last seen article for {lab_name}, skipping remaining.")
                        break
                    
                    if newest_id is None:
                        newest_id = item_id

                    # 提取标题和内容摘要
                    title = entry.title
                    # 尝试多种摘要字段
                    content = entry.get('summary', entry.get('description', ''))
                    # 如果内容包含 HTML 标签，进行简单清理
                    if '<' in content and '>' in content:
                        from bs4 import BeautifulSoup
                        content = BeautifulSoup(content, 'html.parser').get_text()

                    # 解析发布时间
                    dt_obj = None
                    if 'published_parsed' in entry:
                        dt_obj = datetime(*entry.published_parsed[:6])
                    elif 'updated_parsed' in entry:
                        dt_obj = datetime(*entry.updated_parsed[:6])
                    
                    # 窗口检查
                    if dt_obj and not self.is_within_window(dt_obj):
                        continue

                    self.logger.info(f"✍️ Analyzing: {title[:50]}...")
                    
                    # 🤖 AI 评分与深度分析
                    score, reason, takeaways, cluster_id, mentioned_users, trending_keywords = evaluator.evaluate(
                        f"Official Blog from {lab_name}: {title}", 
                        content
                    )

                    item = {
                        "platform": "labs",
                        "external_id": item_id,
                        "title": f"🏛️ [{lab_name}] {title}",
                        "content": content,
                        "url": entry.link,
                        "published_at": dt_obj.isoformat() if dt_obj else datetime.utcnow().isoformat(),
                        "score": score,
                        "reason": reason,
                        "takeaways": takeaways,
                        "cluster_id": cluster_id,
                        "mentioned_users": mentioned_users,
                        "trending_keywords": trending_keywords,
                        "metadata_json": {
                            "lab": lab_name,
                            "author": entry.get('author', lab_name),
                            "tags": [tag.term for tag in entry.get('tags', [])] if entry.get('tags') else []
                        }
                    }
                    
                    self.push_to_backend(item)
                
                if newest_id:
                    self.update_last_id(lab_name, newest_id)
                    self._save_state()

            except Exception as e:
                self.logger.error(f"Error scraping {lab_name}: {e}")

        self.logger.info("🏁 Labs scraping finished.")
