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

            # 📝 Capture browser console logs for debugging
            page.on("console", lambda msg: logger.info(f"🌐 [Browser Console] {msg.text}"))
            page.on("pageerror", lambda exc: logger.error(f"❌ [Browser Error] {exc}"))
            
            # 修复之前的 AttributeError
            async def handle_request_failed(request):
                error_text = request.failure if isinstance(request.failure, str) else (request.failure.get("errorText") if isinstance(request.failure, dict) else "Unknown")
                logger.warning(f"⚠️ [Network Error] {request.method} {request.url} - {error_text}")
            
            page.on("requestfailed", handle_request_failed)

            try:
                logger.info(f"🌐 Navigating to {self.frontend_url}")
                response = await page.goto(self.frontend_url, wait_until="domcontentloaded", timeout=60000)
                
                if not response or response.status != 200:
                    status_code = response.status if response else 'No Response'
                    logger.error(f"❌ Failed to load page: {status_code}")
                    if status_code == 404:
                        logger.error("🚀 Hint: The /report route returned 404. This means your CLOUD SERVER needs 'npm run build' inside the frontend folder and a uvicorn restart.")
                    return None

                logger.info("⏳ Waiting for report readiness signal (#report-ready)...")
                try:
                    # 使用较短的等待，如果没取到数据也强制截图
                    await page.wait_for_selector("#report-ready", timeout=15000, state="attached")
                except Exception as e:
                    logger.warning("⚠️ Readiness signal timeout. The page might be empty or API failed.")
                
                # 给一定的渲染缓冲时间
                await asyncio.sleep(2)
                
                element = await page.query_selector("#report-content")
                if not element:
                    logger.error("❌ Could not find #report-content element. Is the page rendering correctly?")
                    # Screenshot the whole page to debug
                    await page.screenshot(path=temp_path.replace(".png", "_error_full.png"))
                    return None
                    
                await element.screenshot(path=temp_path)
                logger.info(f"✅ Screenshot captured at: {temp_path}")

                # 🚀 Upload to backend media service (matching MediaMirror pattern)
                # Using /media/upload (legacy support) or /api/media/upload
                # We'll try the /api/ one first as it's the new standard
                upload_url = f"{self.api_url}/api/media/upload"
                logger.info(f"📤 Uploading report to {upload_url}...")
                
                with open(temp_path, "rb") as f:
                    # File name for the upload is descriptive, backend will rename it to MD5
                    files = {"file": (f"daily-report-{date_str}.png", f, "image/png")}
                    res = requests.post(upload_url, files=files, timeout=30)
                
                if res.status_code != 200:
                    # Fallback to legacy endpoint if new one fails
                    upload_url_legacy = f"{self.api_url}/media/upload"
                    logger.info(f"⚠️ New API failed, retrying legacy upload to {upload_url_legacy}...")
                    with open(temp_path, "rb") as f:
                        files = {"file": (f"daily-report-{date_str}.png", f, "image/png")}
                        res = requests.post(upload_url_legacy, files=files, timeout=30)
                
                if res.status_code != 200:
                    logger.error(f"❌ All upload attempts failed: {res.text}")
                    return None
                
                report_data = res.json()
                # Backend returns path starting with /f/
                report_url = report_data.get("url")
                logger.info(f"✅ Uploaded to media pool! URL: {report_url}")

                # 💾 Update DailyInsight in database with the consistent relative path
                logger.info(f"💾 Reporting report_url to database for {date_str}...")
                update_res = requests.patch(
                    f"{self.api_url}/api/insights/{date_str}", 
                    json={"report_url": report_url},
                    timeout=10
                )
                
                if update_res.status_code in [200, 201]:
                    logger.info(f"✨ Successfully linked report to database record.")
                    # Clean up temp file after successful reporting
                    try:
                        os.remove(temp_path)
                        logger.info(f"🗑️ Cleaned up temporary screenshot.")
                    except: pass
                    return report_url
                else:
                    logger.error(f"❌ Database reporting failed: {update_res.text}")
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
