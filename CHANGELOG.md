# Changelog

All notable changes to this project will be documented in this file.

## [2026-05-24]

### Added
- **Multi-Style AI Briefings**:
  - Introduced `--style` parameter for AI report generation, supporting `toxic` (sarcastic insider) and `official` (formal strategic) narrative modes.
  - Refactored AI prompt engineering to support 2000+ word deep-dive summaries with distinct structural requirements.
- **Visual Intelligence Engine**:
  - Integrated Playwright-based screenshot engine (`report_engine.py`) to automatically generate PNG infographics from AI insights.
  - Added signal-based rendering synchronization (using `#report-ready` DOM marker) to ensure perfect timing for visual capture.
  - Implemented automated media upload and database linking for generated reports.
- **Enhanced AI Metadata Extraction**:
  - Updated `GeminiEvaluator` to extract `mentioned_users` and `trending_keywords` from content for downstream discovery and search expansion.
  - Added support for latest Gemini 3.1 models and improved automated model fallback logic.
- **CLI Robustness**:
  - Expanded `scrapers/run.py` with granular flags (e.g., `--no-clustering`, `--no-curation`, `--style`) for surgical lifecycle control.
  - Added loop mode with configurable intervals for autonomous perpetual operation.

### Updated
- **Comprehensive Documentation**:
  - Synchronized `README.md`, `DEPLOY.md`, `docs/api.md`, and `docs/scrapers.md` with the latest feature set.
  - Expanded environment variable documentation for visual reporting and AI configuration.

## [2026-05-21]

### Added
- **Cross-Source Resonance (Topic Clustering)**:
  - Implemented semantic topic clustering to aggregate related news from multiple platforms (Twitter, Reddit, GitHub, etc.).
  - Added "Resonance Score" to measure global topic impact.
  - Introduced `ResonanceCard` component for high-level topic overview and platform matrix visualization.
  - Added backend support for `topic_clusters` and many-to-many news mapping.
- **Intelligence Sidebar & Curation**:
  - Implemented professional sidebar with "Inner Circle" (KOL tracking) and "Discovery Radar" for real-time signals.
  - Added soft-delete (blacklist) functionality for targets with a feedback loop to the discovery engine.
- **Mobile UX Enhancement**:
  - Implemented off-canvas sidebar (left drawer) for mobile navigation, replacing the experimental bottom sheet.
  - Refactored platform filter to a space-efficient select dropdown on mobile.
- **Search Capabilities**:
  - Enhanced global search to support searching by author handle (e.g., "@username").
  - Improved backend search compatibility for JSON fields with explicit string casting.

### Fixed
- **Frontend**:
  - Resolved TypeScript errors in `ResonanceCard.vue` related to missing interfaces and `unknown` type inference.
  - Cleaned up unused imports in `Sidebar.vue`.
  - Successfully verified production build with `npm run build`.
- **UI/UX**:
  - Resolved mobile header layout issues and fixed SVG click targets.
  - Fixed button click bubbling and scope issues in various components.
  - Removed duplicated style blocks and dead code in `App.vue`.
- **Backend/Scrapers**:
  - Resolved utils import errors in scraper engines.
  - Fixed JSON search issues by explicitly casting to String for universal compatibility.

## [2026-05-15] - Initial Beta Release

### Added
- Core AI-driven news aggregation from Twitter, GitHub, YouTube, Reddit, and Arxiv.
- AI Intelligence Hub powered by Google Gemini for takeaways and clustering.
- Magazine-style layout for high-density information display.
- Automated source discovery and curation engine.
