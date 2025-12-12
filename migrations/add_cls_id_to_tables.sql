-- Migration: Add cls_id (classification_id) column to tasks and followups tables
-- This links tasks and followups to their source classifications from ms4-classification service

ALTER TABLE tasks 
ADD COLUMN cls_id VARCHAR(36) NULL COMMENT 'Classification ID from ms4-classification service (UUID)',
ADD INDEX idx_cls_id (cls_id);

ALTER TABLE followups 
ADD COLUMN cls_id VARCHAR(36) NULL COMMENT 'Classification ID from ms4-classification service (UUID)',
ADD INDEX idx_cls_id (cls_id);

