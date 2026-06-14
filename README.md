# AI News Nexus - 全方位 AI 资讯情报中心

AI News Nexus 是一个高度自动化的 AI 行业垂直情报系统。它不仅能从全网聚合资讯，还能利用 Google Gemini 对内容进行深度分析、语义聚类和全自动信源扩张，打造属于你的“AI 时代情报指挥部”。

## 🌟 核心特性 (V2.0 更新)

- **采集引擎 2.0 (全真模拟)**：
  - **Twikit 登录态抓取**：彻底告别不稳定的 Nitter 方案，采用基于真实 Session/Cookie 的 API 模拟抓取，完美绕过 Twitter 的 403 封锁与 login wall。
  - **Intelligence Sourcing (首发溯源)**：引入 First Mover 算法，自动识别全球 AI 资讯的首发源头，并授予 **“FIRST BREAK”** 勋章。
- **战略资产库 (Intelligence Assets)**：
  - **技术百科 (AI Wiki)**：基于 AI 自动沉淀的行业技术名词库。支持全文搜索、热度排序及词条 hover 实时定义。
  - **深度白皮书 (Whitepapers)**：每半月自动生成的行业趋势深度研报。采用沉浸式“卷宗”阅读体验。
  - **多格式导出**：白皮书支持一键下载 **Markdown** 源码或导出 **PDF** 格式。
- **AI 智能中枢 (Gemini 驱动)**：
  - **核心提炼**：自动生成 5 条精华要点（Takeaways），并对内容进行 **0-100 分** 精准打分，全站仅展示 71 分以上高价值干货。
  - **跨源共振 (Topic Resonance)**：全自动识别跨平台热点，计算“共振指数”，揭示全网最真实的行业趋势。
  - **Asset Engine**：全自动识别新闻中的高频技术词汇并实现词条沉淀，打造自进化的知识图谱。
- **自动化治理与进化**：
  - **Strike 实时分级制**：引入 `failure_count` 实时反馈，自动识别并下线频繁水推或原创度低的信源。
  - **15天沉默清算**：系统自动剔除超过 15 天无高质量产出的“失踪人口”，确保情报网始终处于核心活跃状态。
  - **关注同步功能**：支持脚本一键同步 Twitter 小号关注列表，实现“随手关注，自动入库”。
- **专业级 UI/UX (Indigo Unified)**：
  - **靛蓝统一视觉**：全站升级为深邃靛蓝 (Indigo) 调色盘，搭配结构化枢纽布局，营造顶级情报中心质感。
  - **WikiTooltip 交互**：全站新闻标题支持技术词条 hover 实时解析。
  - **高密度仪表盘**：1400px 专业级排版，实时展示全平台脉冲与情报热值。
  - **移动端全功能支持**：针对手机优化的白皮书阅读器与下载功能。

## 🏗️ 系统架构

系统遵循 **“生产 -> 存储 -> 消费”** 的解耦架构：

1. **Scrapers (生产层)**：模块化 Python 爬虫，负责抓取、AI 评估与信号提取。
2. **Backend (存储层)**：基于 FastAPI + MySQL + Redis 缓存，提供极致响应的情报分发。
3. **Frontend (消费层)**：基于 Vue 3 + Tailwind CSS 的专业响应式数据终端。

## 📂 核心工具指南

```text
scrapers/
├── generate_cookies.py # [NEW] 基于 .env 账号信息生成 Twitter 登录 Cookie
├── sync_following.py   # [NEW] 同步 Twitter 关注列表至抓取名单
├── curation_run.py     # 信源质量评估与 15 天沉默期自动清理
└── discovery_run.py    # 发现引擎：全网挖掘潜在 AI 大佬
```

## 🛠️ 技术栈

- **Frontend**: Vue 3, Vite, Tailwind CSS, Lucide Icons, Axios.
- **Backend**: Python 3.9+, FastAPI, SQLAlchemy, Redis (Caching), MySQL.
- **AI/NLP**: Google Gemini API (Flash/Pro), BeautifulSoup 4.
- **Automation**: Twikit (X/Twitter API), Playwright (Reporting).

## 🚀 快速开始

1. **环境配置**：
   - 参考 `scrapers/.env.example` 配置你的 `GEMINI_API_KEY` 和推特小号凭证。
   - 生成 Cookie：`python3 scrapers/generate_cookies.py`。
   - (可选) 同步关注列表：`python3 scrapers/sync_following.py`。

2. **全自动运行**：
   ```bash
   python3 scrapers/run.py --loop --interval 3600
   ```

### 命令行参数说明
| 参数 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `--discovery` | `True` | 挖掘新大佬及热词信号。 |
| `--scrape` | `True` | 内容采集（支持单平台 `-p twitter`）。 |
| `--curation` | `True` | 质量评估与 15 天沉默账号清理。 |
| `--clustering` | `True` | 过去 24 小时话题聚类与共振计算。 |
| `--insights` | `True` | 生成双风格每日简报。 |

3. **详细文档**：
    - [DEPLOY.md](./DEPLOY.md) 部署手册。
    - [docs/api.md](./docs/api.md) 后端接口参考。
    - [docs/specs/](./docs/specs/) 详细设计规范。

## 📄 许可证

MIT License
