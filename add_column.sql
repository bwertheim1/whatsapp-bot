ALTER TABLE eventos ADD COLUMN IF NOT EXISTS estructura_excel JSONB DEFAULT '{}'::jsonb;
