import os
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any
from .ai import evaluator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("asset_engine")

class AssetEngine:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url

    def process_daily_assets(self, force_report: bool = False):
        """
        核心逻辑：
        1. 扫描今日高分资讯，同步至百科 (Terms)。
        2. 检查并生成周期性白皮书 (Reports)。
        """
        # --- Step 1: 每日词条沉淀 ---
        self._curate_terms()

        # --- Step 2: 周期性白皮书生成 ---
        self._check_and_generate_report(force_report)

    def _curate_terms(self):
        logger.info("🏺 Starting Knowledge Asset Curation (Terms)...")
        try:
            start_time = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            res = requests.get(
                f"{self.api_url}/news/", 
                params={"limit": 200, "min_score": 80, "start_date": start_time},
                timeout=15
            )
            if res.status_code != 200: return

            items = res.json().get("items", [])
            if not items: return

            raw_keywords = []
            for item in items:
                if item.get('trending_keywords'):
                    raw_keywords.extend(item['trending_keywords'])
            
            if not raw_keywords: return

            from collections import Counter
            kw_counts = Counter([k.strip() for k in raw_keywords if k and len(k.strip()) > 1])
            
            for kw, count in kw_counts.most_common(15):
                self._sync_keyword_to_wiki(kw, count, items)
            logger.info("✅ Terms curation completed.")
        except Exception as e:
            logger.error(f"Error during terms curation: {e}")

    def _check_and_generate_report(self, force: bool = False):
        """检查时间周期并生成白皮书"""
        logger.info("📄 Checking for Periodic Whitepaper generation...")
        try:
            # 1. 获取最后一份报告的截止日期
            last_reports = requests.get(f"{self.api_url}/api/assets/reports", params={"limit": 1}).json()
            
            should_generate = force
            start_date = (datetime.now() - timedelta(days=15)).date()
            
            if last_reports:
                last_end = datetime.strptime(last_reports[0]['end_date'], "%Y-%m-%d").date()
                days_passed = (datetime.now().date() - last_end).days
                if days_passed >= 15:
                    should_generate = True
                    start_date = last_end + timedelta(days=1)
            else:
                should_generate = True # 首次生成

            if not should_generate:
                logger.info(f"⏭️ Not time for a new report yet ({days_passed}/15 days). Use --assets to force.")
                return

            # 2. 收集素材
            end_date = datetime.now().date()
            logger.info(f"🤖 Generating Strategic Whitepaper from {start_date} to {end_date}...")
            
            # 获取期间高热词条
            terms = requests.get(f"{self.api_url}/api/assets/terms", params={"limit": 40}).json()
            if not terms:
                logger.warning("❌ No terms found to synthesize a report.")
                return

            # 3. AI 合成
            payload = "近期关键技术资产:\n" + "\n".join([f"- {t['keyword']}: {t['description']}" for t in terms[:30]])
            
            prompt = f"""
            你是一个顶级 AI 行业智库。请根据以下近期沉淀的技术资产，撰写一份深度‘战略白皮书’。
            
            {payload}
            
            要求：
            1. 标题必须具有行业高度（如：2026年Q2 AI 技术演进与势力版图白皮书）。
            2. 结构严谨：包含【执行摘要】、【核心技术演进趋势】、【大厂战略对比】、【未来风险与机遇】。
            3. 字数不少于 2000 字，Markdown 格式。
            """
            
            ai_res = evaluator.generate_content(prompt)
            if not ai_res: return

            # 4. 存储
            report_payload = {
                "title": f"AI 战略资产库深度白皮书 ({start_date} - {end_date})",
                "content": ai_res.text,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "stats_json": {"term_count": len(terms)}
            }
            res = requests.post(f"{self.api_url}/api/assets/reports", json=report_payload)
            if res.status_code in (200, 201):
                logger.info("✅ Periodic Whitepaper successfully generated and archived!")
            
        except Exception as e:
            logger.error(f"Error during report generation: {e}")

    def _sync_keyword_to_wiki(self, keyword: str, daily_heat: int, source_items: List[Dict]):
        """将单个关键词同步到百科，若是新词则生成定义"""
        try:
            # 1. 检查是否存在
            res = requests.get(f"{self.api_url}/api/assets/terms", params={"keyword": keyword}, timeout=5)
            existing_term = None
            if res.status_code == 200:
                terms = res.json()
                for t in terms:
                    if t['keyword'].lower() == keyword.lower():
                        existing_term = t
                        break

            related_ids = [i['id'] for i in source_items if keyword in (i.get('trending_keywords') or [])][:5]

            if existing_term:
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
        context = ""
        for i in items:
            if keyword in (i.get('trending_keywords') or []):
                context += f"- {i['title']}: {i.get('reason', '')[:150]}\n"
        
        prompt = f"""
        你是一个资深的 AI 技术百科编辑。请为以下技术名词编写一个专业、准确且简洁的定义。
        技术名词: {keyword}
        近期提及背景: {context}
        请返回 JSON: {{"category": "...", "definition": "..."}}
        """
        ai_res = evaluator.generate_content(prompt)
        if not ai_res: return None, "general"
        try:
            text = ai_res.text.strip()
            if "```json" in text: text = text.split("```json")[1].split("```")[0].strip()
            data = json.loads(text)
            return data.get('definition'), data.get('category', 'general')
        except: return None, "general"

if __name__ == "__main__":
    api_url = os.getenv("SCRAPER_API_URL", "http://localhost:8000")
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-report", action="store_true")
    args = parser.parse_args()
    engine = AssetEngine(api_url)
    engine.process_daily_assets(force_report=args.force_report)
