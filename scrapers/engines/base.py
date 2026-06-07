import requests
from datetime import datetime
import logging
import json
import os
import re
from ..utils.media_mirror import MediaMirror

class BaseScraper:
    def __init__(self, platform: str, api_url: str = "http://localhost:8000", region: str = "global"):
        self.platform = platform
        self.api_url = api_url
        self.region = region  # 'global' or 'cn'
        self.logger = logging.getLogger(f"scraper.{platform}")
        # 抓取时间窗口 (默认 72 小时)
        self.scrape_window_hours = int(os.getenv("SCRAPE_WINDOW_HOURS", 72))
        # 初始化媒体转存工具
        self.mirror = MediaMirror(api_url)
        # 本地去重缓存（仅限本次运行）
        self.seen_ids = set()
        
        # 状态持久化文件路径 (放在 scrapers 根目录)
        self.state_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "state.json")
        self.state = self._load_state()

    def _is_valid_twitter_handle(self, handle: str) -> bool:
        """验证是否为合法的 Twitter Handle"""
        if not handle or not isinstance(handle, str):
            return False
            
        # 1. 长度校验 (1-15位)
        if not (1 <= len(handle) <= 15):
            return False
        
        # 2. 字符校验 (仅允许字母、数字、下划线)
        if not re.match(r"^[A-Za-z0-9_]+$", handle):
            return False
        
        # 3. 关键词黑名单 (排除一些容易被 AI 误认的词或系统路径)
        blacklist = {
            "twitter", "x", "status", "web", "iphone", "android", "ai", "news", 
            "nexus", "scrapers", "frontend", "backend", "src", "index", "home",
            "api", "v1", "discovery", "targets", "clusters", "insights", "media"
        }
        if handle.lower() in blacklist:
            return False
            
        return True

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

    def is_within_window(self, dt: datetime) -> bool:
        """检查给定的时间是否在抓取窗口内"""
        if not dt:
            return False
        delta = datetime.utcnow() - dt
        return delta.total_seconds() <= (self.scrape_window_hours * 3600)

    def push_to_backend(self, item: dict):
        # 1. 采集端本地去重
        item_key = f"{item['platform']}:{item['external_id']}"
        if item_key in self.seen_ids:
            return
        
        # 2. 媒体转存 (Mirroring) —— 核心：将外部链接转化为本站链接
        if item.get('media_urls'):
            self.logger.info(f"📸 Mirroring {len(item['media_urls'])} media items...")
            item['media_urls'] = self.mirror.mirror_all(item['media_urls'])

        try:
            # 3. 推送到后端
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
        
        for user in users:
            # 1. 基础清理：移除 @，截断空格、斜杠和点号
            clean_user = user.strip().strip('@').split(' ')[0].split('/')[0].split('.')[0]
            
            # 2. 严格合法性校验
            if not self._is_valid_twitter_handle(clean_user):
                if clean_user: # 仅对非空字符串记录调试日志
                    self.logger.debug(f"⏩ Dropping invalid handle: {clean_user}")
                continue
            
            payload = {
                "type": "user",
                "value": clean_user,
                "source_id": 0,
                "discovery_reason": f"From high-score content: {item['title'][:30]}"
            }
            try:
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
