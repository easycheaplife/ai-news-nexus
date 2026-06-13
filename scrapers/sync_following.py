import json
import os
import requests
import logging
from twikit import Client
from dotenv import load_dotenv

# 加载配置
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("sync_following")

def sync():
    api_url = os.getenv("SCRAPER_API_URL", "http://localhost:8000")
    cookies_path = 'scrapers/cookies.json'
    my_twitter_handle = os.getenv("TWITTER_USERNAME")

    if not os.path.exists(cookies_path):
        logger.error(f"❌ {cookies_path} 不存在，请先生成 Cookie。")
        return
    
    if not my_twitter_handle:
        logger.error("❌ 请在 .env 中设置 TWITTER_USERNAME。")
        return

    # 1. 初始化 Twikit 并加载 Cookie
    client = Client('en-US')
    try:
        with open(cookies_path, 'r', encoding='utf-8') as f:
            client.set_cookies(json.load(f))
        logger.info(f"🍪 已成功加载 Cookie。")
    except Exception as e:
        logger.error(f"❌ 加载 Cookie 失败: {e}")
        return

    # 2. 获取自己的用户信息及关注列表
    try:
        me = client.get_user_by_screen_name(my_twitter_handle)
        logger.info(f"👤 正在获取 @{my_twitter_handle} 的关注列表...")
        # twikit 1.1.29 的 get_user_following 返回一个可以迭代的列表/结果对象
        following_users = client.get_user_following(me.id, count=200) # 假设关注数不多，一次拉取
        logger.info(f"📡 发现 {len(following_users)} 个正在关注的账号。")
    except Exception as e:
        logger.error(f"❌ 获取关注列表失败: {e}")
        return

    # 3. 同步到后端
    new_count = 0
    exist_count = 0
    
    for u in following_users:
        handle = u.screen_name
        name = u.name
        description = getattr(u, 'description', '')
        
        # 检查是否已存在于抓取目标中
        try:
            check_res = requests.get(f"{api_url}/targets/", params={"platform": "twitter", "handle": handle}, timeout=5)
            if check_res.status_code == 200:
                data = check_res.json()
                if data and len(data) > 0:
                    # 如果已存在且被停用了，尝试重新激活它
                    target = data[0]
                    if not target.get('is_active'):
                        logger.info(f"🔄 重新激活已关注的账号: @{handle}")
                        requests.patch(f"{api_url}/targets/{target['id']}", json={"is_active": True, "status": "active"}, timeout=5)
                    exist_count += 1
                    continue
            
            # 如果不存在，则添加
            payload = {
                "platform": "twitter",
                "handle": handle,
                "name": name,
                "description": description,
                "is_active": True,
                "status": "active"
            }
            add_res = requests.post(f"{api_url}/targets/", json=payload, timeout=5)
            if add_res.status_code == 200:
                logger.info(f"✅ 已同步新关注账号: @{handle} ({name})")
                new_count += 1
            else:
                logger.warning(f"⚠️ 添加 @{handle} 失败: {add_res.text}")
                
        except Exception as e:
            logger.error(f"❌ 同步 @{handle} 时出错: {e}")

    logger.info(f"🏁 同步完成！新增: {new_count}, 已存在/激活: {exist_count}")

if __name__ == "__main__":
    sync()
