import requests
import feedparser
from .base import BaseScraper
from datetime import datetime
from ..utils.ai import evaluator

class ArxivScraper(BaseScraper):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("arxiv", api_url)
        # 获取 cs.AI 最新论文
        self.api_url_base = "http://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=20"

    def scrape(self):
        self.logger.info("🎓 Starting ArXiv scraping...")
        last_id = self.get_last_id("cs_ai")
        
        try:
            feed = feedparser.parse(self.api_url_base)
            newest_id = None
            
            for entry in feed.entries:
                # ArXiv ID 通常类似于 http://arxiv.org/abs/2605.12345v1
                paper_id = entry.id.split('/abs/')[-1]
                
                # 增量判断 (ArXiv ID 大多是时间递增的，可以按字符串比较)
                if last_id and paper_id <= last_id:
                    self.logger.info("⏱️ Reached last seen ArXiv paper, stopping.")
                    break
                    
                if newest_id is None:
                    newest_id = paper_id
                    
                title = entry.title.replace('\n', ' ')
                abstract = entry.summary.replace('\n', ' ')
                authors = [author.name for author in entry.authors]
                pdf_link = next((link.href for link in entry.links if link.get('title') == 'pdf'), entry.link)

                # 🤖 AI 评分与理由
                score, reason, takeaways, cluster_id, mentioned_users, trending_keywords = evaluator.evaluate(f"ArXiv Paper: {title}", abstract)

                item = {
                    "platform": "arxiv",
                    "external_id": paper_id,
                    "title": f"📄 {title}",
                    "content": abstract,
                    "url": entry.link,
                    "published_at": datetime(*entry.published_parsed[:6]).isoformat(),
                    "score": score,
                    "reason": reason,
                    "takeaways": takeaways,
                            "cluster_id": cluster_id,
                            "mentioned_users": mentioned_users,
                            "trending_keywords": trending_keywords,
                    "metadata_json": {
                        "author": ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else ""),
                        "pdf_url": pdf_link
                    }
                }
                self.push_to_backend(item)
                
            if newest_id:
                self.update_last_id("cs_ai", newest_id)
                
        except Exception as e:
            self.logger.error(f"Error scraping ArXiv: {e}")
