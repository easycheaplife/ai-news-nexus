import asyncio
import os
import logging
from playwright.async_api import async_playwright
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("report_engine")

class ReportEngine:
    def __init__(self, frontend_url: str = None, output_dir: str = None):
        self.frontend_url = frontend_url or os.getenv("REPORT_FRONTEND_URL", "http://localhost:8000/report")
        self.output_dir = output_dir or os.getenv("REPORT_OUTPUT_DIR", "backend/data/reports")
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    async def generate_daily_report(self, date_str: str = None):
        """
        Generate a PNG report for a specific date (default: today)
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
            
        output_path = os.path.join(self.output_dir, f"{date_str}.png")
        logger.info(f"📸 Generating report for {date_str} -> {output_path}")

        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                viewport={'width': 800, 'height': 1200},
                device_scale_factor=2 # Retina quality
            )

            try:
                # Visit the report template
                # We can append ?date=date_str if the frontend supports it, 
                # but currently it fetches latest.
                target_url = self.frontend_url
                logger.info(f"🌐 Navigating to {target_url}")
                
                await page.goto(target_url, wait_until="networkidle")
                
                # Wait for the "ready" signal from the Vue component
                logger.info("⏳ Waiting for report readiness signal...")
                await page.wait_for_selector("#report-ready", timeout=30000, state="attached")
                
                # Take the screenshot of the specific element
                element = await page.query_selector("#report-content")
                if element:
                    await element.screenshot(path=output_path)
                    logger.info(f"✅ Report successfully saved: {output_path}")
                    return output_path
                else:
                    logger.error("❌ Could not find #report-content element")
                    return None

            except Exception as e:
                logger.error(f"❌ Failed to generate report: {e}")
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
