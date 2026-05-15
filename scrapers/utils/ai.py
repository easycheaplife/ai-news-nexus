import os
import json
import logging
from typing import Dict, Any, Tuple, Optional
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

    def evaluate(self, title: str, content: str) -> Tuple[int, Optional[str]]:
        """
        使用 Gemini 对内容进行评分并给出推荐理由
        返回: (分数, 理由)
        """
        if not self.enabled:
            return 0, None

        prompt = f"""
        你是一个资深的 AI 行业分析师。请对以下新闻/动态进行评估：
        
        标题: {title}
        内容: {content}
        
        请基于以下标准进行评分 (0-100)：
        1. 创新性: 是否是重大的技术突破或新产品发布？
        2. 影响力: 对 AI 行业、开发者或普通用户的潜在影响。
        3. 真实性/来源: 是否是可靠的一手信息。
        
        请严格按以下 JSON 格式返回结果，不要包含任何其他文字：
        {{
            "score": 评分值(数字),
            "reason": "一句话推荐理由 (50字以内，重点说明为什么值得关注)"
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            # 尝试解析返回的 JSON
            text = response.text.strip()
            # 有时模型会返回 ```json ... ```
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(text)
            return data.get("score", 0), data.get("reason")
        except Exception as e:
            self.logger.error(f"❌ Gemini evaluation failed: {e}")
            return 0, None

# 单例模式
evaluator = GeminiEvaluator()
