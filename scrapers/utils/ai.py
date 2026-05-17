import os
import json
import logging
from typing import Dict, Any, Tuple, Optional, List
from google import genai
from dotenv import load_dotenv

load_dotenv()

class GeminiEvaluator:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        # 支持以逗号分隔的模型列表，按优先级尝试
        models_str = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite,gemini-3.1-flash-lite-preview,gemini-2.5-flash-lite,gemini-2.5-flash,gemini-2.0-flash-lite,gemini-2.0-flash,gemini-flash-latest")
        self.model_names = [m.strip() for m in models_str.split(",") if m.strip()]
        self.logger = logging.getLogger("evaluator.gemini")
        
        if not self.api_key:
            self.logger.warning("⚠️ GEMINI_API_KEY not found in environment. AI evaluation will be skipped.")
            self.enabled = False
        else:
            try:
                self.client = genai.Client(api_key=self.api_key)
                self.enabled = True
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize Gemini client: {e}")
                self.enabled = False

    def _generate_content_with_fallback(self, prompt: str):
        """核心生成逻辑：支持模型自动降级 (使用新版 google-genai SDK)"""
        for model_name in self.model_names:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                return response
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "quota" in error_msg.lower():
                    self.logger.warning(f"⚠️ Model {model_name} hit quota limit (429). Trying next fallback...")
                    continue
                else:
                    self.logger.error(f"❌ Gemini error with model {model_name}: {e}")
                    continue
        
        self.logger.error("🚫 All Gemini fallback models failed.")
        return None

    def generate_content(self, prompt: str):
        """通用生成方法，支持模型自动降级"""
        if not self.enabled:
            return None
        return self._generate_content_with_fallback(prompt)

    def evaluate(self, title: str, content: str) -> Tuple[int, Optional[str], Optional[List[str]], Optional[str], Optional[List[str]], Optional[List[str]]]:
        """
        使用 Gemini 对内容进行多维分析：评分、摘要、要点、语义聚类、新账号发现及热词提取
        返回: (分数, 理由, 核心要点列表, 语义聚类ID, 提到用户列表, 趋势关键词列表)
        """
        if not self.enabled:
            return 0, None, None, None, None, None

        prompt = f"""
        你是一个资深的 AI 行业分析师。请对以下新闻/动态进行评估，如果内容包含“热门评论”或“社区讨论”，请务必提炼出社区的核心观点：
        
        标题: {title}
        内容: {content}
        
        请严格按以下 JSON 格式返回结果，不要包含任何其他文字：
        {{
            "score": 评分值(数字 0-100),
            "reason": "一句话推荐理由 (50字以内)",
            "takeaways": ["核心要点1", "核心要点2", "核心要点3"],
            "cluster_id": "核心语义主题 (2-4个词)",
            "mentioned_users": ["提取内容中提到的其他高价值 AI 相关用户名/Handle，没有则为空列表"],
            "trending_keywords": ["提取该资讯涉及的 2-3 个核心技术热词"]
        }}
        """

        try:
            response = self._generate_content_with_fallback(prompt)
            if not response:
                return 0, None, None, None, None, None

            # 尝试解析返回的 JSON
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(text)
            return (
                data.get("score", 0), 
                data.get("reason"), 
                data.get("takeaways"),
                data.get("cluster_id"),
                data.get("mentioned_users"),
                data.get("trending_keywords")
            )
        except Exception as e:
            self.logger.error(f"❌ Gemini evaluation failed: {e}")
            return 0, None, None, None, None, None

    def summarize_clusters(self, clusters_data: List[Dict[str, Any]]) -> str:
        """
        根据今日抓取的聚类簇信息，生成一份全局战略简报
        """
        if not self.enabled or not clusters_data:
            return "今日暂无深度情报分析。"

        # 将聚类信息序列化为提示词背景
        summary_payload = ""
        for i, c in enumerate(clusters_data[:10]): # 仅分析前10个最火的热点
            summary_payload += f"{i+1}. 热点: {c['cluster_id']}\n   规模: {c['count']} 条相关资讯\n   观点摘要: {c['reasons'][:3]}\n\n"

        prompt = f"""
        你是一个资深的 AI 行业战略分析师。以下是今日全球 AI 圈最重要的热点事件聚合数据：
        
        {summary_payload}
        
        请基于以上数据，撰写一份 200 字左右的《今日 AI 战略简报》。
        要求：
        1. 使用 Markdown 格式，语言专业、犀利。
        2. 识别出今日最重要的 1-2 个核心趋势。
        3. 解释为什么这些进展值得关注，以及对行业的潜在影响。
        4. 不要包含任何客套话，直接进入核心洞察。
        5. 结尾给出一句“明日关注建议”。
        """

        try:
            response = self._generate_content_with_fallback(prompt)
            return response.text.strip() if response else "深度简报生成失败。"
        except Exception as e:
            self.logger.error(f"❌ Summary generation failed: {e}")
            return "深度简报生成失败，请稍后重试。"

# 单例模式
evaluator = GeminiEvaluator()
