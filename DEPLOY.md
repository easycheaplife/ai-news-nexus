# AI News Nexus 部署与运行指南 (V2.0 完整版)

本手册涵盖了 AI News Nexus 情报中心的完整部署流程、环境变量配置及自动化运维参数。

---

## 1. 核心依赖

- **Python 3.9+**: 逻辑支撑。
- **MySQL 5.7+**: 结构化存储。
- **Redis 6.0+**: 必需。负责高性能缓存与任务队列。
- **Node.js 18+**: 前端构建。

---

## 2. 环境变量配置 (.env)

系统采用解耦配置，需在 `backend/` 和项目根目录各配置一个 `.env` 文件。

### 2.1 后端环境 (`backend/.env`)
| 变量名 | 示例值 | 说明 |
| :--- | :--- | :--- |
| `MYSQL_USER` | `root` | 数据库用户名。 |
| `MYSQL_PASSWORD` | `******` | 数据库密码。 |
| `MYSQL_HOST` | `localhost` | 数据库地址。 |
| `MYSQL_DB` | `ai_news` | 数据库名称。 |
| `REDIS_HOST` | `localhost` | Redis 地址，用于缓存首页接口。 |
| `MIN_SCORE` | `60` | 全局最低分过滤阈值（仅针对普通用户）。 |

### 2.2 采集环境 (`.env` 在根目录)
| 变量名 | 示例值 | 说明 |
| :--- | :--- | :--- |
| `SCRAPER_API_URL` | `http://8.x.x.x:8000` | 后端 API 入口，采集器将数据推送至此。 |
| `GEMINI_API_KEY` | `AIza...` | Google Gemini API Key。 |
| `TWITTER_USERNAME` | `jason_202606` | 用于同步关注列表的推特用户名。 |
| `TWITTER_EMAIL` | `x@mail.com` | 用于自动登录推特的邮箱。 |
| `TWITTER_PASSWORD` | `******` | 推荐使用推特小号。 |
| `MAX_SILENCE_DAYS` | `15` | **沉默惩罚期**：连续 X 天无产出则自动下线。 |
| `TWITTER_SCRAPE_INTERVAL_HOURS` | `1.0` | **抓取冷却期**：同一账号在此时间内不重复抓取。 |

---

## 3. 运维工具链使用

系统内置了多项自动化运维脚本，均在 `scrapers/` 目录下。

### 3.1 权限准备
V2.0 采用登录态抓取，必须首先获取推特 Cookie：
```bash
# 自动登录并生成 scrapers/cookies.json
python3 scrapers/generate_cookies.py
```

### 3.2 情报源同步
通过推特关注动作快速扩充情报网：
```bash
# 将推特小号的关注列表一键同步至系统名单
python3 scrapers/sync_following.py
```

---

## 4. 运行参数说明 (run.py)

主调度器支持细粒度的模块化控制：

| 参数 | 示例用法 | 效果 |
| :--- | :--- | :--- |
| `--loop` | `-l` | 开启持久化运行模式。 |
| `--interval` | `-i 3600` | 每次抓取的循环间隔（秒）。 |
| `--assets` | `--assets` | [NEW] 强制执行百科词条同步与白皮书合成。 |
| `--platform` | `-p twitter` | 仅抓取指定的单一平台，适合调试。 |
| `--style` | `--style official` | 指定生成的简报人格（toxic 或 official）。 |
| `--no-discovery` | - | 跳过挖掘新账号阶段。 |
| `--no-scrape` | - | 跳过采集阶段（常与 --assets 配合进行纯资产更新）。 |
| `--no-curation` | - | 跳过 15 天沉默账号的自动清理。 |

---

## 5. 生产环境部署建议 (Best Practices)

1. **后台常驻**: 推荐使用 `pm2` 或 `systemd` 管理后端和爬虫进程。
   ```bash
   # 使用 pm2 运行全自动爬虫
   pm2 start "python3 -m scrapers.run --loop" --name nexus-scrapers
   ```
2. **CDN 缓存**: 前端静态文件构建后 (`npm run build`) 推荐配合 Cloudflare 或阿里云 OSS 分发，以减轻后端服务器压力。
3. **安全加固**: 数据库与 Redis 端口严禁公网开放，后端 API 建议仅限 127.0.0.1 访问并由 Nginx 代理。
