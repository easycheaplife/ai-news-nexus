import subprocess
import sys
import os

def main():
    """
    海外 AI 资讯采集入口
    主要用于海外服务器，抓取 Twitter, Reddit, HN, YouTube 等。
    """
    print("🌐 Starting Global AI Scrapers...")
    
    # 构建命令
    cmd = [
        sys.executable, "-m", "scrapers.run",
        "--discovery",
        "--scrape",
        "--curation",
        "--region", "global",
        "--insights"
    ]
    
    # 透传剩余参数
    cmd.extend(sys.argv[1:])
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Global Scrapers failed with exit code {e.returncode}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
