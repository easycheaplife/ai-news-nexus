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
                text_to_check = (title + " " + content).lower()
                
                # 🛡️ 极其严格的 AI 关键词双重过滤
                import re
                strict_ai_keywords = [
                    "llm", "gpt", "大模型", "智能体", "agent", "rag", "深度学习", "机器学习", 
                    "transformer", "claude", "deepseek", "sora", "算力", "英伟达", "nvidia", 
                    "生成式", "语言模型", "向量数据库", "推理", "训练", "微调", "提示词", "prompt", 
                    "机器人", "自动驾驶", "端到端", "多模态", "aigc", "算力", "h100", "b200", 
                    "openrouter", "openai", "anthropic", "mistral", "llama", "qwen", "通义千问", 
                    "智谱", "kimi", "月之暗面", "零一万物", "百川智能", "面壁智能", "商汤", "字节跳动 ai"
                ]
                # 🚫 噪音黑名单：针对开发者社区，排除普通编程教学和基础架构内容
                blacklist = [
                    "融资", "上市", "财报", "股价", "收购", "裁员", "面试题", "面经", "javascript", 
                    "vue", "react", "css", "html", "mysql", "sql", "redis", "重构", "执行计划", 
                    "spring boot", "java 基础", "内存视角", "精通指南"
                ]

                has_standalone_ai = bool(re.search(r'\bai\b', text_to_check))
                has_core_ai = any(k in text_to_check for k in strict_ai_keywords)
                is_noise = any(k in text_to_check for k in blacklist)

                if not (has_standalone_ai or has_core_ai) or is_noise:
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
