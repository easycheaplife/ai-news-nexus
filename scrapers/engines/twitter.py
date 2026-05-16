import requests
import json
import time
from bs4 import BeautifulSoup
from .base import BaseScraper
from datetime import datetime
from ..utils.ai import evaluator

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

    def scrape(self):
        self.logger.info("🚀 Starting Twitter scraping via Syndication API (No-Login)...")
        
        for username in self.ai_accounts:
            try:
                # 💡 增加延迟防止 429
                time.sleep(2)
                self.logger.info(f"👤 Scraping tweets from: @{username}")
                last_id = self.get_last_id(username)
                url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}"
                
                response = requests.get(url, headers=self.headers, timeout=15)
                if response.status_code != 200:
                    self.logger.error(f"❌ Failed to fetch timeline for @{username}: HTTP {response.status_code}")
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')
                script_tag = soup.find('script', id='__NEXT_DATA__')
                
                if not script_tag:
                    self.logger.error(f"❌ Could not find data script for @{username}. Page structure might have changed.")
                    continue

                data = json.loads(script_tag.string)
                
                try:
                    timeline = data['props']['pageProps']['timeline']['entries']
                except KeyError:
                    self.logger.error(f"❌ Unexpected data structure for @{username}")
                    continue

                newest_id = None
                for entry in timeline:
                    try:
                        tweet = entry.get('content', {}).get('tweet')
                        if not tweet:
                            continue
                        
                        tweet_id = tweet['id_str']
                        
                        if newest_id is None:
                            newest_id = tweet_id

                        # 增量判断
                        if last_id and int(tweet_id) <= int(last_id):
                            self.logger.info(f"⏱️ Reached last seen tweet for @{username}, stopping.")
                            break
                        
                        text = tweet.get('full_text', tweet.get('text', ''))
                        
                        # 🧵 捕捉上下文 (如果是回复，尝试获取父推文内容)
                        full_content = text
                        parent_tweet = None
                        if tweet.get('in_reply_to_status_id_str'):
                            # 尝试从 JSON 数据中寻找引用的推文 (有时包含在 data 中)
                            # 在免登录 API 中，通常很难获取完整的 thread，但我们可以尝试提取可用信息
                            parent_name = tweet.get('in_reply_to_screen_name')
                            if parent_name:
                                full_content = f"回复 @{parent_name}: {text}\n\n(上下文: 这是一条回复消息)"

                        # 🖼️ 提取多媒体内容
                        media_urls = []
                        
                        # 优先从扩展实体中提取视频
                        ext_entities = tweet.get('extended_entities', {})
                        for m in ext_entities.get('media', []):
                            if m.get('type') == 'video' or m.get('type') == 'animated_gif':
                                variants = m.get('video_info', {}).get('variants', [])
                                # 寻找比特率最高的 mp4
                                mp4_variants = [v for v in variants if v.get('content_type') == 'video/mp4']
                                if mp4_variants:
                                    best_video = max(mp4_variants, key=lambda x: x.get('bitrate', 0))
                                    media_urls.append(best_video['url'])
                            
                            # 同时也把封面图存下来作为备选
                            if m.get('media_url_https') not in media_urls:
                                media_urls.append(m.get('media_url_https'))
                        
                        # 如果没有扩展实体，尝试普通实体
                        if not media_urls:
                            for m in tweet.get('entities', {}).get('media', []):
                                media_urls.append(m.get('media_url_https'))
                        
                        # 🤖 AI 评分与理由
                        score, reason, takeaways, cluster_id = evaluator.evaluate(f"Tweet from @{username}", full_content)

                        # 解析推特日期格式: "Mon May 11 13:10:12 +0000 2026"
                        raw_date = tweet.get('created_at')
                        published_at = datetime.utcnow().isoformat()
                        if raw_date:
                            try:
                                dt = datetime.strptime(raw_date, '%a %b %d %H:%M:%S +0000 %Y')
                                published_at = dt.isoformat()
                            except Exception as date_e:
                                self.logger.warning(f"Date parsing failed for {raw_date}: {date_e}")

                        # 优化标题展示
                        display_title = text[:100].replace('\n', ' ') + ('...' if len(text) > 100 else '')

                        item = {
                            "platform": "twitter",
                            "external_id": tweet_id,
                            "title": f"@{username}: {display_title}",
                            "content": full_content,
                            "url": f"https://twitter.com/{username}/status/{tweet_id}",
                            "published_at": published_at,
                            "score": score,
                            "reason": reason,
                            "takeaways": takeaways,
                            "cluster_id": cluster_id,
                            "media_urls": media_urls,
                            "metadata_json": {
                                "author": tweet.get('user', {}).get('name', username),
                                "stats": {
                                    "retweets": tweet.get('retweet_count', 0),
                                    "likes": tweet.get('favorite_count', 0),
                                    "replies": tweet.get('reply_count', 0)
                                }
                            }
                        }
                        self.push_to_backend(item)
                    except Exception as inner_e:
                        self.logger.error(f"Error processing tweet: {inner_e}")
                
                # 更新游标
                if newest_id:
                    self.update_last_id(username, newest_id)
                        
            except Exception as e:
                self.logger.error(f"Critical error scraping @{username}: {e}")
