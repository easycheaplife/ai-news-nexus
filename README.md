# AI News Nexus - 全方位 AI 资讯情报中心

AI News Nexus 是一个高度自动化的 AI 行业垂直情报系统。它不仅能从全网（Twitter, Reddit, GitHub, ArXiv, YouTube）聚合资讯，还能利用 Google Gemini 对内容进行深度分析、语义聚类和全自动信源扩张。

## 🌟 核心特性

- **多维采集引擎**：模块化设计的爬虫集群，支持长推文（Thread）拼接、视频字幕提取、外链内容穿透以及论文摘要分析。
- **AI 智能分析 (Gemini Driven)**：
  - **核心提炼**：自动生成 3 条精华要点（Takeaways），实现 5 秒极速扫读。
  - **语义聚类**：全自动识别跨平台讨论热点（Cluster），实现话题级聚合。
  - **战略简报**：每日自动生成深度行业总结报告。
- **混合式发现引擎**：
  - **社交扩张**：自动挖掘 KOL 互动圈，经过 AI 身份验证后自动加入抓取白名单。
  - **全网猎词**：基于每日技术热词自动发起全球检索。
- **专业级 UI/UX**：
  - **社论流排版**：针对深度阅读优化的单列横向布局。
  - **沉浸式灯箱**：支持高清图片预览和视频自动播放。
  - **高密度仪表盘**：顶置今日简报、热词云及各平台脉冲统计。

## 🏗️ 系统架构

系统遵循 **“生产 -> 存储 -> 消费”** 的解耦架构：

1. **Scrapers (生产层)**：
   - 负责原始数据抓取。
   - 调用 Gemini API 进行多维评估与发现信号提取。
   - 将处理后的“情报包”推送到后端。
2. **Backend (存储/接口层)**：
   - 基于 FastAPI 和 SQLAlchemy。
   - 负责数据的持久化（MySQL）与去重。
   - 提供高性能的情报分发接口。
3. **Frontend (消费层)**：
   - 基于 Vue 3 + Vite + Tailwind CSS。
   - 实现响应式的专业数据终端界面。

## 📂 目录结构

```text
ai-news-nexus/
├── backend/            # FastAPI 后端服务
│   ├── app/
│   │   ├── api/        # 接口路由 (news, insights, discovery, targets)
│   │   ├── models/     # 数据库模型
│   │   └── schemas/    # Pydantic 数据定义
│   └── main.py         # 后端入口
├── scrapers/           # 模块化采集引擎
│   ├── engines/        # 平台爬虫实现 (twitter, github, youtube等)
│   ├── utils/          # 共享工具 (AI Evaluator, LinkScraper)
│   ├── run.py          # 主抓取调度器
│   └── discovery_run.py # 情报发现与信源扩张脚本
├── docs/               # 文档库
│   ├── api.md          # 详细接口文档
│   └── specs/          # 核心功能设计规范 (中文)
└── frontend/           # Vue 3 仪表盘
```

## 🚀 快速开始

请参阅 [DEPLOY.md](./DEPLOY.md) 查看详细的部署与运行指南。

## 📄 接口文档

详细的 API 使用说明请查阅 [docs/api.md](./docs/api.md)。
或者在后端运行时访问：`http://localhost:8000/docs` (Swagger UI)。
