import os
import json
import logging
import re
import threading
import time
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List
from google import genai
from dotenv import load_dotenv
from zhipuai import ZhipuAI

# 加载 .env 文件
def load_env_robust():
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY"):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        load_dotenv(os.path.join(base_dir, ".env"))
    if not os.getenv("GEMINI_API_KEY"):
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        load_dotenv(os.path.join(root_dir, ".env"))

load_env_robust()

class BaseEvaluator:
    def evaluate(self, title: str, content: str) -> Tuple[int, Optional[str], Optional[List[str]], Optional[str], Optional[List[str]], Optional[List[str]]]:
        raise NotImplementedError

class GeminiEvaluator(BaseEvaluator):
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        models_str = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite,gemini-2.0-flash,gemini-2.0-flash-lite,gemini-1.5-pro,gemini-1.5-flash")
        self.model_names = [m.strip() for m in models_str.split(",") if m.strip()]
        self.logger = logging.getLogger("evaluator.gemini")
        self.lock = threading.Semaphore(2) 
        
        if not self.api_key:
            self.logger.warning("⚠️ GEMINI_API_KEY not found.")
            self.enabled = False
        else:
            self.client = genai.Client(api_key=self.api_key)
            self.enabled = True

    def _generate(self, prompt: str):
        with self.lock:
            for model_name in self.model_names:
                try:
                    response = self.client.models.generate_content(model=model_name, contents=prompt)
                    return response
                except Exception as e:
                    self.logger.error(f"❌ Gemini error: {e}")
                    continue
        return None

    def evaluate(self, title: str, content: str) -> Tuple[int, Optional[str], Optional[List[str]], Optional[str], Optional[List[str]], Optional[List[str]]]:
        if not self.enabled: return (0, None, None, None, None, None)
        
        prompt = self._build_prompt(title, content)
        response = self._generate(prompt)
        if not response: return (0, None, None, None, None, None)
        
        # Simple extraction for Gemini (assuming no thinking block or handled elsewhere)
        text = response.text
        return self._parse_json(text)

    def _build_prompt(self, title, content):
        return f"分析此新闻: {title}\n{content}\n返回JSON格式: {{'score': int, 'reason': str, 'takeaways': list, 'cluster_id': str, 'mentioned_users': list, 'trending_keywords': list}}"

    def _parse_json(self, text):
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match: text = json_match.group(0)
        try:
            data = json.loads(text)
            return (data.get("score", 0), data.get("reason"), data.get("takeaways"), data.get("cluster_id"), data.get("mentioned_users"), data.get("trending_keywords"))
        except:
            return (0, None, None, None, None, None)

class ZhipuEvaluator(BaseEvaluator):
    def __init__(self):
        self.api_key = os.getenv("ZHIPU_API_KEY")
        self.model = os.getenv("ZHIPU_MODEL", "glm-4-flash")
        self.logger = logging.getLogger("evaluator.zhipu")
        self.enabled = False
        if self.api_key:
            self.client = ZhipuAI(api_key=self.api_key)
            self.enabled = True
        else:
            self.logger.warning("⚠️ ZHIPU_API_KEY not found.")

    def evaluate(self, title: str, content: str) -> Tuple[int, Optional[str], Optional[List[str]], Optional[str], Optional[List[str]], Optional[List[str]]]:
        if not self.enabled: return (0, None, None, None, None, None)
        
        prompt = f"""
        你是一个资深的 AI 行业分析师。请对以下新闻进行评估。
        标题: {title}
        内容: {content}

        请严格按以下 JSON格式返回结果，不要包含 Markdown 块，不要包含任何其他文字：
        {{
            "score": 0,
            "reason": "...",
            "takeaways": ["..."],
            "cluster_id": "...",
            "mentioned_users": [],
            "trending_keywords": []
        }}
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.choices[0].message.content
            # 移除 Markdown 代码块包装
            text = re.sub(r'^```json\n', '', text.strip())
            text = re.sub(r'\n```$', '', text.strip())
            
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match: text = json_match.group(0)
            data = json.loads(text)
            return (data.get("score", 0), data.get("reason"), data.get("takeaways"), data.get("cluster_id"), data.get("mentioned_users"), data.get("trending_keywords"))
        except Exception as e:
            self.logger.error(f"❌ Zhipu error: {e}")
            return (0, None, None, None, None, None)

# Factory function
def get_evaluator(provider="gemini"):
    if provider == "zhipu":
        return ZhipuEvaluator()
    return GeminiEvaluator()
