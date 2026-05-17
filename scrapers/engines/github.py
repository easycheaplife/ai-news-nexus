import requests
from bs4 import BeautifulSoup
from .base import BaseScraper
from datetime import datetime
import time
import re
from ..utils.ai import evaluator

class GitHubScraper(BaseScraper):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("github", api_url)
        # 抓取全语言和 Python 语言的 trending
        self.urls = [
            "https://github.com/trending?since=daily",
            "https://github.com/trending/python?since=daily"
        ]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

    def _get_readme(self, repo_path: str) -> str:
        """尝试抓取仓库的 README 内容"""
        # 尝试几个常见的分支名
        branches = ["main", "master"]
        for branch in branches:
            url = f"https://raw.githubusercontent.com/{repo_path}/{branch}/README.md"
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    # 截取前 4000 字，防止内容过长
                    return response.text[:4000]
            except Exception:
                continue
        return ""

    def scrape(self):
        self.logger.info("🚀 Starting GitHub Trending scraping...")
        last_id = self.get_last_id("trending")
        newest_id = None
        
        keywords = ["ai ", "llm", "gpt", "model", "agent", "deep learning", "machine learning", "diffusion", "deepseek"]

        for url in self.urls:
            try:
                time.sleep(2) # 礼貌延迟
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
                    description = p_desc.text.strip() if p_desc else "No description provided."
                    
                    # 使用库名和描述作为判断依据
                    combined_text = (title + " " + description).lower()
                    
                    if not any(k in combined_text for k in keywords):
                        continue
                        
                    # 尝试获取 stars
                    stars_tag = article.select_one('a[href$="/stargazers"]')
                    stars = stars_tag.text.strip().replace(',', '') if stars_tag else "0"

                    # 用当天日期和库名作为外部 ID，确保每天可以记录一次新的上榜
                    today_str = datetime.utcnow().strftime('%Y-%m-%d')
                    external_id = f"{today_str}_{repo_path.replace('/', '_')}"

                    if newest_id is None:
                        newest_id = today_str

                    # 🤖 获取 README 深度内容
                    readme_content = self._get_readme(repo_path)
                    full_content = (description + "\n\n" + readme_content).strip()

                    # 🖼️ 提取封面图 (从 README 中找第一张大图)
                    media_urls = []
                    # 匹配 Markdown 图片格式 ![alt](url) 或 HTML 格式 <img src="url">
                    img_match = re.search(r'!\[.*?\]\((https?://.*?\.(?:png|jpg|jpeg|gif|webp).*?)\)', readme_content) or \
                                re.search(r'<img.*?src=["\'](https?://.*?\.(?:png|jpg|jpeg|gif|webp).*?)["\']', readme_content)
                    if img_match:
                        media_urls.append(img_match.group(1))

                    # 🤖 AI 评分与理由
                    score, reason, takeaways, cluster_id, mentioned_users, trending_keywords = evaluator.evaluate(f"GitHub Repository: {title}", full_content)

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
                            "stars": stars
                        }
                    }
                    self.push_to_backend(item)
                    
            except Exception as e:
                self.logger.error(f"Error scraping GitHub: {e}")

        if newest_id:
            self.update_last_id("trending", newest_id)
