import requests
import os
import io
import logging
from typing import List, Optional
from urllib.parse import urlparse

logger = logging.getLogger("scraper.media_mirror")

class MediaMirror:
    def __init__(self, api_url: str):
        self.api_url = api_url.rstrip('/')
        # 允许转存的文件后缀
        self.allowed_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.mp4', '.webm']

    def mirror_all(self, urls: List[str]) -> List[str]:
        """将一组外部 URL 转存到自有服务器，返回新的 URL 列表"""
        if not urls:
            return []
        
        mirrored_urls = []
        for url in urls:
            new_url = self.mirror_one(url)
            if new_url:
                mirrored_urls.append(new_url)
            else:
                # 如果转存失败，保留原始 URL 以免显示空白（虽然国内可能打不开）
                mirrored_urls.append(url)
        return mirrored_urls

    def mirror_one(self, url: str) -> Optional[str]:
        """转存单个文件"""
        if not url: return None
        
        # 1. 检查后缀
        parsed = urlparse(url)
        ext = os.path.splitext(parsed.path)[1].lower()
        if not ext and '?' in url: # 处理带参数的 URL 如 ?name=orig
            ext = os.path.splitext(url.split('?')[0])[1].lower()
        
        if ext not in self.allowed_exts:
            # 如果没后缀但包含特定视频标识，强制设为 mp4
            if any(k in url.lower() for k in ['video', 'ext_tw_video', 'amplify_video']):
                ext = '.mp4'
            else:
                ext = '.jpg'

        try:
            # 2. 下载文件 (使用代理，如果有配置)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            # 这里的下载应该走系统的代理配置
            response = requests.get(url, headers=headers, timeout=20, stream=True)
            if response.status_code != 200:
                return None
            
            # 3. 将二进制流直接 POST 到后端上传接口
            file_data = response.content
            files = {
                'file': (f"temp{ext}", file_data)
            }
            
            upload_res = requests.post(f"{self.api_url}/media/upload", files=files, timeout=30)
            if upload_res.status_code == 200:
                result = upload_res.json()
                # 构造完整的公网链接 (如果后端返回的是相对路径)
                # 我们优先把相对路径存入数据库，前端根据当前域名拼接，或者后端返回绝对路径
                return result.get('url')
            
        except Exception as e:
            logger.warning(f"Failed to mirror media {url}: {e}")
        
        return None
