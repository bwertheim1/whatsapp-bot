-- Crear tabla de organizadores
CREATE TABLE IF NOT EXISTS organizadores (
    id SERIAL PRIMARY KEY,
    numero TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Crear tabla de eventos
CREATE TABLE IF NOT EXISTS eventos (
    id SERIAL PRIMARY KEY,
    organizador_id INTEGER REFERENCES organizadores(id),
    nombre TEXT NOT NULL,
    descripcion TEXT,
    fecha TIMESTAMP WITH TIME ZONE,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Modificar la tabla de invitados existente para agregar evento_id
ALTER TABLE invitados ADD COLUMN IF NOT EXISTS evento_id INTEGER REFERENCES eventos(id);

-- Crear índices para optimizar búsquedas
CREATE INDEX IF NOT EXISTS idx_organizadores_numero ON organizadores(numero);
CREATE INDEX IF NOT EXISTS idx_eventos_organizador ON eventos(organizador_id);
CREATE INDEX IF NOT EXISTS idx_invitados_evento ON invitados(evento_id);
CREATE INDEX IF NOT EXISTS idx_invitados_numero ON invitados(numero);

-- Configuración de políticas RLS para la tabla organizadores
ALTER TABLE public.organizadores ENABLE ROW LEVEL SECURITY;

-- Política para permitir todas las operaciones (insertar, leer, actualizar, eliminar)
CREATE POLICY "Permitir todas las operaciones para organizadores" 
ON public.organizadores 
FOR ALL 
USING (true)
WITH CHECK (true);

-- Configuración de políticas RLS para la tabla eventos
ALTER TABLE public.eventos ENABLE ROW LEVEL SECURITY;

-- Política para permitir todas las operaciones (insertar, leer, actualizar, eliminar)
CREATE POLICY "Permitir todas las operaciones para eventos" 
ON public.eventos 
FOR ALL 
USING (true)
WITH CHECK (true);

-- Configuración de políticas RLS para la tabla invitados (por si acaso)
ALTER TABLE public.invitados ENABLE ROW LEVEL SECURITY;

-- Política para permitir todas las operaciones (insertar, leer, actualizar, eliminar)
CREATE POLICY "Permitir todas las operaciones para invitados" 
ON public.invitados 
FOR ALL 
USING (true)
WITH CHECK (true); 