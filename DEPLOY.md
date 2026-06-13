# AI News Nexus 部署与运行指南 (V2.0)

本指南将帮助您完成 AI News Nexus 情报中心的本地搭建与生产部署。V2.0 版本引入了 **Twikit 全真模拟抓取**、**Redis 缓存** 及 **Strike 自动化治理**。

## 1. 环境要求

-   **Python**: 3.9+ (生产环境推荐 3.10+)
-   **Node.js**: 18+ (推荐 20+)
-   **MySQL**: 5.7+ (推荐 8.0)
-   **Redis**: 必需。用于加速首页接口及缓存聚类数据。
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
    mysql -u root -p ai_news < backend/schema.sql
    # 同步增量更新
    mysql -u root -p ai_news < backend/migrations/cross_source_correlation_schema.sql
    mysql -u root -p ai_news < backend/migrations/update_targets_schema.sql
    ```
3.  **配置后端环境**: 在 `backend/` 目录下创建 `.env`：
    ```env
    MYSQL_USER=root
    MYSQL_PASSWORD=your_password
    MYSQL_HOST=localhost
    MYSQL_PORT=3306
    MYSQL_DB=ai_news
    REDIS_HOST=localhost
    REDIS_PORT=6379
    ```

---

## 3. 后端启动 (FastAPI)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 安装 Playwright 浏览器依赖 (日报生成引擎必需)
playwright install --with-deps chromium

# 启动服务
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 4. 采集引擎配置 (Scrapers)

### 4.1 核心环境配置
在项目根目录下创建 `.env`：
```env
SCRAPER_API_URL=http://localhost:8000
GEMINI_API_KEY=your_gemini_key
# Twitter 账号配置 (用于 Twikit 登录，建议使用小号)
TWITTER_USERNAME=your_handle
TWITTER_EMAIL=your_email
TWITTER_PASSWORD=your_password
```

### 4.2 [重要] 生成 Twitter Cookie
V2.0 采用登录态抓取，必须先生成 `cookies.json`：
```bash
python3 scrapers/generate_cookies.py
```
*注：如果脚本登录失败，请参考 README 说明进行手动 Cookie 提取。*

### 4.3 自动化同步
如果您在推特上关注了新大佬，运行此脚本将其同步至系统：
```bash
python3 scrapers/sync_following.py
```

### 4.4 运行模式
- **全球闭环 (海外节点)**：`python3 -m scrapers.run_global --loop --interval 3600`
- **国内采集 (国内节点)**：`python3 -m scrapers.run_cn --loop --interval 600`

---

## 5. 前端部署 (Vue 3)

```bash
cd frontend
npm install
# 本地开发
npm run dev
# 生产构建
npm run build
```

---

## 6. 自动化运维逻辑 (Strike System)

系统现在会自动执行以下“除草”逻辑：
- **实时下线**：抓取时发现账号不存在或被封，立即标记为 `deactivated`。
- **质量惩罚**：连续 15 次抓取无有效原创/高分内容，自动下线。
- **沉默清理**：运行 `python3 -m scrapers.curation_run` 清理 15 天未发言的僵尸号。

---

## 7. 常见问题 (Q&A)

### Q: 首页“核心圈”数据不更新？
后端开启了 10 分钟缓存。手动修改账号状态后，系统会自动清除缓存。如仍未更新，请检查 Redis 是否正常运行。

### Q: 聚类板块 (Resonance) 消失？
聚类引擎依赖过去 24 小时的高分资讯。请确保已运行 `python3 -m scrapers.utils.clustering`。
