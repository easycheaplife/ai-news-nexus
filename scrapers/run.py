import logging
import argparse
import os
import time
import random
from dotenv import load_dotenv
from datetime import datetime, timedelta
import requests

# 加载 .env 文件
load_dotenv()

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def generate_daily_insights(api_url: str, style: str = "toxic", skip_scoring: bool = False):
    """
    抓取后分析逻辑：从后端获取最近 24 小时资讯，进行聚类分析并生成 AI 战略简报
    """
    # 🚀 Lazy Load AI Utilities
    from scrapers.utils.ai import evaluator
    from scrapers.utils.report_engine import run_report_generation
    
    logging.info(f"🧠 Starting AI Deep Insights synthesis ({style} style)...")
    try:
        # 1. 获取最近 24 小时发布的内容进行分析
        lookback_start = datetime.now() - timedelta(hours=24)
        
        response = requests.get(
            f"{api_url}/news/", 
            params={
                "limit": 1000, 
                "start_date": lookback_start.isoformat()
            }
        )
            
        if response.status_code != 200:
            logging.error(f"❌ Failed to fetch news for analysis: {response.text}")
            return

        resp_json = response.json()
        all_news = resp_json.get("items", []) if isinstance(resp_json, dict) else resp_json
        
        if not all_news:
            logging.warning(f"⚠️ No news found since {lookback_start.date()} to analyze.")
            return
        
        # --- 🚀 核心优化：补偿性评价 ---
        evaluated_count = 0
        if not skip_scoring:
            for item in all_news:
                if item.get('score') == 0 and evaluator.enabled:
                    logging.info(f"🤖 Late-evaluating today's item: {item['title'][:30]}...")
                    score, reason, takeaways, cluster_id, users, keywords = evaluator.evaluate(item['title'], item['content'])
                    
                    update_payload = {
                        "score": score,
                        "reason": reason,
                        "takeaways": takeaways,
                        "cluster_id": cluster_id,
                        "mentioned_users": users,
                        "trending_keywords": keywords
                    }
                    try:
                        requests.patch(f"{api_url}/news/{item['id']}", json=update_payload)
                        item.update(update_payload)
                        evaluated_count += 1
                    except Exception as e:
                        logging.error(f"Failed to update evaluated item: {e}")
        
        if evaluated_count > 0:
            logging.info(f"✅ Completed catch-up evaluation for {evaluated_count} items.")
        elif skip_scoring:
            logging.info("⏩ Skipping individual item scoring phase as requested.")

        # 2. 按 cluster_id 聚合
        clusters = {}
        platform_counts = {}
        all_keywords = []
        
        for item in all_news:
            p = item['platform']
            platform_counts[p] = platform_counts.get(p, 0) + 1
            if item.get('trending_keywords'):
                all_keywords.extend(item['trending_keywords'])

            cid = item.get('cluster_id')
            if not cid: continue
            
            if cid not in clusters:
                clusters[cid] = {"cluster_id": cid, "count": 0, "reasons": []}
            
            clusters[cid]["count"] += 1
            if item.get('reason'):
                clusters[cid]["reasons"].append(item['reason'])

        # 3. 提取关键词
        from collections import Counter
        normalized_keywords = []
        for kw in all_keywords:
            if not kw or len(kw) < 2: continue
            norm = kw.lower().strip().rstrip('s').replace('-', '')
            normalized_keywords.append((norm, kw))

        kw_counts = Counter([n[0] for n in normalized_keywords])
        final_kws = []
        seen_norms = set()
        for norm, count in kw_counts.most_common(15):
            if norm in seen_norms: continue
            original_variations = [n[1] for n in normalized_keywords if n[0] == norm]
            best_original = max(set(original_variations), key=original_variations.count)
            final_kws.append(best_original)
            seen_norms.add(norm)

        # 4. 排序并取前 25 个热点进行总结
        sorted_clusters = sorted(clusters.values(), key=lambda x: x['count'], reverse=True)
        briefing_content = evaluator.summarize_clusters(sorted_clusters[:25], style=style)

        if not briefing_content:
            logging.error("❌ AI Insights generation failed. Skipping archival to protect existing data.")
            return

        # 5. 上传简报到后端
        today_str = datetime.now().strftime("%Y-%m-%d")
        insight_data = {
            "date": today_str,
            "content": briefing_content,
            "hot_topics": final_kws[:8],
            "stats_json": platform_counts
        }
        
        res = requests.post(f"{api_url}/api/insights/", json=insight_data)

        if res.status_code in (200, 201):
            logging.info(f"✅ Daily Strategic Briefing ({today_str}) successfully archived.")
            report_url = None
            try:
                report_url = run_report_generation(today_str)
            except Exception as e:
                logging.error(f"❌ Failed to generate automated report: {e}")

            from scrapers.utils.notifier import notifier
            try:
                notifier.notify_all(today_str, briefing_content, report_url)
            except Exception as e:
                logging.error(f"❌ Notification failed: {e}")
        else:
            logging.error(f"❌ Failed to archive briefing: {res.text}")

    except Exception as e:
        logging.error(f"Error during insight generation: {e}")


