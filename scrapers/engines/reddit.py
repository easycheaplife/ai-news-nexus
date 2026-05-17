import requests
import time
from .base import BaseScraper
from datetime import datetime
from ..utils.ai import evaluator
from ..utils.link_scraper import scrape_link_content

class RedditScraper(BaseScraper):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("reddit", api_url)
        self.reddit_url = "https://www.reddit.com/r/MachineLearning/new.json?limit=50"
        self.headers = {"User-Agent": "AI News Bot 1.0"}

    def _get_top_comments(self, permalink: str, limit: int = 8) -> str:
        """获取帖子的热门评论 (带质量过滤)"""
        url = f"https://www.reddit.com{permalink}.json"
        try:
            time.sleep(1) # 礼貌延迟
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return ""
            
            # Reddit 评论接口返回一个列表，[0] 是帖子信息，[1] 是评论树
            comments_data = response.json()[1]['data']['children']
            qualified_comments = []
            
            for comment in comments_data:
                if comment['kind'] == 't1': # 确保是评论
                    c_data = comment['data']
                    body = c_data.get('body', '').strip()
                    ups = c_data.get('ups', 0)
                    
                    # 质量过滤：长度 > 40，点赞 > 2，且不是删除内容
                    if len(body) > 40 and ups >= 2 and body != '[deleted]' and body != '[removed]':
                        qualified_comments.append(f"💬 (Ups: {ups}): {body}")
                
                if len(qualified_comments) >= limit:
                    break
            
            if qualified_comments:
                return "\n\n--- Reddit Community Insights ---\n" + "\n\n".join(qualified_comments)
        except Exception as e:
            self.logger.warning(f"Failed to fetch comments for {permalink}: {e}")
        return ""

    def scrape(self):
        subs = ["MachineLearning", "ArtificialInteligence", "OpenAI", "LocalLLaMA"]
        for sub in subs:
            last_timestamp = self.get_last_id(sub)
            url = f"https://www.reddit.com/r/{sub}/new.json?limit=25"
            try:
                response = requests.get(url, headers=self.headers)
                data = response.json()
                
                newest_timestamp = None
                
                for post in data['data']['children']:
                    p_data = post['data']
                    created_utc = str(int(p_data['created_utc']))
                    
                    # 增量判断
                    if last_timestamp and int(created_utc) <= int(last_timestamp):
                        self.logger.info(f"⏱️ Reached last seen post in r/{sub}, stopping.")
                        break
                    
                    if newest_timestamp is None:
                        newest_timestamp = created_utc
                    
                    # 🧵 获取热门评论增强内容
                    comments_text = self._get_top_comments(p_data['permalink'])
                    
                    # 🔗 获取外链内容摘要 (如果帖子是一个外链)
                    link_context = ""
                    if p_data.get('url') and not any(p_data['url'].endswith(ext) for ext in ['.jpg', '.png', '.gif', '.jpeg']):
                        # 排除掉图片链接，只抓取文章类链接
                        link_context = scrape_link_content(p_data['url'])
                    
                    full_content = f"{p_data['selftext'] or ''}\n\n{link_context}\n\n{comments_text}".strip()

                    # 🖼️ 提取多媒体 (强制高清)
                    media_urls = []
                    
                    # 1. 优先提取 Reddit 视频
                    if p_data.get('is_video') and p_data.get('media', {}).get('reddit_video'):
                        video_url = p_data['media']['reddit_video'].get('fallback_url')
                        if video_url:
                            clean_video_url = video_url.split('?')[0]
                            media_urls.append(clean_video_url)
                    
                    # 2. 尝试提取高清预览图
                    # Reddit 的 preview 节点包含原始高清地址，避免使用 140px 的 thumbnail
                    if p_data.get('preview', {}).get('images'):
                        try:
                            import html
                            source_img = p_data['preview']['images'][0]['source']['url']
                            # Reddit API 返回的 URL 经常带 &amp; 需要转义回去
                            high_res_url = html.unescape(source_img)
                            media_urls.append(high_res_url)
                        except: pass
                    
                    # 3. 备选提取缩略图或直接图
                    if not media_urls and p_data.get('thumbnail') and p_data['thumbnail'].startswith('http'):
                        media_urls.append(p_data['thumbnail'])
                    
                    if p_data.get('url') and any(p_data['url'].endswith(ext) for ext in ['.jpg', '.png', '.gif', '.jpeg']):
                        if p_data['url'] not in media_urls:
                            media_urls.append(p_data['url'])

                    # 🤖 AI 评分与理由
                    score, reason, takeaways, cluster_id, mentioned_users, trending_keywords = evaluator.evaluate(p_data['title'], full_content)

                    item = {
                        "platform": "reddit",
                        "external_id": p_data['id'],
                        "title": p_data['title'],
                        "content": full_content,
                        "url": f"https://reddit.com{p_data['permalink']}",
                        "published_at": datetime.fromtimestamp(p_data['created_utc']).isoformat(),
                        "score": score,
                        "reason": reason,
                        "takeaways": takeaways,
                            "cluster_id": cluster_id,
                            "mentioned_users": mentioned_users,
                            "trending_keywords": trending_keywords,
                        "media_urls": media_urls,
                        "metadata_json": {
                            "subreddit": sub,
                            "ups": p_data['ups'],
                            "num_comments": p_data['num_comments'],
                            "author": p_data['author']
                        }
                    }
                    self.push_to_backend(item)
                
                # 更新游标
                if newest_timestamp:
                    self.update_last_id(sub, newest_timestamp)
                    
            except Exception as e:
                self.logger.error(f"Error scraping Reddit r/{sub}: {e}")
