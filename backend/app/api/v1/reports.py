import os
from fastapi import APIRouter
from typing import List

router = APIRouter()

@router.get("/list", response_model=List[str])
def list_reports():
    reports_dir = "data/reports"
    if not os.path.exists(reports_dir):
        return []
    
    # 获取所有 .png 文件
    try:
        files = [f for f in os.listdir(reports_dir) if f.endswith(".png")]
        # 按日期降序排列 (文件名格式为 YYYY-MM-DD.png)
        files.sort(reverse=True)
        return files
    except Exception:
        return []
