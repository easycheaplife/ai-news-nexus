# Design Spec: AI-Enhanced Editorial Feed & Intelligence Dashboard

- **Topic**: Integrating AI-driven insights, trending analysis, and content clustering into the existing feed.
- **Date**: 2026-05-15
- **Status**: Draft

## 1. Overview
This design aims to transform the "AI News Nexus" from a simple aggregator into an intelligence hub. It focuses on three core features: collapsible daily briefings, AI-generated key takeaways, and smart grouping of related news.

## 2. Feature Details

### 2.1 The Briefing Center (Top Dashboard)
- **UI**: A collapsible area at the top of the main feed.
- **Components**:
    - **Hot Topics**: A horizontal list of tag-like keywords derived from today's highest-scoring content.
    - **Daily Pulse**: A mini-bar chart showing the volume of news per platform today.
    - **AI Summary**: A high-level summary (30-50 words) of "What happened in AI today."

### 2.2 Key Takeaways (Card Level)
- **UI**: A new section within `NewsCard.vue`.
- **Behavior**: Collapsed by default to save space; expands when clicked or hovered.
- **Content**: 3 bullet points提炼 from the `content` field using Gemini.

### 2.3 Smart Clustering (Aggregation)
- **UI**: A badge on cards saying "Discussed in X other places."
- **Behavior**: Clicking shows a list of related links (Twitter, Reddit, etc.) discussing the same topic.
- **Logic**: Backend or frontend logic to group items with similar titles or entities.

## 3. Technical Implementation

### 3.1 Backend Updates
- **Models**: Add `takeaways` (JSON) and `cluster_id` (String/UUID) to `NewsItem`.
- **Logic**: 
    - Update Gemini prompt in `scrapers/utils/ai.py` to include `takeaways`.
    - Implement a simple entity-based clustering during the scraping/pushing phase.

### 3.2 Frontend Updates
- **App.vue**: Implement the "Briefing Center" component logic.
- **NewsCard.vue**: Add the animated "Takeaways" expansion and "Source Badge."

## 4. Implementation Plan

1. **Phase 1: Backend Data Enrichment**
   - Update `schema.sql` and SQLAlchemy models.
   - Refine Gemini prompt to generate bullet points (Takeaways).
2. **Phase 2: UI - Briefing Center**
   - Build the top dashboard component with mock data first.
3. **Phase 3: UI - Card Enhancements**
   - Add the bullet point UI and clustering badge.
4. **Phase 4: Real-time Analysis**
   - Implement the actual clustering and summary calculation logic.

## 5. Success Criteria
- [ ] Users can get the core of any news item in under 5 seconds using Takeaways.
- [ ] The dashboard correctly identifies the top 3 trends of the day.
- [ ] Related news items are visibly linked together.
