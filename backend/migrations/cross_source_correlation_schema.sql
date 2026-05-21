-- Migration for Cross-Source Correlation (Phase 1)
-- Adds topic_clusters and cluster_news_mapping tables

-- 话题簇表：用于跨源聚合关联资讯
CREATE TABLE IF NOT EXISTS `topic_clusters` (
    `id` VARCHAR(36) PRIMARY KEY COMMENT 'UUID',
    `title` VARCHAR(500) NOT NULL COMMENT '话题标题',
    `summary` TEXT COMMENT '话题综述',
    `resonance_score` INT DEFAULT 0 COMMENT '共振指数',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_score` (`resonance_score`)
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
