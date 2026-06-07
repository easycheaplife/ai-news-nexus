import feedparser
import requests
from datetime import datetime
from .base import BaseScraper
import time

class ITHomeScraper(BaseScraper):
    """
    ITHome (IT之家) 引擎 (官方 RSS 版)
    从官方 RSS 抓取并进行严格的 AI 关键词过滤。
    """
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__(platform="ithome", api_url=api_url, region="cn")
        self.rss_url = "https://www.ithome.com/rss/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

    def scrape(self):
        self.logger.info("Fetching latest AI news from ITHome Official RSS...")
        try:
            response = requests.get(self.rss_url, headers=self.headers, timeout=20)
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch ITHome RSS: {response.status_code}")
                return

            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                self.logger.warning("No entries found in ITHome RSS.")
                return

            for entry in feed.entries:
                title = entry.title.lower()
                summary = (entry.summary if hasattr(entry, 'summary') else title).lower()
                
                # 🚫 强力黑名单：出现这些词基本就是普通数码/数码硬件新闻，直接过滤
                hardware_blacklist = [
                    "开售", "发售", "上市", "价格", "预约", "预订", "配色", "版本", 
                    "手机", "笔记本", "电脑", "键盘", "鼠标", "耳机", "手表", "空调", 
                    "冰箱", "洗衣机", "电视", "显示器", "处理器", "骁龙", "天玑", 
                    "游戏", "dlc", "发发行", "公测", "封测", "路由器", "充电器", 
                    "电池", "续航", "屏", "镜头", "影像"
                ]
                
                if any(hw in title for hw in hardware_blacklist):
                    continue

                # ✅ 核心 AI 关键词：必须包含这些强关联词
                core_ai_tags = [
                    "大模型", "llm", "gpt", "deepseek", "sora", "英伟达", "nvidia", 
                    "智算", "机器之心", "深度学习", "transformer", "claude", "gemini", 
                    "agent", "智能体", "rag", "通义千问", "文心一言", "智谱", "混元", 
                    "天工", "字节跳动 ai", "腾讯 ai", "百度 ai", "阿里 ai", "生成式"
                ]
                
                # 🏆 严格匹配 "ai" 单词 (前后需有非字母字符)
                import re
                has_standalone_ai = bool(re.search(r'\bai\b', title)) or bool(re.search(r'\bai\b', summary))
                
                # 判定逻辑：没有强 AI 词且没有独立 AI 单词，则过滤
                if not (any(tag in title or tag in summary for tag in core_ai_tags) or has_standalone_ai):
                    continue
                
                # 🛡️ 二次加固：如果标题中包含了一些模糊词（如“机器人”、“智能”），必须伴随其他 AI 关键词
                fuzzy_keywords = ["机器人", "智能", "架构"]
                if any(fk in title for fk in fuzzy_keywords):
                     if not (any(tag in summary for tag in core_ai_tags) or has_standalone_ai):
                         continue

                external_id = entry.id if hasattr(entry, 'id') else entry.link
                
                # 时间处理 (RSS 通常是 GMT)
                dt = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))

                if not self.is_within_window(dt):
                    continue

                news_item = {
                    "platform": "ithome",
                    "external_id": external_id,
                    "title": title,
                    "content": summary,
                    "url": entry.link,
                    "author": "IT之家",
                    "published_at": dt.isoformat() if dt else datetime.utcnow().isoformat(),
                    "score": 0,
                    "raw_data": {"source": "official_rss"}
                }
                self.push_to_backend(news_item)

        except Exception as e:
            self.logger.error(f"Error scraping ITHome RSS: {e}")
