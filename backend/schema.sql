-- AI News Nexus Database Schema
-- Optimized for MySQL 5.7+

CREATE DATABASE IF NOT EXISTS ai_news CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE ai_news;

CREATE TABLE IF NOT EXISTS `news_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `platform` VARCHAR(50) NOT NULL COMMENT '抓取平台: twitter, youtube, reddit, ph, hn',
    `external_id` VARCHAR(255) NOT NULL COMMENT '平台原始ID',
    `title` VARCHAR(500) NOT NULL COMMENT '文章/动态标题',
    `content` LONGTEXT COMMENT '正文内容',
    `url` VARCHAR(768) NOT NULL COMMENT '原始链接',
    `published_at` DATETIME NOT NULL COMMENT '发布时间',
    `scraped_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '系统抓取时间',
    `metadata_json` JSON COMMENT '扩展数据 (存储点赞数、评论数、作者信息等)',
    `score` INT DEFAULT 0 COMMENT 'AI 评分 (0-100)',
    `reason` TEXT COMMENT 'AI 推荐理由',
    `media_urls` JSON COMMENT '多媒体链接列表 (图片、视频)',
    `takeaways` JSON COMMENT 'AI 提炼的核心要点 (列表)',
    `cluster_id` VARCHAR(100) COMMENT '聚合簇ID，用于关联相似资讯',
    
    -- 唯一性约束与索引
    UNIQUE KEY `uk_platform_external` (`platform`, `external_id`), -- 防止同一平台重复抓取
    UNIQUE KEY `uk_url` (`url`),                                   -- 确保链接全局唯一
    INDEX `idx_platform` (`platform`),                             -- 加速按平台筛选
    INDEX `idx_published` (`published_at`),                         -- 加速按时间排序和范围搜索
    FULLTEXT INDEX `idx_search` (`title`, `content`)               -- 支持全文检索关键字
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 每日 AI 深度洞察表
CREATE TABLE IF NOT EXISTS `daily_insights` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `date` DATE NOT NULL COMMENT '简报日期',
    `content` LONGTEXT NOT NULL COMMENT 'AI 生成的 Markdown 简报内容',
    `hot_topics` JSON COMMENT '当日热门关键词/聚类列表',
    `stats_json` JSON COMMENT '各平台资讯量统计',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uk_date` (`date`),
    INDEX `idx_date` (`date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
