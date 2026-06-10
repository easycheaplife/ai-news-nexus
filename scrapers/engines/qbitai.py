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
                title = entry.title
                summary = entry.summary if hasattr(entry, 'summary') else title
                text_to_check = (title + " " + summary).lower()

                # 🛡️ 极其严格的 AI 关键词双重过滤
                strict_ai_keywords = [
                    "ai", "llm", "gpt", "大模型", "智能体", "agent", "rag", "深度学习", "机器学习", 
                    "transformer", "claude", "deepseek", "sora", "算力", "英伟达", "nvidia", 
                    "生成式", "语言模型", "向量数据库", "推理", "训练", "微调", "提示词", "prompt", 
                    "机器人", "自动驾驶", "端到端", "多模态", "aigc", "算力", "h100", "b200", 
                    "openrouter", "openai", "anthropic", "mistral", "llama", "qwen", "通义千问", 
                    "智谱", "kimi", "月之暗面", "零一万物", "百川智能", "面壁智能", "商汤", "字节跳动 ai"
                ]
                blacklist = ["融资", "上市", "财报", "股价", "收购", "亏损", "裁员", "高管变动", "内斗", "手机", "数码", "笔记本", "游戏", "发布会", "预订", "开售"]

                is_ai = any(k in text_to_check for k in strict_ai_keywords)
                is_noise = any(k in text_to_check for k in blacklist)

                if not is_ai or is_noise:
                    continue

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
