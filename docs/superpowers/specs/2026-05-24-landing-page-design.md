# AI News Nexus Landing Page (Linear Style) 设计文档

## 1. 目标与定位
为 AI News Nexus 打造一个具有“顶级生产力工具”质感的落地页。将产品定位为**“个人 AI 情报指挥部 (Personal AI Intelligence Command Center)”**，目标用户为创业者、投资人及追求极致信息效率的决策者。

## 2. 视觉规范 (Brand Identity)
参考 `design-md/linear.app/DESIGN.md`，执行极致深色美学。

- **核心配色**:
  - `Canvas` (背景): `#010102` (极深蓝黑)
  - `Primary` (点缀): `#5e6ad2` (薰衣草紫)
  - `Ink` (正文): `#f7f8f8` (浅灰)
  - `Surface-1`: `#0f1011` (炭黑，用于卡片)
  - `Hairline`: `#23252a` (边框)
- **排版**:
  - 字体：优先使用 `Inter` 或 `SF Pro Display`。
  - 追踪：大标题使用负间距 (`-1.8px` 到 `-3.0px`)，营造紧凑专业感。
- **动效**:
  - 微弱的渐变发光效果 (Glow)。
  - 极细腻的阴影和线条。

## 3. 页面结构 (Page Structure)

### 3.1 Hero Section
- **标题**: `AI News Nexus.`
- **副标题**: `Your Intelligence Command Center.`
- **视觉核心**: 3D 倾斜展示的“战略日报”精美截图，带有发光边框。
- **文案**: "Stop drowning in raw feeds. Nexus processes thousands of signals from Twitter, GitHub, and Labs into a single, high-stakes decision briefing."

### 3.2 Signal Resonance (话题共振)
- **展示方式**: 使用 `Surface-1` 提升感的卡片。
- **内容**: 强调语义聚类和共振指数，将分散的信号转化为清晰的趋势。

### 3.3 Autonomous Curation (无人值守)
- **展示方式**: 简洁的动态面板模拟。
- **内容**: 展示发现新信源、末位淘汰的闭环逻辑。

### 3.4 Bilingual Narrative (叙事风格)
- **内容**: 展示 `toxic` (毒舌) 与 `official` (正经) 风格的切换对比。

### 3.5 Craftsmanship (技术底色)
- **内容**: 展示 CLI 运行状态或配置文件，体现“开发者友好”与“可控性”。

## 4. 技术实现
- **框架**: Vue 3 (SFC)
- **样式**: Vanilla CSS / Tailwind (遵循 Linear 间距规范)
- **图标**: `lucide-vue-next`

## 5. 验收标准
1. 页面在深色模式下展现出静谧、豪华的视觉质感。
2. 响应式适配：移动端标题自动缩放，卡片流式排列。
3. 文案精准传达“降噪”与“情报”的核心价值。
