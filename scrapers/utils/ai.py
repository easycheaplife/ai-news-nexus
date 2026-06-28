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
    
    def summarize_clusters(self, clusters_data: List[Dict[str, Any]], style: str = "toxic") -> str:
        raise NotImplementedError
        
    def generate_content(self, prompt: str) -> Any:
        raise NotImplementedError

class GeminiEvaluator(BaseEvaluator):
    # ... (keep existing methods)
    
    def generate_content(self, prompt: str) -> Any:
        return self._generate(prompt)

# ... (inside ZhipuEvaluator)
    def generate_content(self, prompt: str) -> Any:
        if not self.enabled: return None
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response
        except Exception as e:
            self.logger.error(f"❌ Zhipu error: {e}")
            return None
    # ... (keep __init__, _generate, evaluate, _build_prompt, _parse_json)
    
    def _extract_text_from_response(self, response) -> str:
        """从多部分响应中提取纯文本，跳过思维链(thought/thought_signature)"""
        if not response or not response.candidates:
            return ""
        
        full_text = []
        for part in response.candidates[0].content.parts:
            # 跳过思维链部分 (Gemini 2.0/3.1 特性)
            is_thought = False
            if hasattr(part, 'thought') and part.thought:
                is_thought = True
            
            if not is_thought:
                if hasattr(part, 'text') and part.text:
                    full_text.append(part.text)
        
        return "".join(full_text).strip()

    def summarize_clusters(self, clusters_data: List[Dict[str, Any]], style: str = "toxic") -> str:
        """
        整合最近 24 小时的聚类信息，生成深度综述。
        支持多种风格：'toxic' (毒舌吐槽版), 'official' (正经战略版)
        """
        if not self.enabled:
            return "今日暂无深度情报分析。"

        # 将聚类信息序列化为提示词背景
        summary_payload = ""
        if clusters_data:
            for i, c in enumerate(clusters_data[:30]): 
                reasons_text = " | ".join(c.get('reasons', [])[:8])
                summary_payload += f"【主题: {c.get('cluster_id')} (规模:{c.get('count')})】\n核心内容: {reasons_text}\n\n"
        else:
            summary_payload = "（数据库内暂无最近 24 小时的深度聚类数据）"

        current_date = datetime.now().strftime("%Y年%m月%d日")
        
        # 🧪 综合提示词
        base_instruction = f"""
        你现在是顶级 AI 情报官。你的任务是根据我提供的数据库聚类信息，整合出过去 24 小时内全球 AI 圈最重要的动态。

        当前日期: {current_date}

        🚨 **核心指令：**
        1. **24小时视野**：你的综述必须严格覆盖过去 24 小时内的动态。
        2. **重大新闻事件**：必须重点包含发布 24 小时内的重大新闻。
        3. **深度整合**：请完全基于我提供的背景数据进行深度整合，提炼出技术趋势和行业洞察。

        提供的原始数据背景:
        {summary_payload}

        要求遵循“信息金字塔”结构：

        1. **今日头条 (Headline Summary)**：用 3 个极其犀利、抓人眼球的标题总结过去 24 小时最劲爆或最具争议的 3 件事。
        2. **情报快览 (Quick-Look)**：用 5-8 条极简的 Bullet Points 罗列 24 小时内必读的硬核动态。
        3. **深度拆解 (Thematic Deep Dives)**：识别 6-10 个“大事件”板块，自行拟定标题。
           - **核心原则**：对于 24 小时内的重大发布，**必须设立独立的深度拆解章节**。
           - 覆盖板块需包含：基座模型进展、芯片算力焦虑、Agent 落地现状、基础设施变现等。
        4. **叙事要求**：每一个板块下必须包含 3 个以上的深度分析段落。
        5. **格式**：使用标准的 Markdown 二级标题 (##) 和三级标题 (###)。
        6. **禁止事项**：严禁在正文末尾添加任何“撰写人”、“作者”、“日期”或落款签名信息。直接以监控指标结束。
        7. **结尾**：给出 5 条监控指标。
        """

        toxic_role = """
        角色风格：硅谷最资深的“毒舌情报官”。直接、犀利、幽默，直戳行业脊脊梁骨。
        """

        official_role = """
        角色风格：顶级 AI 智库首席战略官。专业、客观、严谨，追求“洞察”而非单纯的“新闻”。
        """

        role_prompt = toxic_role if style == "toxic" else official_role
        prompt = f"{base_instruction}\n{role_prompt}"

        response = self._generate(prompt)
        if not response:
            return None
        
        text = self._extract_text_from_response(response)
        # 🧹 后置处理：剥离 Markdown 代码块标签
        if text.startswith("```"):
            text = re.sub(r'^```[a-zA-Z]*\n', '', text)
            text = re.sub(r'\n```$', '', text)
        
        # 🧹 后置处理：移除元数据行
        cleaned_text = []
        blacklist = ["撰写人", "报告人", "日期", "撰写日期"]
        for line in text.split('\n'):
            l_strip = line.strip()
            is_metadata = any(kw in l_strip for kw in blacklist) and (":" in l_strip or "：" in l_strip)
            if is_metadata:
                continue
            cleaned_text.append(line)
        
        return '\n'.join(cleaned_text).strip()

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
