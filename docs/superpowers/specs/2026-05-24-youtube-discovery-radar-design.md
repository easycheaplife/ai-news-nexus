# YouTube 趋势发现雷达 (YouTube Discovery Radar) 设计文档

## 1. 背景与目标
目前系统的 YouTube 抓取基于固定的频道列表。为了扩大覆盖范围，本设计旨在实现一个“趋势发现雷达”，能够根据全网热点动态搜索并抓取 YouTube 上的深度内容。

## 2. 核心逻辑 (3-Stage Pulse)
雷达将作为 `scrapers/run.py` 的一个执行阶段，在常规抓取任务完成后触发。

### 阶段 1：趋势词提取 (Hot Topic Extraction)
- **数据源**：从数据库中查询过去 12 小时内 `score >= 80` 的所有资讯。
- **算法**：提取这些资讯的 `trending_keywords`，进行归一化处理（小写、去空格、去复数），按出现频次排序。
- **产出**：选取频次最高的 **Top 3** 关键词作为本轮搜索的锚点。

### 阶段 2：YouTube 脉冲采样 (Pulse Sampling)
- **搜索执行**：针对每个关键词，通过 YouTube API (或兼容接口) 检索过去 24 小时内的视频。
- **搜索参数**：`q={keyword}, order=relevance, publishedAfter=24h, maxResults=15`。
- **AI 初筛 (Pre-filtering)**：
    - 将 15 条搜索结果的标题和描述发送给 Gemini Flash Lite。
    - **Prompt 指令**：识别具有深度技术含量、由专家/大厂发布、或具有行业战略价值的视频。
    - **过滤**：排除短视频 (Shorts)、纯推销内容和低质量标题党。
    - **产出**：每个关键词选出 **Top 3** 优胜视频。

### 阶段 3：深度内容精读 (Deep Extraction)
- **字幕抓取**：针对优胜视频，调用 `YouTubeTranscriptApi` 获取完整字幕。
- **AI 评估**：调用现有的 `GeminiEvaluator` 对“描述 + 字幕”进行深度评分、提炼 Takeaways 和聚类。
- **数据持久化**：将最终结果推送至后端 `news_items`。

## 3. 架构设计

### 3.1 新增组件
- `scrapers/utils/youtube_radar.py`: 核心类 `YouTubeDiscoveryRadar`。
- `YouTubeDiscoveryRadar.run()`: 主入口，由 `run.py` 调用。

### 3.2 流程整合 (`run.py`)
1. 执行 `DiscoveryEngine` (信源发现)
2. 执行常规 Scrapers (内容抓取)
3. **执行 `YouTubeDiscoveryRadar` (新增：根据本轮抓取的关键词动态抓取 YouTube)**
4. 执行 `ClusteringEngine` (语义聚类)
5. 执行 `generate_daily_insights` (日报生成)

## 4. 关键技术细节
- **API 配额管理**：由于 YouTube Search API 配额昂贵 (100 pts/search)，系统将限制每轮运行的搜索词数量（Max 3），并对搜索结果进行本地缓存，防止短时间内重复搜索同一词条。
- **字幕降级**：若视频无字幕，则仅依靠标题和描述进行评估，但权重会降低。
- **并发控制**：YouTube 抓取涉及较多网络请求和 AI 调用，需保持合理的延迟防止触发频率限制。

## 5. 验收标准
1. `run.py` 能够根据本轮抓取到的热词（如 "GPT-4o"）自动在 YouTube 上发现相关的解析视频。
2. 发现的视频能正确参与语义聚类。
3. 视频详情包含 Takeaways，且媒体预览图显示正常。
