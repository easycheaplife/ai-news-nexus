# Design Spec: AI Intelligence Assets Hub (Knowledge Base & Whitepapers)

## 1. 概述 (Overview)
旨在将碎片化的每日资讯转化为持久化的“情报资产”。系统将自动维护一个 **AI 技术百科 (Concept Wiki)** 并周期性产出 **双周战略白皮书 (Bi-Weekly Reports)**，支持专业术语的即时悬浮解释。

## 2. 核心架构 (Architecture)

### 2.1 数据模型 (Data Model)
- **`knowledge_terms` (百科词条表)**:
    - `id`: INT PRIMARY KEY
    - `keyword`: VARCHAR(100) UNIQUE (如: "VLA Model")
    - `category`: VARCHAR(50) (模型, 算力, 框架, 应用, 趋势)
    - `description`: TEXT (AI 生成的专业定义)
    - `heat_score`: INT (共鸣次数累计)
    - `trend_json`: JSON (存储过去 30 天的历史热度序列，用于绘图)
    - `related_news_ids`: JSON (关联的最具代表性的 5 条新闻 ID)
    - `updated_at`: DATETIME

- **`periodic_reports` (周期性白皮书表)**:
    - `id`: INT PRIMARY KEY
    - `title`: VARCHAR(500)
    - `content`: LONGTEXT (Markdown 格式长文)
    - `start_date`, `end_date`: DATE (覆盖范围)
    - `stats_json`: JSON (本期核心统计指标)

### 2.2 处理流程 (Logic Flow)
1.  **词条沉淀 (Daily)**: 每天 `clustering` 任务后，AI 将提取的高频热词与 `knowledge_terms` 比对。新词自动生成定义，旧词累加热度并记录趋势点。
2.  **白皮书合成 (Bi-Weekly)**: 每 15 天触发。AI 读取过去两周的 `knowledge_terms`（热度变化）和 `daily_insights`（每日快照），撰写深度白皮书。
3.  **阅读增强 (UI)**: 前端在渲染简报内容时，正则匹配已入库的关键词，自动包裹 `<Tooltip>` 标签。

## 3. UI/UX 设计

### 3.1 百科频道 (Wiki View)
- 独立页面，展示词条卡片流。
- **视觉逻辑**: 高热度词条带“🔥”标记，点击展开热度折线图和深度溯源列表。

### 3.2 嵌入式气泡 (Inline Tooltips)
- **交互**: 鼠标悬浮在高亮词汇上，弹出一个半透明、具有科技感的浮窗。
- **内容**: 展示词条的极简定义 + 当前全网热度百分比。

### 3.3 白皮书展示 (Report View)
- 采用“长读模式”排版。
- 包含 **技术演进线 (Facts)** 和 **竞争格局分析 (Analysis)** 两个核心板块。

## 4. 实施阶段 (Phases)

- **Phase 1 (地基)**: 数据库建模，实现关键词自动入库与定义生成脚本。
- **Phase 2 (交互)**: 开发前端 Tooltip 组件，支持简报内容的动态增强。
- **Phase 3 (产出)**: 编写白皮书生成 AI 模板，开发独立百科频道页面。

## 5. 验证计划 (Verification)
- 验证 `VLA Model` 被多次提及后，其 `heat_score` 是否正确累加并出现在 Tooltip 中。
- 验证 15 天后能否正确抓取两周的数据特征并生成一份逻辑通顺的 Markdown 长文。
