# AI News Nexus API 接口文档 (V2.0 完整版)

本文档详述了 AI News Nexus 后端提供的所有 API 接口，包括参数细节、数据结构及缓存行为。

**Base URL**: `/api/v1` (推荐) 或 `/` (Legacy 兼容)

---

## 1. 资讯分发 (News API)

### 1.1 获取资讯列表
- **Endpoint**: `GET /news/`
- **说明**: 获取聚合后的资讯项，支持高性能全文检索与多维过滤。已开启 **5 分钟** 缓存。
- **Query 参数**:
  | 参数 | 类型 | 默认值 | 说明 |
  | :--- | :--- | :--- | :--- |
  | `min_score` | `int` | `0` | 最低 AI 评分过滤（0-100）。首页建议使用 `71`。 |
  | `include_pending` | `bool` | `false` | 是否包含分数为 0（AI 尚未处理）的项。 |
  | `platform` | `string` | - | 指定单一平台 (twitter, github, arxiv, hn, ph, etc.)。 |
  | `platforms` | `string` | - | 逗号分隔的平台列表（用于智涌中国聚合）。 |
  | `query` | `string` | - | 关键词搜索。支持作者前缀 `@handle` 或正文匹配。 |
  | `author` | `string` | - | 精确匹配推特用户名。 |
  | `cluster_id` | `string` | - | 获取属于特定话题共振簇的资讯。 |
  | `start_date` | `datetime` | - | ISO 格式，仅返回该时间点之后发布的资讯。 |
  | `limit` | `int` | `50` | 单次返回最大条数。 |
  | `skip` | `int` | `0` | 分页偏移量。 |

### 1.2 上报新资讯
- **Endpoint**: `POST /news/`
- **说明**: 推送新抓取的资讯。后端会根据 `platform` + `external_id` 自动去重。

### 1.3 更新资讯
- **Endpoint**: `PATCH /news/{id}`
- **说明**: 用于 AI 后补评价分数、Takeaways 或关联话题 ID。

---

## 2. 采集目标 (Targets API)

### 2.1 获取信源名单
- **Endpoint**: `GET /targets/`
- **说明**: 获取抓取白名单。已开启 **10 分钟** 缓存。
- **Query 参数**:
  | 参数 | 类型 | 默认值 | 说明 |
  | :--- | :--- | :--- | :--- |
  | `platform` | `string` | - | 过滤平台。 |
  | `handle` | `string` | - | 精确搜索特定用户名。 |
  | `is_active` | `bool` | - | 是否活跃（过滤掉已下线的僵尸号）。 |
  | `has_scraped_data` | `bool` | - | `true`: 仅返回成功抓取过的；`false`: 仅返回从未抓取过的新人。 |
  | `status` | `string` | - | 状态过滤 (active, probation, deactivated, blacklisted)。 |

### 2.2 更新/下线信源
- **Endpoint**: `PATCH /targets/{id}`
- **说明**: 触发 Strike 系统下线或更新最后抓取时间。调用后自动清除 `targets` 缓存。

---

## 3. 话题共振 (Clusters API)

### 3.1 获取趋势话题
- **Endpoint**: `GET /clusters/trending`
- **说明**: 获取过去 48 小时内最具影响力的共振话题。已开启 **5 分钟** 缓存。

### 3.2 获取聚类详情
- **Endpoint**: `GET /clusters/{id}`
- **说明**: 获取特定话题的背景综述及所有关联资讯项。

---

## 4. 战略简报 (Insights API)

### 4.1 获取最新简报
- **Endpoint**: `GET /insights/latest`
- **说明**: 获取 AI 针对全网热点生成的深度综述。已开启 **10 分钟** 缓存。

### 4.2 获取历史简报
- **Endpoint**: `GET /insights/` | `GET /insights/{date}`
- **说明**: 查阅往期简报记录。

---

## 5. 战略资产库 (Assets API)

### 5.1 技术百科 (Wiki Terms)
- **获取词条列表**: `GET /api/assets/terms`
  - 参数: `limit` (默认 100), `category` (模型, 算力, 应用等)
  - 缓存: 30 分钟。
- **更新词条**: `PATCH /api/assets/terms/{id}`
  - 用于手动修正定义或调整热度值。

### 5.2 深度白皮书 (Reports)
- **获取白皮书列表**: `GET /api/assets/reports`
  - 参数: `limit` (默认 20)
  - 缓存: 30 分钟。
- **上报新白皮书**: `POST /api/assets/reports`
  - **幂等性**: 接口会根据 `end_date` 自动判断。若日期重合则执行 **Upsert** (更新现有内容)，防止重复。

---

## 6. 媒体存储 (Media API)
...
## 7. 开发约定

1. **缓存管理**: 写入类接口 (POST/PATCH/DELETE) 成功后会自动执行 `FastAPICache.clear()`。
2. **错误处理**: 标准 HTTP 状态码。429 表示频率限制，500 表示数据库或 AI 引擎异常。
3. **安全提示**: API 暂无内建 Token 校验，建议在生产环境通过 Nginx 限制请求来源。
