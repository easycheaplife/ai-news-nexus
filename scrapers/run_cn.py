import subprocess
import sys
import os

def main():
    """
    国内 AI 资讯采集入口
    主要用于国内云服务器，实时抓取 AI HOT、微信公众号等国内信源。
    """
    print("🇨🇳 Starting Domestic (CN) AI Scrapers...")
    
    # 构建命令
    cmd = [
        sys.executable, "-m", "scrapers.run",
        "--scrape",
        "--region", "cn"
        # 移除了 --insights，国内节点只采集，不分析
    ]
    
    # 透传剩余参数
    cmd.extend(sys.argv[1:])
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ CN Scrapers failed with exit code {e.returncode}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
