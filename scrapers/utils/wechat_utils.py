import requests
import logging
import re

logger = logging.getLogger("scraper.wechat_utils")

def extract_wechat_full_text(url: str) -> str:
    """使用 r.jina.ai 穿透抓取公众号全文"""
    if "mp.weixin.qq.com" not in url:
        return ""
        
    jina_url = f"https://r.jina.ai/{url}"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "X-With-Generated-Alt": "true" # 尝试让 Jina 生成图片的描述
        }
        res = requests.get(jina_url, headers=headers, timeout=30)
        if res.status_code == 200:
            content = res.text
            # 基础清洗逻辑
            if "Markdown Content:" in content:
                content = content.split("Markdown Content:")[1]
            
            # 移除多余的 Jina 脚注
            content = re.sub(r'\[Source\].*$', '', content, flags=re.DOTALL)
            
            return content.strip()[:10000] # 公众号文章通常较长
    except Exception as e:
        logger.warning(f"Failed to fetch WeChat full text via Jina: {e}")
    return ""
