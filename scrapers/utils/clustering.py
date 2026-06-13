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
        Fetches recent high-value news (last 24 hours) and uses AI to group them into topic clusters.
        """
        logger.info("🧠 Starting AI News Clustering phase (Last 24 hours)...")
        
        try:
            # 🕒 核心优化：聚合过去 24 小时的新闻，而不仅仅是今天起始，确保凌晨运行也能抓到数据
            from datetime import datetime, timedelta
            start_time = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            
            # 1. Fetch recent news items (limit to items from last 24h)
            response = requests.get(
                f"{self.api_url}/news/", 
                params={"limit": 500, "start_date": start_time}, 
                timeout=20
            )
                
            if response.status_code != 200:
                logger.error(f"Failed to fetch news: {response.text}")
                return

            resp_json = response.json()
            news_items = resp_json.get("items", []) if isinstance(resp_json, dict) else resp_json
            
            if not news_items:
                logger.info("No fresh news items found in last 24h for clustering.")
                return

            # Filter items that are relevant (score >= 60)
            target_news = [n for n in news_items if n.get('score', 0) >= 60]
            if len(target_news) < 3:
                logger.info("Not enough fresh high-quality news (need at least 3) to perform resonance clustering.")
                return

            logger.info(f"📊 Found {len(target_news)} candidate news items. Preparing AI prompt...")

            # 2. Prepare payload for AI
            news_payload = []
            # 🚀 扩容：发送前 80 条最相关的资讯给 AI，获得更广的视野
            for n in target_news[:80]: 
                platform_str = f"[{n.get('platform', 'unknown').upper()}]"
                news_payload.append({
                    "id": n['id'],
                    "source": platform_str,
                    "title": n['title'],
                    "summary": n.get('reason', '')[:120] 
                })

            prompt = f"""
            你是一个顶级 AI 战略分析师。你的任务是分析过去 24 小时全球 AI 圈的资讯，并将讨论“同一件事”的条目进行聚合（聚类）。

            **聚类标准：**
            1. 讨论的是同一个技术项目（如 Llama 3, GPT-4o）。
            2. 讨论的是同一个行业大事件（如 某巨头裁员、某实验室发布新论文）。
            3. 讨论的是同一个极其具体的技术趋势（如 Flash-Attention 优化、MCP 协议落地）。

            **资讯列表:**
            {json.dumps(news_payload, ensure_ascii=False, indent=2)}

            **输出格式：**
            请返回严格的 JSON 数组格式（不要包含 markdown 代码块标记，只返回 JSON 数组）：
            [
              {{
                "title": "高度概括、专业且抓人眼球的标题",
                "summary": "一句话深度综述各方视角，体现共振（Resonance）的价值",
                "news_ids": [id1, id2, id3] // 必须是原始数据中的数字 ID。只有包含 2 个及以上 ID 的聚类才返回。
              }}
            ]
            
            如果你认为某些资讯是完全孤立的，请忽略它们。优先输出共鸣最强（跨平台、跨来源）的话题。
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
