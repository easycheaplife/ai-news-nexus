import requests
from datetime import datetime
import logging
import json
import os

class BaseScraper:
    def __init__(self, platform: str, api_url: str = "http://localhost:8000"):
        self.platform = platform
        self.api_url = api_url
        self.logger = logging.getLogger(f"scraper.{platform}")
        # 本地去重缓存（仅限本次运行）
        self.seen_ids = set()
        
        # 状态持久化文件路径 (放在 scrapers 根目录)
        self.state_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "state.json")
        self.state = self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading state file: {e}")
        return {}

    def _save_state(self):
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving state file: {e}")

    def get_last_id(self, sub_key: str):
        """获取某个子项（如账号、子版块）上次抓取的最后 ID"""
        return self.state.get(self.platform, {}).get(sub_key)

    def update_last_id(self, sub_key: str, current_id: str):
        """更新游标，确保它是最大的（最新的）"""
        if self.platform not in self.state:
            self.state[self.platform] = {}
        
        # 对于 ID 是数字字符串的情况，进行数值比较；否则进行字符串或时间戳比较
        last_id = self.state[self.platform].get(sub_key)
        
        is_newer = False
        if last_id is None:
            is_newer = True
        else:
            try:
                # 尝试数值比较（适用于 Twitter ID, HN ID）
                if int(current_id) > int(last_id):
                    is_newer = True
            except (ValueError, TypeError):
                # 字符串比较（适用于时间戳字符串或 UUID）
                if str(current_id) > str(last_id):
                    is_newer = True
        
        if is_newer:
            self.state[self.platform][sub_key] = current_id
            self._save_state()

    def push_to_backend(self, item: dict):
        # 1. 采集端本地去重
        item_key = f"{item['platform']}:{item['external_id']}"
        if item_key in self.seen_ids:
            return
        
        try:
            # 2. 推送到后端
            response = requests.post(f"{self.api_url}/news/", json=item)
            if response.status_code == 200:
                self.logger.info(f"✅ Successfully pushed: {item['title'][:50]}...")
                self.seen_ids.add(item_key)
                
                # 3. 处理发现信号 (如果是 90+ 高分内容，提取信号)
                if item.get('score', 0) >= 80:
                    self._push_discovery_signals(item)

            elif response.status_code == 409: # 已存在
                self.seen_ids.add(item_key)
            else:
                self.logger.error(f"❌ Failed to push: {response.text}")
        except Exception as e:
            self.logger.error(f"Error pushing to backend: {e}")

    def _push_discovery_signals(self, item: dict):
        """将内容中提取到的新账号和热词存入发现池"""
        users = item.get('mentioned_users') or []
        keywords = item.get('trending_keywords') or []
        
        # 过滤掉已有的白名单账号 (简化处理，只针对 Twitter)
        # TODO: 更好的过滤逻辑
        
        for user in users:
            # 简单的清理逻辑
            clean_user = user.strip('@').split(' ')[0]
            if not clean_user: continue
            
            payload = {
                "type": "user",
                "value": clean_user,
                "source_id": 0, # 这里暂时填 0，后端如果没查到 ID 允许为空
                "discovery_reason": f"From high-score content: {item['title'][:30]}"
            }
            try:
                # 使用一个专用的发现接口，或者复用 insights 接口 (这里建议新建接口)
                # 为保持进度，假设我们已经有了 /discovery/ 接口
                requests.post(f"{self.api_url}/discovery/", json=payload)
            except: pass

        for kw in keywords:
            if not kw: continue
            payload = {
                "type": "keyword",
                "value": kw,
                "source_id": 0,
                "discovery_reason": f"Trending in: {item['title'][:30]}"
            }
            try:
                requests.post(f"{self.api_url}/discovery/", json=payload)
            except: pass

    def scrape(self):
        raise NotImplementedError("Subclasses must implement scrape()")
