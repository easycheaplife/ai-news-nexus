import os
import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List
from google import genai
from google.genai import types
from dotenv import load_dotenv

# 加载 .env 文件
def load_env_robust():
    # 尝试加载当前目录的 .env
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY"):
        # 尝试加载 scrapers 目录下的 .env
        base_dir = os.path.dirname(os.path.dirname(__file__))
        load_dotenv(os.path.join(base_dir, ".env"))
    if not os.getenv("GEMINI_API_KEY"):
        # 尝试加载父目录（项目根目录）下的 .env
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        load_dotenv(os.path.join(root_dir, ".env"))

load_env_robust()

class GeminiEvaluator:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        # 🚀 优先使用 gemini-3.1 系列，因为其目前额度更充裕
        models_str = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite,gemini-2.0-flash,gemini-2.0-flash-lite,gemini-1.5-pro,gemini-1.5-flash")
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
        """核心生成逻辑：支持模型自动降级"""
        for model_name in self.model_names:
            try:
                import time
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                return response
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "quota" in error_msg.lower():
                    self.logger.warning(f"⚠️ Model {model_name} hit quota limit (429). Waiting 2s before fallback...")
                    time.sleep(2) # 增加延迟以规避 RPM 限制
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
        使用 Gemini 对内容进行多维分析
        """
        if not self.enabled:
            return 0, None, None, None, None, None

        prompt = f"""
        你是一个资深的 AI 行业分析师。请对以下新闻/动态进行全方位深度评估。
        如果内容包含“热门评论”或“社区讨论”，请务必提炼出社区的核心观点、技术争议点或实战避坑指南：

        标题: {title}
        内容: {content}

        请严格按以下 JSON格式返回结果，不要包含任何其他文字：
        {{
            "score": 评分值(数字 0-100),
            "reason": "深度价值分析：请从技术创新性、行业影响力、实际落地价值三个维度进行详细评述 (150字左右)",
            "takeaways": ["核心要点1：详细描述", "核心要点2：详细描述", "核心要点3：详细描述", "核心要点4：详细描述", "核心要点5：详细描述"],
            "cluster_id": "核心语义主题 (2-4个词)",
            "mentioned_users": ["提取内容中提到的其他高价值 AI 相关用户名/Handle"],
            "trending_keywords": ["提取该资讯涉及的 3-5 个核心技术热词 (每个词 1-3 单词，如 'LLM', 'Agent', 'VLA')"]
        }}
        """

        try:
            response = self._generate_content_with_fallback(prompt)
            if not response:
                return 0, None, None, None, None, None

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
                reasons_text = " | ".join(c['reasons'][:8])
                summary_payload += f"【主题: {c['cluster_id']} (规模:{c['count']})】\n核心内容: {reasons_text}\n\n"
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

        try:
            response = self._generate_content_with_fallback(prompt)
            if not response:
                return None
            
            text = response.text.strip()
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
        except Exception as e:
            self.logger.error(f"❌ Summary generation failed: {e}")
            return None

# 单例模式
evaluator = GeminiEvaluator()
