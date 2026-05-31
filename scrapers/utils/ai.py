import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List
from google import genai
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
        你现在是硅谷 AI 圈最资深、最不留情面的“毒舌情报官”。你专门为那些厌倦了公关稿、想直戳行业脊梁骨的顶级玩家撰写内参。

        当前日期: {current_date}

        请根据以下今日全网 AI 圈的海量聚类数据，撰写一份极高密度的深度内参。

        原始数据背景:
        {summary_payload}

        要求遵循“信息金字塔”结构：

        1. **今日头条 (Headline Summary)**：用 3 个极其犀利、抓人眼球的标题总结今日最劲爆或最具争议的 3 件事。**如果数据中有重大模型发布 (如 Claude 4.8, GPT-5等)，必须占据头条之一。**
        2. **情报快览 (Quick-Look)**：用 5-8 条极简的 Bullet Points 罗列今日必读的硬核动态，追求极致信息密度。
        3. **深度拆解 (Thematic Deep Dives)**：识别 6-10 个“大事件”板块，自行拟定讽刺标题。
           - **核心原则**：如果某个聚类中有评分较高的重大发布，**必须为其设立独立的深度拆解章节**，详细对比其技术参数、社区反应和背后的画饼逻辑。
           - 覆盖板块需包含：基座模型进展、芯片算力焦虑、Agent 落地现状、基础设施变现等。
        4. **叙事要求**：每一个板块下必须包含 3 个以上的深度分析段落。不仅要说发生了什么，更要撕开它“画饼”的表象，揭露其背后的真实目的。
        5. **极致毒舌**：直接、犀利、幽默。严禁流水账。
        6. **篇幅与格式**：总字数 3000 字左右。使用标准的 Markdown 二级标题 (##) 和三级标题 (###)。
        7. **结尾**：以“## 【明日看戏指南：重点防忽悠指标】”给出 5 条监控指标。
        """

        # 🏛️ 正经战略版 Prompt
        official_prompt = f"""
        你是一个顶级 AI 行业智库的首席战略官，参考 36Kr《8点1氪》的高效率情报结构，专门为决策者撰写全维战略综述。

        当前日期: {current_date}

        请根据以下今日全球 AI 圈的海量聚类数据，撰写一份极高密度的战略内参。

        原始数据背景:
        {summary_payload}

        要求遵循“信息金字塔”结构：

        1. **核心摘要 (Top Headlines)**：提炼今日对全球 AI 格局产生深远影响的 3 大核心里程碑。
        2. **战略快讯 (Strategic Bullets)**：用 5-8 条精炼的短句总结今日各维度的重要信号，确保高信噪比。
        3. **全维分析 (Thematic Analysis)**：识别 6-10 个战略板块，自行拟定宏大标题。分析必须涵盖全产业链：
           - **硬件与基建**：HBM/GPU/算力网络最新动态。
           - **模型演进**：SOTA 排名变动、底层范式位移（如推理能力突破）。
           - **工程与应用**：AI Agent 原生支付、垂直领域落地案例、企业级 ROI 评估。
           - **投融资与地缘**：大厂财报深度拆解、行业并购与监管红线。
        4. **逻辑整合**：每一个事件下必须包含 3-4 个深度段落，结合数据和事实，分析其对未来 3-6 个月行业演进的本质影响。
        5. **智库口吻**：专业、客观、严谨，追求“洞察”而非“新闻”。
        6. **篇幅与格式**：总字数 3000 字左右。使用标准的 Markdown 二级标题 (##) 和三级标题 (###)。
        7. **结尾**：以“## 【核心情报雷达：下阶段重点监控指标】”给出 5 条监控指标。
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
