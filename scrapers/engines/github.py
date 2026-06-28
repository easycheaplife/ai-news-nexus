import requests
from bs4 import BeautifulSoup
import feedparser
from .base import BaseScraper
from datetime import datetime
import time
import re


class GitHubScraper(BaseScraper):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("github", api_url)
        # 抓取全语言和 Python 语言的 trending
        self.trending_urls = [
            "https://github.com/trending?since=daily",
            "https://github.com/trending/python?since=daily"
        ]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
        }
        self.keywords = ["ai ", "llm", "gpt", "model", "agent", "deep learning", "machine learning", "diffusion", "deepseek", "transformer"]

    def _get_readme(self, repo_path: str) -> str:
        """尝试抓取仓库的 README 内容"""
        branches = ["main", "master"]
        for branch in branches:
            url = f"https://raw.githubusercontent.com/{repo_path}/{branch}/README.md"
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    return response.text[:4000]
            except Exception:
                continue
        return ""

    def scrape_trending(self):
        self.logger.info("🚀 Starting GitHub Trending scraping...")
        last_id = self.get_last_id("trending")
        newest_id = None
        
        for url in self.trending_urls:
            try:
                time.sleep(2) 
                response = requests.get(url, headers=self.headers, timeout=15)
                if response.status_code != 200:
                    self.logger.error(f"❌ Failed to fetch GitHub Trending: {response.status_code}")
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')
                articles = soup.select('article.Box-row')

                for article in articles:
                    h2 = article.select_one('h2.h3 a')
                    if not h2: continue
                    
                    repo_path = h2['href'].strip('/')
                    title = repo_path
                    full_url = f"https://github.com/{repo_path}"
                    
                    p_desc = article.select_one('p.col-9')
                    description = p_desc.text.strip() if p_desc else ""
                    
                    combined_text = (title + " " + description).lower()
                    if not any(k in combined_text for k in self.keywords):
                        continue
                        
                    stars_tag = article.select_one('a[href$="/stargazers"]')
                    stars = stars_tag.text.strip().replace(',', '') if stars_tag else "0"

                    today_str = datetime.utcnow().strftime('%Y-%m-%d')
                    external_id = f"trending_{today_str}_{repo_path.replace('/', '_')}"

                    if newest_id is None:
                        newest_id = today_str

                    readme_content = self._get_readme(repo_path)
                    full_content = (description + "\n\n" + readme_content).strip()

                    score, reason, takeaways, cluster_id, mentioned_users, trending_keywords = self.evaluator.evaluate(f"GitHub Repository: {title}", full_content)

                    item = {
                        "platform": "github",
                        "external_id": external_id,
                        "title": f"🐙 {title}",
                        "content": full_content,
                        "url": full_url,
                        "published_at": datetime.utcnow().isoformat(),
                        "score": score,
                        "reason": reason,
                        "takeaways": takeaways,
                        "cluster_id": cluster_id,
                        "mentioned_users": mentioned_users,
                        "trending_keywords": trending_keywords,
                        "metadata_json": {
                            "author": title.split('/')[0],
                            "stars": stars,
                            "type": "trending"
                        }
                    }
                    self.push_to_backend(item)
                    
            except Exception as e:
                self.logger.error(f"Error scraping GitHub Trending: {e}")

        if newest_id:
            self.update_last_id("trending", newest_id)

    def scrape_targets(self):
        self.logger.info("🎯 Starting GitHub Targets scraping via Atom feeds...")
        try:
            res = requests.get(f"{self.api_url}/targets/", params={"platform": "github", "is_active": True})
            if res.status_code != 200:
                self.logger.error(f"Failed to fetch targets: {res.text}")
                return
            
            targets = res.json()
            for target in targets:
                handle = target['handle']
                feed_url = f"https://github.com/{handle}.atom"
                self.logger.info(f"📡 Checking feed for {handle}: {feed_url}")
                
                last_id = self.get_last_id(f"target_{handle}")
                feed = feedparser.parse(feed_url)
                
                if not feed.entries:
                    continue

                newest_id = feed.entries[0].id if feed.entries else None
                
                for entry in feed.entries:
                    if entry.id == last_id:
                        break
                    
                    # 识别 repository 相关的事件 (PushEvent, CreateEvent 等)
                    # GitHub Atom feed 的 title 格式通常是 "user pushed to repo" 或 "user created a repository"
                    # 我们主要关心新的 push 或创建
                    title_text = entry.title
                    
                    # 提取仓库名称，格式通常是 handle/repo
                    # 例子: "huggingface pushed to main in huggingface/transformers"
                    repo_match = re.search(r'in ([\w\-\.]+/[\w\-\.]+)', title_text) or \
                                 re.search(r'created a repository ([\w\-\.]+/[\w\-\.]+)', title_text)
                    
                    if not repo_match:
                        continue
                    
                    repo_path = repo_match.group(1)
                    repo_url = f"https://github.com/{repo_path}"
                    
                    # 避免对同一个 handle 的同一个 repo 在同一次抓取中重复处理
                    external_id = f"target_{repo_path.replace('/', '_')}_{entry.updated}"
                    
                    self.logger.info(f"✨ Found update in {repo_path}")
                    
                    # 获取 Readme 进行 AI 评估
                    readme_content = self._get_readme(repo_path)
                    
                    # 过滤: 如果仓库名或 Readme 不含关键词，则跳过
                    combined_text = (repo_path + " " + readme_content[:500]).lower()
                    if not any(k in combined_text for k in self.keywords):
                        self.logger.info(f"⏩ Skipping {repo_path} (No AI keywords found)")
                        continue

                    score, reason, takeaways, cluster_id, mentioned_users, trending_keywords = self.evaluator.evaluate(f"GitHub Target Update: {repo_path}", readme_content)

                    item = {
                        "platform": "github",
                        "external_id": external_id,
                        "title": f"🐙 {repo_path}",
                        "content": readme_content,
                        "url": repo_url,
                        "published_at": entry.updated if hasattr(entry, 'updated') else datetime.utcnow().isoformat(),
                        "score": score,
                        "reason": reason,
                        "takeaways": takeaways,
                        "cluster_id": cluster_id,
                        "mentioned_users": mentioned_users,
                        "trending_keywords": trending_keywords,
                        "metadata_json": {
                            "author": handle,
                            "repo_path": repo_path,
                            "type": "target_feed"
                        }
                    }
                    self.push_to_backend(item)

                if newest_id:
                    self.update_last_id(f"target_{handle}", newest_id)
                    self._save_state()
                    
        except Exception as e:
            self.logger.error(f"Error scraping GitHub Targets: {e}")

    def scrape(self):
        self.scrape_trending()
        self.scrape_targets()
