import os
import json
import logging
import requests
from datetime import datetime
from typing import List, Dict, Any
from .ai import evaluator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("asset_engine")

class AssetEngine:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url

    def process_daily_assets(self):
        """
        核心逻辑：扫描今日高分资讯，提取关键词并同步至百科知识库。
        """
        logger.info("🏺 Starting Knowledge Asset Curation...")
        
        try:
            # 1. 获取最近 24 小时的高分资讯 (Score >= 80)
            from datetime import timedelta
            start_time = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            
            res = requests.get(
                f"{self.api_url}/news/", 
                params={"limit": 200, "min_score": 80, "start_date": start_time},
                timeout=15
            )
            
            if res.status_code != 200:
                logger.error(f"Failed to fetch news for asset curation: {res.text}")
                return

            items = res.json().get("items", [])
            if not items:
                logger.info("No high-score news found in the last 24h to extract assets.")
                return

            # 2. 汇总所有的关键词
            raw_keywords = []
            for item in items:
                if item.get('trending_keywords'):
                    raw_keywords.extend(item['trending_keywords'])
            
            if not raw_keywords:
                logger.info("No keywords found in recent news items.")
                return

            # 去重并计数
            from collections import Counter
            kw_counts = Counter([k.strip() for k in raw_keywords if k and len(k.strip()) > 1])
            
            logger.info(f"📊 Found {len(kw_counts)} candidate keywords. Processing top ones...")

            # 3. 处理 Top 15 个高频词
            for kw, count in kw_counts.most_common(15):
                self._sync_keyword_to_wiki(kw, count, items)

            logger.info("✅ Knowledge Asset Curation completed.")

        except Exception as e:
            logger.error(f"Error during asset curation: {e}")

    def _sync_keyword_to_wiki(self, keyword: str, daily_heat: int, source_items: List[Dict]):
        """将单个关键词同步到百科，若是新词则生成定义"""
        try:
            # 1. 检查是否存在
            res = requests.get(f"{self.api_url}/api/assets/terms", params={"keyword": keyword}, timeout=5)
            existing_term = None
            if res.status_code == 200:
                terms = res.json()
                # 寻找精确匹配
                for t in terms:
                    if t['keyword'].lower() == keyword.lower():
                        existing_term = t
                        break

            # 获取该词相关的资讯 ID
            related_ids = [i['id'] for i in source_items if keyword in (i.get('trending_keywords') or [])][:5]

            if existing_term:
                # 2. 已存在：更新热度与趋势
                new_heat = existing_term['heat_score'] + daily_heat
                trend = existing_term.get('trend_json') or {}
                today_str = datetime.now().strftime("%Y-%m-%d")
                trend[today_str] = daily_heat
                
                requests.patch(
                    f"{self.api_url}/api/assets/terms/{existing_term['id']}",
                    json={
                        "heat_score": new_heat,
                        "trend_json": trend,
                        "related_news_ids": list(set(existing_term.get('related_news_ids', []) + related_ids))[:8]
                    },
                    timeout=5
                )
                logger.info(f"📈 Updated existing term: {keyword} (New Heat: {new_heat})")
            else:
                # 3. 新词：通过 AI 生成定义
                logger.info(f"✨ New tech term detected: {keyword}. Generating definition...")
                definition, category = self._generate_definition_with_ai(keyword, source_items)
                
                if definition:
                    payload = {
                        "keyword": keyword,
                        "category": category,
                        "description": definition,
                        "heat_score": daily_heat,
                        "trend_json": {datetime.now().strftime("%Y-%m-%d"): daily_heat},
                        "related_news_ids": related_ids
                    }
                    requests.post(f"{self.api_url}/api/assets/terms", json=payload, timeout=10)
                    logger.info(f"🆕 Created new wiki term: {keyword} ({category})")

        except Exception as e:
            logger.error(f"Failed to sync keyword {keyword}: {e}")

    def _generate_definition_with_ai(self, keyword: str, items: List[Dict]):
        """调用 AI 生成该名词的专业定义"""
        # 寻找包含该词的背景内容
        context = ""
        for i in items:
            if keyword in (i.get('trending_keywords') or []):
                context += f"- {i['title']}: {i.get('reason', '')[:150]}\n"
        
        prompt = f"""
        你是一个资深的 AI 技术百科编辑。请为以下技术名词编写一个专业、准确且简洁的定义。

        技术名词: {keyword}
        近期提及背景:
        {context}

        请返回以下 JSON 格式：
        {{
          "category": "所属类别（模型/算力/框架/应用/趋势 选其一）",
          "definition": "300字以内的专业定义，描述其核心原理、主要价值及为何在近期受到关注。"
        }}
        """
        
        ai_res = evaluator.generate_content(prompt)
        if not ai_res: return None, "general"
        
        try:
            text = ai_res.text.strip()
            if "```json" in text: text = text.split("```json")[1].split("```")[0].strip()
            data = json.loads(text)
            return data.get('definition'), data.get('category', 'general')
        except:
            return None, "general"

if __name__ == "__main__":
    api_url = os.getenv("SCRAPER_API_URL", "http://localhost:8000")
    engine = AssetEngine(api_url)
    engine.process_daily_assets()
