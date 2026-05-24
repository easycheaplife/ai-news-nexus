import requests
import json
import time
import random
import re
from bs4 import BeautifulSoup
from .base import BaseScraper
from datetime import datetime
from ..utils.ai import evaluator
from ..utils.link_scraper import scrape_link_content

class TwitterScraper(BaseScraper):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("twitter", api_url)
        self.ai_accounts = self._load_targets()
        import os
        self.max_429_errors = int(os.getenv("TWITTER_MAX_429_ERRORS", 10))
        self.current_429_count = 0
        self.consecutive_nitter_failures = 0
        self.max_nitter_failures = 5 # 连续 5 个账号抓取完全失败则跳过 Twitter
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        # 增加 Nitter 实例列表作为备份
        self.nitter_instances = [
            "https://nitter.net",
            "https://nitter.cz",
            "https://nitter.privacydev.net",
            "https://nitter.it",
            "https://nitter.sethforprivacy.com",
            "https://nitter.moomoo.me",
            "https://nitter.mint.lgbt"
        ]

    def _load_targets(self) -> list:
        """从后端获取活跃的抓取账号"""
        default_list = [
            "OpenAI", "DeepSeek_AI", "MistralAI", "GoogleDeepMind", "ylecun", "karpathy",
            "AnthropicAI", "sama", "gdb", "demishassabis", "perplexity_ai", "Cohere"
        ]
        try:
            response = requests.get(f"{self.api_url}/targets/?platform=twitter&is_active=true", timeout=10)
            if response.status_code == 200:
                targets = response.json()
                if targets:
                    # 过滤掉非法的 Twitter Handle (如路径、过长字符等)
                    return [t['handle'] for t in targets if self._is_valid_twitter_handle(t['handle'])]
        except Exception as e:
            self.logger.warning(f"Failed to load targets from backend, using defaults: {e}")
        return default_list

    def _fetch_from_nitter(self, username: str) -> list:
        """从 Nitter 实例尝试获取推文 (作为 429 后的备份)"""
        random.shuffle(self.nitter_instances)
        success = False
        tweets = []
        for instance in self.nitter_instances:
            try:
                self.logger.info(f"Trying Nitter instance: {instance} for @{username}")
                # 使用 RSS 格式通常更稳定且易于解析
                url = f"{instance}/{username}/rss"
                response = requests.get(url, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    tweets = self._parse_nitter_rss(response.text, username)
                    success = True
                    break
                else:
                    self.logger.warning(f"Nitter instance {instance} returned {response.status_code}")
            except Exception as e:
                self.logger.warning(f"Failed to fetch from Nitter {instance}: {e}")
        
        if success:
            self.consecutive_nitter_failures = 0
        else:
            self.consecutive_nitter_failures += 1
            
        return tweets

    def _parse_nitter_rss(self, rss_content: str, username: str) -> list:
        """解析 Nitter RSS 内容"""
        soup = BeautifulSoup(rss_content, 'xml')
        items = soup.find_all('item')
        tweets = []
        for item in items:
            title = item.title.text if item.title else ""
            link = item.link.text if item.link else ""
            description = item.description.text if item.description else ""
            pub_date = item.pubDate.text if item.pubDate else ""
            
            # 提取 ID
            tid = link.split('/')[-1].split('#')[0]
            
            # 简单封装成类似 Twitter API 的结构
            tweet = {
                'id_str': tid,
                'full_text': description, # Nitter RSS 的 description 通常包含推文正文
                'created_at': pub_date,
                'user': {'screen_name': username},
                'is_nitter': True,
                'url': link
            }
            tweets.append(tweet)
        return tweets

    def _process_tweet_media(self, tweet: dict) -> list:
        """提取推文的多媒体内容 (强制高清)"""
        if tweet.get('is_nitter'):
            # Nitter 的媒体提取逻辑不同，RSS 中通常在 description 的 <img> 标签里
            description = tweet.get('full_text', '')
            soup = BeautifulSoup(description, 'html.parser')
            return [img['src'] for img in soup.find_all('img') if img.get('src')]

        media_urls = []
        ext_entities = tweet.get('extended_entities', {})
        for m in ext_entities.get('media', []):
            if m.get('type') in ['video', 'animated_gif']:
                variants = m.get('video_info', {}).get('variants', [])
                mp4_variants = [v for v in variants if v.get('content_type') == 'video/mp4']
                if mp4_variants:
                    best_video = max(mp4_variants, key=lambda x: x.get('bitrate', 0))
                    media_urls.append(best_video['url'])
            
            # 🖼️ 获取原始大图
            orig_img = m.get('media_url_https', '')
            if orig_img:
                if '?' in orig_img:
                    orig_img = orig_img.split('?')[0] + "?name=orig"
                else:
                    orig_img += "?name=orig"
                if orig_img not in media_urls:
                    media_urls.append(orig_img)
        
        if not media_urls:
            for m in tweet.get('entities', {}).get('media', []):
                img_url = m.get('media_url_https', '')
                if img_url:
                    img_url = img_url.split('?')[0] + "?name=orig"
                    media_urls.append(img_url)
        return media_urls

    def scrape(self):
        self.logger.info(f"🚀 Starting Twitter scraping (Accounts: {len(self.ai_accounts)})...")
        
        base_wait_min = 5
        base_wait_max = 10
        
        for username in self.ai_accounts:
            if self.consecutive_nitter_failures >= self.max_nitter_failures:
                self.logger.error("🛑 Too many consecutive Nitter failures. Skipping remaining Twitter targets.")
                break

            try:
                multiplier = 2 ** self.current_429_count
                wait_time = random.uniform(base_wait_min * multiplier, base_wait_max * multiplier)
                time.sleep(wait_time)
                
                self.logger.info(f"👤 Scraping: @{username}")
                last_id = self.get_last_id(username)
                
                # 尝试 A 方案: Syndication
                url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}"
                response = None
                valid_tweets = []
                newest_id = None
                syndication_success = False

                try:
                    response = requests.get(url, headers=self.headers, timeout=15)
                    self.logger.info(f"📡 Syndication check for @{username}: HTTP {response.status_code}")
                except Exception as e:
                    self.logger.warning(f"Syndication connection error for @{username}: {e}")
                
                if response and response.status_code == 200:
                    syndication_success = True
                    soup = BeautifulSoup(response.text, 'html.parser')
                    script_tag = soup.find('script', id='__NEXT_DATA__')
                    if script_tag:
                        data = json.loads(script_tag.string)
                        timeline = data.get('props', {}).get('pageProps', {}).get('timeline', {}).get('entries', [])
                        
                        for entry in timeline:
                            tweet = entry.get('content', {}).get('tweet')
                            if not tweet: continue
                            tid = tweet['id_str']
                            if newest_id is None: newest_id = tid
                            
                            # 增量判断
                            if last_id and int(tid) <= int(last_id): 
                                break
                            valid_tweets.append(tweet)
                        
                        self.logger.info(f"✅ Syndication found {len(valid_tweets)} new tweets for @{username}")
                        
                        if self.current_429_count > 0:
                            self.logger.info("✅ Connection recovered. Resetting 429 error counter.")
                            self.current_429_count = 0
                
                # 尝试 B 方案: Nitter (仅当 A 方案明确失败或触发 429 时才降级)
                # 如果 syndication_success 为 True 且 valid_tweets 为空，说明确实没新内容，无需降级
                if not syndication_success or (response and response.status_code == 429):
                    if response and response.status_code == 429:
                        self.logger.warning(f"⚠️ Syndication 429 for @{username}. Switching to Nitter...")
                        self.current_429_count = min(self.current_429_count + 1, self.max_429_errors)
                    else:
                        self.logger.warning(f"⚠️ Syndication failed for @{username}. Trying Nitter...")
                    
                    nitter_tweets = self._fetch_from_nitter(username)
                    for nt in nitter_tweets:
                        tid = nt['id_str']
                        if last_id and int(tid) <= int(last_id): break
                        if newest_id is None: newest_id = tid
                        valid_tweets.append(nt)

                if not valid_tweets:
                    # 如果主方案抓到了 newest_id (虽然可能都在 window 外)，也更新一下状态
                    if newest_id:
                        self.update_last_id(username, newest_id)
                        self._save_state()
                    continue

                # 后续处理逻辑
                processed_ids = set()
                # 按时间正序处理（从旧到新），确保 newest_id 最终更新正确
                for tweet in reversed(valid_tweets):
                    tid = tweet['id_str']
                    if tid in processed_ids: continue
                    processed_ids.add(tid)

                    full_content = tweet.get('full_text', '')
                    if tweet.get('is_nitter'):
                        full_content = BeautifulSoup(full_content, 'html.parser').get_text()

                    raw_date = tweet.get('created_at')
                    dt_obj = None
                    if raw_date:
                        try:
                            if tweet.get('is_nitter'):
                                # Nitter RSS: Fri, 22 May 2026 12:34:56 GMT
                                dt_obj = datetime.strptime(raw_date, '%a, %d %b %Y %H:%M:%S %Z')
                            else:
                                # Syndication: Fri May 22 12:34:56 +0000 2026
                                dt_obj = datetime.strptime(raw_date, '%a %b %d %H:%M:%S +0000 %Y')
                        except: pass

                    if dt_obj and not self.is_within_window(dt_obj):
                        continue

                    score, reason, takeaways, cluster_id, mentioned_users, trending_keywords = evaluator.evaluate(f"Tweet from @{username}", full_content)
                    
                    item = {
                        "platform": "twitter",
                        "external_id": tid,
                        "title": f"@{username}: {full_content[:100].strip()}",
                        "content": full_content,
                        "url": tweet.get('url', f"https://twitter.com/{username}/status/{tid}"),
                        "published_at": dt_obj.isoformat() if dt_obj else datetime.utcnow().isoformat(),
                        "score": score,
                        "reason": reason,
                        "takeaways": takeaways,
                        "cluster_id": cluster_id,
                        "mentioned_users": mentioned_users,
                        "trending_keywords": trending_keywords,
                        "media_urls": self._process_tweet_media(tweet),
                        "metadata_json": {"author": username, "source": "nitter" if tweet.get('is_nitter') else "syndication"}
                    }
                    self.push_to_backend(item)

                if newest_id:
                    self.update_last_id(username, newest_id)
                    self._save_state() # 显式保存状态，确保及时持久化
                        
            except Exception as e:
                self.logger.error(f"Error scraping @{username}: {e}")
