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
    mysql -u your_user -p ai_news < backend/schema.sql
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

# 启动后端服务
python3 -m uvicorn main:app --reload --port 8000
```

---

## 4. 采集引擎配置 (Scrapers)

采集器是系统的“心脏”，负责抓取和 AI 分析。

1.  **配置环境**: 在项目根目录下创建 `.env` 文件：
    ```env
    # 后端 API 地址 (本地开发)
    SCRAPER_API_URL=http://localhost:8000

    # Gemini AI 配置
    GEMINI_API_KEY=your_gemini_api_key_here
    GEMINI_MODEL=gemini-3.1-flash-lite

    # 网络代理 (国内环境访问 Twitter/Google 通常需要)
    # HTTP_PROXY=http://127.0.0.1:7890
    # HTTPS_PROXY=http://127.0.0.1:7890
    ```

2.  **初始化采集目标**: 首次运行前需将初始 KOL 名单导入数据库：
    ```bash
    python3 -m scrapers.seed_targets
    ```

3.  **手动运行抓取**:
    ```bash
    # 全量抓取并自动生成今日简报 (推荐)
    python3 -m scrapers.run

    # 指定平台抓取 (不触发简报总结)
    python3 -m scrapers.run -p twitter
    python3 -m scrapers.run -p github
    ```

4.  **运行发现引擎 (信源扩张)**:
    ```bash
    # 定期运行以自动面试并加入新发现的 KOL
    python3 -m scrapers.discovery_run
    ```

---

## 5. 前端部署 (Vue 3)

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
