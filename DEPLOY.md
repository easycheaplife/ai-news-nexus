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
pip install playwright yt-dlp
playwright install --with-deps chromium

# 启动后端服务
# 推荐方式：使用 uvicorn 命令行启动（支持热重载和更多生产参数）
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 备选方式：直接运行脚本（仅当 main.py 包含 uvicorn.run 逻辑时有效）
# python3 main.py
```

---

## 4. 采集引擎配置 (Scrapers)

采集器是系统的“心脏”，负责抓取和 AI 分析。系统现支持 **“全球分布式采集”** 架构，建议根据服务器所在地选择不同的部署方案。

### 4.1 环境配置
在项目根目录下创建 `.env` 文件：
```env
# 后端 API 地址 (本地开发或内网地址)
SCRAPER_API_URL=http://your-backend-ip:8000

# Gemini AI 配置 (海外节点必需)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.1-flash-lite,gemini-2.0-flash

# 采集控制
SCRAPE_WINDOW_HOURS=72         # 抓取过去多少小时内的内容
```

### 4.2 方案 A：国内节点部署 (CN Node)
适用于阿里云、腾讯云等国内服务器。主要抓取国内信源（智涌中国），无需科学上网。

- **核心特点**：不直接调用 Gemini API（规避网络限制），只负责“原始数据采集”。
- **运行命令**：
  ```bash
  # 运行国内专属脚本 (自动跳过海外发现、评价与雷达阶段)
  python3 -m scrapers.run_cn --loop --interval 600
  ```

### 4.3 方案 B：海外节点部署 (Global Node)
适用于 AWS、Google Cloud、Vultr 等海外服务器。作为系统的“大脑”。

- **核心特点**：抓取全球信源 + 执行 **“全局补偿评价”**（帮国内节点抓取的数据补齐 AI 评分）。
- **运行命令**：
  ```bash
  # 运行海外专属脚本 (包含发现、评价、聚类与每日简报生成)
  python3 -m scrapers.run_global --loop --interval 3600
  ```

### 4.4 独立报告生成与维护 (Advanced Usage)
在某些情况下（如 Gemini API 触发 429 限流，或者需要补发历史报告），您可以独立运行报告生成逻辑，而无需重新抓取数据或消耗大量 AI 额度。

- **仅生成今日报告 (跳过抓取与评分)**：
  ```bash
  python3 -m scrapers.run --report
  ```
- **生成指定日期的报告**：
  ```bash
  python3 -m scrapers.run --report --date 2026-06-10
  ```
- **生成综述但跳过逐条评分 (大幅减少 Gemini 请求)**：
  ```bash
  python3 -m scrapers.run --insights --report --skip-scoring
  ```

---

## 5. 智涌中国 (CN AI Pulse) 统一命名
系统已将国内 AI 数据源（AI HOT、量子位等）统一命名为 **“智涌中国”**。

- **数据流向**：国内节点抓取 -> 后端 (Score: 0) -> 海外节点读取 (自动识别 Score 0) -> 调用 Gemini 补齐评价 -> 后端更新 -> 前端展示。
- **前端展示**：在“智涌中国”分类下可一览国内精华资讯。

---

## 6. 自动化运维 (Crontab)

建议根据节点角色配置不同的 Cron 任务：

### 国内节点 (CN Node)
```bash
# 每 10 分钟高频抓取国内实时资讯
*/10 * * * * cd /path/to/ai-news-nexus && /path/to/venv/bin/python3 -m scrapers.run_cn >> logs/run_cn.log 2>&1
```

### 海外节点 (Global Node)
```bash
# 每 1 小时运行一次全球抓取与全局 AI 分析
0 * * * * cd /path/to/ai-news-nexus && /path/to/venv/bin/python3 -m scrapers.run_global >> logs/run_global.log 2>&1
```

---

## 7. 跨源互证 (Resonance) 展示条件

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
