import os
import json
import logging
from datetime import datetime
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
            "trending_keywords": ["提取该资讯涉及的 3-5 个核心技术热词 (每个词 1-3 单词，如 'LLM', 'Agent', 'VLA')"]
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

    def summarize_clusters(self, clusters_data: List[Dict[str, Any]], style: str = "toxic") -> str:
        """
        根据今日抓取的聚类簇信息，生成一份深度整合的《全球 AI 行业综述报告》
        支持多种风格：'toxic' (毒舌吐槽版), 'official' (正经战略版)
        """
        if not self.enabled or not clusters_data:
            return "今日暂无深度情报分析。"

        # 将聚类信息序列化为提示词背景
        summary_payload = ""
        for i, c in enumerate(clusters_data[:25]): 
            reasons_text = " | ".join(c['reasons'][:8])
            summary_payload += f"【主题: {c['cluster_id']} (规模:{c['count']})】\n核心内容: {reasons_text}\n\n"

        current_date = datetime.now().strftime("%Y年%m月%d日")
        
        # 🧪 毒舌吐槽版 Prompt
        toxic_prompt = f"""
        你现在是硅谷 AI 圈最资深、最不留情面的“毒舌情报官”。你深谙各大厂的画饼套路，对无脑吹捧免疫，专门为看透行业本质的圈内老炮儿撰写内参。
        
        当前日期: {current_date}
        
        请根据以下今日全球 AI 圈的海量原始数据，撰写一份 2000 字左右的《今日全球 AI 毒舌情报大内参》。
        
        原始数据背景:
        {summary_payload}
        
        要求：
        1. **极致毒舌与穿透力**：绝不打官腔！你要直接撕开厂商的新闻通稿，指出背后的真实目的（比如抢算力、炒股价、掩盖技术短板）。
        2. **禁止流水账**：严禁罗列新闻。提取核心矛盾。每一个大板块必须包含 3-4 个深度段落。
        3. **格式规范**：使用标准的 Markdown 二级标题 (##) 和三级标题 (###)。
        4. **结构化板块**：
           ## 一、 今日黑话与圈内缩影
           ## 二、 红黑榜：谁在真赢，谁在硬演？
           ## 三、 巨头宫斗：算力与生态位的修罗场
           ## 四、 开发者嘴替：开源社区的怨气与反击
           ## 五、 避坑雷达：少交智商税
        5. 确保日期正确: {current_date}。确保术语统一（如统一使用 Agent）。
        6. 结尾：以“## 【明日看戏指南：重点防忽悠指标】”给出 5 条监控指标。
        """

        # 🏛️ 正经战略版 Prompt
        official_prompt = f"""
        你是一个顶级 AI 行业智库的首席战略官，专门为跨国公司 CEO 和顶级投资者撰写内参。
        
        当前日期: {current_date}
        
        请根据以下今日全球 AI 圈的海量原始数据，撰写一份 2000 字左右的《今日全球 AI 全维战略情报大综述》。
        
        原始数据背景:
        {summary_payload}
        
        要求：
        1. **深度逻辑整合**：构建宏大的行业叙事。每一个大板块必须包含 3-4 个深度段落。
        2. **格式规范**：使用标准的 Markdown 二级标题 (##) 和三级标题 (###)。
        3. **结构化板块**：
           ## 一、 范式演进：底层架构与算法重构
           ## 二、 巨头博弈：全球算力与生态位争夺战
           ## 三、 垂直渗透：AI 在核心产业的工程化落地
           ## 四、 开发者脉搏：开源社区的情绪共识与技术趋势
           ## 五、 宏观与监管：政策红线与全球协同态势
        4. 必须包含“## 【3-6个月行业影响深度评估】”和“## 【企业与开发者战术执行指南】”板块。
        5. 风格犀利专业，像高盛或麦肯锡内参。
        6. 确保日期正确: {current_date}。
        7. 结尾：以“## 【核心情报雷达：明日重点监控指标】”给出 5 条监控指标。
        """

        prompt = toxic_prompt if style == "toxic" else official_prompt

        try:
            response = self._generate_content_with_fallback(prompt)
            return response.text.strip() if response else "深度综述生成失败。"
        except Exception as e:
            self.logger.error(f"❌ Summary generation failed: {e}")
            return "深度综述生成失败，请稍后重试。"

# 单例模式
evaluator = GeminiEvaluator()
