ALTER TABLE invitados ADD COLUMN IF NOT EXISTS respuestas_adicionales JSONB DEFAULT '{}'::jsonb;
