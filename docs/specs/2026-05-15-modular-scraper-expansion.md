# 设计规范：模块化爬虫架构与功能扩展

- **主题**：将爬虫重构为模块化结构，并新增 AI 数据源。
- **日期**：2026-05-15
- **状态**：已完成

## 1. 概述
当前的 `scrapers/engines/platforms.py` 包含了多个爬虫类，难以维护和扩展。本设计提出“一类一文件”的架构，并计划新增三个高价值 AI 资讯源：GitHub Trending、ArXiv (cs.AI) 和 YouTube。

## 2. 架构变更

### 2.1 目录结构
我们将从单体文件迁移到基于目录的包结构：
- `scrapers/engines/base.py`：包含 `BaseScraper` 基类和通用工具。
- `scrapers/engines/twitter.py`：重构后的 Twitter 逻辑。
- `scrapers/engines/reddit.py`：重构后的 Reddit 逻辑。
- `scrapers/engines/ph.py`：重构后的 Product Hunt 逻辑。
- `scrapers/engines/hn.py`：现有的 Hacker News 逻辑（按命名规范移动）。
- `scrapers/engines/github.py`：[新增] GitHub Trending 爬虫。
- `scrapers/engines/arxiv.py`：[新增] ArXiv cs.AI 论文爬虫。
- `scrapers/engines/youtube.py`：[新增] YouTube AI 频道监控。

### 2.2 共享逻辑
- 所有引擎均继承自 `BaseScraper`。
- Gemini 评估逻辑作为共享工具保留在 `scrapers/utils/ai.py` 中。

## 3. 新增数据源

### 3.1 GitHub Trending
- **入口**：`https://github.com/trending/python?since=daily`（过滤 AI 相关库）。
- **提取内容**：仓库名、描述、Star 数、主要语言。
- **AI 重点**：根据描述和 README 片段进行评估。

### 3.2 ArXiv cs.AI
- **入口**：ArXiv API (`http://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending`)。
- **提取内容**：论文标题、摘要、作者、PDF 链接。
- **AI 重点**：将学术摘要提炼为一句话推荐理由。

### 3.3 YouTube AI
- **入口**：YouTube RSS 或 Data API。
- **目标**：`Andrej Karpathy`, `Two Minute Papers`, `DeepLearning.AI`。
- **提取内容**：视频标题、描述、高分辨率缩略图。

## 4. 实施计划

1. **第一阶段：重构**
   - 创建 `scrapers/engines/base.py` 并移动 `BaseScraper`。
   - 将 `platforms.py` 拆分为 `twitter.py`, `reddit.py`, `ph.py`。
   - 更新 `run.py` 以从新路径导入。
   - 验证现有爬虫是否正常工作。

2. **第二阶段：扩展**
   - 实现 `github.py`。
   - 实现 `arxiv.py`。
   - 实现 `youtube.py`。

3. **第三阶段：最终润色**
   - 确保所有新来源都使用 Gemini AI 评分和汉化的“推荐理由”。

## 5. 验收标准
- [x] Twitter/Reddit/PH/HN 抓取无回退故障。
- [x] 新来源能正确将数据推送到后端。
- [x] 所有数据项均包含高质量的 AI 评分和理由。
- [x] 前端正确展示新平台（图标、媒体）。
