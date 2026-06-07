import requests
from datetime import datetime
from .base import BaseScraper

class JuejinScraper(BaseScraper):
    """
    Juejin (掘金) AI 频道引擎
    专注于 AI 开发、RAG 实战和技术深度。
    """
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__(platform="juejin", api_url=api_url, region="cn")
        self.api_endpoint = "https://api.juejin.cn/recommend_api/v1/article/recommend_all_feed"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Content-Type": "application/json"
        }

    def scrape(self):
        self.logger.info("Fetching latest AI articles from Juejin...")
        
        # 掘金 AI 频道的分类 ID (6809635626661445640 是 AI 频道的常客)
        payload = {
            "id_type": 2,
            "client_type": 2608,
            "sort_type": 300, # 300 为“最新”
            "cursor": "0",
            "limit": 20,
            "cate_id": "6809635626661445640" # AI 频道 ID
        }

        try:
            response = requests.post(self.api_endpoint, json=payload, headers=self.headers, timeout=15)
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch Juejin: {response.status_code}")
                return

            data = response.json()
            items = data.get("data", [])
            
            for item in items:
                info = item.get("item_info", {})
                if not info: continue
                
                article = info.get("article_info", {})
                author = info.get("author_user_info", {}).get("user_name", "掘金")
                
                title = article.get("title", "")
                content = article.get("brief_content") or title
                
                # 🛡️ 严格 AI 关键词过滤 (针对掘金这种综合社区)
                ai_keywords = [
                    "ai", "llm", "gpt", "大模型", "智能体", "agent", "rag", "深度学习", 
                    "机器学习", "神经网络", "transformer", "claude", "deepseek", "sora", 
                    "stable diffusion", "midjourney", "算力", "英伟达", "nvidia", "智算"
                ]
                if not any(k in title.lower() or k in content.lower() for k in ai_keywords):
                    continue

                external_id = str(article.get("article_id"))
                pub_time = int(article.get("ctime")) # 字符串秒级时间戳
                
                dt = datetime.fromtimestamp(pub_time) if pub_time else None

                if not self.is_within_window(dt):
                    continue

                news_item = {
                    "platform": "juejin",
                    "external_id": external_id,
                    "title": title,
                    "content": content,
                    "url": f"https://juejin.cn/post/{external_id}",
                    "author": author,
                    "published_at": dt.isoformat() if dt else datetime.utcnow().isoformat(),
                    "score": 0,
                    "raw_data": {"juejin_category": article.get("category_name")}
                }
                
                self.push_to_backend(news_item)

        except Exception as e:
            self.logger.error(f"Error scraping Juejin: {e}")
