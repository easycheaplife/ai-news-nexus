import logging
import argparse
import os
import time
import random
from dotenv import load_dotenv
from datetime import datetime
import requests

from scrapers.utils.ai import evaluator
from scrapers.engines.hn import HNScraper
from scrapers.engines.reddit import RedditScraper
from scrapers.engines.twitter import TwitterScraper
from scrapers.engines.ph import ProductHuntScraper
from scrapers.engines.github import GitHubScraper
from scrapers.engines.arxiv import ArxivScraper
from scrapers.engines.youtube import YouTubeScraper
from scrapers.engines.labs import LabsScraper
from scrapers.engines.huggingface import HuggingFaceScraper
from scrapers.engines.trend_hunter import TrendHunterScraper
from scrapers.discovery_run import DiscoveryEngine
from scrapers.curation_run import SourceCurator
from scrapers.utils.clustering import ClusteringEngine
from scrapers.utils.report_engine import run_report_generation
from scrapers.utils.youtube_radar import YouTubeDiscoveryRadar

# 加载 .env 文件
load_dotenv()

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def generate_daily_insights(api_url: str, style: str = "toxic"):
    """
    抓取后分析逻辑：从后端获取今日资讯，进行聚类分析并生成 AI 战略简报
    """
    logging.info(f"🧠 Starting AI Deep Insights synthesis ({style} style)...")
    try:
        # 1. 获取近期资讯用于分析 (进一步增加到 1000 条以获得极致深度的关联)
        response = requests.get(f"{api_url}/news/", params={"limit": 1000})
            
        if response.status_code != 200:
            logging.error(f"❌ Failed to fetch news for analysis: {response.text}")
            return

        all_news = response.json()
        if not all_news:
            logging.warning("⚠️ No news found to analyze.")
            return
        
        # 2. 按 cluster_id 聚合
        clusters = {}
        platform_counts = {}
        all_keywords = []
        
        for item in all_news:
            # 统计平台分布
            p = item['platform']
            platform_counts[p] = platform_counts.get(p, 0) + 1
            
            # 收集关键词用于统计
            if item.get('trending_keywords'):
                all_keywords.extend(item['trending_keywords'])

            cid = item.get('cluster_id')
            if not cid: continue
            
            if cid not in clusters:
                clusters[cid] = {"cluster_id": cid, "count": 0, "reasons": []}
            
            clusters[cid]["count"] += 1
            if item.get('reason'):
                clusters[cid]["reasons"].append(item['reason'])

        # 3. 提取最高频的 12 个关键词作为 hot_topics (替代 UUID)
        from collections import Counter
        import re

        normalized_keywords = []
        for kw in all_keywords:
            if not kw or len(kw) < 2: continue
            # 基础归一化：小写 -> 去空格 -> 去掉结尾的 's' (简单的单复数合并) -> 去掉连字符
            norm = kw.lower().strip().rstrip('s').replace('-', '')
            normalized_keywords.append((norm, kw)) # 记录归一化后的词和原始词

        # 统计频次
        kw_counts = Counter([n[0] for n in normalized_keywords])

        # 映射回最常见的原始写法
        final_kws = []
        seen_norms = set()
        for norm, count in kw_counts.most_common(15):
            if norm in seen_norms: continue
            # 找到这个归一化词对应的最原始写法（比如取最长的一个，通常更准确）
            original_variations = [n[1] for n in normalized_keywords if n[0] == norm]
            best_original = max(set(original_variations), key=original_variations.count)
            final_kws.append(best_original)
            seen_norms.add(norm)

        # 4. 排序并取前 25 个热点进行总结
        sorted_clusters = sorted(clusters.values(), key=lambda x: x['count'], reverse=True)

        if not sorted_clusters:
            logging.warning("⚠️ No topic clusters found to summarize.")
            return

        # 5. 调用 AI 生成简报
        briefing_content = evaluator.summarize_clusters(sorted_clusters, style=style)

        # 6. 获取今日处理的全量总数
        total_count = len(all_news)
        try:
            platform_counts['Total'] = total_count
        except: pass
        # 7. 回传到后端存储 (统一使用本地日期，确保与截图引擎对齐)
        today_str = datetime.now().strftime('%Y-%m-%d')
        insight_data = {
            "date": today_str,
            "content": briefing_content,
            "hot_topics": final_kws[:8], # 这里现在存的是去重后的真关键词
            "stats_json": platform_counts
        }
        
        res = requests.post(f"{api_url}/insights/", json=insight_data)

        if res.status_code in (200, 201):
            logging.info(f"✅ Daily Strategic Briefing ({today_str}) successfully archived.")
            # 自动生成日报图片 (传递明确的日期)
            try:
                run_report_generation(today_str)
            except Exception as e:
                logging.error(f"❌ Failed to generate automated report: {e}")
        else:
            logging.error(f"❌ Failed to archive briefing: {res.text}")

    except Exception as e:
        logging.error(f"Error during insight generation: {e}")


