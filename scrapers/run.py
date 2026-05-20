import logging
import argparse
import os
import time
from dotenv import load_dotenv
from datetime import datetime
import requests

from scrapers.utils.ai import evaluator
from scrapers.engines.hn import HNScraper
from scrapers.engines.reddit import RedditScraper
from scrapers.engines.twitter import TwitterScraper
from scrapers.engines.ph import ProductHuntScraper
from scrapers.engines.github import GitHubScraper
from scrapers.engines.arxiv import ArxivScraper
from scrapers.engines.youtube import YouTubeScraper
from scrapers.engines.trend_hunter import TrendHunterScraper
from scrapers.discovery_run import DiscoveryEngine
from scrapers.curation_run import SourceCurator

# 加载 .env 文件
load_dotenv()

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def generate_daily_insights(api_url: str):
    """
    抓取后分析逻辑：从后端获取今日资讯，进行聚类分析并生成 AI 战略简报
    """
    logging.info("🧠 Starting AI Deep Insights synthesis...")
    try:
        # 1. 获取近期资讯用于分析
        response = requests.get(f"{api_url}/news/", params={"limit": 200})
        if response.status_code != 200:
            logging.error(f"❌ Failed to fetch news for analysis: {response.text}")
            return

        all_news = response.json()
        if not all_news:
            logging.warning("⚠️ No news found to analyze.")
            return
        
        # 2. 按 cluster_id 聚合
        clusters = {}
        platform_counts = {}
        for item in all_news:
            # 统计平台分布
            p = item['platform']
            platform_counts[p] = platform_counts.get(p, 0) + 1

            cid = item.get('cluster_id')
            if not cid: continue
            
            if cid not in clusters:
                clusters[cid] = {"cluster_id": cid, "count": 0, "reasons": []}
            
            clusters[cid]["count"] += 1
            if item.get('reason'):
                clusters[cid]["reasons"].append(item['reason'])

        # 3. 排序并取前 10 个热点
        sorted_clusters = sorted(clusters.values(), key=lambda x: x['count'], reverse=True)
        
        # 4. 调用 AI 生成简报
        briefing_content = evaluator.summarize_clusters(sorted_clusters)
        
        # 5. 回传到后端存储 (使用 UTC 日期)
        today = datetime.utcnow().strftime('%Y-%m-%d')
        insight_data = {
            "date": today,
            "content": briefing_content,
            "hot_topics": [c['cluster_id'] for c in sorted_clusters[:8]],
            "stats_json": platform_counts
        }
        
        res = requests.post(f"{api_url}/insights/", json=insight_data)
        if res.status_code == 200:
            logging.info("✅ Daily Strategic Briefing successfully archived.")
        else:
            logging.error(f"❌ Failed to archive briefing: {res.text}")

    except Exception as e:
        logging.error(f"Error during insight generation: {e}")

def run_scrapers(target_platform: str = None, 
                 do_discovery: bool = True,
                 do_scrape: bool = True,
                 do_curation: bool = True,
                 do_insights: bool = True):
    # 获取后端 API 地址
    api_url = os.getenv("SCRAPER_API_URL", "http://localhost:8000")
    
    # 1. 运行信源自动发现与扩张 (Expansion)
    if do_discovery and not target_platform:
        discovery_engine = DiscoveryEngine(api_url)
        discovery_engine.run_expansion()
    else:
        logging.info("⏩ Skipping discovery phase")

    # 2. 运行可用采集引擎
    if do_scrape:
        all_engines = [
            HNScraper(api_url=api_url),
            RedditScraper(api_url=api_url),
            TwitterScraper(api_url=api_url),
            ProductHuntScraper(api_url=api_url),
            GitHubScraper(api_url=api_url),
            ArxivScraper(api_url=api_url),
            YouTubeScraper(api_url=api_url)
        ]
        
        if target_platform:
            engines = [e for e in all_engines if e.platform.lower() == target_platform.lower()]
            if not engines:
                logging.error(f"❌ Platform '{target_platform}' not found. Available: {[e.platform for e in all_engines]}")
                return
        else:
            engines = all_engines
        
        for engine in engines:
            logging.info(f"🚀 Starting {engine.platform} engine...")
            try:
                engine.scrape()
            except Exception as e:
                logging.error(f"❌ Error in {engine.platform} engine: {e}")
    else:
        logging.info("⏩ Skipping account scraping phase")
            
    # 3. 运行信源质量评价与汰换 (Curation)
    if do_curation and not target_platform:
        curator = SourceCurator(api_url)
        curator.run_curation()
    else:
        logging.info("⏩ Skipping curation phase")
        
    # 4. 抓取结束后自动生成今日 AI 深度洞察
    if do_insights and not target_platform:
        generate_daily_insights(api_url)
    else:
        logging.info("⏩ Skipping insights generation phase")

    logging.info("🏁 All requested tasks finished successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI News Nexus Scraper Runner")
    
    # 功能开关 (默认全部 True)
    parser.add_argument("--discovery", action="store_true", default=True, help="Run discovery engine (default: True)")
    parser.add_argument("--scrape", action="store_true", default=True, help="Run scraping engines (default: True)")
    parser.add_argument("--curation", action="store_true", default=True, help="Run curation engine (default: True)")
    parser.add_argument("--insights", action="store_true", default=True, help="Run insights generation (default: True)")
    
    # 禁用特定功能的便捷开关
    parser.add_argument("--no-discovery", action="store_false", dest="discovery", help="Disable discovery engine")
    parser.add_argument("--no-scrape", action="store_false", dest="scrape", help="Disable scraping engines")
    parser.add_argument("--no-curation", action="store_false", dest="curation", help="Disable curation engine")
    parser.add_argument("--no-insights", action="store_false", dest="insights", help="Disable insights generation")

    parser.add_argument("--platform", "-p", help="Specific platform to scrape (hn, reddit, twitter, ph)")
    parser.add_argument("--loop", "-l", action="store_true", help="Run in continuous loop mode")
    parser.add_argument("--interval", "-i", type=int, default=3600, help="Wait interval between loops in seconds (default: 3600)")
    
    args = parser.parse_args()
    
    # 如果用户显式指定了任何 --do-X 参数，而没有指定其他的，Argparse 会处理默认值。
    # 这里的逻辑是：默认全部开启。
    
    if args.loop:
        logging.info(f"🔄 Entering continuous loop mode (Interval: {args.interval}s)")
        while True:
            run_scrapers(args.platform, args.discovery, args.scrape, args.curation, args.insights)
            logging.info(f"⏳ Sleeping for {args.interval}s before next run...")
            time.sleep(args.interval)
    else:
        run_scrapers(args.platform, args.discovery, args.scrape, args.curation, args.insights)
