import requests
from .base import BaseScraper
from datetime import datetime
from ..utils.ai import evaluator
from ..utils.link_scraper import scrape_link_content
from bs4 import BeautifulSoup

class HNScraper(BaseScraper):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("hn", api_url)
        self.hn_api = "https://hacker-news.firebaseio.com/v0"

    def _get_top_comments(self, story_data: dict, limit: int = 5) -> str:
        """获取 HN 帖子的高赞评论"""
        kids = story_data.get("kids", [])
        if not kids:
            return ""
        
        comments = []
        # 只取前 15 个子节点进行尝试，防止请求过多
        for comment_id in kids[:15]:
            try:
                res = requests.get(f"{self.hn_api}/item/{comment_id}.json", timeout=5)
                c_data = res.json()
                if c_data and not c_data.get("deleted") and not c_data.get("dead"):
                    text = c_data.get("text", "").strip()
                    # 过滤掉太短或没意义的评论
                    if len(text) > 60:
                        # 清理 HTML 标签
                        clean_text = BeautifulSoup(text, "html.parser").get_text()
                        comments.append(f"💬 by {c_data.get('by')}: {clean_text}")
                
                if len(comments) >= limit:
                    break
            except Exception:
                continue
        
        if comments:
            return "\n\n--- HN Top Discussions ---\n" + "\n\n".join(comments)
        return ""

    def scrape(self):
        self.logger.info("📡 Scraping Hacker News top stories...")
        try:
            # 获取最新 top stories
            top_stories = requests.get(f"{self.hn_api}/topstories.json").json()
            # 记录本次抓取的最新 ID 
            newest_id = str(top_stories[0])
            last_id = self.get_last_id("latest_id")

            # 遍历前 50 条
            for story_id in top_stories[:50]:
                date_str = "N/A"
                self.logger.info(f"🔗 Processing Item ID: {story_id} | Date: {date_str}")
                if last_id and int(story_id) <= int(last_id):
                    self.logger.info("⏱️ Reached last seen HN story, stopping.")
                    break

                try:
                    story = requests.get(f"{self.hn_api}/item/{story_id}.json").json()
                    if not story: continue
                    
                    title = story.get("title", "")
                    text = story.get("text", "")
                    
                    # Simple AI keyword check
                    keywords = [
                        "ai ", "llm", "gpt", "neural", "machine learning", "deepseek", 
                        "openai", "claude", "anthropic", "mistral", "llama", "sora", 
                        "gemini", "groq", "opus", "sonnet", "haiku"
                    ]
                    if any(k in title.lower() for k in keywords):

                        # 🧵 获取深度评论
                        comments_text = self._get_top_comments(story)
                        
                        # 🔗 获取外链内容摘要 (针对只有标题和链接的帖子)
                        link_context = ""
                        if story.get("url"):
                            link_context = scrape_link_content(story["url"])
                        
                        full_content = f"{text}\n\n{link_context}\n\n{comments_text}".strip()

                        # 🤖 AI 评分与理由
                        score, reason, takeaways, cluster_id, mentioned_users, trending_keywords = evaluator.evaluate(title, full_content)

                        item = {
                            "platform": "hn",
                            "external_id": str(story_id),
                            "title": title,
                            "content": full_content,
                            "url": story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                            "published_at": datetime.fromtimestamp(story.get("time")).isoformat(),
                            "score": score,
                            "reason": reason,
                            "takeaways": takeaways,
                            "cluster_id": cluster_id,
                            "mentioned_users": mentioned_users,
                            "trending_keywords": trending_keywords,
                            "metadata_json": {
                                "hn_score": story.get("score"),
                                "by": story.get("by"),
                                "descendants": story.get("descendants")
                            }
                        }
                        self.push_to_backend(item)
                except Exception as e:
                    self.logger.error(f"Error fetching HN item {story_id}: {e}")
            
            # 更新游标
            if newest_id:
                self.update_last_id("latest_id", newest_id)

        except Exception as e:
            self.logger.error(f"Error scraping Hacker News: {e}")
