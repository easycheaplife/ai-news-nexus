import asyncio
import os
import logging
import requests
from playwright.async_api import async_playwright
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("report_engine")

class ReportEngine:
    def __init__(self, frontend_url: str = None, api_url: str = None, output_dir: str = None):
        # 统一使用 .env 中的 SCRAPER_API_URL
        self.api_url = (api_url or os.getenv("SCRAPER_API_URL", "http://localhost:8000")).rstrip('/')
        
        # 截图访问地址，如果未指定则默认使用 API 地址下的 /report 路由
        self.frontend_url = frontend_url or os.getenv("REPORT_FRONTEND_URL", f"{self.api_url}/report")
        self.output_dir = output_dir or "backend/data/reports"
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    async def generate_daily_report(self, date_str: str = None):
        """
        Generate a PNG report for a specific date (default: today),
        then upload it to the backend media service and update the database.
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
            
        temp_path = os.path.join(self.output_dir, f"temp_{date_str}.png")
        logger.info(f"📸 Generating report for {date_str} -> {temp_path}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                viewport={'width': 800, 'height': 1200},
                device_scale_factor=2
            )

            try:
                logger.info(f"🌐 Navigating to {self.frontend_url}")
                await page.goto(self.frontend_url, wait_until="networkidle")
                
                logger.info("⏳ Waiting for report readiness signal...")
                await page.wait_for_selector("#report-ready", timeout=30000, state="attached")
                
                element = await page.query_selector("#report-content")
                if not element:
                    logger.error("❌ Could not find #report-content element")
                    return None
                    
                await element.screenshot(path=temp_path)
                logger.info(f"✅ Screenshot captured at: {temp_path}")

                # 🚀 Upload to backend media service
                upload_url = f"{self.api_url}/api/media/upload"
                logger.info(f"📤 Uploading report to {upload_url}...")
                
                with open(temp_path, "rb") as f:
                    files = {"file": (f"{date_str}.png", f, "image/png")}
                    res = requests.post(upload_url, files=files, timeout=30)
                
                if res.status_code != 200:
                    logger.error(f"❌ Upload failed: {res.text}")
                    return None
                
                report_data = res.json()
                report_url = report_data.get("url")
                logger.info(f"✅ Uploaded! URL: {report_url}")

                # 💾 Update DailyInsight in database
                logger.info(f"💾 Updating database for date {date_str}...")
                update_res = requests.patch(
                    f"{self.api_url}/api/insights/{date_str}", 
                    json={"report_url": report_url},
                    timeout=10
                )
                
                if update_res.status_code in [200, 201]:
                    logger.info(f"✨ Successfully updated report_url for {date_str}")
                    # Clean up temp file
                    # os.remove(temp_path)
                    return report_url
                else:
                    logger.error(f"❌ Database update failed: {update_res.text}")
                    return None

            except Exception as e:
                logger.error(f"❌ Failed to generate/upload report: {e}")
                return None
            finally:
                await browser.close()

def run_report_generation(date_str: str = None):
    """
    Synchronous wrapper to run the async generation
    """
    engine = ReportEngine()
    return asyncio.run(engine.generate_daily_report(date_str))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    run_report_generation(target_date)
