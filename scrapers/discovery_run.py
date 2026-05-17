import logging
import requests
import os
import json
import time
from dotenv import load_dotenv
from scrapers.utils.ai import evaluator

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("discovery_engine")

class DiscoveryEngine:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url

    def run_expansion(self):
        """执行信源自动扩张逻辑 (方案 A)"""
        logger.info("🚀 Starting Network Expansion phase...")
        
        # 1. 获取待验证的用户
        try:
            response = requests.get(f"{self.api_url}/discovery/?status=pending", timeout=10)
            if response.status_code != 200:
                return
            
            pending_items = response.json()
            users_to_vet = [item for item in pending_items if item['type'] == 'user']
            
            if not users_to_vet:
                logger.info("No pending users to vet.")
                return

            for item in users_to_vet:
                username = item['value']
                logger.info(f"🔍 Vetting user: @{username}")
                
                # 2. 调用 AI 进行身份画像 (Vetting)
                # 这里的逻辑可以更复杂，比如先抓取该用户的简介。
                # 目前为了闭环，我们直接让 AI 根据上下文和 handle 进行判断。
                is_worthy, reason = self._vet_user(username, item['discovery_reason'])
                
                if is_worthy:
                    logger.info(f"✅ User @{username} vetted! Adding to active targets.")
                    # 加入活跃目标
                    self._promote_to_target("twitter", username, reason)
                    # 更新发现池状态
                    self._update_discovery_status(item['id'], "vetted")
                else:
                    logger.info(f"❌ User @{username} rejected.")
                    self._update_discovery_status(item['id'], "rejected")
                
                time.sleep(1) # 避免 API 请求过快

        except Exception as e:
            logger.error(f"Error in discovery phase: {e}")

    def _vet_user(self, username: str, context: str) -> tuple:
        """调用 Gemini 评估该账号是否值得长期追踪"""
        prompt = f"""
        你是一个资深 AI 行业观察员。我们需要决定是否将推特用户 @{username} 加入我们的核心采集名单。
        
        发现背景: {context}
        
        请评估该账号是否属于以下类型：
        1. AI 领域的核心研究员、科学家或工程师。
        2. 知名 AI 初创公司的创始人或高管。
        3. 产出高质量 AI 技术评论或实战经验的 KOL。
        
        请严格按 JSON 格式返回：
        {{
            "is_worthy": true/false,
            "reason": "简短的一句话描述其身份/价值 (20字以内)"
        }}
        """
        try:
            # 使用 evaluator 的通用生成方法，支持多模型降级
            response = evaluator.generate_content(prompt)
            if not response:
                return False, "AI 服务暂时不可用"
                
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            data = json.loads(text)
            return data.get("is_worthy", False), data.get("reason", "")
        except Exception as e:
            logger.error(f"AI Vetting failed for {username}: {e}")
            return False, ""

    def _promote_to_target(self, platform: str, handle: str, description: str):
        """将验证通过的账号正式加入采集表"""
        payload = {
            "platform": platform,
            "handle": handle,
            "name": handle,
            "description": description,
            "is_active": True
        }
        try:
            requests.post(f"{self.api_url}/targets/", json=payload)
        except: pass

    def _update_discovery_status(self, discovery_id: int, status: str):
        """更新发现池中的状态（由于目前没有 PATCH 接口，我们简单通过 POST 逻辑模拟或记录）
        实际生产中这里应该有对应的状态更新 API。
        """
        # TODO: 实现后端 PATCH /discovery/{id} 接口
        pass

if __name__ == "__main__":
    api_url = os.getenv("SCRAPER_API_URL", "http://localhost:8000")
    engine = DiscoveryEngine(api_url)
    engine.run_expansion()
