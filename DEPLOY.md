# AI News Nexus 部署与运行指南

本指南将帮助您从零开始完成 AI News Nexus 情报中心的本地搭建与服务器部署。

## 1. 环境要求

-   **Python**: 3.9+ (推荐 3.10+)
-   **Node.js**: 18+ (推荐 20+)
-   **MySQL**: 5.7+ (推荐 8.0)
-   **Google Gemini API Key**: 必须具备有效 Key 才能激活 AI 分析功能。

---

## 2. 数据库配置 (MySQL)

1.  **创建数据库**:
    ```sql
    CREATE DATABASE ai_news CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ```
2.  **初始化表结构**:
    ```bash
    # 基础表结构
    mysql -u your_user -p ai_news < backend/schema.sql
    
    # 增量更新：话题聚类与共振功能 (2026-05-21)
    mysql -u your_user -p ai_news < backend/migrations/cross_source_correlation_schema.sql
    
    # 增量更新：信源管理与黑名单优化 (2026-05-21)
    mysql -u your_user -p ai_news < backend/migrations/update_targets_schema.sql
    ```
3.  **配置后端环境**: 在 `backend/` 目录下创建 `.env` 文件：
    ```env
    MYSQL_USER=your_user
    MYSQL_PASSWORD=your_password
    MYSQL_HOST=localhost
    MYSQL_DB=ai_news
    APP_PORT=8000
    ```

---

## 3. 后端启动 (FastAPI)

```bash
cd backend
# 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装核心依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器依赖 (日报生成引擎必需)
pip install playwright
playwright install --with-deps chromium

# 启动后端服务
python3 -m uvicorn main:app --reload --port 8000
```

---

## 4. 采集引擎配置 (Scrapers)

采集器是系统的“心脏”，负责抓取和 AI 分析。**注意：请务必在项目根目录下运行采集命令。**

1.  **配置环境**: 在项目根目录下创建 `.env` 文件：
    ```env
    # 后端 API 地址 (本地开发)
    SCRAPER_API_URL=http://localhost:8000

    # Gemini AI 配置 (支持以逗号分隔的模型列表，按优先级自动降级)
    GEMINI_API_KEY=your_gemini_api_key_here
    GEMINI_MODEL=gemini-3.1-flash-lite,gemini-2.0-flash,gemini-flash-latest

    # 截图与报表配置
    REPORT_FRONTEND_URL=http://localhost:5173/report # 截图访问的前端地址
    
    # 采集控制
    SCRAPE_WINDOW_HOURS=72         # 抓取过去多少小时内的内容
    TWITTER_MAX_429_ERRORS=10      # 允许的最大 Twitter 429 报错次数
    PRODUCTHUNT_TOKEN=your_token   # 可选：ProductHunt API Token

    # 发现引擎限制
    MAX_ACTIVE_TARGETS=100
    DISCOVERY_MAX_VETTING=50

    # 网络代理 (国内环境访问 Twitter/Google 通常需要)
    # HTTP_PROXY=http://127.0.0.1:7890
    # HTTPS_PROXY=http://127.0.0.1:7890
    ```

2.  **初始化采集目标**: 首次运行前需将初始 KOL 名单导入数据库：
    ```bash
    python3 -m scrapers.seed_targets
    ```

3.  **执行核心流程**:
    ```bash
    # 1. 运行全量抓取与分析 (推荐使用 -m 模式运行，避免包引入错误)
    python3 -m scrapers.run --scrape --insights

    # 2. 运行信源自动扩张 (发现新大咖)
    python3 -m scrapers.run --discovery

    # 3. 运行跨源话题聚类 (生成“共振”卡片)
    python3 -m scrapers.utils.clustering
    ```

---

## 5. 跨源互证 (Resonance) 展示条件

要让前端首页显示“跨源互证”卡片，必须同时满足：
1.  **后端有数据**：已成功运行过 `python3 -m scrapers.utils.clustering`。
2.  **语义重合**：AI 识别出至少两个不同平台的资讯在讨论同一话题。
3.  **前端状态**：
    -   搜索框为空 (`filters.query == ''`)。
    -   平台筛选为“全部来源”。

### 5.1 本地开发
```bash
cd frontend
npm install
npm run dev
```

### 5.2 生产构建 (Netlify)
-   **Build Command**: `npm run build`
-   **Publish directory**: `dist`
-   **Environment Variables**: 
    - `VITE_API_URL`: 设置为 `/api` (配合项目中的 `_redirects` 使用)。
-   **Proxy 配置**: 项目已包含 `public/_redirects` 和 `netlify.toml`，会自动处理跨域转发。

---

## 6. 自动化运维 (Crontab)

建议在服务器上配置以下定时任务：

```bash
# 每 2 小时运行一次全量抓取与分析
0 */2 * * * cd /path/to/ai-news-nexus && /path/to/venv/bin/python3 -m scrapers.run >> logs/run.log 2>&1

# 每天凌晨 4 点运行一次信源扩张引擎
0 4 * * * cd /path/to/ai-news-nexus && /path/to/venv/bin/python3 -m scrapers.discovery_run >> logs/discovery.log 2>&1
```

---

## 7. 常见问题 (Q&A)

### Q: 抓取显示成功，但前端没数据？
1. 检查后端控制台是否有 `mentioned_users` 相关的 SQL 报错，如有，请根据 `schema.sql` 同步表结构。
2. 确认 `GEMINI_API_KEY` 是否有效，评分低于 60 的资讯默认在前端不展示。

### Q: Twitter 抓取全是 429 报错？
Twitter 的免登录接口对同一 IP 限制极严。建议增加抓取间隔（修改 `twitter.py` 中的 `random.uniform`）或在根目录 `.env` 中配置高质量代理。

### Q: 如何手动添加新信源？
可以直接调用 `POST /targets/` 接口，或在数据库 `scraping_targets` 表中手动插入一行。