def run_scrapers(target_platform: str = None, 
                 target_region: str = None,
                 do_discovery: bool = True,
                 do_scrape: bool = True,
                 do_clustering: bool = True,
                 do_curation: bool = True,
                 do_insights: bool = True,
                 do_report: bool = True,
                 style: str = "toxic",
                 skip_scoring: bool = False,
                 date_str: str = None):
    api_url = os.getenv("SCRAPER_API_URL", "http://localhost:8000")
    
    if do_discovery and not target_platform and (not target_region or target_region.lower() == "global"):
        from scrapers.discovery_run import DiscoveryEngine
        discovery_engine = DiscoveryEngine(api_url)
        discovery_engine.run_expansion()
    else:
        logging.info("⏩ Skipping discovery phase")

    if do_scrape:
        # 🚀 Lazy Load All Scrapers to decouple dependencies like twikit/google-genai
        all_engines = []
        
        # CN / Domestic Engines (Minimal dependencies)
        from scrapers.engines.domestic_media import DomesticMediaScraper
        from scrapers.engines.aihot import AIHotScraper
        from scrapers.engines.qbitai import QbitAIScraper
        from scrapers.engines.kr36 import Kr36Scraper
        from scrapers.engines.juejin import JuejinScraper
        from scrapers.engines.ithome import ITHomeScraper
        from scrapers.engines.caict import CAICTScraper
        
        all_engines.extend([
            DomesticMediaScraper(api_url=api_url),
            AIHotScraper(api_url=api_url),
            QbitAIScraper(api_url=api_url),
            Kr36Scraper(api_url=api_url),
            JuejinScraper(api_url=api_url),
            ITHomeScraper(api_url=api_url),
            CAICTScraper(api_url=api_url)
        ])
        
        # Global Engines (Require proxy/Gemini/twikit)
        if not target_region or target_region.lower() == "global":
            from scrapers.engines.hn import HNScraper
            from scrapers.engines.reddit import RedditScraper
            from scrapers.engines.twitter import TwitterScraper
            from scrapers.engines.ph import ProductHuntScraper
            from scrapers.engines.github import GitHubScraper
            from scrapers.engines.arxiv import ArxivScraper
            from scrapers.engines.youtube import YouTubeScraper
            from scrapers.engines.labs import LabsScraper
            from scrapers.engines.huggingface import HuggingFaceScraper
            
            all_engines.extend([
                HNScraper(api_url=api_url),
                RedditScraper(api_url=api_url),
                TwitterScraper(api_url=api_url),
                ProductHuntScraper(api_url=api_url),
                GitHubScraper(api_url=api_url),
                ArxivScraper(api_url=api_url),
                YouTubeScraper(api_url=api_url),
                LabsScraper(api_url=api_url),
                HuggingFaceScraper(api_url=api_url)
            ])
        
        engines = all_engines
        if target_platform:
            engines = [e for e in engines if e.platform.lower() == target_platform.lower()]
        if target_region:
            engines = [e for e in engines if e.region.lower() == target_region.lower()]

        if not engines:
            logging.error(f"❌ No engines found for platform='{target_platform}' region='{target_region}'.")
            return
        
        for engine in engines:
            logging.info(f"🚀 Starting {engine.platform} ({engine.region}) engine...")
            try:
                engine.scrape()
            except Exception as e:
                logging.error(f"❌ Error in {engine.platform} engine: {e}")
    else:
        logging.info("⏩ Skipping account scraping phase")

    if do_clustering and not target_platform:
        from scrapers.utils.clustering import ClusteringEngine
        clustering_engine = ClusteringEngine(api_url)
        clustering_engine.run_clustering()
    else:
        logging.info("⏩ Skipping clustering phase")
            
    if do_curation and not target_platform and (not target_region or target_region.lower() == "global"):
        from scrapers.curation_run import SourceCurator
        curator = SourceCurator(api_url)
        curator.run_curation()
    else:
        logging.info("⏩ Skipping curation phase")
        
    if do_scrape and (not target_platform or target_platform.lower() == "youtube") and (not target_region or target_region.lower() == "global"):
        from scrapers.utils.youtube_radar import YouTubeDiscoveryRadar
        yt_radar = YouTubeDiscoveryRadar(api_url)
        yt_radar.run()
    else:
        logging.info("⏩ Skipping YouTube radar phase")

    if do_insights and not target_platform:
        actual_style = style
        if not actual_style:
            actual_style = random.choice(["toxic", "official"])
            logging.info(f"🎲 No style selected. Randomly selected: {actual_style}")
            
        generate_daily_insights(api_url, style=actual_style, skip_scoring=skip_scoring)

        # 🏺 Phase 1: 知识资产沉淀 (Knowledge Asset Curation)
        try:
            from scrapers.utils.asset_engine import AssetEngine
            asset_engine = AssetEngine(api_url)
            asset_engine.process_daily_assets()
        except Exception as e:
            logging.error(f"❌ Asset curation failed: {e}")
    else:
        logging.info("⏩ Skipping insights generation phase")

    if do_report and not target_platform and not do_insights:
        from scrapers.utils.report_engine import run_report_generation
        logging.info(f"📸 Manually triggering report generation for {date_str or 'today'}...")
        try:
            run_report_generation(date_str)
        except Exception as e:
            logging.error(f"❌ Report generation failed: {e}")

    logging.info("🏁 All requested tasks finished successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI News Nexus Scraper Runner")
    
    parser.add_argument("--discovery", action="store_true", help="Run discovery engine")
    parser.add_argument("--scrape", "-s", action="store_true", help="Run scraping engines")
    parser.add_argument("--clustering", action="store_true", help="Run clustering engine")
    parser.add_argument("--curation", action="store_true", help="Run curation engine")
    parser.add_argument("--insights", action="store_true", help="Run insights generation")
    parser.add_argument("--report", action="store_true", help="Run report image generation")
    
    parser.add_argument("--no-discovery", action="store_true", help="Explicitly disable discovery engine")
    parser.add_argument("--no-scrape", action="store_true", help="Explicitly disable scraping engines")
    parser.add_argument("--no-clustering", action="store_true", help="Explicitly disable clustering engine")
    parser.add_argument("--no-curation", action="store_true", help="Explicitly disable curation engine")
    parser.add_argument("--no-insights", action="store_true", help="Explicitly disable insights generation")
    parser.add_argument("--no-report", action="store_true", help="Explicitly disable report generation")

    parser.add_argument("--platform", "-p", help="Specific platform to scrape")
    parser.add_argument("--region", "-r", choices=["cn", "global"], help="Filter engines by region")
    parser.add_argument("--skip-scoring", action="store_true", help="Skip catch-up AI scoring for raw items")
    parser.add_argument("--style", choices=["toxic", "official"], help="Report style")
    parser.add_argument("--date", help="Target date for report generation (YYYY-MM-DD)")
    parser.add_argument("--loop", "-l", action="store_true", help="Run in continuous loop mode")
    parser.add_argument("--interval", "-i", type=int, default=3600, help="Wait interval in seconds")
    
    args = parser.parse_args()
    
    any_positive_flag_set = args.discovery or args.scrape or args.clustering or args.curation or args.insights or args.report
    do_discovery = args.discovery if any_positive_flag_set else True
    do_scrape = args.scrape if any_positive_flag_set else True
    do_clustering = args.clustering if any_positive_flag_set else True
    do_curation = args.curation if any_positive_flag_set else True
    do_insights = args.insights if any_positive_flag_set else True
    do_report = args.report if any_positive_flag_set else True

    if args.no_discovery: do_discovery = False
    if args.no_scrape: do_scrape = False
    if args.no_clustering: do_clustering = False
    if args.no_curation: do_curation = False
    if args.no_insights: do_insights = False
    if args.no_report: do_report = False

    if args.loop:
        logging.info(f"🔄 Entering continuous loop mode (Interval: {args.interval}s)")
        while True:
            run_scrapers(args.platform, args.region, do_discovery, do_scrape, do_clustering, do_curation, do_insights, do_report, style=args.style, skip_scoring=args.skip_scoring, date_str=args.date)
            logging.info(f"⏳ Sleeping for {args.interval}s before next run...")
            time.sleep(args.interval)
    else:
        run_scrapers(args.platform, args.region, do_discovery, do_scrape, do_clustering, do_curation, do_insights, do_report, style=args.style, skip_scoring=args.skip_scoring, date_str=args.date)
