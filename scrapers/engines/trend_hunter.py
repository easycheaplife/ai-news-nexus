import requests
import feedparser
import urllib.parse
from datetime import datetime, timedelta
from .base import BaseScraper

from ..utils.link_scraper import scrape_link_content

class TrendHunterScraper(BaseScraper):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("search", api_url)
        # Google News RSS Search 模板
        self.search_base = "https://news.google.com/rss/search?q={query}+when:24h&hl=en-US&gl=US&ceid=US:en"

    def _get_vetted_keywords(self) -> list:
        """从发现池获取已验证的技术关键词"""
        try:
            # 优先选择状态为 vetted 的词，如果没有则尝试评分极高的 pending 词
            response = requests.get(f"{self.api_url}/discovery/?type=keyword", timeout=10)
            if response.status_code == 200:
                items = response.json()
                # 简单逻辑：取最近发现的 5 个关键词进行追踪
                return [item['value'] for item in items if item['type'] == 'keyword'][:5]
        except Exception as e:
            self.logger.warning(f"Failed to fetch keywords from pool: {e}")
        return ["AI Model", "LLM optimization"] # 兜底词

    def scrape(self):
        keywords = self._get_vetted_keywords()
        self.logger.info(f"🔍 Trend Hunter starting with keywords: {keywords}")

        for kw in keywords:
            query = urllib.parse.quote(kw)
            url = self.search_base.format(query=query)
            
            try:
                feed = feedparser.parse(url)
                # 针对每个搜索结果，我们只取前 3 条最高质量的
                for entry in feed.entries[:3]:
                    link = entry.link
                    date_str = entry.get('published', 'N/A')
                    self.logger.info(f"🔗 Processing Item ID: {link} | Date: {date_str}")
                    # 避免重复抓取主站
                    if any(domain in link for domain in ['twitter.com', 'reddit.com', 'github.com']):
                        continue

                    self.logger.info(f"🌍 Found trend link: {link}")
                    
                    # 穿透抓取正文
                    article_content = scrape_link_content(link)
                    if not article_content: continue

                    # 🤖 AI 评估该趋势内容
                    title = entry.title
                    score, reason, takeaways, cluster_id, _, _ = self.evaluator.evaluate(f"Trend Search [{kw}]: {title}", article_content)

                    # 只有真正高质量的才入库
                    if score < 75: continue

                    item = {
                        "platform": "search",
                        "external_id": f"search_{hash(link)}",
                        "title": f"🌐 {title}",
                        "content": article_content,
                        "url": link,
                        "published_at": datetime(*entry.published_parsed[:6]).isoformat(),
                        "score": score,
                        "reason": reason,
                        "takeaways": takeaways,
                        "cluster_id": cluster_id or kw, # 如果 AI 没给聚类，使用搜索词作为聚类
                        "metadata_json": {
                            "keyword": kw,
                            "source": entry.get('source', {}).get('title', 'Web')
                        }
                    }
                    self.push_to_backend(item)

            except Exception as e:
                self.logger.error(f"Error hunting trend for '{kw}': {e}")
