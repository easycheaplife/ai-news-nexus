import requests
from .base import BaseScraper
from datetime import datetime
from ..utils.ai import evaluator

class HNScraper(BaseScraper):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("hn", api_url)
        self.hn_api = "https://hacker-news.firebaseio.com/v0"

    def scrape(self):
        # Get top stories
        self.logger.info("📡 Scraping Hacker News top stories...")
        last_id = self.get_last_id("latest_id")
        
        response = requests.get(f"{self.hn_api}/topstories.json")
        story_ids = response.json()[:50] # Check top 50

        for story_id in story_ids:
            # 增量判断：HN ID 是递增的
            if last_id and int(story_id) <= int(last_id):
                continue
            
            # 💡 优化：发现新 ID 立即更新状态
            self.update_last_id("latest_id", str(story_id))

            try:
                story = requests.get(f"{self.hn_api}/item/{story_id}.json").json()
                if not story: continue
                
                title = story.get("title", "")
                text = story.get("text", "")
                
                # Simple AI keyword check
                keywords = ["ai ", "llm", "gpt", "neural", "machine learning", "deepseek", "openai", "claude"]
                if any(k in title.lower() for k in keywords):
                    # 🤖 AI 评分与理由
                    score, reason, takeaways, cluster_id = evaluator.evaluate(title, text)

                    item = {
                        "platform": "hn",
                        "external_id": str(story_id),
                        "title": title,
                        "content": text,
                        "url": story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                        "published_at": datetime.fromtimestamp(story.get("time")).isoformat(),
                        "score": score,
                        "reason": reason,
                        "takeaways": takeaways,
                            "cluster_id": cluster_id,
                        "metadata_json": {
                            "hn_score": story.get("score"),
                            "by": story.get("by"),
                            "descendants": story.get("descendants")
                        }
                    }
                    self.push_to_backend(item)
            except Exception as e:
                self.logger.error(f"Error fetching HN item {story_id}: {e}")
