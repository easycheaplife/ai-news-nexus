import requests
import json
import time
from bs4 import BeautifulSoup
from .base import BaseScraper
from datetime import datetime
from ..utils.ai import evaluator
from ..utils.link_scraper import scrape_link_content

class TwitterScraper(BaseScraper):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("twitter", api_url)
        self.ai_accounts = [
            "OpenAI", "DeepSeek_AI", "MistralAI", "GoogleDeepMind", "ylecun", "karpathy",
            "AnthropicAI", "sama", "gdb", "demishassabis", "perplexity_ai", "Cohere",
            "NVIDIAAI", "MetaAI", "AndrewYNg", "ArowLau", "DrJimFan", "fchollet",
            "bindureddy", "emostaque", "swyx", "RowanChevalier", "levelsio", "AravSrinivas",
            "shaneleg", "ilyasut", "gdb", "woj_zaremba", "reidhoffman", "p_george"
        ]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _process_tweet_media(self, tweet: dict) -> list:
        """提取推文的多媒体内容"""
        media_urls = []
        ext_entities = tweet.get('extended_entities', {})
        for m in ext_entities.get('media', []):
            if m.get('type') in ['video', 'animated_gif']:
                variants = m.get('video_info', {}).get('variants', [])
                mp4_variants = [v for v in variants if v.get('content_type') == 'video/mp4']
                if mp4_variants:
                    best_video = max(mp4_variants, key=lambda x: x.get('bitrate', 0))
                    media_urls.append(best_video['url'])
            if m.get('media_url_https') not in media_urls:
                media_urls.append(m.get('media_url_https'))
        
        if not media_urls:
            for m in tweet.get('entities', {}).get('media', []):
                media_urls.append(m.get('media_url_https'))
        return media_urls

    def scrape(self):
        self.logger.info("🚀 Starting Twitter scraping with Thread stitching...")
        
        for username in self.ai_accounts:
            try:
                # 💡 增加随机延迟防止 429
                import random
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
                # 将推文按 ID 映射，方便查找父推文
                tweet_map = {t['id_str']: t for t in valid_tweets}
                processed_ids = set()
                
                # 按时间正序排列（从旧到新），方便拼接
                valid_tweets.reverse()

                for tweet in valid_tweets:
                    tid = tweet['id_str']
                    if tid in processed_ids: continue

                    # 检查是否为 Thread 的一部分（回复自己）
                    is_reply_to_self = (
                        tweet.get('in_reply_to_screen_name') == username or 
                        tweet.get('in_reply_to_user_id_str') == tweet.get('user', {}).get('id_str')
                    )
                    
                    parent_id = tweet.get('in_reply_to_status_id_str')
                    
                    # 如果这是一条回复，且父推文在本次抓取列表中，我们跳过它（等待从父推文开始拼接）
                    if is_reply_to_self and parent_id in tweet_map:
                        continue
                    
                    # 开始构建（可能是单条，也可能是 Thread 头部）
                    thread_tweets = [tweet]
                    processed_ids.add(tid)
                    
                    # 寻找后续回复（同一作者）
                    current_parent_id = tid
                    while True:
                        child = next((t for t in valid_tweets if t.get('in_reply_to_status_id_str') == current_parent_id and t['id_str'] not in processed_ids), None)
                        if child:
                            thread_tweets.append(child)
                            processed_ids.add(child['id_str'])
                            current_parent_id = child['id_str']
                        else:
                            break
                    
                    # 3. 组装最终内容
                    main_tweet = thread_tweets[0]
                    full_text_list = []
                    all_media = []
                    
                    for i, t in enumerate(thread_tweets):
                        text = t.get('full_text', t.get('text', ''))
                        # 抓取外链摘要 (仅针对每条推文的第一个链接)
                        link_context = ""
                        urls = t.get('entities', {}).get('urls', [])
                        if urls:
                            link_context = scrape_link_content(urls[0].get('expanded_url'))
                        
                        prefix = f"[{i+1}/{len(thread_tweets)}] " if len(thread_tweets) > 1 else ""
                        full_text_list.append(f"{prefix}{text}\n{link_context}".strip())
                        all_media.extend(self._process_tweet_media(t))

                    full_content = "\n\n---\n\n".join(full_text_list)
                    
                    # 🤖 AI 评估
                    score, reason, takeaways, cluster_id = evaluator.evaluate(f"Tweet from @{username}", full_content)

                    # 日期处理
                    raw_date = main_tweet.get('created_at')
                    published_at = datetime.utcnow().isoformat()
                    if raw_date:
                        try:
                            dt = datetime.strptime(raw_date, '%a %b %d %H:%M:%S +0000 %Y')
                            published_at = dt.isoformat()
                        except: pass

                    display_title = main_tweet.get('full_text', main_tweet.get('text', ''))[:100].replace('\n', ' ')
                    
                    item = {
                        "platform": "twitter",
                        "external_id": main_tweet['id_str'],
                        "title": f"@{username}: {display_title}",
                        "content": full_content,
                        "url": f"https://twitter.com/{username}/status/{main_tweet['id_str']}",
                        "published_at": published_at,
                        "score": score,
                        "reason": reason,
                        "takeaways": takeaways,
                        "cluster_id": cluster_id,
                        "media_urls": list(dict.fromkeys(all_media)), # 去重保持顺序
                        "metadata_json": {
                            "author": username,
                            "thread_count": len(thread_tweets),
                            "stats": {
                                "likes": main_tweet.get('favorite_count', 0),
                                "retweets": main_tweet.get('retweet_count', 0)
                            }
                        }
                    }
                    self.push_to_backend(item)

                if newest_id:
                    self.update_last_id(username, newest_id)
                        
            except Exception as e:
                self.logger.error(f"Error scraping @{username}: {e}")
