import logging
import requests
import json
import subprocess
from datetime import datetime, timedelta
from scrapers.utils.ai import get_evaluator
evaluator = get_evaluator("gemini")
from scrapers.utils.media_mirror import MediaMirror
from youtube_transcript_api import YouTubeTranscriptApi

logger = logging.getLogger("youtube_radar")

class YouTubeDiscoveryRadar:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url.rstrip('/')
        self.mirror = MediaMirror(self.api_url)

    def _get_hot_keywords(self) -> list:
        """从后端获取过去 12 小时的热门技术关键词"""
        try:
            # 获取最近 1000 条资讯 (覆盖约 12-24 小时)
            res = requests.get(f"{self.api_url}/news/", params={"limit": 500})
            if res.status_code != 200:
                return []
            
            resp_json = res.json()
            all_news = resp_json.get("items", []) if isinstance(resp_json, dict) else resp_json
            keywords = []
            for item in all_news:
                # 仅统计高分资讯的关键词
                if item.get('score', 0) >= 80 and item.get('trending_keywords'):
                    keywords.extend(item['trending_keywords'])
            
            if not keywords:
                return []

            # 统计频次
            from collections import Counter
            counts = Counter([kw.lower().strip() for kw in keywords if len(kw) > 1])
            
            # 返回前 3 个最热的词
            return [item[0] for item in counts.most_common(3)]
        except Exception as e:
            logger.error(f"Failed to fetch hot keywords: {e}")
            return []

    def _search_videos(self, keyword: str) -> list:
        """使用 yt-dlp 无令牌搜索视频"""
        logger.info(f"🔍 Searching YouTube for: {keyword}")
        try:
            # 搜索过去 24 小时内最相关的 15 条视频
            # 使用 yt-dlp 命令行获取 JSON 信息
            cmd = [
                "yt-dlp",
                f"ytsearch15:{keyword}",
                "--dateafter", (datetime.now() - timedelta(days=1)).strftime("%Y%m%d"),
                "--dump-json",
                "--flat-playlist",
                "--quiet",
                "--no-warnings"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"yt-dlp search failed: {result.stderr}")
                return []
            
            videos = []
            for line in result.stdout.splitlines():
                if not line.strip(): continue
                video_data = json.loads(line)
                
                # 尝试从 thumbnails 列表中提取最高分辨率的预览图
                thumbnails = video_data.get("thumbnails", [])
                best_thumbnail = video_data.get("thumbnail") # 回退方案
                if thumbnails:
                    # 找到最宽的图
                    best_thumbnail = max(thumbnails, key=lambda x: x.get("width", 0)).get("url")

                videos.append({
                    "id": video_data.get("id"),
                    "title": video_data.get("title"),
                    "description": video_data.get("description") or "",
                    "url": f"https://www.youtube.com/watch?v={video_data.get('id')}",
                    "thumbnail": best_thumbnail
                })
            return videos
        except Exception as e:
            logger.error(f"Error during yt-dlp search: {e}")
            return []

    def _filter_with_ai(self, videos: list, keyword: str) -> list:
        """使用 AI 对搜索结果进行初筛"""
        if not videos: return []
        
        candidates = "\n".join([f"- [{v['id']}] {v['title']}: {v['description'][:100]}..." for v in videos])
        
        prompt = f"""
        你是 AI 行业资深雷达。以下是关于关键词 '{keyword}' 的 YouTube 搜索结果。
        请从中选出最具有深度技术含量、或是由知名专家/大厂发布、具有行业情报价值的 3 个视频 ID。
        排除短视频 (Shorts)、纯营销软广或低质量标题党。
        
        待选列表:
        {candidates}
        
        请严格按 JSON 格式返回: {{"selected_ids": ["id1", "id2", "id3"]}}
        """
        
        try:
            res = evaluator.generate_content(prompt)
            if not res: return videos[:3] # 降级：取前 3 个
            
            text = res.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            data = json.loads(text)
            selected_ids = data.get("selected_ids", [])
            
            return [v for v in videos if v['id'] in selected_ids]
        except Exception as e:
            logger.error(f"AI pre-filtering failed: {e}")
            return videos[:3]

    def _get_transcript(self, video_id: str) -> str:
        """获取视频字幕"""
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            try:
                transcript = transcript_list.find_transcript(['zh-Hans', 'zh-CN', 'en'])
            except:
                transcript = next(iter(transcript_list))
            
            data = transcript.fetch()
            return " ".join([t['text'] for t in data])[:3000]
        except:
            return ""

    def run(self):
        logger.info("📡 Activating YouTube Discovery Radar...")
        
        keywords = self._get_hot_keywords()
        if not keywords:
            logger.warning("No hot keywords found for YouTube radar.")
            return

        for kw in keywords:
            # 1. 搜索
            search_results = self._search_videos(kw)
            
            # 2. AI 初筛
            worthy_videos = self._filter_with_ai(search_results, kw)
            
            # 3. 深度精读并上报
            for video in worthy_videos:
                logger.info(f"📖 Deep reading video: {video['title']}")
                
                # 获取字幕
                transcript = self._get_transcript(video['id'])
                full_content = f"{video['description']}\n\n[视频字幕摘要]:\n{transcript}".strip()
                
                # 使用镜像服务转存封面图，确保显示稳定性
                mirrored_media = self.mirror.mirror_all([video['thumbnail']]) if video['thumbnail'] else []

                # AI 深度评估
                score, reason, takeaways, cluster_id, mentioned_users, trending_keywords = evaluator.evaluate(
                    f"YouTube Radar: {video['title']}", 
                    full_content
                )
                
                if score < 70: # 发现模式门槛略高
                    logger.info(f"⏩ Video score too low ({score}), skipping.")
                    continue
                
                # 构建 Item
                item = {
                    "platform": "youtube",
                    "external_id": video['id'],
                    "title": video['title'],
                    "content": full_content,
                    "url": video['url'],
                    "published_at": datetime.now().isoformat(), # 发现模式统一设为当前时间
                    "score": score,
                    "reason": reason,
                    "takeaways": takeaways,
                    "cluster_id": cluster_id,
                    "mentioned_users": mentioned_users,
                    "trending_keywords": trending_keywords,
                    "media_urls": mirrored_media,
                    "metadata_json": {
                        "discovery_keyword": kw,
                        "type": "radar_found"
                    }
                }
                
                # 推送到后端
                try:
                    res = requests.post(f"{self.api_url}/news/", json=item)
                    if res.status_code in [200, 201]:
                        logger.info(f"✨ Successfully integrated YouTube intel: {video['title']}")
                except Exception as e:
                    logger.error(f"Failed to push YouTube intel to backend: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    radar = YouTubeDiscoveryRadar()
    radar.run()
