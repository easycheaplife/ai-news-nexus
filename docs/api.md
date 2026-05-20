# AI News Nexus API 接口文档

本文档详细说明了 AI News Nexus 后端提供的核心 API 接口，用于数据采集、分发、情报分析及动态发现管理。

## 1. 资讯分发接口 (News API)

### 1.1 获取资讯列表
- **Endpoint**: `GET /news/`
- **说明**: 获取聚合后的资讯，按发现时间降序排列。
- **Query 参数**:
  - `platform` (Optional): 指定平台 (twitter, reddit, github, arxiv, youtube, hn, ph, search)。
  - `query` (Optional): 关键词搜索。
  - `skip` (Default: 0): 分页偏移。
  - `limit` (Default: 50): 每页数量。
- **响应示例**:
  ```json
  [
    {
      "id": 123,
      "title": "...",
      "content": "...",
      "score": 95,
      "reason": "AI推荐理由",
      "takeaways": ["要点1", "要点2"],
      "cluster_id": "语义话题ID",
      "media_urls": ["url1", "url2"],
      "scraped_at": "2026-05-15T..."
    }
  ]
  ```

### 1.2 上报新资讯
- **Endpoint**: `POST /news/`
- **说明**: 采集引擎推送抓取到的资讯，后端自动根据 `(platform, external_id)` 进行去重。

---

## 2. 深度简报接口 (Insights API)

### 2.1 获取最新战略简报
- **Endpoint**: `GET /insights/latest`
- **说明**: 获取由 AI 综合今日所有热点生成的全局总结。

### 2.2 上报每日简报
- **Endpoint**: `POST /insights/`
- **说明**: 供采集调度器在抓取结束后提交汇总分析结果。

---

## 3. 情报发现接口 (Discovery API)

### 3.1 获取待验证池内容
- **Endpoint**: `GET /discovery/`
- **说明**: 获取发现引擎从高分资讯中挖掘到的新账号（user）或技术热词（keyword）。
- **Query 参数**:
  - `status`: 过滤状态 (pending, vetted, rejected)。

### 3.2 提交发现信号
- **Endpoint**: `POST /discovery/`
- **说明**: 采集引擎将内容中提取到的 Mentions 或 Keywords 实时存入发现池。

### 3.3 更新发现池状态
- **Endpoint**: `PATCH /discovery/{id}`
- **说明**: 发现引擎验证通过后，更新其状态为 `vetted` 或 `rejected`。
- **Payload 示例**:
  ```json
  {
    "status": "vetted"
  }
  ```

---

## 4. 采集目标管理 (Targets API)

### 4.1 获取采集白名单
- **Endpoint**: `GET /targets/`
- **说明**: 获取当前账号名单，支持质量指标筛选。
- **Query 参数**:
  - `platform`: 指定平台。
  - `is_active`: (Optional) 是否活跃。
  - `status`: (Optional) 过滤状态 (active, probation, deactivated, blacklisted)。

### 4.2 更新采集目标状态
- **Endpoint**: `PATCH /targets/{id}`
- **说明**: 质量评价引擎提交评分、更新状态或下架低质信源。
- **Payload 示例**:
  ```json
  {
    "avg_score": 75,
    "total_posts": 45,
    "status": "active",
    "is_active": true
  }
  ```

### 4.3 注册新采集账号
- **Endpoint**: `POST /targets/`
- **说明**: 发现引擎验证（Vetting）通过后，将新牛人账号正式录入采集列表。

---

## 5. 开发建议

- **认证**: 目前接口主要面向内部封闭环境，建议在生产环境前端通过 Nginx 限制公网 POST 访问。
- **并发**: 后端基于异步 FastAPI 框架，但在数据库层面使用了 SQLAlchemy 同步引擎，在高频采集时建议维持合理的连接池配置。
