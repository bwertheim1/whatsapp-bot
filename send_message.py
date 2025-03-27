from twilio.rest import Client
import pandas as pd
import time
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Twilio credentials
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")

# Configuración de WhatsApp Web JS
USE_WHATSAPP_WEB = os.getenv("USE_WHATSAPP_WEB", "false").lower() == "true"
WHATSAPP_SERVER_URL = f"http://localhost:{os.getenv('WHATSAPP_SERVER_PORT', '3000')}"

# Inicializar cliente según configuración
if not USE_WHATSAPP_WEB:
    client = Client(account_sid, auth_token)
    from_whatsapp_number = os.getenv("TWILIO_PHONE_NUMBER", "whatsapp:+14155238886")
    
    # Si no tiene el formato correcto, añadirlo
    if not from_whatsapp_number.startswith("whatsapp:"):
        from_whatsapp_number = f"whatsapp:{from_whatsapp_number}"

def enviar_invitacion(numero, nombre):
    """Envía un mensaje de invitación personalizado a un número"""
    try:
        mensaje = f"""¡Hola {nombre}! 🎉

Estás cordialmente invitado a nuestra celebración. 

Por favor, confirma tu asistencia respondiendo a este mensaje.
Si vienes acompañado, indícalo en tu respuesta.
Si tienes alguna restricción alimenticia, también háznoslo saber.

¡Esperamos tu respuesta! 🙂"""

        if USE_WHATSAPP_WEB:
            # Usar WhatsApp Web JS
            numero_limpio = numero.replace("whatsapp:+", "").replace("+", "")
            response = requests.post(
                f"{WHATSAPP_SERVER_URL}/send-message",
                json={"number": numero_limpio, "message": mensaje}
            )
            if response.status_code == 200:
                print(f"Mensaje enviado a {nombre} ({numero_limpio}) usando WhatsApp Web JS")
                return True, "Mensaje enviado con WhatsApp Web JS"
            else:
                print(f"Error al enviar mensaje usando WhatsApp Web JS: {response.text}")
                return False, f"Error: {response.text}"
        else:
            # Usar Twilio
            # Asegurarse que el número tenga el formato correcto
            if not numero.startswith("whatsapp:+"):
                numero = f"whatsapp:+{numero}"

            message = client.messages.create(
                body=mensaje,
                from_=from_whatsapp_number,
                to=numero
            )
            
            return True, message.sid
    except Exception as e:
        return False, str(e)

def enviar_invitaciones_masivas(excel_file):
    """Envía invitaciones a todos los números en el Excel que no han respondido"""
    try:
        df = pd.read_excel(excel_file)
        total = 0
        enviados = 0
        errores = []

        for index, row in df.iterrows():
            total += 1
            numero = str(row["Numero"]).strip()
            nombre = str(row["Nombre"]).strip()
            confirmacion = str(row["Confirmacion"]).strip().lower()
            
            # Solo enviar a los que no han respondido
            if confirmacion not in ["sí", "no"]:
                success, result = enviar_invitacion(numero, nombre)
                if success:
                    enviados += 1
                    print(f"✅ Mensaje enviado a {nombre} ({numero})")
                else:
                    errores.append(f"❌ Error al enviar a {nombre} ({numero}): {result}")
                # Esperar 1 segundo entre mensajes para evitar límites de rate
                time.sleep(1)

        reporte = f"""�� Reporte de envío:
- Total procesados: {total}
- Mensajes enviados: {enviados}
- Errores: {len(errores)}"""

        if errores:
            reporte += "\n\nDetalles de errores:"
            for error in errores:
                reporte += f"\n{error}"

        return True, reporte

    except Exception as e:
        return False, f"Error al procesar envío masivo: {str(e)}"

if __name__ == "__main__":
    # Ejemplo de uso directo
    resultado, mensaje = enviar_invitaciones_masivas("invitados.xlsx")
    print(mensaje)
