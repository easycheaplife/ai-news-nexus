import logging
import sys
import os
from scrapers.utils.report_engine import run_report_generation
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("manual_report")

def main():
    """
    Manual trigger for report generation.
    Usage: python3 scrapers/generate_report.py [YYYY-MM-DD]
    """
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    
    logger.info("🎬 Manually triggering report generation...")
    try:
        path = run_report_generation(target_date)
        if path:
            logger.info(f"✨ Success! Report generated at: {path}")
        else:
            logger.error("❌ Failed to generate report.")
    except Exception as e:
        logger.error(f"❌ Error during manual report generation: {e}")

if __name__ == "__main__":
    main()
