import requests
import os
from ..base import BaseScraper
from datetime import datetime
from ntscraper import Nitter
from twikit import Client
import asyncio

class RedditScraper(BaseScraper):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("reddit", api_url)
        self.reddit_url = "https://www.reddit.com/r/MachineLearning/new.json?limit=50"
        self.headers = {"User-Agent": "AI News Bot 1.0"}

    def scrape(self):
        subs = ["MachineLearning", "ArtificialInteligence", "OpenAI", "LocalLLaMA"]
        for sub in subs:
            url = f"https://www.reddit.com/r/{sub}/new.json?limit=25"
            try:
                response = requests.get(url, headers=self.headers)
                data = response.json()
                for post in data['data']['children']:
                    p_data = post['data']
                    item = {
                        "platform": "reddit",
                        "external_id": p_data['id'],
                        "title": p_data['title'],
                        "content": p_data['selftext'],
                        "url": f"https://reddit.com{p_data['permalink']}",
                        "published_at": datetime.fromtimestamp(p_data['created_utc']).isoformat(),
                        "metadata_json": {
                            "subreddit": sub,
                            "ups": p_data['ups'],
                            "num_comments": p_data['num_comments'],
                            "author": p_data['author']
                        }
                    }
                    self.push_to_backend(item)
            except Exception as e:
                self.logger.error(f"Error scraping Reddit r/{sub}: {e}")

import json
from bs4 import BeautifulSoup

class TwitterScraper(BaseScraper):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("twitter", api_url)
        self.ai_accounts = ["OpenAI", "DeepSeek_AI", "MistralAI", "GoogleDeepMind", "ylecun", "karpathy"]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def scrape(self):
        self.logger.info("🚀 Starting Twitter scraping via Syndication API (No-Login)...")
        
        for username in self.ai_accounts:
            try:
                self.logger.info(f"👤 Scraping tweets from: @{username}")
                url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}"
                
                response = requests.get(url, headers=self.headers, timeout=15)
                if response.status_code != 200:
                    self.logger.error(f"❌ Failed to fetch timeline for @{username}: HTTP {response.status_code}")
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')
                # Twitter 嵌入页面将数据存储在 <script id="__NEXT_DATA__"> 中
                script_tag = soup.find('script', id='__NEXT_DATA__')
                
                if not script_tag:
                    self.logger.error(f"❌ Could not find data script for @{username}. Page structure might have changed.")
                    continue

                data = json.loads(script_tag.string)
                
                # 提取推文列表
                # 路径通常是: props -> pageProps -> timeline -> entries
                try:
                    timeline = data['props']['pageProps']['timeline']['entries']
                except KeyError:
                    self.logger.error(f"❌ Unexpected data structure for @{username}")
                    continue

                for entry in timeline:
                    try:
                        tweet = entry.get('content', {}).get('tweet')
                        if not tweet:
                            continue
                        
                        tweet_id = tweet['id_str']
                        text = tweet.get('full_text', tweet.get('text', ''))
                        
                        # 解析推特日期格式: "Mon May 11 13:10:12 +0000 2026"
                        raw_date = tweet.get('created_at')
                        published_at = datetime.utcnow().isoformat()
                        if raw_date:
                            try:
                                # Twitter 日期格式转换
                                dt = datetime.strptime(raw_date, '%a %b %d %H:%M:%S +0000 %Y')
                                published_at = dt.isoformat()
                            except Exception as date_e:
                                self.logger.warning(f"Date parsing failed for {raw_date}: {date_e}")

                        item = {
                            "platform": "twitter",
                            "external_id": tweet_id,
                            "title": f"Tweet from @{username}: " + (text[:80] + "..."),
                            "content": text,
                            "url": f"https://twitter.com/{username}/status/{tweet_id}",
                            "published_at": published_at,
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
            feed = feedparser.parse(self.rss_url)
            for entry in feed.entries:
                if any(k in (entry.title + entry.get('summary', '')).lower() for k in ["ai ", "gpt", "llm", "bot"]):
                    item = {
                        "platform": "ph",
                        "external_id": entry.id.split('/')[-1],
                        "title": entry.title,
                        "content": entry.get('summary', ''),
                        "url": entry.link,
                        "published_at": datetime.utcnow().isoformat(),
                        "metadata_json": {
                            "author": entry.get("author", "Unknown")
                        }
                    }
                    self.push_to_backend(item)
        except Exception as e:
            self.logger.error(f"Error scraping Product Hunt: {e}")
