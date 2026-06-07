import os
import json
import logging
import requests
from typing import List, Dict, Any
from .ai import evaluator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("clustering_engine")

class ClusteringEngine:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url

    def run_clustering(self):
        """
        Fetches recent high-value news (published today) and uses AI to group them into topic clusters.
        """
        logger.info("🧠 Starting AI News Clustering phase (Today's news only)...")
        
        try:
            # 🕒 核心优化：只对今天发布的新闻进行聚类，确保共振话题的实时性
            from datetime import datetime
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            
            # 1. Fetch recent news items (limit to items published today)
            response = requests.get(
                f"{self.api_url}/news/", 
                params={"limit": 200, "start_date": today_start}, 
                timeout=15
            )
                
            if response.status_code != 200:
                logger.error(f"Failed to fetch news: {response.text}")
                return

            resp_json = response.json()
            news_items = resp_json.get("items", []) if isinstance(resp_json, dict) else resp_json
            
            if not news_items:
                logger.info("No fresh news items found today for clustering.")
                return

            # Filter items that are relevant (score >= 60)
            target_news = [n for n in news_items if n.get('score', 0) >= 60]
            if len(target_news) < 2:
                logger.info("Not enough fresh high-quality news to perform resonance clustering.")
                return

            logger.info(f"📊 Found {len(target_news)} fresh candidate news items. Preparing AI prompt...")

            # 2. Prepare payload for AI
            news_payload = []
            for n in target_news[:50]: # limit to top 50 to avoid token limits
                platform_str = f"[{n.get('platform', 'unknown').upper()}]"
                news_payload.append({
                    "id": n['id'],
                    "source": platform_str,
                    "title": n['title'],
                    "summary": n.get('reason', '')[:100] # Use reason or truncated content as summary
                })

            prompt = f"""
            你是一个资深的 AI 行业分析师。这是过去 24 小时 AI 领域的近期热门资讯。
            请将讨论同一核心技术、同一项目或同一重大事件的条目进行聚类。

            资讯列表:
            {json.dumps(news_payload, ensure_ascii=False, indent=2)}

            请返回严格的 JSON 格式（不要包含 markdown 代码块标记，只返回 JSON 数组）：
            [
              {{
                "title": "聚类话题的标题（例如：Meta 宣布 Llama 3 开源）",
                "summary": "一句话总结各方观点（例如：Twitter欢呼开源，HN在讨论其评测细节）",
                "news_ids": [12, 34, 55] // 属于该话题的资讯 ID 列表
              }}
            ]
            如果某条资讯是独立的，不需要归入任何聚类，直接忽略即可。只返回至少包含 2 条资讯的聚类。
            """

            # 3. Request clustering from AI
            ai_response = evaluator.generate_content(prompt)
            if not ai_response:
                logger.error("AI clustering generation failed or returned empty.")
                return

            text = ai_response.text.strip()
            # Clean markdown code blocks if any
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            try:
                clusters = json.loads(text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI clustering JSON: {e}\nRaw output: {text}")
                return

            if not clusters:
                logger.info("AI returned no clusters.")
                return

            logger.info(f"✨ AI generated {len(clusters)} valid clusters. Sending to backend...")

            # 4. Save clusters to backend
            save_res = requests.post(
                f"{self.api_url}/clusters/batch", 
                json={"clusters": clusters},
                timeout=15
            )

            if save_res.status_code in (200, 201):
                logger.info("✅ Clusters successfully saved to backend!")
            else:
                logger.error(f"Failed to save clusters: {save_res.text}")


        except Exception as e:
            logger.error(f"Error during clustering phase: {e}")

if __name__ == "__main__":
    api_url = os.getenv("SCRAPER_API_URL", "http://localhost:8000")
    engine = ClusteringEngine(api_url)
    engine.run_clustering()
