-- Migration: Add Knowledge Base and Periodic Reports tables
-- Date: 2026-06-13

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
