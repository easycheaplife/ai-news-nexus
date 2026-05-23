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

GITHUB_TARGETS = [
    ("huggingface", "Home of open-source AI models"),
    ("microsoft", "Major AI research and tools (phi, olive, etc.)"),
    ("google", "Google's open-source projects"),
    ("meta-llama", "Official Llama model repository"),
    ("langchain-ai", "LLM orchestration framework"),
    ("openai", "OpenAI open-source repositories"),
    ("anthropics", "Anthropic's open-source contributions"),
    ("deepseek-ai", "DeepSeek-V2 and other open-source models"),
    ("comfyanonymous", "ComfyUI creator"),
    ("AUTOMATIC1111", "Stable Diffusion WebUI"),
    ("karpathy", "AI education and small implementations")
]

def seed_twitter_targets():
    logger.info(f"Seeding Twitter KOLs to {API_URL}...")
    for handle, desc in TWITTER_KOLS:
        handle = handle.strip()
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
                logger.info(f"✅ Twitter target added: @{handle}")
            else:
                logger.error(f"❌ Failed to add @{handle}: {res.text}")
        except Exception as e:
            logger.error(f"Error seeding @{handle}: {e}")

def seed_github_targets():
    logger.info(f"Seeding GitHub Targets to {API_URL}...")
    for handle, desc in GITHUB_TARGETS:
        handle = handle.strip()
        payload = {
            "platform": "github",
            "handle": handle,
            "name": handle,
            "description": desc,
            "is_active": True
        }
        try:
            res = requests.post(f"{API_URL}/targets/", json=payload, timeout=5)
            if res.status_code == 200:
                logger.info(f"✅ GitHub target added: {handle}")
            else:
                logger.error(f"❌ Failed to add {handle}: {res.text}")
        except Exception as e:
            logger.error(f"Error seeding {handle}: {e}")

if __name__ == "__main__":
    seed_twitter_targets()
    seed_github_targets()