def run_scrapers(target_platform: str = None, 
                 do_discovery: bool = True,
                 do_scrape: bool = True,
                 do_clustering: bool = True,
                 do_curation: bool = True,
                 do_insights: bool = True,
                 do_report: bool = True,
                 style: str = "toxic"):
    # 获取后端 API 地址
    api_url = os.getenv("SCRAPER_API_URL", "http://localhost:8000")
    
    # 1. 运行信源自动发现与扩张 (Expansion)
    if do_discovery and not target_platform:
        discovery_engine = DiscoveryEngine(api_url)
        discovery_engine.run_expansion()
    else:
        logging.info("⏩ Skipping discovery phase")

    # 2. 运行可用采集引擎
    if do_scrape:
        all_engines = [
            HNScraper(api_url=api_url),
            RedditScraper(api_url=api_url),
            TwitterScraper(api_url=api_url),
            ProductHuntScraper(api_url=api_url),
            GitHubScraper(api_url=api_url),
            ArxivScraper(api_url=api_url),
            YouTubeScraper(api_url=api_url),
            LabsScraper(api_url=api_url),
            HuggingFaceScraper(api_url=api_url)
        ]
        
        if target_platform:
            engines = [e for e in all_engines if e.platform.lower() == target_platform.lower()]
            if not engines:
                logging.error(f"❌ Platform '{target_platform}' not found. Available: {[e.platform for e in all_engines]}")
                return
        else:
            engines = all_engines
        
        for engine in engines:
            logging.info(f"🚀 Starting {engine.platform} engine...")
            try:
                engine.scrape()
            except Exception as e:
                logging.error(f"❌ Error in {engine.platform} engine: {e}")
    else:
        logging.info("⏩ Skipping account scraping phase")

    # 3. 运行语义聚类 (Clustering) - 在抓取完成后
    if do_clustering and not target_platform:
        clustering_engine = ClusteringEngine(api_url)
        clustering_engine.run_clustering()
    else:
        logging.info("⏩ Skipping clustering phase")
            
    # 4. 运行信源质量评价与汰换 (Curation)
    if do_curation and not target_platform:
        curator = SourceCurator(api_url)
        curator.run_curation()
    else:
        logging.info("⏩ Skipping curation phase")
        
    # 5. 运行 YouTube 发现雷达 (YouTube Radar)
    # 只有在全局运行或者显式指定 youtube 平台时才运行雷达，且必须开启了 scrape 开关
    if do_scrape and (not target_platform or target_platform.lower() == "youtube"):
        yt_radar = YouTubeDiscoveryRadar(api_url)
        yt_radar.run()
    else:
        logging.info("⏩ Skipping YouTube radar phase")

    # 6. 抓取结束后自动生成今日 AI 深度洞察
    if do_insights and not target_platform:
        # 如果未指定风格，随机选择毒舌或正经版
        actual_style = style
        if not actual_style:
            actual_style = random.choice(["toxic", "official"])
            logging.info(f"🎲 No style specified. Randomly selected: {actual_style}")
            
        generate_daily_insights(api_url, style=actual_style)
    else:
        logging.info("⏩ Skipping insights generation phase")

    # 7. 生成日报图片 (仅当手动指定 --report 且不跑 insights 时)
    if do_report and not target_platform and not do_insights:
        logging.info("📸 Manually triggering report generation...")
        try:
            run_report_generation()
        except Exception as e:
            logging.error(f"❌ Report generation failed: {e}")

    logging.info("🏁 All requested tasks finished successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI News Nexus Scraper Runner")
    
    # 功能开关 (默认不设置，通过后续逻辑判断)
    parser.add_argument("--discovery", action="store_true", help="Run discovery engine")
    parser.add_argument("--scrape", "-s", action="store_true", help="Run scraping engines")
    parser.add_argument("--clustering", action="store_true", help="Run clustering engine")
    parser.add_argument("--curation", action="store_true", help="Run curation engine")
    parser.add_argument("--insights", action="store_true", help="Run insights generation")
    parser.add_argument("--report", action="store_true", help="Run report image generation")
    
    # 禁用特定功能的便捷开关
    parser.add_argument("--no-discovery", action="store_true", help="Explicitly disable discovery engine")
    parser.add_argument("--no-scrape", action="store_true", help="Explicitly disable scraping engines")
    parser.add_argument("--no-clustering", action="store_true", help="Explicitly disable clustering engine")
    parser.add_argument("--no-curation", action="store_true", help="Explicitly disable curation engine")
    parser.add_argument("--no-insights", action="store_true", help="Explicitly disable insights generation")
    parser.add_argument("--no-report", action="store_true", help="Explicitly disable report generation")

    parser.add_argument("--platform", "-p", help="Specific platform to scrape (hn, reddit, twitter, ph)")
    parser.add_argument("--style", choices=["toxic", "official"], help="Report style: toxic or official (default: random)")
    parser.add_argument("--loop", "-l", action="store_true", help="Run in continuous loop mode")
    parser.add_argument("--interval", "-i", type=int, default=3600, help="Wait interval between loops in seconds (default: 3600)")
    
    args = parser.parse_args()
    
    # 逻辑判断：如果用户显式指定了任何正向功能参数，则只运行指定的。否则，默认全部开启。
    any_positive_flag_set = args.discovery or args.scrape or args.clustering or args.curation or args.insights or args.report
    
    do_discovery = args.discovery if any_positive_flag_set else True
    do_scrape = args.scrape if any_positive_flag_set else True
    do_clustering = args.clustering if any_positive_flag_set else True
    do_curation = args.curation if any_positive_flag_set else True
    do_insights = args.insights if any_positive_flag_set else True
    do_report = args.report if any_positive_flag_set else True

    # 显式禁用的优先级最高
    if args.no_discovery: do_discovery = False
    if args.no_scrape: do_scrape = False
    if args.no_clustering: do_clustering = False
    if args.no_curation: do_curation = False
    if args.no_insights: do_insights = False
    if args.no_report: do_report = False

    if args.loop:
        logging.info(f"🔄 Entering continuous loop mode (Interval: {args.interval}s)")
        while True:
            run_scrapers(args.platform, do_discovery, do_scrape, do_clustering, do_curation, do_insights, do_report, style=args.style)
            logging.info(f"⏳ Sleeping for {args.interval}s before next run...")
            time.sleep(args.interval)
    else:
        run_scrapers(args.platform, do_discovery, do_scrape, do_clustering, do_curation, do_insights, do_report, style=args.style)
