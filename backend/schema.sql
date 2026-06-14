-- AI News Nexus Database Schema
-- Optimized for MySQL 5.7+

CREATE DATABASE IF NOT EXISTS ai_news CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE ai_news;

CREATE TABLE IF NOT EXISTS `news_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `platform` VARCHAR(50) NOT NULL COMMENT '抓取平台: twitter, youtube, reddit, ph, hn',
    `external_id` VARCHAR(768) NOT NULL COMMENT '平台原始ID',
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
    `mentioned_users` JSON COMMENT '内容中提到的高价值用户列表',
    `trending_keywords` JSON COMMENT '内容涉及的技术热词列表',
    
    -- 唯一性约束与索引
    UNIQUE KEY `uk_platform_external` (`platform`, `external_id`), -- 防止同一平台重复抓取
    INDEX `idx_url` (`url`),                                       -- 加速链接搜索
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
    `report_url` VARCHAR(500) COMMENT '生成的日报图片 URL',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uk_date` (`date`),
    INDEX `idx_date` (`date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 发现池表：存储待验证的新账号和热词
CREATE TABLE IF NOT EXISTS `discovery_pool` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `type` ENUM('user', 'keyword') NOT NULL COMMENT '发现类型：账号或关键词',
    `value` VARCHAR(255) NOT NULL COMMENT '账号名(handle)或关键词',
    `status` ENUM('pending', 'vetted', 'rejected') DEFAULT 'pending' COMMENT '状态',
    `source_id` INT COMMENT '发现该信号的原始资讯ID',
    `discovery_reason` TEXT COMMENT 'AI 推荐关注/搜索的理由',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uk_type_value` (`type`, `value`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 采集目标表：存储活跃的抓取账号（如 Twitter handle）
CREATE TABLE IF NOT EXISTS `scraping_targets` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `platform` VARCHAR(50) NOT NULL,
    `handle` VARCHAR(255) NOT NULL,
    `name` VARCHAR(255),
    `description` TEXT,
    `is_active` BOOLEAN DEFAULT TRUE,
    `added_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 质量评价维度 (新增)
    `avg_score` INT DEFAULT 50 COMMENT 'AI 评分均值',
    `total_posts` INT DEFAULT 0 COMMENT '抓取总数',
    `high_value_posts` INT DEFAULT 0 COMMENT '高价值内容(>80分)总数',
    `status` ENUM('active', 'probation', 'deactivated', 'blacklisted') DEFAULT 'active' COMMENT '信源状态',
    `last_scraped_at` DATETIME COMMENT '最后抓取时间',
    `last_high_score_at` DATETIME COMMENT '最后产出高分内容时间',
    `failure_count` INT DEFAULT 0 COMMENT '连续低质/失败计数',
    
    UNIQUE KEY `uk_platform_handle` (`platform`, `handle`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 话题簇表：用于跨源聚合关联资讯
CREATE TABLE IF NOT EXISTS `topic_clusters` (
    `id` VARCHAR(36) PRIMARY KEY COMMENT 'UUID',
    `title` VARCHAR(500) NOT NULL COMMENT '话题标题',
    `summary` TEXT COMMENT '话题综述',
    `resonance_score` INT DEFAULT 0 COMMENT '共振指数',
    `first_mover_news_id` INT COMMENT '首发资讯ID',
    `first_mover_tier` VARCHAR(10) COMMENT '首发者等级 (S/A/B)',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_score` (`resonance_score`),
    CONSTRAINT `fk_first_mover` FOREIGN KEY (`first_mover_news_id`) REFERENCES `news_items`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 话题簇与资讯关联表
CREATE TABLE IF NOT EXISTS `cluster_news_mapping` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `cluster_id` VARCHAR(36) NOT NULL COMMENT '话题ID',
    `news_id` INT NOT NULL COMMENT '资讯ID',
    `platform_role` VARCHAR(50) COMMENT '该资讯在话题中的角色',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uk_cluster_news` (`cluster_id`, `news_id`),
    INDEX `idx_cluster` (`cluster_id`),
    INDEX `idx_news` (`news_id`),
    FOREIGN KEY (`cluster_id`) REFERENCES `topic_clusters`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`news_id`) REFERENCES `news_items`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 百科词条表：存储长线技术名词
CREATE TABLE IF NOT EXISTS `knowledge_terms` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `keyword` VARCHAR(100) NOT NULL UNIQUE COMMENT '技术关键词',
    `category` VARCHAR(50) DEFAULT 'general' COMMENT '类别：模型, 算力, 框架, 应用, 趋势',
    `description` TEXT COMMENT 'AI 生成的专业定义',
    `heat_score` INT DEFAULT 1 COMMENT '热度/共鸣次数累计',
    `trend_json` JSON COMMENT '历史热度序列 (用于绘图)',
    `related_news_ids` JSON COMMENT '最具代表性的关联新闻 ID 列表',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_keyword` (`keyword`),
    INDEX `idx_heat` (`heat_score`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 周期性战略白皮书表
CREATE TABLE IF NOT EXISTS `periodic_reports` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(500) NOT NULL COMMENT '白皮书标题',
    `content` LONGTEXT NOT NULL COMMENT 'Markdown 格式深度综述',
    `start_date` DATE NOT NULL COMMENT '起始日期',
    `end_date` DATE NOT NULL COMMENT '结束日期',
    `stats_json` JSON COMMENT '核心统计指标',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_date_range` (`start_date`, `end_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
