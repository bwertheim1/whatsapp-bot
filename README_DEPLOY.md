# Guía para desplegar la aplicación con ngrok

## Introducción

Esta guía te mostrará cómo exponer tu aplicación local de WhatsApp Bot a Internet usando ngrok, lo que permitirá que tus amigos prueben el servicio sin necesidad de instalar nada en sus dispositivos.

## Requisitos previos

- Node.js y npm instalados
- Python 3.7 o superior instalado
- ngrok instalado globalmente (`npm install -g ngrok`)
- Configuración completa del proyecto WhatsApp Bot

## Pasos para desplegar

### 1. Iniciar los servidores

Puedes iniciar todos los servidores necesarios ejecutando el archivo batch incluido:

```
start_servers.bat
```

Esto iniciará:
- Servidor Node.js para WhatsApp Web JS (puerto 3000)
- Servidor Flask para el backend (puerto 5000)

### 2. Exponer los servidores con ngrok

Una vez que los servidores estén funcionando, puedes exponerlos a Internet ejecutando:

```
ngrok_config.bat
```

Esto abrirá dos ventanas de ngrok:
- Una para el servidor Flask (puerto 5000)
- Otra para el servidor WhatsApp Web JS (puerto 3000)

### 3. Obtener las URLs públicas

Después de ejecutar ngrok, obtendrás dos URLs públicas (ejemplo: `https://a1b2c3d4.ngrok.io`):

- URL para el servidor Flask: Esta es la dirección que tus amigos usarán para acceder al landing page
- URL para el servidor WhatsApp Web JS: Esta es la dirección que se usará para la comunicación interna

### 4. Compartir la URL con tus amigos

Comparte la URL del servidor Flask con tus amigos. Ellos podrán acceder al landing page y probar la aplicación directamente desde sus navegadores.

## Consideraciones importantes

1. **Sesiones de ngrok**: Las URLs gratuitas de ngrok cambian cada vez que reinicias el servicio. Si tienes una cuenta de ngrok, puedes obtener URLs persistentes.

2. **Configuración de Twilio**: Si estás usando Twilio, necesitarás actualizar la URL del webhook en tu panel de Twilio cada vez que cambies la URL de ngrok.

3. **Autenticación de WhatsApp Web JS**: Necesitarás escanear el código QR para autenticar la sesión de WhatsApp Web JS cada vez que inicies el servidor.

4. **Tiempo límite de ngrok**: La versión gratuita de ngrok tiene límites de tiempo y conexiones. Para un uso prolongado, considera obtener una cuenta premium.

## Solución de problemas

- **Error de conexión**: Asegúrate de que los servidores estén funcionando correctamente antes de iniciar ngrok.
- **Código QR no escaneable**: Si el código QR no se puede escanear, reinicia el servidor WhatsApp Web JS.
- **ngrok se desconecta**: ngrok gratuito tiene limitaciones de tiempo. Reinicia el servicio si se desconecta.

## Despliegue permanente

Para un despliegue más permanente, considera:
- Usar un VPS o servicio en la nube (AWS, Google Cloud, etc.)
- Configurar un servidor web como Nginx o Apache
- Usar un dominio propio
- Configurar certificados SSL para conexiones seguras 