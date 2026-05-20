# AI News Nexus - 全方位 AI 资讯情报中心

AI News Nexus 是一个高度自动化的 AI 行业垂直情报系统。它不仅能从全网聚合资讯，还能利用 Google Gemini 对内容进行深度分析、语义聚类和全自动信源扩张，打造属于你的“AI 时代情报指挥部”。

## 🌟 核心特性

- **多维深度采集**：
  - **穿透式抓取**：自动解析外链内容正文，告别“只有标题”的资讯。
  - **Thread 拼接**：自动合并 Twitter 长推文，提供完整语境。
  - **多模态感知**：自动抓取 YouTube 视频字幕，支持视频静音自播与 4K 高清原图。
  - **高可用抗封锁**：Twitter 采集支持官方接口与 **Nitter 实例轮询** 双引擎，自动应对 429 频率限制。
- **AI 智能中枢 (Gemini 驱动)**：
  - **核心提炼**：自动生成 3 条精华要点（Takeaways），5 秒掌握精髓。
  - **语义聚类**：全自动识别跨平台热点（Cluster），话题级精准聚合。
  - **战略简报**：每日自动生成 Markdown 格式的深度行业总结报告。
  - **信源汰换**：自动执行“信用分”评估，基于 AI 评分对账号进行末位淘汰与智能晋升。
- **混合式发现引擎**：
  - **社交扩张**：自动挖掘大佬互动圈，AI 自动面试并加入抓取白名单。
  - **全网猎词**：基于每日技术热词发起全球检索，捕捉圈外爆款。
  - **全链路闭环**：实现从“信号发现 -> AI 面试 -> 试用采集 -> 自动汰换”的全生命周期无人值守管理。
- **专业级 UI/UX**：
  - **战略横条布局**：1400px 高密度信息排版，极大提升扫读效率。
  - **沉浸式灯箱**：一键预览高清素材，支持 ESC 极速退出。
  - **数据仪表盘**：实时展示今日简报、热词云及全平台活跃脉冲。

## 🏗️ 系统架构

系统遵循 **“生产 -> 存储 -> 消费”** 的解耦架构：

1. **Scrapers (生产层)**：模块化 Python 爬虫，负责抓取、AI 评估与信号提取。
2. **Backend (存储层)**：基于 FastAPI + MySQL，提供高性能数据持久化与情报分发。
3. **Frontend (消费层)**：基于 Vue 3 + Tailwind CSS 的响应式专业数据终端。

## 📂 目录结构

```text
ai-news-nexus/
├── backend/            # FastAPI 后端服务 (逻辑轻量化，只读写数据)
├── scrapers/           # 采集引擎 (重逻辑，全量调用 Gemini API)
│   ├── engines/        # 各平台爬虫 (twitter, github, youtube, arxiv等)
│   ├── utils/          # AI 分析、外链穿透等工具
│   └── discovery_run.py # 核心：发现引擎与信源扩张脚本
├── docs/               # 完整的文档库 (API 手册、设计规范)
└── frontend/           # Vue 3 仪表盘 (1400px 高密度排版)
```

## 🛠️ 技术栈

- **Frontend**: Vue 3, Vite, Tailwind CSS, Lucide Icons, Axios.
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy, Pydantic, MySQL.
- **AI/NLP**: Google Gemini API (Flash/Pro), BeautifulSoup 4, Feedparser.

## 🚀 快速开始

1. **基础部署**：请参阅 [DEPLOY.md](./DEPLOY.md)。
2. **全自动运行 (推荐)**：
   运行以下命令开启“无人值守”模式，系统将每小时自动执行一次完整的闭环流程：
   ```bash
   python3 scrapers/run.py --loop --scrape --interval 3600
   ```

### 命令行参数说明

| 参数 | 缩写 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `--scrape` | `-s` | `False` | **核心开关**。是否开启各平台（Twitter, Reddit 等）的账号内容采集。默认关闭，仅执行维护任务。 |
| `--platform` | `-p` | `None` | 指定抓取单一平台（如 `twitter`, `hn`）。指定后会自动开启该平台的采集。 |
| `--loop` | `-l` | `False` | 开启循环模式，程序将常驻运行。 |
| `--interval` | `-i` | `3600` | 循环模式下的等待间隔（秒）。 |

### 常见运行场景

- **仅执行维护任务** (发现新账号 + 汰换低质信源 + 生成简报)：
  ```bash
  python3 scrapers/run.py
  ```
- **全量闭环运行** (维护任务 + 全平台采集)：
  ```bash
  python3 scrapers/run.py --scrape
  ```
- **调试特定平台**：
  ```bash
  python3 scrapers/run.py -p twitter
  ```

3. **接口参考**：请参阅 [docs/api.md](./docs/api.md)。
3. 设计细节：请参阅 [docs/specs/](./docs/specs/) 目录下的详细方案。

## 📄 许可证

MIT License
