import logging
import argparse
import os
from dotenv import load_dotenv
from scrapers.engines.hn import HNScraper
from scrapers.engines.platforms import RedditScraper, TwitterScraper, ProductHuntScraper

# 加载 .env 文件
load_dotenv()

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def run_scrapers(target_platform: str = None):
    # 获取后端 API 地址
    api_url = os.getenv("SCRAPER_API_URL", "http://localhost:8000")
    
    # 所有可用引擎
    all_engines = [
        HNScraper(api_url=api_url),
        RedditScraper(api_url=api_url),
        TwitterScraper(api_url=api_url),
        ProductHuntScraper(api_url=api_url),
    ]
    
    # 如果指定了平台，则进行过滤
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI News Nexus Scraper Runner")
    parser.add_argument("--platform", "-p", help="Specific platform to scrape (hn, reddit, twitter, ph)")
    args = parser.parse_args()
    
    run_scrapers(args.platform)
