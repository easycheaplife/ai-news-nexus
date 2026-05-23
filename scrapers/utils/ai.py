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
        你是一个资深的 AI 行业分析师。请对以下新闻/动态进行全方位深度评估。
        如果内容包含“热门评论”或“社区讨论”，请务必提炼出社区的核心观点、技术争议点或实战避坑指南：

        标题: {title}
        内容: {content}

        请严格按以下 JSON 格式返回结果，不要包含任何其他文字：
        {{
            "score": 评分值(数字 0-100),
            "reason": "深度价值分析：请从技术创新性、行业影响力、实际落地价值三个维度进行详细评述 (150字左右)",
            "takeaways": ["核心要点1：详细描述", "核心要点2：详细描述", "核心要点3：详细描述", "核心要点4：详细描述", "核心要点5：详细描述"],
            "cluster_id": "核心语义主题 (2-4个词)",
            "mentioned_users": ["提取内容中提到的其他高价值 AI 相关用户名/Handle"],
            "trending_keywords": ["提取该资讯涉及的 3-5 个核心技术热词"]
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
        根据今日抓取的聚类簇信息，生成一份全天候、深度整合的《全球 AI 行业综述报告》
        """
        if not self.enabled or not clusters_data:
            return "今日暂无深度情报分析。"

        # 将聚类信息序列化为提示词背景
        summary_payload = ""
        for i, c in enumerate(clusters_data[:25]): 
            reasons_text = " | ".join(c['reasons'][:8])
            summary_payload += f"【主题: {c['cluster_id']} (规模:{c['count']})】\n核心内容: {reasons_text}\n\n"

        current_date = datetime.now().strftime("%Y年%m月%d日")
        prompt = f"""
        你是一个顶级 AI 行业智库的首席战略官，专门为跨国公司 CEO 和顶级投资者撰写内参。

        当前日期: {current_date}

        请根据以下今日全球 AI 圈的海量原始数据，撰写一份 1500-2000 字的《今日全球 AI 全维战略情报大综述》。

        原始数据背景:
        {summary_payload}

        要求（极其重要）：
        1. **极致深度整合**：禁止单纯罗列新闻。你需要构建一个宏大的行业叙事，将微观的技术进展、中观的厂商博弈与宏观的产业趋势进行“全维穿插”式加工。
        2. **日期准确性**：在报告正文开头的“日期”字段，必须使用真实日期: {current_date}。
        3. **热词去重**：在提炼技术概念时，请确保术语统一，不要同时出现“Agent”和“Agents”这种重复概念。
        4. **增加更多专业板块**：
           - **### 范式演进：底层架构与算法重构**
           - **### 巨头博弈：全球算力与生态位争夺战**
           - **### 垂直渗透：AI 在核心产业的工程化落地**
           - **### 开发者脉搏：开源社区的情绪共识与技术槽点**
           - **### 宏观与监管：政策红线与全球协同态势**
        5. **深度评估与实战建议**：
           - 必须包含“【3-6个月行业影响深度评估】”，至少列出 5 个维度的预测。
           - 必须包含“【企业与开发者战术执行指南】”，提供极具可操作性的 5 条建议。
        6. **语言风格**：极其犀利、充满前瞻性、数据支撑感强，避免任何废话和客套话。
        7. **结尾**：以“【核心情报雷达：明日重点监控指标】”给出 5 条极具穿透力的监控指标。
        """

        try:
            response = self._generate_content_with_fallback(prompt)
            return response.text.strip() if response else "深度综述生成失败。"
        except Exception as e:
            self.logger.error(f"❌ Summary generation failed: {e}")
            return "深度综述生成失败，请稍后重试。"

# 单例模式
evaluator = GeminiEvaluator()
