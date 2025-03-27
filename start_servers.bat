@echo off
echo ==============================
echo Iniciando servidores de WhatsApp Bot
echo ==============================

echo Iniciando servidor de WhatsApp Web JS...
start cmd /k "node whatsapp-server.js"

echo Iniciando servidor Flask...
start cmd /k "python webhook.py"

echo.
echo Los servidores se han iniciado:
echo - Servidor Flask: http://localhost:5000
echo - Servidor WhatsApp Web JS: http://localhost:3000
echo.
echo Para exponer los servidores a Internet, ejecuta ngrok_config.bat
echo.
echo Para detener los servidores, cierra las ventanas de comandos abiertas
echo ============================== 