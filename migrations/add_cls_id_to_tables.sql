-- Migration: Add cls_id (classification_id) column to tasks/todos/followups tables
-- This links created items to their source classifications from ms4-classification service.
--
-- Note: This file is intended to be re-runnable. The migration runner should ignore
-- "duplicate column" / "duplicate key name" errors when re-applying.

ALTER TABLE tasks
ADD COLUMN cls_id VARCHAR(36) NULL COMMENT 'Classification ID from ms4-classification service (UUID)';

ALTER TABLE tasks
ADD INDEX idx_cls_id (cls_id);

ALTER TABLE todos
ADD COLUMN cls_id VARCHAR(36) NULL COMMENT 'Classification ID from ms4-classification service (UUID)';

ALTER TABLE todos
ADD INDEX idx_cls_id (cls_id);

ALTER TABLE followups
ADD COLUMN cls_id VARCHAR(36) NULL COMMENT 'Classification ID from ms4-classification service (UUID)';

ALTER TABLE followups
ADD INDEX idx_cls_id (cls_id);

