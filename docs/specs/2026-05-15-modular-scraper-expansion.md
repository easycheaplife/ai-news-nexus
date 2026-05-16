# Design Spec: Modular Scraper Architecture & Expansion

- **Topic**: Refactoring scrapers into a modular structure and adding new AI data sources.
- **Date**: 2026-05-15
- **Status**: Draft

## 1. Overview
The current `scrapers/engines/platforms.py` contains multiple scraper classes, making it difficult to maintain and scale. This design proposes a "One Class, One File" architecture and the addition of three high-value AI information sources: GitHub Trending, ArXiv (cs.AI), and YouTube.

## 2. Architecture Changes

### 2.1 Directory Structure
We will move from a monolithic file to a directory-based package:
- `scrapers/engines/base.py`: Contains `BaseScraper` and common utilities.
- `scrapers/engines/twitter.py`: Refactored Twitter logic.
- `scrapers/engines/reddit.py`: Refactored Reddit logic.
- `scrapers/engines/ph.py`: Refactored Product Hunt logic.
- `scrapers/engines/hn.py`: Existing Hacker News logic (moved to follow naming convention).
- `scrapers/engines/github.py`: [New] GitHub Trending.
- `scrapers/engines/arxiv.py`: [New] ArXiv cs.AI.
- `scrapers/engines/youtube.py`: [New] YouTube AI Channels.

### 2.2 Shared Logic
- All engines inherit from `BaseScraper`.
- Gemini evaluation remains a shared utility in `scrapers/utils/ai.py`.

## 3. New Data Sources

### 3.1 GitHub Trending
- **Endpoint**: `https://github.com/trending/python?since=daily` (filtered for AI libraries).
- **Extraction**: Repository name, description, star count, and primary language.
- **AI Focus**: Evaluate based on description and README snippet.

### 3.2 ArXiv cs.AI
- **Endpoint**: ArXiv API (`http://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending`).
- **Extraction**: Paper title, summary, authors, and PDF link.
- **AI Focus**: Summarize the abstract into a one-sentence recommendation.

### 3.3 YouTube AI
- **Endpoint**: YouTube RSS or Data API.
- **Targets**: `Andrej Karpathy`, `Two Minute Papers`, `DeepLearning.AI`.
- **Extraction**: Video title, description, and high-res thumbnail.

## 4. Implementation Plan

1. **Phase 1: Refactor**
   - Create `scrapers/engines/base.py` and move `BaseScraper`.
   - Split `platforms.py` into `twitter.py`, `reddit.py`, `ph.py`.
   - Update `run.py` to import from new paths.
   - Verify existing scrapers still work.

2. **Phase 2: Expansion**
   - Implement `github.py`.
   - Implement `arxiv.py`.
   - Implement `youtube.py`.

3. **Phase 3: Final Polish**
   - Ensure all new sources use the Gemini AI scoring and localized "推荐理由".

## 5. Success Criteria
- [ ] No regression in Twitter/Reddit/PH/HN scraping.
- [ ] New sources correctly push data to the backend.
- [ ] All data items include high-quality AI scores and reasons.
- [ ] Frontend displays new items correctly (icons, media).
