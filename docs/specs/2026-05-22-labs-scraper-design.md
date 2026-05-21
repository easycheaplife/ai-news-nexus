# LabsScraper: Universal AI Lab News Aggregator Design Spec

## 1. 背景与目标
由于 Twitter (Nitter) 和 YouTube 数据源存在不稳定性及信噪比波动，本项目需要建立一个高可靠、高信号的“核心情报网”。官方实验室的博客提供最权威的发布动态，且通常支持标准的 RSS/Atom 订阅，非常适合作为项目的核心补充。

## 2. 核心架构
`LabsScraper` 将继承自 `BaseScraper`，采用配置驱动的模式实现。

### 2.1 关键特性
- **通用性**：通过字典配置管理多个实验室的 RSS 链接。
- **稳定性**：直接请求官方 Feed，不依赖代理或第三方镜像。
- **增量抓取**：利用 `state.json` 记录每个实验室最后一次处理的 Link 或 Published Date。
- **AI 分析**：复用 `evaluator` 进行 0-100 评分、摘要提取及语义聚类。

### 2.2 初始信源列表
| 实验室名称 | RSS/Atom 地址 |
| :--- | :--- |
| OpenAI | `https://openai.com/news/rss.xml` |
| Anthropic | `https://www.anthropic.com/news/rss.xml` |
| Google DeepMind | `https://deepmind.google/blog/rss.xml` |
| Mistral AI | `https://mistral.ai/news/index.xml` |
| DeepSeek | `https://blog.deepseek.com/rss.xml` |

## 3. 数据流程
1. **Fetch**: 遍历配置字典，使用 `feedparser` 获取 RSS 内容。
2. **Filter**: 
    - 检查 `state.json`，跳过已处理的条目。
    - 检查发布时间，确保在 `SCRAPE_WINDOW_HOURS` 窗口内。
3. **Analyze**: 
    - 提取标题和正文摘要。
    - 调用 AI Evaluator 进行多维评分。
4. **Push**: 将格式化的 `item` 推送到后端 `/news/` 接口。
5. **Persist**: 成功处理后更新 `state.json`。

## 4. 技术挑战与对策
- **字段不一致**：不同 RSS 的标题、摘要、发布日期字段名可能不同。
    - *对策*：在解析逻辑中加入字段嗅探（如尝试 `summary`, `description`, `content:encoded`）。
- **内容截断**：部分 RSS 只提供摘要。
    - *对策*：利用现有的 `LinkScraper` 在评分较低或摘要过短时尝试抓取全文（可选）。

## 5. 验收标准
1. `LabsScraper` 能够成功启动并遍历所有配置的源。
2. 抓取的数据能够正确在 `state.json` 中记录游标。
3. 数据成功推送到后端，并在前端“核心圈”或对应平台过滤中显示。
4. 能够正确处理网络超时或无效 XML 且不崩溃。
