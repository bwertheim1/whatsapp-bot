# Instrucciones para WhatsApp Web JS

Este proyecto ahora soporta dos formas de enviar mensajes de WhatsApp:
1. Twilio (método original)
2. WhatsApp Web JS (método directo)

## Ventajas de usar WhatsApp Web JS

- **Envío directo de archivos**: Puedes enviar el Excel directamente como adjunto sin necesidad de subirlo a almacenamiento externo
- **Sin costos adicionales**: No requiere pagar por los mensajes de Twilio
- **Mayor funcionalidad**: Acceso a más funcionalidades de WhatsApp

## Requisitos previos

- Node.js y npm instalados
- Python 3.7 o superior instalado
- Acceso a una cuenta de WhatsApp

## Configuración

1. **Instalar dependencias de Python**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Instalar dependencias de Node.js**:
   ```bash
   npm install
   ```

3. **Configurar .env**:
   Asegúrate de que tu archivo `.env` tenga configuradas las siguientes variables:
   ```
   USE_WHATSAPP_WEB=true
   WHATSAPP_SERVER_PORT=3000
   ADMIN_NUMBER=56XXXXXXXXX  # Sin "+" delante
   EXCEL_FILE=invitados.xlsx
   ```

## Ejecución

1. **Iniciar el servidor de WhatsApp Web JS**:
   ```bash
   node whatsapp-server.js
   ```
   La primera vez, se generará un código QR en la terminal. Escanea este código con tu aplicación de WhatsApp en el teléfono para vincular tu cuenta.

2. **Iniciar el servidor de Flask**:
   ```bash
   python webhook.py
   ```

3. **Verificar conexión**:
   Una vez que ambos servidores estén ejecutándose y WhatsApp Web JS esté conectado, verás un mensaje en la consola del servidor Node.js: "Cliente de WhatsApp Web JS listo y conectado!"

## Uso

1. **Enviar mensajes de prueba**:
   - Envía "Hola" desde tu WhatsApp al número vinculado para recibir un mensaje de bienvenida
   - Usa el comando `!excel` para recibir el Excel actualizado
   - Sube un archivo Excel y será procesado automáticamente

2. **Envío de archivos Excel**:
   Ahora, cuando el sistema necesite enviarte un archivo Excel, lo recibirás directamente como adjunto en WhatsApp, sin necesidad de abrir enlaces externos.

## Solución de problemas

- **Código QR no se escanea**: Asegúrate de escanear el código QR con la opción "WhatsApp Web" o "Dispositivos vinculados" de tu aplicación de WhatsApp
- **Problemas de conexión**: Reinicia ambos servidores y asegúrate de que los puertos no estén bloqueados
- **Sesión expirada**: Si la sesión expira, el servidor de WhatsApp Web JS generará un nuevo código QR para escanear

## Volver a Twilio

Si deseas volver a utilizar Twilio en lugar de WhatsApp Web JS, simplemente cambia `USE_WHATSAPP_WEB=false` en tu archivo `.env` y reinicia el servidor de Flask.

## Limitaciones

- La sesión de WhatsApp Web JS necesita ser revalidada periódicamente
- Solo puedes tener una sesión de WhatsApp Web activa a la vez (WhatsApp limita a 4 dispositivos concurrentes)
- WhatsApp puede detectar y bloquear el uso automatizado si se envían demasiados mensajes en poco tiempo 