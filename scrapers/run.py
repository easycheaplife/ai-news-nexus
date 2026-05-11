import logging
from scrapers.engines.hn import HNScraper
from scrapers.engines.platforms import RedditScraper

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def run_scrapers():
    # 以后可以扩展更多引擎
    engines = [
        HNScraper(),
        RedditScraper(),
    ]
    
    for engine in engines:
        logging.info(f"🚀 Starting {engine.platform} engine...")
        try:
            engine.scrape()
        except Exception as e:
            logging.error(f"❌ Error in {engine.platform} engine: {e}")

if __name__ == "__main__":
    run_scrapers()
