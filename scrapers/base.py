import requests
from datetime import datetime
import logging

class BaseScraper:
    def __init__(self, platform: str, api_url: str = "http://localhost:8000"):
        self.platform = platform
        self.api_url = api_url
        self.logger = logging.getLogger(f"scraper.{platform}")

    def push_to_backend(self, item: dict):
        try:
            response = requests.post(f"{self.api_url}/news/", json=item)
            if response.status_code == 200:
                self.logger.info(f"Successfully pushed: {item['title']}")
            else:
                self.logger.error(f"Failed to push: {response.text}")
        except Exception as e:
            self.logger.error(f"Error pushing to backend: {e}")

    def scrape(self):
        raise NotImplementedError("Subclasses must implement scrape()")
