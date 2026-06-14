# Design Spec: Intelligence Sourcing & First Mover Identification

## 1. 概述 (Overview)
为了挖掘情报源头的价值，本功能旨在为每个话题共振簇（Topic Cluster）自动识别并标记“首发贡献者 (First Mover)”。该机制不仅仅依据绝对发布时间，还引入了基于历史表现的权重加权算法，优先尊重高价值、权威性强的信源。

## 2. 动态分级体系 (Dynamic Tiering System)
系统根据 `scraping_targets` 表中的 `avg_score`（历史平均分）将信源实时划分为三个等级：

| 等级 | 判定标准 | 溯源特权 (Grace Period) |
| :--- | :--- | :--- |
| **Tier S (Elite)** | `avg_score >= 90` | **15 分钟**：只要在话题首发后的 15 分钟内发推，即判定为首发者。 |
| **Tier A (Core)** | `80 <= avg_score < 90` | **5 分钟**：面对 Tier B 时拥有 5 分钟的优先判定权。 |
| **Tier B (Common)** | `avg_score < 80` | **无**：仅参与纯绝对时间的竞赛。 |

## 3. 核心算法 (Selection Algorithm)
当一个话题簇被创建或更新时，执行以下判定流程：
1.  **数据收集**：拉取话题簇关联的所有 `news_items`。
2.  **确定基准**：找到发布时间最早的项目，记其时间为 `T_start`。
3.  **Tier S 扫描**：检查是否有 Tier S 级别的信源发布于 `[T_start, T_start + 15min]` 范围内。若有，选取其中最早的一项作为 First Mover。
4.  **Tier A 扫描**：若无 Tier S，检查是否有 Tier A 级别信源发布于 `[T_start, T_start + 5min]` 范围内。若有，选取其中最早的一项作为 First Mover。
5.  **绝对优胜判定**：若以上均无，则 `T_start` 对应的信源即为 First Mover。

## 4. 技术实施方案 (Technical Implementation)

### 4.1 数据库变更 (Database)
- 在 `topic_clusters` 表中新增字段：
    - `first_mover_news_id`: 指向 `news_items` 的外键。
    - `first_mover_tier`: 记录当时判定的等级。

### 4.2 后端逻辑 (Backend)
- **API 更新**：
    - `GET /api/clusters/trending`：返回结果中需包含 `first_mover` 对象（含 handle, name, tier, published_at）。
- **计算服务**：
    - 在 `ClusteringEngine` 执行完毕后，调用 `FirstMoverResolver` 进行二次扫描计算并持久化。

### 4.3 前端视觉 (Frontend)
- **组件更新**：修改 `ResonanceCard.vue`。
- **UI 元素**：
    - 在卡片顶部或左侧增加一个带动效的勋章。
    - **Tier S**：金色发光勋章 + "Strategic Source"。
    - **Tier A**：靛蓝色勋章 + "Core Discovery"。
    - **Tier B**：灰色简约勋章 + "First to Break"。

## 5. 验证计划 (Testing)
1.  **场景 A (加权测试)**：构造数据，使 OpenAI (@OpenAI, S-Tier) 比一个小号晚 10 分钟发推。验证系统是否正确判定 OpenAI 为 First Mover。
2.  **场景 B (超时测试)**：构造数据，使 OpenAI 比一个小号晚 20 分钟发推。验证系统是否将首发权归还给小号。
3.  **场景 C (平级竞争)**：两个 S-Tier 都在 15 分钟内。验证系统是否选取其中更早的一个。
