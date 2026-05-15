# 采集器增量抓取方案 (Incremental Scraping)

## 1. 目标
通过记录上次抓取的“最后位置”（游标），实现高效抓取。只处理自上次运行以来的新数据，遇到旧数据立即停止。

## 2. 状态管理
采集器使用 `scrapers/state.json` 文件持久化存储每个平台和账号的抓取状态。

### 状态结构
```json
{
  "twitter": {
    "OpenAI": "1890123456789012345"
  },
  "reddit": {
    "MachineLearning": "1715612345"
  },
  "hn": {
    "latest_id": 40345678
  }
}
```

## 3. 实现细节

### BaseScraper (基类)
- `load_state()`: 启动时加载 `state.json`。
- `save_state()`: 抓取完成后保存最新的游标。
- `get_last_id(platform, sub_key)`: 获取指定账号/板块的最后 ID。
- `update_last_id(platform, sub_key, current_id)`: 实时更新最大 ID 游标。

### 平台处理
- **Twitter**: 解析推文 ID (id_str)，若 `id_str <= last_id` 则停止该账号的抓取。
- **Reddit**: 解析 `created_utc` 时间戳，若 `timestamp <= last_timestamp` 则停止。
- **Hacker News**: 记录扫描过的最大 `story_id`，只处理更大的 ID。
- **Product Hunt**: 基于 RSS 条目的唯一 ID 或发布时间进行过滤。

## 4. AI 智能评估 (AI Evaluation)
采集器集成了 Google Gemini API，对抓取到的内容进行自动化评分和推荐理由生成。

### 配置方法
在项目根目录或 `scrapers/` 目录下的 `.env` 文件中配置：
```env
# Gemini API Key (从 Google AI Studio 获取)
GEMINI_API_KEY=your_api_key_here

# 选用的 Gemini 模型
GEMINI_MODEL=gemini-1.5-flash
```

### 可用模型列表 (2026版)
根据环境支持，以下模型 ID 可直接填入 `GEMINI_MODEL`：

| 模型 ID | 说明 | 推荐场景 |
| :--- | :--- | :--- |
| `gemini-1.5-flash` | 速度极快，高性价比 | 基础采集、批量处理 |
| `gemini-2.0-flash` | 下一代快速模型，逻辑更强 | 默认推荐 |
| `gemini-3.1-flash-lite` | **3.1系列首选**，极速响应 | 实时资讯评分 |
| `gemini-3.1-pro-preview` | 强推理能力，分析更深刻 | 深度内容分析 |
| `gemini-3.1-flash-image-preview` | 支持图像分析的 3.1 预览版 | 包含图片的推文分析 |

## 5. 异常恢复
如果 `state.json` 丢失，采集器将回退到全量抓取模式（后端会自动去重），并在完成后重新生成状态文件。
