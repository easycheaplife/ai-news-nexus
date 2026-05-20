-- Migration script to add performance metrics to scraping_targets
USE ai_news;

ALTER TABLE `scraping_targets`
ADD COLUMN `avg_score` INT DEFAULT 50 COMMENT 'AI 评分均值',
ADD COLUMN `total_posts` INT DEFAULT 0 COMMENT '抓取总数',
ADD COLUMN `high_value_posts` INT DEFAULT 0 COMMENT '高价值内容(>80分)总数',
ADD COLUMN `status` ENUM('active', 'probation', 'deactivated', 'blacklisted') DEFAULT 'active' COMMENT '信源状态',
ADD COLUMN `last_scraped_at` DATETIME COMMENT '最后抓取时间',
ADD COLUMN `last_high_score_at` DATETIME COMMENT '最后产出高分内容时间',
ADD COLUMN `failure_count` INT DEFAULT 0 COMMENT '连续低质/失败计数';

-- Initialize metrics for existing targets
UPDATE `scraping_targets` SET `status` = 'active' WHERE `is_active` = TRUE;
UPDATE `scraping_targets` SET `status` = 'deactivated' WHERE `is_active` = FALSE;
