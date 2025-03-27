@echo off
echo ==============================
echo Configuracion de ngrok para WhatsApp Bot
echo ==============================

echo Iniciando servicio ngrok...
start cmd /k "ngrok http 5000 --host-header=rewrite"

echo Iniciando otro servicio ngrok para el servidor de WhatsApp Web JS...
start cmd /k "ngrok http 3000 --host-header=rewrite"

echo.
echo Instrucciones:
echo 1. Toma nota de las URLs publicas generadas por ngrok
echo 2. Actualiza la URL de webhook en tu panel de Twilio (si usas Twilio)
echo 3. Actualiza la direccion en tu navegador para acceder al landing page
echo.
echo Para detener ngrok, cierra las ventanas de comandos abiertas
echo ============================== 