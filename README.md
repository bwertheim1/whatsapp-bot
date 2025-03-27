# WhatsApp Bot con Supabase

Bot de WhatsApp para gestión de invitaciones con respaldo en Supabase.

## Características

- Envío de invitaciones por WhatsApp usando Twilio
- Gestión de respuestas con NLP a través de OpenAI
- Almacenamiento de datos en Supabase
- Análisis automatizado de respuestas
- Comandos administrativos
- Exportación e importación de datos en Excel

## Requisitos

- Python 3.7+
- Cuenta de Twilio con WhatsApp habilitado
- Cuenta en Supabase
- Cuenta de OpenAI

## Instalación

1. Clonar el repositorio:
```
git clone <url-repositorio>
cd whatsapp-bot
```

2. Instalar dependencias:
```
pip install -r requirements.txt
```

3. Configurar variables de entorno (o editar directamente los archivos):
   - Credenciales de Twilio
   - API Key de OpenAI
   - URL y Key de Supabase

## Configuración de Supabase

1. Crear una cuenta en [Supabase](https://supabase.com/)
2. Crear un nuevo proyecto
3. En el Dashboard de Supabase, ir a SQL Editor y crear una tabla 'invitados' con la siguiente estructura:

```sql
CREATE TABLE invitados (
  id SERIAL PRIMARY KEY,
  nombre TEXT NOT NULL,
  numero TEXT NOT NULL,
  confirmacion TEXT,
  acompanante TEXT,
  restricciones_alimenticias TEXT
);
```

4. En la sección "Project Settings" > "API", obtener la URL y la anon/public key para configurarlas en el archivo `webhook.py`.

## Configuración de Twilio

1. Registrarse en [Twilio](https://www.twilio.com/)
2. Configurar un Sender para WhatsApp
3. Configurar un webhook para la URL de tu servidor donde se ejecutará `webhook.py`
4. Añadir los números de teléfono de prueba en la Sandbox de Twilio

## Uso

1. Iniciar el servidor Flask:
```
python webhook.py
```

2. Para pruebas locales, usar ngrok para exponer el puerto 5000:
```
ngrok http 5000
```

3. Configurar la URL de ngrok en Twilio como webhook para recibir mensajes

## Comandos de Administrador

- **!ayuda**: Muestra la lista de comandos disponibles
- **!enviar**: Inicia el envío de invitaciones
- **!reporte**: Muestra el estado actual de respuestas
- **!excel**: Obtiene el archivo Excel actualizado
- **!supabase**: Administra la base de datos Supabase

## Migración de Excel a Supabase

Si ya tienes datos en Excel, puedes importarlos a Supabase con el comando:

```
!supabase importar
```

Asegúrate de que el Excel tenga el formato correcto con las columnas: Nombre, Numero, Confirmacion, +1, Restricciones alimenticias.

## Arquitectura del Sistema

```
WhatsApp <-> Twilio API <-> Flask Server <-> OpenAI API
                                      <-> Supabase
                                      <-> Excel (importación/exportación)
```

## Contribuciones

Contribuciones son bienvenidas. Por favor, abre un issue o pull request para sugerencias o cambios.

## Licencia

[MIT License](LICENSE) 