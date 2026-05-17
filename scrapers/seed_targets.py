import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_targets")

API_URL = os.getenv("SCRAPER_API_URL", "http://localhost:8000")

TWITTER_KOLS = [
    # 原有核心账号
    ("OpenAI", "Official OpenAI account"),
    ("DeepSeek_AI", "Open-source LLM challenger"),
    ("MistralAI", "European AI leader"),
    ("GoogleDeepMind", "DeepMind researchers"),
    ("ylecun", "Yann LeCun, Meta Chief AI Scientist"),
    ("karpathy", "Andrej Karpathy, AI Developer"),
    ("AnthropicAI", "Claude developers"),
    ("sama", "Sam Altman, CEO of OpenAI"),
    ("gdb", "Greg Brockman, OpenAI co-founder"),
    ("demishassabis", "Demis Hassabis, DeepMind CEO"),
    ("perplexity_ai", "AI Search disruptor"),
    ("Cohere", "Enterprise AI focus"),
    
    # 新增头部 KOL
    ("DrJimFan", "Jim Fan, NVIDIA Senior AI Scientist"),
    ("fchollet", "Francois Chollet, Keras creator"),
    ("bindureddy", "Bindu Reddy, Abacus.ai CEO"),
    ("AravSrinivas", "Aravind Srinivas, Perplexity CEO"),
    ("levelsio", "Indie AI Hacker"),
    ("swyx", "Latent Space podcast / AI Engineer"),
    ("RowanChevalier", "High-signal AI content curator"),
    ("shaneleg", "Shane Legg, Google DeepMind co-founder"),
    ("ilyasut", "Ilya Sutskever, SSI / OpenAI co-founder"),
    ("woj_zaremba", "Wojciech Zaremba, OpenAI co-founder"),
    ("p_george", "George Hotz, Comma.ai / tinygrad")
]

def seed_twitter_targets():
    logger.info(f"Seeding Twitter KOLs to {API_URL}...")
    for handle, desc in TWITTER_KOLS:
        payload = {
            "platform": "twitter",
            "handle": handle,
            "name": handle,
            "description": desc,
            "is_active": True
        }
        try:
            res = requests.post(f"{API_URL}/targets/", json=payload, timeout=5)
            if res.status_code == 200:
                logger.info(f"✅ Target added: @{handle}")
            else:
                logger.error(f"❌ Failed to add @{handle}: {res.text}")
        except Exception as e:
            logger.error(f"Error seeding @{handle}: {e}")

if __name__ == "__main__":
    seed_twitter_targets()
