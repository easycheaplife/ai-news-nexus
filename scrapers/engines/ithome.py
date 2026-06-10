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
                text_to_check = title + " " + summary

                # 🚫 强力黑名单：出现这些词基本就是普通数码/数码硬件新闻，直接过滤
                noise_blacklist = [
                    "开售", "发售", "上市", "价格", "预约", "预订", "配色", "版本", 
                    "手机", "笔记本", "电脑", "键盘", "鼠标", "耳机", "手表", "空调", 
                    "冰箱", "洗衣机", "电视", "显示器", "处理器", "骁龙", "天玑", 
                    "游戏", "dlc", "发行", "公测", "封测", "路由器", "充电器", 
                    "电池", "续航", "屏", "镜头", "影像", "融资", "财报", "股价"
                ]

                if any(noise in text_to_check for noise in noise_blacklist):
                    continue

                # ✅ 核心 AI 关键词白名单
                strict_ai_keywords = [
                    "ai", "llm", "gpt", "大模型", "智能体", "agent", "rag", "深度学习", "机器学习", 
                    "transformer", "claude", "deepseek", "sora", "算力", "英伟达", "nvidia", 
                    "生成式", "语言模型", "向量数据库", "推理", "训练", "微调", "提示词", "prompt", 
                    "机器人", "自动驾驶", "端到端", "多模态", "aigc", "算力", "h100", "b200", 
                    "openai", "anthropic", "mistral", "llama", "qwen", "通义千问", 
                    "智谱", "kimi", "月之暗面", "零一万物", "百川智能", "面壁智能", "商汤", "字节跳动 ai"
                ]

                # 🏆 严格匹配 "ai" 单词 (前后需有非字母字符，防止误伤 like 'said')
                import re
                has_standalone_ai = bool(re.search(r'\bai\b', text_to_check))

                # 判定逻辑：必须包含强 AI 词 或 独立 AI 单词
                if not (any(tag in text_to_check for tag in strict_ai_keywords) or has_standalone_ai):
                    continue

                # 🛡️ 二次加固：如果标题中包含了一些模糊词（如“机器人”、“智能”），必须伴随其他更硬核的 AI 关键词
                fuzzy_keywords = ["机器人", "智能", "架构"]
                if any(fk in title for fk in fuzzy_keywords):
                     if not (any(tag in summary for tag in [k for k in strict_ai_keywords if k != "机器人"]) or has_standalone_ai):
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
