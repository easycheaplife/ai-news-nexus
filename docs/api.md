# AI News Nexus API 接口文档 (V2.0)

本文档详细说明了 AI News Nexus 后端提供的核心 API 接口。V2.0 增加了 **Redis 缓存支持**、**更细粒度的信源过滤** 及 **Strike 自动化治理接口**。

## 1. 采集目标管理 (Targets API)

### 1.1 获取采集名单
- **Endpoint**: `GET /targets/`
- **说明**: 获取当前账号名单，支持质量与状态筛选。已开启 10 分钟 Redis 缓存。
- **Query 参数**:
  - `platform`: 指定平台 (twitter, github, etc.)。
  - `handle`: (New) 精确匹配用户名。
  - `is_active`: 是否活跃 (true/false)。
  - `status`: 过滤状态 (active, probation, deactivated, blacklisted)。
  - `has_scraped_data`: (New) 过滤是否有历史抓取记录。

### 1.2 更新采集目标
- **Endpoint**: `PATCH /targets/{id}`
- **说明**: 更新信源状态、平均分或失败计数。调用后会自动清除 `targets` 缓存空间。
- **Payload**:
  ```json
  {
    "is_active": false,
    "status": "deactivated",
    "failure_count": 15,
    "last_scraped_at": "2026-06-13T..."
  }
  ```

---

## 2. 资讯分发接口 (News API)

### 2.1 获取资讯列表
- **Endpoint**: `GET /news/`
- **说明**: 获取聚合后的资讯，按发布时间降序排列。
- **Query 参数**:
  - `min_score`: (Default: 0) 最低分过滤。首页推荐设置为 71。
  - `include_pending`: (Default: true) 是否包含 0 分（待 AI 处理）的内容。
  - `start_date`: (ISO string) 抓取该日期之后的内容。
  - `query`: 支持 `@handle` 搜索及关键词匹配。
  - `limit`: (Default: 50) 单次返回数量。

---

## 3. 话题聚类接口 (Clusters API)

### 3.1 获取共振话题
- **Endpoint**: `GET /clusters/trending`
- **说明**: 获取过去 48 小时内 AI 识别出的高共鸣话题。已开启 5 分钟 Redis 缓存。

### 3.2 批量创建聚类
- **Endpoint**: `POST /clusters/batch`
- **说明**: 供 AI 聚类引擎上报分析结果。调用后会自动清除 `clusters` 缓存空间。

---

## 4. 情报发现接口 (Discovery API)

### 4.1 获取发现池
- **Endpoint**: `GET /discovery/`
- **说明**: 获取 AI 从资讯中提取的待验证信号。已开启 10 分钟缓存。
- **Query 参数**: `status` (pending, vetted, rejected)。

### 4.2 提交/更新信号
- **Endpoint**: `POST /discovery/` | `PATCH /discovery/{id}`
- **说明**: 实时同步新发现的 Handle 或关键字。

---

## 5. 开发备注

1. **缓存管理**: 系统采用命名空间缓存。写操作（POST/PATCH/DELETE）后会自动触发 `FastAPICache.clear(namespace="...")`，保证数据最终一致性。
2. **时区说明**: 所有 API 返回及接收的时间戳均采用 **UTC** 标准 ISO 格式。
3. **接口版本**: 生产环境建议统一使用 `/api/v1/` 前缀。
