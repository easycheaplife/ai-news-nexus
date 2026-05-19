import requests
import json
import os
import concurrent.futures
from .base import BaseScraper
from datetime import datetime
from ..utils.ai import evaluator

class ProductHuntScraper(BaseScraper):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("ph", api_url)
        self.token = os.getenv("PRODUCTHUNT_TOKEN")
        self.graphql_url = "https://api.producthunt.com/v2/api/graphql"

    def scrape(self):
        if not self.token:
            self.logger.error("❌ PRODUCTHUNT_TOKEN not found in environment. Please set it in .env")
            return

        self.logger.info("📦 Scraping Product Hunt via GraphQL API...")
        last_timestamp = self.get_last_id("ph_main")
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        
        # 抓取最新的 20 条产品，并获取真实的 description (长篇正文)
        query = '''
        {
          posts(first: 20) {
            edges {
              node {
                id
                name
                tagline
                description
                url
                createdAt
                thumbnail {
                  url
                }
              }
            }
          }
        }
        '''
        
        try:
            response = requests.post(
                self.graphql_url,
                headers=headers,
                json={'query': query},
                timeout=30
            )
            
            if response.status_code != 200:
                self.logger.error(f"❌ API Request failed: {response.status_code} - {response.text}")
                return

            data = response.json()
            edges = data.get('data', {}).get('posts', {}).get('edges', [])
            
            if not edges:
                self.logger.info("No posts found in API response.")
                return

            newest_timestamp = None
            tasks = []

            for edge in edges:
                node = edge.get('node', {})
                post_id = node.get('id')
                created_at = node.get('createdAt')
                
                if not created_at:
                    continue
                    
                # 将 ISO 格式时间转换为时间戳 (例如: "2026-05-18T10:00:00Z")
                published_ts = str(int(datetime.fromisoformat(created_at.replace('Z', '+00:00')).timestamp()))
                
                self.logger.info(f"🔗 Processing Item ID: {post_id} | Date: {created_at}")
                
                if last_timestamp and int(published_ts) <= int(last_timestamp):
                    self.logger.info("⏱️ Reached last seen Product Hunt post, stopping.")
                    break
                
                if newest_timestamp is None:
                    newest_timestamp = published_ts

                name = node.get('name', '')
                tagline = node.get('tagline', '')
                description = node.get('description', '')
                
                # 如果正文异常为空，用短标语兜底
                rich_content = description.strip() if description and description.strip() else tagline.strip()
                
                # AI 相关性过滤
                if any(k in (name + tagline + rich_content).lower() for k in ["ai ", "gpt", "llm", "bot", "agent", "machine learning"]):
                    tasks.append((node, published_ts, rich_content))

            def process_node(node, published_ts, rich_content):
                media_urls = []
                thumbnail = node.get('thumbnail')
                if thumbnail and thumbnail.get('url'):
                    media_urls.append(thumbnail['url'])

                # 🤖 AI 评分与理由提取
                try:
                    score, reason, takeaways, cluster_id, mentioned_users, trending_keywords = evaluator.evaluate(node.get('name'), rich_content)
                except Exception as e:
                    self.logger.error(f"Error evaluating item {node.get('id')}: {e}")
                    return None
                    
                item = {
                    "platform": "ph",
                    "external_id": node.get('id'),
                    "title": f"{node.get('name')} - {node.get('tagline')}",
                    "content": rich_content,
                    "url": node.get('url'),
                    "published_at": datetime.fromtimestamp(int(published_ts)).isoformat(),
                    "score": score,
                    "reason": reason,
                    "takeaways": takeaways,
                    "cluster_id": cluster_id,
                    "mentioned_users": mentioned_users,
                    "trending_keywords": trending_keywords,
                    "media_urls": media_urls,
                    "metadata_json": {
                        "author": "Product Hunt"
                    }
                }
                return item

            if tasks:
                self.logger.info(f"⚡ Processing {len(tasks)} items concurrently...")
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_node = {executor.submit(process_node, n, pts, rc): (n, pts) for n, pts, rc in tasks}
                    for future in concurrent.futures.as_completed(future_to_node):
                        item = future.result()
                        if item:
                            self.push_to_backend(item)
                            
            if newest_timestamp:
                self.update_last_id("ph_main", newest_timestamp)
                
        except Exception as e:
            self.logger.error(f"Error scraping Product Hunt API: {e}")
