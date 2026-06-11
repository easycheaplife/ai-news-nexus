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
                text_to_check = (title + " " + summary).lower()

                # 🛡️ 极其严格的 AI 关键词白名单
                import re
                strict_ai_keywords = [
                    "llm", "gpt", "大模型", "智能体", "agent", "rag", "深度学习", "机器学习", 
                    "transformer", "claude", "deepseek", "sora", "算力", "英伟达", "nvidia", 
                    "生成式", "语言模型", "向量数据库", "推理", "训练", "微调", "提示词", "prompt", 
                    "机器人", "自动驾驶", "端到端", "多模态", "aigc", "算力", "h100", "b200", 
                    "openrouter", "openai", "anthropic", "mistral", "llama", "qwen", "通义千问", 
                    "智谱", "kimi", "月之暗面", "零一万物", "百川智能", "面壁智能", "商汤", "字节跳动 ai"
                ]

                # 🚫 噪音黑名单
                blacklist = [
                    "融资", "上市", "财报", "股价", "收购", "裁员", "内斗", "手机", "数码", 
                    "笔记本", "游戏", "发布会", "预订", "开售", "javascript", "vue", "react", "重构"
                ]

                has_standalone_ai = bool(re.search(r'\bai\b', text_to_check))
                has_core_ai = any(k in text_to_check for k in strict_ai_keywords)
                is_noise = any(k in text_to_check for k in blacklist)

                if not (has_standalone_ai or has_core_ai) or is_noise:
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
