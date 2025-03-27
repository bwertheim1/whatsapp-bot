# Creación manual de tablas en Supabase

Para que el sistema de múltiples organizadores funcione correctamente, es necesario crear las siguientes tablas en Supabase. Sigue estos pasos detallados:

## Acceder al Panel de Administración

1. Inicia sesión en [Supabase](https://app.supabase.io/)
2. Selecciona tu proyecto
3. En el menú lateral izquierdo, haz clic en "Table Editor"

## Crear la tabla 'organizadores'

1. Haz clic en el botón "New Table"
2. Ingresa los siguientes datos:
   - **Name**: `organizadores`
   - **Description**: `Almacena información de los organizadores de eventos`
   - **Enable Row Level Security**: Desactivado (por ahora)

3. Define las columnas:
   - `id`: Type: `int8`, Primary: ✓, Default Value: `nextval('organizadores_id_seq'::regclass)`
   - `numero`: Type: `text`, Is Nullable: ✗, Is Unique: ✓
   - `nombre`: Type: `text`, Is Nullable: ✗
   - `fecha_registro`: Type: `timestamp with time zone`, Default Value: `now()`

4. Haz clic en "Save" para crear la tabla

## Crear la tabla 'eventos'

1. Haz clic en el botón "New Table"
2. Ingresa los siguientes datos:
   - **Name**: `eventos`
   - **Description**: `Almacena información de los eventos creados por organizadores`
   - **Enable Row Level Security**: Desactivado (por ahora)

3. Define las columnas:
   - `id`: Type: `int8`, Primary: ✓, Default Value: `nextval('eventos_id_seq'::regclass)`
   - `organizador_id`: Type: `int8`, Is Nullable: ✗
   - `nombre`: Type: `text`, Is Nullable: ✗
   - `descripcion`: Type: `text`, Is Nullable: ✓
   - `fecha`: Type: `timestamp with time zone`, Is Nullable: ✓
   - `fecha_creacion`: Type: `timestamp with time zone`, Default Value: `now()`

4. Haz clic en "Save" para crear la tabla

5. Configura la relación con la tabla 'organizadores':
   - Haz clic en la columna `organizador_id`
   - Selecciona "Foreign Keys" en el menú
   - Selecciona:
     - **Schema**: `public`
     - **Table**: `organizadores`
     - **Column**: `id`
   - Haz clic en "Save"

## Modificar la tabla 'invitados' (si ya existe)

1. Selecciona la tabla 'invitados' en el panel lateral
2. Haz clic en "Edit Table"
3. Añade una nueva columna:
   - `evento_id`: Type: `int8`, Is Nullable: ✓
4. Haz clic en "Save" para actualizar la tabla

5. Configura la relación con la tabla 'eventos':
   - Haz clic en la columna `evento_id`
   - Selecciona "Foreign Keys" en el menú
   - Selecciona:
     - **Schema**: `public`
     - **Table**: `eventos`
     - **Column**: `id`
   - Haz clic en "Save"

## Verificar la configuración

Una vez creadas las tablas, reinicia la aplicación Flask para comprobar que se detectan correctamente.

# Configuración de tablas y políticas de seguridad en Supabase

Vemos que ya tienes creadas las tablas `organizadores`, `eventos` e `invitados` en tu base de datos de Supabase. El problema actual es que las políticas de seguridad RLS (Row Level Security) están impidiendo que la aplicación inserte datos.

## Configurar políticas de seguridad (RLS)

1. Ve al panel de Supabase
2. En el menú lateral, selecciona "Authentication" > "Policies"
3. Para cada una de las tablas (`organizadores`, `eventos` e `invitados`), realiza los siguientes pasos:

   a. Haz clic en la tabla (ej. `organizadores`)
   
   b. En la sección "Row Security", asegúrate de que "Enable RLS" esté activado (ya debe estarlo)
   
   c. Haz clic en el botón "New Policy"
   
   d. Selecciona "Create a policy from scratch"
   
   e. Configura la política:
      - Name: `Permitir todas las operaciones`
      - Target roles: `All`
      - Definition: Selecciona `USING (true)` y `WITH CHECK (true)`
      - Policy applies to: `SELECT`, `INSERT`, `UPDATE`, `DELETE`
   
   f. Haz clic en "Save Policy"

## Alternativa: Usar el SQL Editor

También puedes ejecutar las siguientes sentencias SQL directamente:

1. Ve al menú lateral y selecciona "SQL Editor"

2. Crea un nuevo script y pega el siguiente código:

```sql
-- Configuración de políticas RLS para la tabla organizadores
CREATE POLICY "Permitir todas las operaciones para organizadores" 
ON public.organizadores 
FOR ALL 
USING (true)
WITH CHECK (true);

-- Configuración de políticas RLS para la tabla eventos
CREATE POLICY "Permitir todas las operaciones para eventos" 
ON public.eventos 
FOR ALL 
USING (true)
WITH CHECK (true);

-- Configuración de políticas RLS para la tabla invitados
CREATE POLICY "Permitir todas las operaciones para invitados" 
ON public.invitados 
FOR ALL 
USING (true)
WITH CHECK (true);
```

3. Ejecuta el script haciendo clic en "Run"

## Después de configurar las políticas

Una vez configuradas las políticas, reinicia tu aplicación (`python webhook.py`) y prueba nuevamente:

1. Envía "Hola, soy organizador" desde WhatsApp
2. Luego envía "!crear matrimonio carey y chan"

## Sobre el mensaje "Escanea el código QR con tu WhatsApp para autenticar el sistema"

Este mensaje aparece porque estás usando WhatsApp Web JS como proveedor de mensajería. A diferencia de Twilio, WhatsApp Web JS requiere que escanees un código QR con tu teléfono para vincular la sesión, similar a cuando usas WhatsApp Web en un navegador.

Para usar WhatsApp Web JS:

1. Ejecuta el servidor Node.js: `node whatsapp-server.js`
2. Se mostrará un código QR en la terminal
3. Escanea ese código con tu WhatsApp desde tu teléfono (WhatsApp > Menú > Dispositivos vinculados > Vincular un dispositivo)
4. Una vez vinculado, el servidor estará listo para enviar y recibir mensajes 