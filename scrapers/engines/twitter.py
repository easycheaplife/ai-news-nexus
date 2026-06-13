import requests
import json
import time
import random
import os
from bs4 import BeautifulSoup
from .base import BaseScraper
from datetime import datetime
from ..utils.ai import evaluator
from ..utils.link_scraper import scrape_link_content
from twikit import Client

class TwitterScraper(BaseScraper):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("twitter", api_url)
        self.ai_accounts = self._load_targets()
        
        self.consecutive_failures = 0
        self.max_failures = 10
        self.cookies_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cookies.json')
        
        self.client = Client('en-US')
        self.is_client_ready = False
        
        try:
            if os.path.exists(self.cookies_path):
                with open(self.cookies_path, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                    self.client.set_cookies(cookies)
                self.is_client_ready = True
            else:
                self.logger.error("❌ cookies.json not found. Twikit requires cookies.")
        except Exception as e:
            self.logger.error(f"❌ Error loading cookies: {e}")

    def _load_targets(self) -> list:
        """从后端获取活跃的抓取账号"""
        default_list = [
            {"id": 0, "handle": "OpenAI"}, {"id": 0, "handle": "DeepSeek_AI"}, {"id": 0, "handle": "MistralAI"},
            {"id": 0, "handle": "GoogleDeepMind"}, {"id": 0, "handle": "ylecun"}, {"id": 0, "handle": "karpathy"}
        ]
        try:
            response = requests.get(f"{self.api_url}/targets/?platform=twitter&is_active=true", timeout=10)
            if response.status_code == 200:
                targets = response.json()
                if targets:
                    valid_targets = []
                    interval_hours = float(os.getenv("TWITTER_SCRAPE_INTERVAL_HOURS", 1.0))
                    now = datetime.utcnow()
                    
                    for t in targets:
                        handle = t['handle']
                        if not self._is_valid_twitter_handle(handle): continue
                        
                        last_scraped_str = t.get('last_scraped_at')
                        if last_scraped_str:
                            try:
                                last_scraped = datetime.fromisoformat(last_scraped_str)
                                hours_since = (now - last_scraped).total_seconds() / 3600.0
                                if hours_since < interval_hours:
                                    # 距离上次抓取还不到 1 小时，跳过
                                    continue
                            except Exception:
                                pass
                        
                        valid_targets.append({"id": t['id'], "handle": handle})
                    return valid_targets
        except Exception as e:
            self.logger.warning(f"Failed to load targets from backend, using defaults: {e}")
        return default_list

    def _process_tweet_media(self, tweet_media: list) -> list:
        """提取推文的多媒体内容 (强制高清)"""
        if not tweet_media:
            return []
        
        media_urls = []
        for m in tweet_media:
            if not isinstance(m, dict):
                continue
            
            # Handle Video/GIF
            if m.get('type') in ['video', 'animated_gif']:
                variants = m.get('video_info', {}).get('variants', [])
                mp4_variants = [v for v in variants if v.get('content_type') == 'video/mp4']
                if mp4_variants:
                    best_video = max(mp4_variants, key=lambda x: x.get('bitrate', 0))
                    media_urls.append(best_video['url'])
                    continue
            
            # Handle Image
            img_url = m.get('media_url_https', '')
            if img_url:
                if '?' in img_url:
                    img_url = img_url.split('?')[0] + "?name=orig"
                else:
                    img_url += "?name=orig"
                media_urls.append(img_url)
                
        return list(set(media_urls))

    def _deactivate_target(self, username: str, reason: str):
        """当账号异常（如不存在、被封）时，从后端抓取列表中移除"""
        self.logger.warning(f"🚨 Deactivating target @{username}: {reason}")
        try:
            # 1. 查找 target_id
            response = requests.get(f"{self.api_url}/targets/?platform=twitter&handle={username}", timeout=10)
            if response.status_code == 200:
                targets = response.json()
                if targets:
                    target_id = targets[0]['id']
                    # 2. 更新状态为失效
                    patch_res = requests.patch(
                        f"{self.api_url}/targets/{target_id}",
                        json={
                            "is_active": False,
                            "status": "deactivated",
                            "description": f"Auto-deactivated: {reason} (at {datetime.now().strftime('%Y-%m-%d %H:%M')})"
                        },
                        timeout=10
                    )
                    if patch_res.status_code == 200:
                        self.logger.info(f"✨ Successfully deactivated @{username} in backend.")
        except Exception as e:
            self.logger.error(f"Failed to deactivate target @{username}: {e}")

    def scrape(self):
        if not self.is_client_ready:
            self.logger.error("🛑 Cannot scrape: Twikit client is not initialized with cookies.")
            return

        self.logger.info(f"🚀 Starting Twitter scraping (Accounts: {len(self.ai_accounts)})...")
        
        # 🎲 随机洗牌账号顺序
        random.shuffle(self.ai_accounts)
        preview = ", ".join([f"@{a['handle']}" for a in self.ai_accounts[:3]])
        self.logger.info(f"🔀 Randomized account order. Starting with: {preview}...")
        
        for target_info in self.ai_accounts:
            username = target_info['handle']
            target_id = target_info['id']

            if self.consecutive_failures >= self.max_failures:
                self.logger.error("🛑 Too many consecutive failures. Skipping remaining Twitter targets.")
                break

            try:
                # API 模式抓取速度非常快，加入强制随机休眠，防止短时间内高频请求导致账号被封
                time.sleep(random.uniform(5, 10))
                
                self.logger.info(f"👤 Scraping: @{username}")
                last_id = self.get_last_id(username)
                
                # 获取用户 ID
                user = self.client.get_user_by_screen_name(username)
                if not user:
                    self.logger.warning(f"⚠️ Could not find user @{username}")
                    self._deactivate_target(username, "User not found or suspended")
                    continue

                # 获取用户最新推文
                tweets = self.client.get_user_tweets(user.id, 'Tweets', count=15)
                
                # 记录成功抓取时间 (即使有 0 条新推文，也说明访问通畅)
                if target_id != 0:
                    try:
                        requests.patch(
                            f"{self.api_url}/targets/{target_id}",
                            json={"last_scraped_at": datetime.utcnow().isoformat()},
                            timeout=5
                        )
                    except: pass

                if not tweets:
                    self.logger.info(f"✅ Found 0 new tweets for @{username}")
                    self.consecutive_failures = 0
                    continue

                self.consecutive_failures = 0
                newest_id = None
                valid_tweets = []

                # 增量判断
                for t in tweets:
                    tid = str(t.id)
                    if newest_id is None: newest_id = tid
                    
                    if last_id and int(tid) <= int(last_id):
                        break
                    
                    valid_tweets.append(t)

                self.logger.info(f"✅ Found {len(valid_tweets)} new tweets for @{username}")

                # 后续处理逻辑：按时间正序处理（从旧到新），确保 newest_id 最终更新正确
                for tweet in reversed(valid_tweets):
                    tid = str(tweet.id)
                    content = getattr(tweet, 'text', '') or getattr(tweet, 'full_text', '')
                    raw_date = tweet.created_at # %a %b %d %H:%M:%S +0000 %Y
                    
                    dt_obj = None
                    if raw_date:
                        try:
                            dt_obj = datetime.strptime(raw_date, '%a %b %d %H:%M:%S +0000 %Y')
                        except: pass

                    if dt_obj and not self.is_within_window(dt_obj):
                        continue

                    # 过滤单纯的 Retweets (不包含 Quote Tweets)
                    if content.startswith('RT @'):
                        self.logger.debug(f"⏩ Skipping Retweet for @{username}")
                        continue

                    # AI 评估与推送到后端
                    score, reason, takeaways, cluster_id, mentioned_users, trending_keywords = evaluator.evaluate(f"Tweet from @{username}", content)
                    
                    # 避免低分垃圾推文堆积
                    if score < 50:
                        continue

                    item = {
                        "platform": "twitter",
                        "external_id": tid,
                        "title": f"@{username}: {content[:100].strip()}...",
                        "content": content,
                        "url": f"https://twitter.com/{username}/status/{tid}",
                        "published_at": dt_obj.isoformat() if dt_obj else datetime.utcnow().isoformat(),
                        "score": score,
                        "reason": reason,
                        "takeaways": takeaways,
                        "cluster_id": cluster_id,
                        "mentioned_users": mentioned_users,
                        "trending_keywords": trending_keywords,
                        "media_urls": self._process_tweet_media(getattr(tweet, 'media', [])),
                        "metadata_json": {"author": username, "source": "twikit"}
                    }
                    self.push_to_backend(item)

                if newest_id:
                    self.update_last_id(username, newest_id)
                    self._save_state() # 显式保存状态，确保及时持久化
                        
            except Exception as e:
                self.logger.error(f"Error scraping @{username}: {e}")
                self.consecutive_failures += 1
