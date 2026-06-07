import feedparser
import requests
from datetime import datetime
from .base import BaseScraper
import time
import re
import random
import urllib.parse

class DomesticMediaScraper(BaseScraper):
    """
    国内头部 AI 媒体聚合引擎 (增强版 v4)
    利用 Google News Search 作为高可靠的“绕路”方案，
    同时结合 RSSHub 镜像，确保在官网封锁下依然能获取信号。
    """
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__(platform="domestic_media", api_url=api_url, region="cn")
        
        self.rsshub_instances = [
            "https://rsshub.rssforever.com",
            "https://hub.slarker.me",
            "https://rsshub.pseudoyu.com",
            "https://rsshub.rss.tips"
        ]
        
        # 具体的媒体配置与搜索关键词
        self.media_configs = {
            "synced": {
                "name": "机器之心",
                "search_query": "机器之心 AI",
                "site_query": "site:jiqizhixin.com",
                "rsshub_path": "/wechat/wasi/5b575dd058e5c4583338dbd3",
                "display_name": "机器之心"
            },
            "aiera": {
                "name": "新智元",
                "search_query": "新智元 大模型",
                "site_query": "site:xinzhiyuan.com",
                "rsshub_path": "/xinzhiyuan/latest",
                "display_name": "新智元"
            },
            "paperweekly": {
                "name": "PaperWeekly",
                "search_query": "PaperWeekly AI 论文",
                "site_query": "site:paperweekly.site",
                "rsshub_path": "/paperweekly/latest",
                "display_name": "PaperWeekly"
            },
            "founderpark": {
                "name": "Founder Park",
                "search_query": "Founder Park 极客公园",
                "site_query": "site:geekpark.net",
                "display_name": "Founder Park"
            },
            "guizang": {
                "name": "归藏",
                "search_query": "归藏 AI",
                "rsshub_path": "/wechat/blog/归藏",
                "display_name": "归藏"
            },
            "infoq": {
                "name": "InfoQ",
                "search_query": "InfoQ AI",
                "site_query": "site:infoq.cn",
                "rsshub_path": "/infoq/topic/AI",
                "display_name": "InfoQ"
            },
            "tmtpost": {
                "name": "钛媒体",
                "search_query": "钛媒体 AI",
                "site_query": "site:tmtpost.com",
                "rsshub_path": "/tmtpost/column/50",
                "display_name": "钛媒体"
            }
        }
        
        # Google News Search Base
        # 使用 zh-CN, CN 确保搜到的是国内媒体内容
        self.gn_base = "https://news.google.com/rss/search?q={query}+when:48h&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"

    def _fetch_gn_rss(self, query):
        """通过 Google News RSS 搜索获取资讯"""
        try:
            encoded_query = urllib.parse.quote(query)
            url = self.gn_base.format(query=encoded_query)
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"}
            
            # 搜索建议不走代理，或者直连 Google News (取决于环境)
            # 在国内环境通常需要代理，但在某些 GitHub Runner 或境外 Server 不需要
            res = requests.get(url, headers=headers, timeout=12)
            if res.status_code == 200:
                return res.content
        except Exception as e:
            self.logger.debug(f"Google News search failed for {query}: {e}")
        return None

    def _fetch_rsshub(self, path):
        """通过 RSSHub 镜像轮询"""
        random.shuffle(self.rsshub_instances)
        for instance in self.rsshub_instances:
            try:
                url = f"{instance.rstrip('/')}{path}"
                res = requests.get(url, timeout=10)
                if res.status_code == 200 and ('<rss' in res.text.lower() or '<feed' in res.text.lower()):
                    return res.content
            except: continue
        return None

    def scrape(self):
        self.logger.info(f"🇨🇳 Starting Domestic Media scraping (v4 Strategic Search)...")
        
        for platform_key, config in self.media_configs.items():
            try:
                entries = []
                
                # 方案 1: Google News Domain Search (最精准)
                if config.get("site_query"):
                    self.logger.info(f"🔍 Searching Google News (Site): {config['name']}")
                    content = self._fetch_gn_rss(config["site_query"])
                    if content:
                        feed = feedparser.parse(content)
                        entries.extend(feed.entries)
                
                # 方案 2: Google News Keyword Search (高信号)
                if not entries and config.get("search_query"):
                    self.logger.info(f"🔍 Searching Google News (Keyword): {config['name']}")
                    content = self._fetch_gn_rss(config["search_query"])
                    if content:
                        feed = feedparser.parse(content)
                        entries.extend(feed.entries)

                # 方案 3: RSSHub (作为备份)
                if not entries and config.get("rsshub_path"):
                    self.logger.info(f"📡 Trying RSSHub: {config['name']}")
                    content = self._fetch_rsshub(config["rsshub_path"])
                    if content:
                        feed = feedparser.parse(content)
                        entries.extend(feed.entries)

                if not entries:
                    self.logger.warning(f"❌ Failed to find recent content for {config['name']}")
                    continue

                self.logger.info(f"✅ Found {len(entries)} items for {config['name']}")
                self._process_entries(entries, platform_key, config)

            except Exception as e:
                self.logger.error(f"Error scraping {config['name']}: {e}")

        self.logger.info("🏁 Domestic Media scraping finished.")

    def _process_entries(self, entries, platform_key, config):
        processed_count = 0
        for entry in entries[:10]: # 每个源只取前 10 条
            title = entry.title
            url = entry.link
            
            # Google News 的标题通常带有 " - 来源" 后缀，需要清理
            title = re.sub(r'\s-\s.*$', '', title).strip()

            # 过滤掉非 AI 相关的内容 (Google News 搜索可能引入噪音)
            ai_keywords = ["ai", "llm", "gpt", "大模型", "智能体", "agent", "rag", "深度学习", "机器学习", "transformer", "claude", "deepseek", "sora", "算力", "英伟达", "nvidia"]
            if not any(k in title.lower() for k in ai_keywords):
                continue

            dt = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
            
            if dt and not self.is_within_window(dt):
                continue

            external_id = entry.id if hasattr(entry, 'id') else url
            
            # 🛡️ 兼容性处理：如果 ID 过长（Google News 常见），进行哈希处理以适配数据库 VARCHAR(255)
            if len(external_id) > 255:
                import hashlib
                external_id = hashlib.md5(external_id.encode()).hexdigest()
            
            # 推送到后端
            self.push_to_backend({
                "platform": platform_key,
                "external_id": external_id,
                "title": f"📰 {title}",
                "content": title, # 搜索结果通常只有标题
                "url": url,
                "author": config['display_name'],
                "published_at": dt.isoformat() if dt else datetime.utcnow().isoformat(),
                "score": 0,
                "metadata_json": {
                    "source": config['name'],
                    "discovery_type": "google_news_search"
                }
            })
            processed_count += 1
        
        self.logger.info(f"📝 Processed {processed_count} relevant items for {config['name']}")
