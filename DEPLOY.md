# 部署与开发指南

本指南将帮助您在本地或服务器上完成 AI News Nexus 的安装与运行。

## 1. 环境要求

-   Python 3.9+
-   Node.js 18+
-   MySQL 5.7+ (可选, 默认支持 SQLite)

## 2. 数据库配置 (MySQL)

1.  登录 MySQL 并运行初始化脚本：
    ```bash
    mysql -u root -p < backend/schema.sql
    ```
2.  在 `backend/` 目录下创建 `.env` 文件：
    ```env
    MYSQL_USER=root
    MYSQL_PASSWORD=your_password
    MYSQL_HOST=localhost
    MYSQL_DB=ai_news
    ```
## 3. 后端启动 (FastAPI)

```bash
cd backend
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate
# 安装依赖
pip install -r requirements.txt
# 启动 (推荐使用 python3 -m 方式以确保使用虚拟环境中的包)
python3 -m uvicorn main:app --reload --port 8000
```

## 4. 采集器运行 (Scrapers)

采集器需要后端 API 处于运行状态。在**项目根目录**下运行：

```bash
# 确保在项目根目录 ai-news-nexus 下执行
python3 -m scrapers.run
```

## 5. 前端启动 (Vue 3)

```bash
cd frontend
npm install
npm run dev
```

## 6. 常见问题排查 (Troubleshooting)

### 6.1 ModuleNotFoundError: No module named 'pydantic_settings'
如果出现此错误，说明 `pydantic-settings` 未能正确安装或未被当前路径识别：
1. 确保已激活虚拟环境：`source venv/bin/activate`。
2. 运行安装：`pip install pydantic-settings`。
3. 启动后端时务必使用 `python3 -m uvicorn main:app` 而非直接运行 `uvicorn`。

### 6.2 采集器导入错误 (ModuleNotFoundError: No module named 'scrapers')
务必在 **项目根目录** (`ai-news-nexus/`) 运行命令，而不是进入 `scrapers/` 文件夹。运行命令应为 `python3 -m scrapers.run`。

## 7. 生产环境部署建议

访问 `http://localhost:5173` 即可看到界面。

## 6. 生产环境部署建议

-   **后端**: 使用 `gunicorn` 配合 `uvicorn` 工作进程。
-   **前端**: 使用 `npm run build` 生成静态文件，并通过 Nginx 托管。
-   **定时任务**: 使用 Linux `crontab` 定时执行采集脚本：
    ```bash
    # 每小时执行一次采集
    0 * * * * cd /path/to/ai-news-nexus && /path/to/venv/bin/python3 -m scrapers.run
    ```
