from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
import hashlib
from typing import List

router = APIRouter()

# 存储根目录
MEDIA_ROOT = "data/media"
if not os.path.exists(MEDIA_ROOT):
    os.makedirs(MEDIA_ROOT, exist_ok=True)

@router.post("/upload")
async def upload_media(file: UploadFile = File(...)):
    """接收并保存媒体文件，按 MD5 去重"""
    try:
        # 1. 先读入内存（对图片/短视频没问题）计算 MD5
        content = await file.read()
        md5_hash = hashlib.md5(content).hexdigest()
        
        # 2. 构造文件名 (保持原始后缀)
        ext = os.path.splitext(file.filename)[1].lower() if file.filename else ".jpg"
        file_name = f"{md5_hash}{ext}"
        file_path = os.path.join(MEDIA_ROOT, file_name)
        
        # 3. 检查去重：如果文件已存在，直接返回链接
        if not os.path.exists(file_path):
            with open(file_path, "wb") as f:
                f.write(content)
        
        # 4. 返回本站 URL 路径
        # 注意：这里返回的是相对路径，由前端或配置拼接完整域名
        return {
            "url": f"/f/{file_name}",
            "filename": file_name,
            "size": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
