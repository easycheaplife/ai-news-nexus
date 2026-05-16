import os
import json
import logging
from typing import Dict, Any, Tuple, Optional, List
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class GeminiEvaluator:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.logger = logging.getLogger("evaluator.gemini")
        
        if not self.api_key:
            self.logger.warning("⚠️ GEMINI_API_KEY not found in environment. AI evaluation will be skipped.")
            self.enabled = False
        else:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            self.enabled = True

    def evaluate(self, title: str, content: str) -> Tuple[int, Optional[str], Optional[List[str]], Optional[str]]:
        """
        使用 Gemini 对内容进行评分、理由提炼、核心要点总结及语义聚类
        返回: (分数, 理由, 核心要点列表, 语义聚类ID)
        """
        if not self.enabled:
            return 0, None, None, None

        prompt = f"""
        你是一个资深的 AI 行业分析师。请对以下新闻/动态进行评估：
        
        标题: {title}
        内容: {content}
        
        请严格按以下 JSON 格式返回结果，不要包含任何其他文字：
        {{
            "score": 评分值(数字 0-100),
            "reason": "一句话推荐理由 (50字以内)",
            "takeaways": ["核心要点1", "核心要点2", "核心要点3"],
            "cluster_id": "用2-4个词概括其核心语义主题，作为聚类ID (例如: 'OpenAI Sora', 'DeepSeek V3', 'Apple Intelligence')"
        }}
        """

        try:
            response = self.model.generate_content(prompt)
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
                data.get("cluster_id")
            )
        except Exception as e:
            self.logger.error(f"❌ Gemini evaluation failed: {e}")
            return 0, None, None, None

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
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            self.logger.error(f"❌ Summary generation failed: {e}")
            return "深度简报生成失败，请稍后重试。"

# 单例模式
evaluator = GeminiEvaluator()
