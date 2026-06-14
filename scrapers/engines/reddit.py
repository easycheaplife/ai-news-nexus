import requests
import time
import feedparser
import concurrent.futures
from .base import BaseScraper
from datetime import datetime
from ..utils.ai import evaluator
from ..utils.link_scraper import scrape_link_content
from bs4 import BeautifulSoup

class RedditScraper(BaseScraper):
    """
    Reddit 采集引擎 (RSS 增强版)
    由于 Reddit 官方 JSON API 对数据中心 IP 进行了严格的 403 封锁，
    本引擎改用官方 RSS 订阅源 (.rss) 进行抓取，稳定性显著提升。
    """
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("reddit", api_url)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _extract_post_id(self, guid: str) -> str:
        """从 guid (如 t3_1u4zbld) 中提取 ID"""
        if '_' in guid:
            return guid.split('_')[-1]
        return guid

    def scrape(self):
        # 核心 AI 相关子版块
        subs = ["MachineLearning", "ArtificialInteligence", "OpenAI", "LocalLLaMA", "ChatGPTCoding", "StableDiffusion"]
        
        self.logger.info(f"🚀 Starting Reddit RSS scraping for {len(subs)} subreddits...")

        for sub in subs:
            last_timestamp = self.get_last_id(sub)
            # 使用 .rss 后缀绕过 JSON API 403 限制
            url = f"https://www.reddit.com/r/{sub}/new/.rss"
            
            try:
                # 随机延迟，防止触发 WAF
                time.sleep(random.uniform(2, 5))
                
                response = requests.get(url, headers=self.headers, timeout=15)
                if response.status_code != 200:
                    self.logger.error(f"❌ Failed to fetch r/{sub} RSS: HTTP {response.status_code}")
                    continue

                feed = feedparser.parse(response.content)
                if not feed.entries:
                    self.logger.warning(f"⚠️ No entries found in r/{sub} RSS feed.")
                    continue

                newest_timestamp = None
                tasks = []

                for entry in feed.entries:
                    # 提取时间戳
                    published_at = entry.get('published_parsed')
                    if not published_at:
                        continue
                    
                    # 转换为时间戳字符串用于游标对比
                    timestamp_val = int(time.mktime(published_at))
                    timestamp_str = str(timestamp_val)

                    # 增量判断
                    if last_timestamp and timestamp_val <= int(last_timestamp):
                        break
                    
                    if newest_timestamp is None:
                        newest_timestamp = timestamp_str

                    # 基础信息提取
                    post_id = self._extract_post_id(entry.id)
                    title = entry.title
                    link = entry.link
                    
                    # 过滤低质量标题（如太短或纯求助）
                    if len(title) < 15 or any(q in title.lower() for q in ["help", "error", "question", "why does"]):
                        continue

                    # 将 entry 数据包装成后续处理需要的格式
                    p_data = {
                        "id": post_id,
                        "title": title,
                        "url": link,
                        "published_at": datetime.fromtimestamp(timestamp_val),
                        "summary_html": entry.get('summary', ''),
                        "author": entry.get('author', 'Unknown')
                    }
                    tasks.append((p_data, sub))

                def process_post(p_data, sub):
                    # 🧩 内容提取与清理
                    soup = BeautifulSoup(p_data['summary_html'], 'html.parser')
                    # 移除表格、链接占位符等杂质
                    for tag in soup.find_all(['table', 'thead', 'tbody']):
                        tag.decompose()
                    
                    raw_text = soup.get_text(separator='\n').strip()
                    
                    # 🔗 获取外链内容摘要 (如果存在)
                    # 尝试从摘要中抠出外部链接，或者直接使用 p_data['url'] 如果它不是 reddit 域名
                    external_url = None
                    if 'reddit.com/r/' not in p_data['url']:
                        external_url = p_data['url']
                    else:
                        # 查找摘要中的第一个非 reddit 链接
                        for a in soup.find_all('a', href=True):
                            if 'reddit.com' not in a['href'] and a['href'].startswith('http'):
                                external_url = a['href']
                                break
                    
                    link_context = ""
                    if external_url and not any(external_url.lower().endswith(ext) for ext in ['.jpg', '.png', '.gif', '.jpeg', '.pdf']):
                        link_context = scrape_link_content(external_url)

                    full_content = f"{raw_text}\n\n{link_context}".strip()
                    
                    if len(full_content) < 50 and len(p_data['title']) < 40:
                        return None

                    # 🖼️ 媒体提取 (RSS 版主要靠摘要中的 img 标签)
                    media_urls = []
                    for img in soup.find_all('img'):
                        src = img.get('src')
                        if src and 'http' in src and 'static' not in src:
                            media_urls.append(src)

                    # 🤖 AI 评分
                    try:
                        score, reason, takeaways, cluster_id, users, keywords = evaluator.evaluate(p_data['title'], full_content)
                    except Exception as e:
                        self.logger.error(f"Error evaluating Reddit post {p_data['id']}: {e}")
                        return None

                    return {
                        "platform": "reddit",
                        "external_id": p_data['id'],
                        "title": p_data['title'],
                        "content": full_content,
                        "url": p_data['url'],
                        "published_at": p_data['published_at'].isoformat(),
                        "score": score,
                        "reason": reason,
                        "takeaways": takeaways,
                        "cluster_id": cluster_id,
                        "mentioned_users": users,
                        "trending_keywords": keywords,
                        "media_urls": list(set(media_urls)),
                        "metadata_json": {
                            "subreddit": sub,
                            "author": p_data['author'],
                            "source": "rss_enhanced"
                        }
                    }

                if tasks:
                    self.logger.info(f"⚡ Processing {len(tasks)} new items in r/{sub} via RSS...")
                    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                        future_to_post = {executor.submit(process_post, p_data, sub): p_data for p_data, sub in tasks}
                        for future in concurrent.futures.as_completed(future_to_post):
                            try:
                                item = future.result()
                                if item:
                                    self.push_to_backend(item)
                            except Exception as e:
                                self.logger.error(f"Post processing error: {e}")

                if newest_timestamp:
                    self.update_last_id(sub, newest_timestamp)

            except Exception as e:
                self.logger.error(f"Error scraping Reddit r/{sub}: {e}")

import random # 补充缺失的导入
