import requests
from .base import BaseScraper
from datetime import datetime
import time


class HuggingFaceScraper(BaseScraper):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("huggingface", api_url)
        self.papers_api = "https://huggingface.co/api/daily_papers?limit=15"
        self.trending_api = "https://huggingface.co/api/trending?type=model&limit=10"

    def _fetch_readme(self, repo_id: str) -> str:
        """获取模型的 README 内容以增加上下文"""
        url = f"https://huggingface.co/{repo_id}/raw/main/README.md"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                return res.text[:2000] # 只取前 2000 字符
        except:
            pass
        return ""

    def scrape(self):
        self.logger.info("🤗 Starting Hugging Face scraping...")
        
        # 1. 抓取每日论文 (Daily Papers)
        self._scrape_papers()
        
        # 2. 抓取趋势模型 (Trending Models)
        self._scrape_models()

    def _scrape_papers(self):
        self.logger.info("📄 Scraping HF Daily Papers...")
        last_id = self.get_last_id("papers")
        
        try:
            res = requests.get(self.papers_api, timeout=20)
            if res.status_code != 200:
                self.logger.error(f"Failed to fetch papers: {res.text}")
                return
            
            papers = res.json()
            newest_id = None
            
            for item in papers:
                paper = item.get('paper')
                if not paper: continue
                
                paper_id = paper['id']
                published_at = paper['publishedAt']
                
                # 使用发布日期作为游标
                if last_id and published_at <= last_id:
                    continue
                
                if newest_id is None:
                    newest_id = published_at
                
                title = paper['title']
                summary = paper['summary']
                ai_summary = paper.get('ai_summary', '')
                upvotes = paper.get('upvotes', 0)
                
                full_content = f"{summary}\n\n[HF AI Summary]:\n{ai_summary}".strip()
                
                # AI 评估
                score, reason, takeaways, cluster_id, mentioned_users, trending_keywords = self.evaluator.evaluate(
                    f"Research Paper: {title}", 
                    full_content
                )
                
                # 提取作者
                authors = [a['name'] for a in paper.get('authors', [])]
                
                item_data = {
                    "platform": "huggingface",
                    "external_id": f"paper_{paper_id}",
                    "title": title,
                    "content": full_content,
                    "url": f"https://huggingface.co/papers/{paper_id}",
                    "published_at": published_at,
                    "score": score,
                    "reason": reason,
                    "takeaways": takeaways,
                    "cluster_id": cluster_id,
                    "mentioned_users": mentioned_users + authors,
                    "trending_keywords": trending_keywords,
                    "media_urls": [paper['thumbnail']] if paper.get('thumbnail') else [],
                    "metadata_json": {
                        "type": "paper",
                        "upvotes": upvotes,
                        "authors": authors
                    }
                }
                self.push_to_backend(item_data)
                
            if newest_id:
                self.update_last_id("papers", newest_id)
                
        except Exception as e:
            self.logger.error(f"Error scraping HF papers: {e}")

    def _scrape_models(self):
        self.logger.info("🚀 Scraping HF Trending Models...")
        last_id = self.get_last_id("models")
        
        try:
            res = requests.get(self.trending_api, timeout=20)
            if res.status_code != 200:
                self.logger.error(f"Failed to fetch models: {res.text}")
                return
            
            data = res.json()
            trending_items = data.get('recentlyTrending', [])
            newest_id = None
            
            for item in trending_items:
                repo_data = item.get('repoData')
                if not repo_data: continue
                
                repo_id = repo_data['id']
                last_modified = repo_data['lastModified']
                
                # 使用最后修改日期作为游标
                if last_id and last_modified <= last_id:
                    continue
                
                if newest_id is None:
                    newest_id = last_modified
                
                # 穿透抓取 README
                readme = self._fetch_readme(repo_id)
                pipeline_tag = repo_data.get('pipeline_tag', 'unknown')
                likes = repo_data.get('likes', 0)
                
                full_content = f"Model ID: {repo_id}\nTask: {pipeline_tag}\nLikes: {likes}\n\n[README Preview]:\n{readme}".strip()
                
                # AI 评估
                score, reason, takeaways, cluster_id, mentioned_users, trending_keywords = self.evaluator.evaluate(
                    f"HF Trending Model: {repo_id}", 
                    full_content
                )
                
                item_data = {
                    "platform": "huggingface",
                    "external_id": f"model_{repo_id}",
                    "title": f"Trending Model: {repo_id}",
                    "content": full_content,
                    "url": f"https://huggingface.co/{repo_id}",
                    "published_at": last_modified,
                    "score": score,
                    "reason": reason,
                    "takeaways": takeaways,
                    "cluster_id": cluster_id,
                    "mentioned_users": mentioned_users + [repo_data['author']],
                    "trending_keywords": trending_keywords + [pipeline_tag],
                    "media_urls": [], # 模型通常没预览图
                    "metadata_json": {
                        "type": "model",
                        "likes": likes,
                        "pipeline_tag": pipeline_tag,
                        "author": repo_data['author']
                    }
                }
                self.push_to_backend(item_data)
                
            if newest_id:
                self.update_last_id("models", newest_id)
                
        except Exception as e:
            self.logger.error(f"Error scraping HF models: {e}")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    scraper = HuggingFaceScraper()
    scraper.scrape()
