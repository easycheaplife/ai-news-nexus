# AI News Nexus

AI News Nexus 是一个高性能、视觉美观的 AI 资讯聚合平台，自动从多个平台（Twitter, Reddit, Hacker News 等）抓取 AI 相关的最新趋势、论文和产品。

## 🌟 核心特性

-   **多源聚合**: 自动化抓取 Hacker News, Reddit (Machine Learning, OpenAI 等), Product Hunt 资讯。
-   **智能防重**: 数据库层与 API 层双重去重，确保内容唯一性。
-   **极速搜索**: 支持按平台、日期范围、关键词即时搜索。
-   **现代设计**: 采用 "Editorial Dark Tech" 风格，提供沉浸式的阅读体验。
-   **模块化架构**: 后端基于 FastAPI，前端基于 Vue 3 + Tailwind CSS。

## 🏗️ 项目结构

```text
ai-news-nexus/
├── backend/                # 后端应用
│   ├── app/
│   │   ├── api/            # API 路由分发 (v1)
│   │   ├── core/           # 核心配置与全局变量
│   │   ├── db/             # 数据库连接与会话管理
│   │   ├── models/         # SQLAlchemy 数据库模型
│   │   └── schemas/        # Pydantic 数据验证模型
│   ├── main.py             # 后端入口
│   └── schema.sql          # 数据库初始化脚本
├── frontend/               # Vue 3 前端应用
└── scrapers/               # 独立采集引擎
    ├── engines/            # 各平台采集实现
    ├── base.py             # 采集器基类
    └── run.py              # 采集器执行入口
```

## 🛠️ 技术栈

-   **Frontend**: Vue 3, Vite, Tailwind CSS, Lucide Icons, Axios.
-   **Backend**: Python 3.9+, FastAPI, SQLAlchemy, Pydantic, MySQL/SQLite.
-   **Scrapers**: Requests, Beautiful Soup (可扩展).

## 📄 许可证

MIT License
