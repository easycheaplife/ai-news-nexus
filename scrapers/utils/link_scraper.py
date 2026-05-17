import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import urlparse

logger = logging.getLogger("scraper.link_scraper")

def scrape_link_content(url: str) -> str:
    """抓取并提炼外部链接的核心内容摘要"""
    if not url or not url.startswith('http'):
        return ""
    
    # 排除一些不需要抓取的域名
    parsed = urlparse(url)
    if parsed.netloc in ['twitter.com', 'x.com', 'reddit.com', 'github.com', 'arxiv.org', 'youtube.com']:
        return ""

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code != 200:
            return ""

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. 尝试提取 meta description
        meta_desc = ""
        description_tag = soup.find('meta', attrs={'name': 'description'}) or \
                          soup.find('meta', attrs={'property': 'og:description'})
        if description_tag:
            meta_desc = description_tag.get('content', '').strip()

        # 2. 尝试提取正文前 500 字 (简单的正文剥离)
        # 移除脚本和样式
        for script in soup(["script", "style"]):
            script.extract()
            
        # 获取纯文本
        text = soup.get_text(separator=' ')
        # 简单的清洗逻辑：去除多余空格
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # 截取精华部分
        body_summary = clean_text[:800]
        
        full_summary = f"外部文章摘要:\n{meta_desc}\n\n文章内容片段:\n{body_summary}"
        return full_summary.strip()

    except Exception as e:
        logger.warning(f"Failed to scrape external link {url}: {e}")
        return ""
