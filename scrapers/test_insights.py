import logging
import os
from dotenv import load_dotenv
from scrapers.run import generate_daily_insights

load_dotenv()
logging.basicConfig(level=logging.INFO)

api_url = os.getenv("SCRAPER_API_URL", "http://localhost:8000")
generate_daily_insights(api_url)
