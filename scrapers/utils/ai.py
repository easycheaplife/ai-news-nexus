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

# 单例模式
evaluator = GeminiEvaluator()
