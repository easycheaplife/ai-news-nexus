import asyncio
import os
import logging
from twikit import Client
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def generate_cookies():
    # 从环境变量读取配置
    username = os.getenv("TWITTER_USERNAME")
    email = os.getenv("TWITTER_EMAIL")
    password = os.getenv("TWITTER_PASSWORD")

    if not all([username, email, password]):
        logging.error("❌ 缺少 Twitter 账号配置！请确保 .env 文件中包含 TWITTER_USERNAME, TWITTER_EMAIL 和 TWITTER_PASSWORD。")
        return

    # 初始化 Client
    # 注意：为了稳定，如果你在 .env 配置了代理，应当传给 Client
    proxy = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
    client = Client('en-US', proxy=proxy)

    cookies_path = 'scrapers/cookies.json'

    logging.info(f"🚀 尝试使用账号 @{username} 进行登录...")
    try:
        await client.login(
            auth_info_1=username,
            auth_info_2=email,
            password=password
        )
        
        # 保存 Cookie 以供主爬虫使用
        client.save_cookies(cookies_path)
        logging.info(f"✅ 登录成功！Cookie 已保存至: {cookies_path}")
        
    except Exception as e:
        logging.error(f"❌ 登录失败: {e}")
        logging.error("如果提示输入验证码或邮箱验证，可能需要手动提取 Cookie。")

if __name__ == "__main__":
    asyncio.run(generate_cookies())
