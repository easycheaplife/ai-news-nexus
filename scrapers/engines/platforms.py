import requests
import os
import time
from ..base import BaseScraper
from datetime import datetime
from ..utils.ai import evaluator

class RedditScraper(BaseScraper):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("reddit", api_url)
        self.reddit_url = "https://www.reddit.com/r/MachineLearning/new.json?limit=50"
        self.headers = {"User-Agent": "AI News Bot 1.0"}

    def _get_top_comments(self, permalink: str, limit: int = 5) -> str:
        """获取帖子的热门评论"""
        url = f"https://www.reddit.com{permalink}.json"
        try:
            time.sleep(1) # 礼貌延迟
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return ""
            
            # Reddit 评论接口返回一个列表，[0] 是帖子信息，[1] 是评论树
            comments_data = response.json()[1]['data']['children']
            top_comments = []
            
            for comment in comments_data[:limit]:
                if comment['kind'] == 't1': # 确保是评论
                    c_data = comment['data']
                    body = c_data.get('body', '').strip()
                    ups = c_data.get('ups', 0)
                    if body and body != '[deleted]' and body != '[removed]':
                        top_comments.append(f"💬 (Ups: {ups}): {body}")
            
            if top_comments:
                return "\n\n--- 热门评论 ---\n" + "\n\n".join(top_comments)
        except Exception as e:
            self.logger.warning(f"Failed to fetch comments for {permalink}: {e}")
        return ""

    def scrape(self):
        subs = ["MachineLearning", "ArtificialInteligence", "OpenAI", "LocalLLaMA"]
        for sub in subs:
            last_timestamp = self.get_last_id(sub)
            url = f"https://www.reddit.com/r/{sub}/new.json?limit=25"
            try:
                response = requests.get(url, headers=self.headers)
                data = response.json()
                
                newest_timestamp = None
                
                for post in data['data']['children']:
                    p_data = post['data']
                    created_utc = str(int(p_data['created_utc']))
                    
                    # 增量判断
                    if last_timestamp and int(created_utc) <= int(last_timestamp):
                        self.logger.info(f"⏱️ Reached last seen post in r/{sub}, stopping.")
                        break
                    
                    if newest_timestamp is None:
                        newest_timestamp = created_utc
                    
                    # 🧵 获取热门评论增强内容
                    comments_text = self._get_top_comments(p_data['permalink'])
                    full_content = (p_data['selftext'] or "") + comments_text

                    # 🖼️ 提取多媒体
                    media_urls = []
                    if p_data.get('thumbnail') and p_data['thumbnail'].startswith('http'):
                        media_urls.append(p_data['thumbnail'])
                    if p_data.get('url') and any(p_data['url'].endswith(ext) for ext in ['.jpg', '.png', '.gif', '.jpeg']):
                        if p_data['url'] not in media_urls:
                            media_urls.append(p_data['url'])

                    # 🤖 AI 评分与理由
                    score, reason = evaluator.evaluate(p_data['title'], full_content)

                    item = {
                        "platform": "reddit",
                        "external_id": p_data['id'],
                        "title": p_data['title'],
                        "content": full_content,
                        "url": f"https://reddit.com{p_data['permalink']}",
                        "published_at": datetime.fromtimestamp(p_data['created_utc']).isoformat(),
                        "score": score,
                        "reason": reason,
                        "media_urls": media_urls,
                        "metadata_json": {
                            "subreddit": sub,
                            "ups": p_data['ups'],
                            "num_comments": p_data['num_comments'],
                            "author": p_data['author']
                        }
                    }
                    self.push_to_backend(item)
                
                # 更新游标
                if newest_timestamp:
                    self.update_last_id(sub, newest_timestamp)
                    
            except Exception as e:
                self.logger.error(f"Error scraping Reddit r/{sub}: {e}")

import json
from bs4 import BeautifulSoup

class TwitterScraper(BaseScraper):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("twitter", api_url)
        self.ai_accounts = [
            "OpenAI", "DeepSeek_AI", "MistralAI", "GoogleDeepMind", "ylecun", "karpathy",
            "AnthropicAI", "sama", "gdb", "demishassabis", "perplexity_ai", "Cohere",
            "NVIDIAAI", "MetaAI", "AndrewYNg", "ArowLau"
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
                        media_entries = tweet.get('entities', {}).get('media', [])
                        for m in media_entries:
                            media_urls.append(m.get('media_url_https'))
                        
                        # 如果有扩展媒体 (如视频、多图)
                        ext_media = tweet.get('extended_entities', {}).get('media', [])
                        for m in ext_media:
                            m_url = m.get('media_url_https')
                            if m_url not in media_urls:
                                media_urls.append(m_url)
                        
                        # 🤖 AI 评分与理由
                        score, reason = evaluator.evaluate(f"Tweet from @{username}", full_content)

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

class ProductHuntScraper(BaseScraper):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("ph", api_url)
        self.rss_url = "https://www.producthunt.com/feed"

    def scrape(self):
        try:
            import feedparser
            self.logger.info("📦 Scraping Product Hunt RSS feed...")
            last_timestamp = self.get_last_id("ph_main")
            feed = feedparser.parse(self.rss_url)
            
            newest_timestamp = None
            for entry in feed.entries:
                # 获取时间戳字符串用于比较
                published_ts = str(int(datetime(*entry.published_parsed[:6]).timestamp()))
                
                if last_timestamp and int(published_ts) <= int(last_timestamp):
                    self.logger.info("⏱️ Reached last seen Product Hunt post, stopping.")
                    break
                
                if newest_timestamp is None:
                    newest_timestamp = published_ts

                if any(k in (entry.title + entry.get('summary', '')).lower() for k in ["ai ", "gpt", "llm", "bot"]):
                    # 🖼️ 提取多媒体
                    media_urls = []
                    for link in entry.get('links', []):
                        if link.get('type') == 'image/jpeg' or link.get('type') == 'image/png':
                            media_urls.append(link.get('href'))
                    
                    # 🧩 提取更详细的内容 (RSS feed 可能包含 summary 和 content)
                    rich_content = entry.get('summary', '')
                    if entry.get('content'):
                        # 如果有 content_list，通常包含更详细的描述
                        rich_content = entry.get('content')[0].value
                    
                    # 🤖 AI 评分与理由
                    score, reason = evaluator.evaluate(entry.title, rich_content)

                    item = {
                        "platform": "ph",
                        "external_id": entry.id.split('/')[-1],
                        "title": entry.title,
                        "content": rich_content,
                        "url": entry.link,
                        "published_at": datetime.fromtimestamp(int(published_ts)).isoformat(),
                        "score": score,
                        "reason": reason,
                        "media_urls": media_urls,
                        "metadata_json": {
                            "author": entry.get("author", "Unknown")
                        }
                    }
                    self.push_to_backend(item)
            
            if newest_timestamp:
                self.update_last_id("ph_main", newest_timestamp)
                
        except Exception as e:
            self.logger.error(f"Error scraping Product Hunt: {e}")
