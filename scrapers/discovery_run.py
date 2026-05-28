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
        
        try:
            # 1. 获取全局限制和当前状态
            max_active_targets = int(os.getenv("MAX_ACTIVE_TARGETS", 100))
            
            # 获取所有账号（包括黑名单），用于排查
            all_targets_res = requests.get(f"{self.api_url}/targets/", params={"is_active": None}, timeout=10)
            all_targets = all_targets_res.json() if all_targets_res.status_code == 200 else []
            
            current_active_count = len([t for t in all_targets if t['is_active']])
            blacklisted_handles = {t['handle'].lower() for t in all_targets if t['status'] == 'blacklisted'}
            
            if current_active_count >= max_active_targets:
                logger.info(f"🔄 Reached limit ({current_active_count}/{max_active_targets}). Attempting to recycle low-performers...")
                # 寻找活跃账号中分数最低且产出已达标的“平庸者”
                # 排除 probation 状态（新秀保护）
                recyclable = [t for t in all_targets if t['is_active'] and t['status'] != 'probation' and (t['avg_score'] or 0) < 55]
                if recyclable:
                    # 按分数升序，取分最低的一个
                    worst = min(recyclable, key=lambda x: (x['avg_score'] or 0))
                    logger.warning(f"♻️ Recycling low-performer @{worst['handle']} (Avg: {worst['avg_score']}) to make room.")
                    requests.patch(f"{self.api_url}/targets/{worst['id']}", json={"is_active": False, "status": "deactivated"})
                    current_active_count -= 1
                else:
                    logger.warning(f"⚠️ No recyclable targets found. Skipping expansion.")
                    return

            # 2. 获取待验证的用户
            max_vetting = int(os.getenv("DISCOVERY_MAX_VETTING", 100))
            response = requests.get(f"{self.api_url}/discovery/?status=pending", timeout=10)
            if response.status_code != 200: return
            
            pending_items = response.json()
            users_to_vet = [item for item in pending_items if item['type'] == 'user']
            
            if not users_to_vet:
                logger.info("No pending users to vet.")
                return

            # 3. 限制本次运行的处理数量
            vetted_count = 0
            for item in users_to_vet:
                username = item['value']
                
                # 🛑 黑名单与重复校验
                if username.lower() in blacklisted_handles:
                    logger.info(f"🚫 Skipping blacklisted user: @{username}")
                    self._update_discovery_status(item['id'], "rejected")
                    continue

                if current_active_count >= max_active_targets:
                    logger.info(f"🛑 Reached global active targets limit ({max_active_targets}). Stopping vetting.")
                    break
                if vetted_count >= max_vetting:
                    break
                    
                logger.info(f"🔍 Vetting user: @{username} ({vetted_count + 1}/{max_vetting})")
                
                # 4. 调用 AI 进行面试
                is_worthy, reason = self._vet_user(username, item['discovery_reason'])
                
                if is_worthy:
                    logger.info(f"✅ User @{username} vetted! Adding to probation.")
                    if self._promote_to_target("twitter", username, reason):
                        current_active_count += 1
                    self._update_discovery_status(item['id'], "vetted")
                else:
                    logger.info(f"❌ User @{username} rejected.")
                    self._update_discovery_status(item['id'], "rejected")
                
                vetted_count += 1
                time.sleep(1)

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

    def _promote_to_target(self, platform: str, handle: str, description: str) -> bool:
        """将验证通过的账号正式加入采集表，初始状态设为 probation"""
        payload = {
            "platform": platform,
            "handle": handle,
            "name": handle,
            "description": description,
            "is_active": True,
            "status": "probation" # 新发现的账号先进入试用期
        }
        try:
            res = requests.post(f"{self.api_url}/targets/", json=payload)
            return res.status_code in [200, 201]
        except: 
            return False

    def _update_discovery_status(self, discovery_id: int, status: str):
        """更新发现池中的状态"""
        try:
            requests.patch(f"{self.api_url}/discovery/{discovery_id}", json={"status": status})
        except Exception as e:
            logger.error(f"Failed to update discovery status for {discovery_id}: {e}")

if __name__ == "__main__":
    api_url = os.getenv("SCRAPER_API_URL", "http://localhost:8000")
    engine = DiscoveryEngine(api_url)
    engine.run_expansion()
