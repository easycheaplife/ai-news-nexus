import requests
import json
import time
import random
from bs4 import BeautifulSoup
from .base import BaseScraper
from datetime import datetime
from ..utils.ai import evaluator
from ..utils.link_scraper import scrape_link_content

class TwitterScraper(BaseScraper):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("twitter", api_url)
        self.ai_accounts = self._load_targets()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

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
                    return [t['handle'] for t in targets]
        except Exception as e:
            self.logger.warning(f"Failed to load targets from backend, using defaults: {e}")
        return default_list

    def _process_tweet_media(self, tweet: dict) -> list:
        """提取推文的多媒体内容 (强制高清)"""
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
        self.logger.info("🚀 Starting Twitter scraping with Thread stitching...")
        
        for username in self.ai_accounts:
            try:
                # 💡 增加随机延迟防止 429
                wait_time = random.uniform(2, 5)
                time.sleep(wait_time)
                
                self.logger.info(f"👤 Scraping: @{username}")
                last_id = self.get_last_id(username)
                url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}"
                
                response = requests.get(url, headers=self.headers, timeout=15)
                if response.status_code == 429:
                    self.logger.error(f"❌ Rate limit exceeded (429) for @{username}. Skipping for now.")
                    continue
                elif response.status_code != 200:
                    self.logger.error(f"❌ Failed to fetch timeline for @{username}: HTTP {response.status_code}")
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')
                script_tag = soup.find('script', id='__NEXT_DATA__')
                if not script_tag: continue

                data = json.loads(script_tag.string)
                timeline = data.get('props', {}).get('pageProps', {}).get('timeline', {}).get('entries', [])
                
                # 1. 预处理：收集所有未读推文
                valid_tweets = []
                newest_id = None
                for entry in timeline:
                    tweet = entry.get('content', {}).get('tweet')
                    if not tweet: continue
                    
                    tid = tweet['id_str']
                    if newest_id is None: newest_id = tid
                    
                    if last_id and int(tid) <= int(last_id):
                        break
                    valid_tweets.append(tweet)

                if not valid_tweets:
                    continue

                # 2. Thread 拼接逻辑
                tweet_map = {t['id_str']: t for t in valid_tweets}
                processed_ids = set()
                valid_tweets.reverse() # 按时间正序

                for tweet in valid_tweets:
                    tid = tweet['id_str']
                    if tid in processed_ids: continue

                    is_reply_to_self = (
                        tweet.get('in_reply_to_screen_name') == username or 
                        tweet.get('in_reply_to_user_id_str') == tweet.get('user', {}).get('id_str')
                    )
                    parent_id = tweet.get('in_reply_to_status_id_str')
                    
                    if is_reply_to_self and parent_id in tweet_map:
                        continue
                    
                    thread_tweets = [tweet]
                    processed_ids.add(tid)
                    
                    current_parent_id = tid
                    while True:
                        child = next((t for t in valid_tweets if t.get('in_reply_to_status_id_str') == current_parent_id and t['id_str'] not in processed_ids), None)
                        if child:
                            thread_tweets.append(child)
                            processed_ids.add(child['id_str'])
                            current_parent_id = child['id_str']
                        else:
                            break
                    
                    # 3. 组装内容
                    full_text_list = []
                    all_media = []
                    
                    for i, t in enumerate(thread_tweets):
                        text = t.get('full_text', t.get('text', ''))
                        link_context = ""
                        urls = t.get('entities', {}).get('urls', [])
                        if urls:
                            link_context = scrape_link_content(urls[0].get('expanded_url'))
                        
                        prefix = f"[{i+1}/{len(thread_tweets)}] " if len(thread_tweets) > 1 else ""
                        full_text_list.append(f"{prefix}{text}\n{link_context}".strip())
                        all_media.extend(self._process_tweet_media(t))

                    full_content = "\n\n---\n\n".join(full_text_list)
                    
                    # 日期处理与时间窗口过滤 (前置到 AI 评估之前，节省 API 额度)
                    raw_date = thread_tweets[0].get('created_at')
                    published_at = datetime.utcnow().isoformat()
                    dt_obj = None
                    if raw_date:
                        try:
                            dt_obj = datetime.strptime(raw_date, '%a %b %d %H:%M:%S +0000 %Y')
                            published_at = dt_obj.isoformat()
                        except: pass

                    # 🕒 时间窗口过滤：如果开启了窗口限制，且推文超出时间范围，则跳过
                    if dt_obj and not self.is_within_window(dt_obj):
                        self.logger.info(f"⏩ Skipping old tweet from {dt_obj} (outside {self.scrape_window_hours}h window)")
                        continue

                    # 🤖 AI 评估 (仅对时间窗口内的有效内容进行评估)
                    score, reason, takeaways, cluster_id, mentioned_users, trending_keywords = evaluator.evaluate(f"Tweet from @{username}", full_content)

                    display_title = thread_tweets[0].get('full_text', thread_tweets[0].get('text', ''))[:100].replace('\n', ' ')
                    
                    item = {
                        "platform": "twitter",
                        "external_id": thread_tweets[0]['id_str'],
                        "title": f"@{username}: {display_title}",
                        "content": full_content,
                        "url": f"https://twitter.com/{username}/status/{thread_tweets[0]['id_str']}",
                        "published_at": published_at,
                        "score": score,
                        "reason": reason,
                        "takeaways": takeaways,
                        "cluster_id": cluster_id,
                        "mentioned_users": mentioned_users,
                        "trending_keywords": trending_keywords,
                        "media_urls": list(dict.fromkeys(all_media)),
                        "metadata_json": {
                            "author": username,
                            "thread_count": len(thread_tweets),
                            "stats": {
                                "likes": thread_tweets[0].get('favorite_count', 0),
                                "retweets": thread_tweets[0].get('retweet_count', 0)
                            }
                        }
                    }
                    self.push_to_backend(item)

                if newest_id:
                    self.update_last_id(username, newest_id)
                        
            except Exception as e:
                self.logger.error(f"Error scraping @{username}: {e}")
