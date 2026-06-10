import requests
import logging
from datetime import datetime
from .base import BaseScraper
import os

class AIHotScraper(BaseScraper):
    """
    AI HOT (aihot.virxact.com) 聚合引擎
    国内 AI 资讯的“元信源”，聚合了公众号、主流媒体等。
    """
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__(platform="aihot", api_url=api_url, region="cn")
        self.ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        self.base_url = "https://aihot.virxact.com/api/public/items"

    def scrape(self):
        self.logger.info("Fetching latest AI HOT items...")
        params = {
            "mode": "selected",
            "take": 50
        }
        headers = {"User-Agent": self.ua}
        
        try:
            response = requests.get(self.base_url, params=params, headers=headers, timeout=10)
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch AI HOT: {response.status_code}")
                return

            data = response.json()
            items = data.get("items", [])
            
            for item in items:
                title = item.get("title", "")
                summary = item.get("summary") or title
                text_to_check = (title + " " + summary).lower()

                # 🛡️ 严格 AI 关键词双重过滤
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

                # 转换格式以匹配后端 schema
                external_id = item.get("id")
                published_at_str = item.get("publishedAt")
                
                dt = None
                if published_at_str:
                    try:
                        dt = datetime.fromisoformat(published_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
                    except Exception as e:
                        self.logger.error(f"Error parsing date {published_at_str}: {e}")

                # 检查时间窗口
                if not self.is_within_window(dt):
                    continue

                news_item = {
                    "platform": "aihot",
                    "external_id": external_id,
                    "title": item.get("title"),
                    "content": item.get("summary") or item.get("title"),
                    "url": item.get("url"),
                    "author": item.get("source"),
                    "published_at": published_at_str,
                    "score": 0,  # AI HOT 已经是精选，后端会重新评估
                    "raw_data": item
                }
                
                self.push_to_backend(news_item)
                
        except Exception as e:
            self.logger.error(f"Error scraping AI HOT: {e}")
