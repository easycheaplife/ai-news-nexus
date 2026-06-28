import feedparser
import requests
from datetime import datetime
from .base import BaseScraper
import time
import re
import random
import urllib.parse
import hashlib

class DomesticMediaScraper(BaseScraper):
    """
    国内头部 AI 媒体聚合引擎 (增强版 v4)
    利用 官方RSS直连、Google News Search、RSSHub 镜像 三位一体，
    确保在不同网络环境下都能稳定获取信号。
    """
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__(platform="domestic_media", api_url=api_url, region="cn")
        
        self.rsshub_instances = [
            "https://rsshub.rssforever.com",
            "https://hub.slarker.me",
            "https://rsshub.pseudoyu.com",
            "https://rsshub.rss.tips",
            "https://rsshub.moeyy.cn",
            "https://rsshub.m-moe.xyz",
            "https://rsshub.lihaile.biz",
            "https://rsshub.app"
        ]
        
        # 具体的媒体配置与搜索关键词 (增加官方 RSS)
        self.media_configs = {
            "synced": {
                "name": "机器之心",
                "official_rss": "https://www.jiqizhixin.com/rss",
                "search_query": "机器之心 AI 深度学习",
                "site_query": "site:jiqizhixin.com AI",
                "rsshub_path": "/wechat/wasi/5b575dd058e5c4583338dbd3",
                "display_name": "机器之心"
            },
            "aiera": {
                "name": "新智元",
                "official_rss": "http://www.xinzhiyuan.com/feed",
                "search_query": "新智元 大模型 机器人",
                "site_query": "site:xinzhiyuan.com AI",
                "rsshub_path": "/xinzhiyuan/latest",
                "display_name": "新智元"
            },
            "paperweekly": {
                "name": "PaperWeekly",
                "official_rss": "https://www.paperweekly.site/rss",
                "search_query": "PaperWeekly AI 论文 算法",
                "site_query": "site:paperweekly.site",
                "rsshub_path": "/paperweekly/latest",
                "display_name": "PaperWeekly"
            },
            "founderpark": {
                "name": "Founder Park",
                "official_rss": "https://www.geekpark.net/rss",
                "search_query": "Founder Park 极客公园 AI 应用",
                "site_query": "site:geekpark.net AI",
                "display_name": "Founder Park"
            },
            "guizang": {
                "name": "归藏",
                "search_query": "归藏 AI 提示词",
                "rsshub_path": "/wechat/blog/归藏",
                "display_name": "归藏"
            },
            "infoq": {
                "name": "InfoQ",
                "official_rss": "https://www.infoq.cn/feed",
                "search_query": "InfoQ 机器学习 架构",
                "site_query": "site:infoq.cn AI",
                "rsshub_path": "/infoq/topic/AI",
                "display_name": "InfoQ"
            },
            "tmtpost": {
                "name": "钛媒体",
                "official_rss": "https://www.tmtpost.com/rss.xml",
                "search_query": "钛媒体 AI 数字化",
                "site_query": "site:tmtpost.com AI",
                "rsshub_path": "/tmtpost/column/50",
                "display_name": "钛媒体"
            },
            "ithome": {
                "name": "IT之家",
                "official_rss": "https://www.ithome.com/rss/",
                "display_name": "IT之家"
            },
            "kr36": {
                "name": "36Kr",
                "official_rss": "https://36kr.com/feed",
                "display_name": "36Kr"
            }
        }
        
        self.gn_base = "https://news.google.com/rss/search?q={query}+when:48h&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"

    def _fetch_gn_rss(self, query):
        try:
            encoded_query = urllib.parse.quote(query)
            url = self.gn_base.format(query=encoded_query)
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
            res = requests.get(url, headers=headers, timeout=12)
            if res.status_code == 200:
                return res.content
        except Exception as e:
            self.logger.debug(f"Google News search failed for {query}: {e}")
        return None

    def _fetch_rsshub(self, path):
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
        import os
        skip_google = os.getenv("SKIP_GOOGLE_SEARCH", "false").lower() == "true"
        
        for platform_key, config in self.media_configs.items():
            try:
                entries = []
                
                # 1. 官方 RSS 直连 (优先级最高)
                if config.get("official_rss"):
                    self.logger.info(f"📡 Trying Official RSS: {config['name']}")
                    try:
                        res = requests.get(config["official_rss"], timeout=10)
                        if res.status_code == 200:
                            feed = feedparser.parse(res.content)
                            if feed.entries:
                                entries.extend(feed.entries)
                    except: pass
                
                # 2. Google News Search (如果开启)
                if not entries and not skip_google:
                    if config.get("site_query"):
                        self.logger.info(f"🔍 Searching Google News (Site): {config['name']}")
                        content = self._fetch_gn_rss(config["site_query"])
                        if content:
                            feed = feedparser.parse(content)
                            entries.extend(feed.entries)
                    
                    if not entries and config.get("search_query"):
                        self.logger.info(f"🔍 Searching Google News (Keyword): {config['name']}")
                        content = self._fetch_gn_rss(config["search_query"])
                        if content:
                            feed = feedparser.parse(content)
                            entries.extend(feed.entries)
                elif not entries and skip_google:
                    self.logger.info(f"⏩ Skipping Google Search for {config['name']}")

                # 3. RSSHub (兜底)
                if not entries and config.get("rsshub_path"):
                    self.logger.info(f"📡 Trying RSSHub mirrors: {config['name']}")
                    content = self._fetch_rsshub(config["rsshub_path"])
                    if content:
                        feed = feedparser.parse(content)
                        entries.extend(feed.entries)

                if not entries:
                    self.logger.warning(f"❌ Failed to find recent content for {config['name']}")
                    continue
                
                # Sort entries by publication time descending (newest first)
                entries.sort(key=lambda e: e.get('published_parsed', time.struct_time((0,0,0,0,0,0,0,0,0))), reverse=True)

                self.logger.info(f"✅ Found {len(entries)} items for {config['name']}")
                last_id = self.get_last_id(platform_key)
                self._process_entries(entries, platform_key, config, last_id)

            except Exception as e:
                self.logger.error(f"Error scraping {config['name']}: {e}")

        self.logger.info("🏁 Domestic Media scraping finished.")

    def _process_entries(self, entries, platform_key, config, last_id=None):
        processed_count = 0
        new_max_id = last_id
        import re
        strict_ai_keywords = ["llm", "gpt", "大模型", "智能体", "agent", "rag", "深度学习", "机器学习", "transformer", "claude", "deepseek", "sora", "算力", "英伟达", "nvidia", "生成式", "语言模型", "向量数据库", "推理", "训练", "微调", "提示词", "prompt", "机器人", "自动驾驶", "端到端", "多模态", "aigc", "算力", "h100", "b200", "openrouter", "openai", "anthropic", "mistral", "llama", "qwen", "通义千问", "智谱", "kimi", "月之暗面", "零一万物", "百川智能", "面壁智能", "商汤", "字节跳动 ai"]
        blacklist = ["融资", "上市", "财报", "股价", "收购", "亏损", "裁员", "高管变动", "内斗", "手机", "数码", "笔记本", "游戏", "发布会", "预订", "开售", "javascript", "vue", "react", "css", "html", "mysql", "sql", "redis", "架构设计", "设计模式", "单元测试", "执行计划", "性能调优", "组件重构"]

        for entry in entries[:15]: 
            title = entry.title
            url = entry.link
            title = re.sub(r'\s-\s.*$', '', title).strip()
            
            # 🛡️ 截断超长 URL (针对 Google News 极端情况)，防止数据库插入报错
            clean_url = url
            if len(clean_url) > 500:
                if '?oc=' in clean_url:
                    clean_url = clean_url.split('?')[0]

            external_id = entry.id if hasattr(entry, 'id') else clean_url
            if len(external_id) > 255:
                external_id = hashlib.md5(external_id.encode()).hexdigest()

            # 🛑 如果遇到上次处理的 ID，说明后续的都是旧数据，直接停止
            if last_id and external_id == last_id:
                self.logger.debug(f"🛑 Reached last processed ID {last_id}, stopping.")
                break
            
            self.logger.debug(f"Processing ID: {external_id} (Last: {last_id})")

            title_lower = title.lower()
            has_standalone_ai = bool(re.search(r'\bai\b', title_lower))
            has_core_ai = any(k in title_lower for k in strict_ai_keywords)
            is_noise = any(k in title_lower for k in blacklist)
            if not (has_standalone_ai or has_core_ai) or is_noise: continue

            dt = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
            if dt and not self.is_within_window(dt): continue

            self.push_to_backend({
                "platform": platform_key,
                "external_id": external_id,
                "title": f"📰 {title}",
                "content": title, 
                "url": clean_url,
                "author": config['display_name'],
                "published_at": dt.isoformat() if dt else datetime.utcnow().isoformat(),
                "score": 0,
                "metadata_json": {"source": config['name'], "discovery_type": "official_or_search"}
            })
            processed_count += 1
            
            # 更新最新 ID
            if not new_max_id or external_id > str(new_max_id):
                new_max_id = external_id

        if new_max_id:
            self.update_last_id(platform_key, str(new_max_id))
            
        self.logger.info(f"📝 Processed {processed_count} relevant items for {config['name']}")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    s = DomesticMediaScraper()
    s.scrape()
