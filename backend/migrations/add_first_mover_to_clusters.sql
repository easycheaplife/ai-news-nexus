-- Migration: Add First Mover Identification to Topic Clusters
-- Date: 2026-06-13

ALTER TABLE `topic_clusters` 
ADD COLUMN `first_mover_news_id` INT DEFAULT NULL COMMENT '首发资讯ID',
ADD COLUMN `first_mover_tier` VARCHAR(10) DEFAULT NULL COMMENT '首发者等级 (S/A/B)',
ADD CONSTRAINT `fk_first_mover` FOREIGN KEY (`first_mover_news_id`) REFERENCES `news_items`(`id`) ON DELETE SET NULL;
