from flask import Flask, request, jsonify, render_template, send_from_directory
from openai import OpenAI
import pandas as pd
import json
import os
from datetime import datetime
import requests
from send_message import enviar_invitaciones_masivas
from twilio.rest import Client
from supabase import create_client
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
EXCEL_FILE = os.getenv("EXCEL_FILE", "invitados.xlsx")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_NUMBER = os.getenv("ADMIN_NUMBER")  # Sin el "+" para que coincida con el formato que recibimos

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

# Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Configuración de WhatsApp Web JS
USE_WHATSAPP_WEB = os.getenv("USE_WHATSAPP_WEB", "false").lower() == "true"
WHATSAPP_SERVER_URL = f"http://localhost:{os.getenv('WHATSAPP_SERVER_PORT', '3000')}"

# Configurar OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Estructura para almacenar sesiones activas de organizadores
# {numero_telefono: {evento_activo_id: id, context: {...}}}
sesiones_organizadores = {}

# Diccionario para almacenar los códigos de verificación
codigos_verificacion = {}

# Inicialización de la base de datos
def inicializar_base_de_datos():
    """Verifica y crea las tablas necesarias en Supabase"""
    print("Inicializando aplicación...")
    try:
        supabase = init_supabase()
        if not supabase:
            print("No se pudo conectar a Supabase. Compruebe las credenciales.")
            return False

        # Función para verificar si una tabla existe
        def verificar_tabla(nombre_tabla):
            try:
                response = supabase.table(nombre_tabla).select('*').limit(1).execute()
                print(f"Tabla '{nombre_tabla}' ya existe en Supabase")
                return True
            except Exception as e:
                error_message = str(e)
                print(f"La tabla '{nombre_tabla}' no existe o hay un error: {error_message}")
                
                # Intentar crear la tabla si no existe
                if "relation" in error_message and "does not exist" in error_message:
                    try:
                        if nombre_tabla == 'organizadores':
                            # Crear tabla organizadores
                            query = """
                            CREATE TABLE IF NOT EXISTS public.organizadores (
                                id SERIAL PRIMARY KEY,
                                numero TEXT UNIQUE NOT NULL,
                                nombre TEXT,
                                fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                            );
                            """
                            supabase.table('_dummy').select('*').limit(1).execute()
                            return False
                        elif nombre_tabla == 'eventos':
                            # Crear tabla eventos
                            query = """
                            CREATE TABLE IF NOT EXISTS public.eventos (
                                id SERIAL PRIMARY KEY,
                                organizador_id INTEGER REFERENCES public.organizadores(id),
                                nombre TEXT,
                                descripcion TEXT,
                                fecha TIMESTAMP WITH TIME ZONE,
                                fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                            );
                            """
                            supabase.table('_dummy').select('*').limit(1).execute()
                            return False
                    except Exception as create_error:
                        print(f"Error al intentar crear la tabla '{nombre_tabla}': {str(create_error)}")
                return False

        # Verificar todas las tablas necesarias
        invitados_existe = verificar_tabla('invitados')
        organizadores_existe = verificar_tabla('organizadores')
        eventos_existe = verificar_tabla('eventos')
        
        if not organizadores_existe or not eventos_existe:
            print("⚠️ Se recomienda crear las siguientes tablas manualmente en el panel de Supabase:")
            if not organizadores_existe:
                print("Tabla 'organizadores':")
                print("- id (int, primary key, auto-increment)")
                print("- numero (text, unique)")
                print("- nombre (text)")
                print("- fecha_registro (timestamp with time zone, default: now())")
            
            if not eventos_existe:
                print("Tabla 'eventos':")
                print("- id (int, primary key, auto-increment)")
                print("- organizador_id (int, foreign key -> organizadores.id)")
                print("- nombre (text)")
                print("- descripcion (text)")
                print("- fecha (timestamp with time zone)")
                print("- fecha_creacion (timestamp with time zone, default: now())")

        return True
    except Exception as e:
        print(f"Error al inicializar base de datos: {str(e)}")
        return False

# Clase Adaptador para mensajería
class WhatsAppAdapter:
    def __init__(self):
        self.use_whatsapp_web = USE_WHATSAPP_WEB
        if not self.use_whatsapp_web:
            self.twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
    def send_message(self, number, message):
        """Envía un mensaje de texto a un número de WhatsApp"""
        try:
            if self.use_whatsapp_web:
                # Limpiar número para WhatsApp Web JS (solo dígitos)
                clean_number = number.replace("whatsapp:+", "").replace("+", "")
                
                # Usar WhatsApp Web JS
                response = requests.post(
                    f"{WHATSAPP_SERVER_URL}/send-message",
                    json={"number": clean_number, "message": message}
                )
                if response.status_code == 200:
                    print(f"Mensaje enviado a {clean_number} usando WhatsApp Web JS")
                    return True
                else:
                    print(f"Error al enviar mensaje usando WhatsApp Web JS: {response.text}")
                    return False
            else:
                # Usar Twilio
                message = self.twilio_client.messages.create(
                    body=message,
                    from_=f"whatsapp:+14155238886",
                    to=f"whatsapp:+{number}"
                )
                print(f"Mensaje enviado a {number} usando Twilio")
                return True
        except Exception as e:
            print(f"Error al enviar mensaje: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
    
    def send_file(self, number, file_path, caption=None):
        """Envía un archivo a un número de WhatsApp"""
        try:
            if self.use_whatsapp_web:
                # Limpiar número para WhatsApp Web JS (solo dígitos)
                clean_number = number.replace("whatsapp:+", "").replace("+", "")
                
                # Usar WhatsApp Web JS
                response = requests.post(
                    f"{WHATSAPP_SERVER_URL}/send-file",
                    json={"number": clean_number, "filePath": file_path, "caption": caption or ""}
                )
                if response.status_code == 200:
                    print(f"Archivo enviado a {clean_number} usando WhatsApp Web JS")
                    return True
                else:
                    print(f"Error al enviar archivo usando WhatsApp Web JS: {response.text}")
                    return False
            else:
                # Usar Twilio (requiere URL pública)
                # Para Twilio, deberíamos tener una URL pública al archivo
                print(f"Para Twilio, se requiere una URL pública para enviar archivos.")
                return False
        except Exception as e:
            print(f"Error al enviar archivo: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False

# Inicializar el adaptador de WhatsApp
whatsapp = WhatsAppAdapter()

# Configurar OpenAI y Twilio
client = OpenAI(api_key=OPENAI_API_KEY)
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Inicializar cliente de Supabase
def init_supabase():
    """Inicializa y devuelve el cliente de Supabase"""
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        return supabase
    except Exception as e:
        print(f"Error al inicializar Supabase: {str(e)}")
        return None

# Funciones para gestionar invitados con Supabase
def obtener_invitados_supabase():
    """Obtiene todos los invitados de Supabase"""
    try:
        supabase = init_supabase()
        if not supabase:
            return False, "No se pudo conectar a Supabase"
        
        response = supabase.table('invitados').select('*').execute()
        return True, response.data
    except Exception as e:
        return False, f"Error al obtener invitados: {str(e)}"

def obtener_invitado_por_numero_supabase(numero):
    """Busca un invitado por su número de teléfono"""
    try:
        supabase = init_supabase()
        if not supabase:
            return False, "No se pudo conectar a Supabase"
        
        response = supabase.table('invitados').select('*').eq('numero', numero).execute()
        if len(response.data) == 0:
            return False, "Invitado no encontrado"
        
        return True, response.data[0]
    except Exception as e:
        return False, f"Error al buscar invitado: {str(e)}"

def actualizar_respuesta_supabase(numero, confirmacion=None, acompanante=None, restricciones=None):
    """Actualiza la respuesta de un invitado en Supabase"""
    try:
        supabase = init_supabase()
        if not supabase:
            return False, "No se pudo conectar a Supabase"
        
        # Obtener el ID del invitado
        success, data = obtener_invitado_por_numero_supabase(numero)
        if not success:
            return False, data
        
        invitado_id = data['id']
        update_data = {}
        
        # Actualizar solo los campos proporcionados
        if confirmacion is not None:
            update_data['confirmacion'] = confirmacion
        if acompanante is not None:
            update_data['acompanante'] = acompanante
        if restricciones is not None:
            update_data['restricciones_alimenticias'] = restricciones
        
        # Si no hay datos para actualizar, salir
        if not update_data:
            return True, "No hay cambios para actualizar"
        
        # Actualizar en Supabase
        response = supabase.table('invitados').update(update_data).eq('id', invitado_id).execute()
        return True, "Respuesta actualizada correctamente"
    except Exception as e:
        return False, f"Error al actualizar respuesta: {str(e)}"

def verificar_todas_respuestas_supabase():
    """Verifica si todos los invitados han respondido usando Supabase"""
    try:
        supabase = init_supabase()
        if not supabase:
            return False, 0, 0
        
        # Obtener todos los invitados
        response = supabase.table('invitados').select('*').execute()
        invitados = response.data
        
        total = len(invitados)
        respondidos = 0
        
        # Contar respondidos
        for invitado in invitados:
            if invitado.get('confirmacion') in ['Sí', 'No', 'sí', 'no']:
                respondidos += 1
        
        return respondidos == total, respondidos, total
    except Exception as e:
        print(f"Error al verificar respuestas: {str(e)}")
        return False, 0, 0

def importar_excel_a_supabase(file_path):
    """Importa datos de Excel a Supabase"""
    try:
        # Leer Excel
        df = pd.read_excel(file_path)
        
        # Limpiar nombres de columnas
        df.columns = df.columns.str.strip()
        
        # Inicializar Supabase
        supabase = init_supabase()
        if not supabase:
            return False, "No se pudo conectar a Supabase"
        
        # Verificar columnas requeridas
        required_columns = ["Nombre", "Numero"]
        current_columns = [col.strip() for col in df.columns]
        required_columns_clean = [col.strip() for col in required_columns]
        
        if not all(col in current_columns for col in required_columns_clean):
            missing_cols = [col for col in required_columns_clean if col not in current_columns]
            return False, f"El Excel debe contener las columnas obligatorias: {', '.join(missing_cols)}"
            
        # Convertir DataFrame a lista de diccionarios con manejo adecuado de valores nulos
        invitados_formateados = []
        
        for _, row in df.iterrows():
            # Crear diccionario con valores convertidos a string o vacíos si son nulos
            invitado_formateado = {
                'nombre': str(row.get('Nombre', '')) if not pd.isna(row.get('Nombre', '')) else '',
                'numero': str(row.get('Numero', '')) if not pd.isna(row.get('Numero', '')) else '',
                'confirmacion': str(row.get('Confirmacion', '')) if not pd.isna(row.get('Confirmacion', '')) else '',
                'acompanante': str(row.get('+1', '')) if not pd.isna(row.get('+1', '')) else '',
                'restricciones_alimenticias': str(row.get('Restricciones alimenticias', '')) if not pd.isna(row.get('Restricciones alimenticias', '')) else ''
            }
            
            # Validar que el número no esté vacío
            if invitado_formateado['nombre'] and invitado_formateado['numero']:
                invitados_formateados.append(invitado_formateado)
        
        if not invitados_formateados:
            return False, "No se encontraron datos válidos para importar"
            
        # Eliminar datos existentes (opcional)
        supabase.table('invitados').delete().neq('id', 0).execute()
        
        # Insertar nuevos datos
        response = supabase.table('invitados').insert(invitados_formateados).execute()
        
        print(f"DEBUG: Datos importados a Supabase: {len(invitados_formateados)} invitados")
        return True, f"Excel importado con éxito. {len(invitados_formateados)} invitados registrados en Supabase."
    except Exception as e:
        print(f"ERROR detallado en importar_excel_a_supabase: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False, f"Error al importar Excel a Supabase: {str(e)}"

def exportar_supabase_a_excel():
    """Exporta datos de Supabase a Excel"""
    try:
        # Obtener datos de Supabase
        success, invitados = obtener_invitados_supabase()
        if not success:
            return False, invitados
        
        # Convertir a DataFrame
        df = pd.DataFrame(invitados)
        
        # Renombrar columnas para formato Excel
        df = df.rename(columns={
            'nombre': 'Nombre',
            'numero': 'Numero',
            'confirmacion': 'Confirmacion',
            'acompanante': '+1',
            'restricciones_alimenticias': 'Restricciones alimenticias'
        })
        
        # Seleccionar columnas relevantes
        columns = ['Nombre', 'Numero', 'Confirmacion', '+1', 'Restricciones alimenticias']
        df = df[columns]
        
        # Guardar Excel
        df.to_excel(EXCEL_FILE, index=False)
        
        return True, f"Datos exportados con éxito a {EXCEL_FILE}"
    except Exception as e:
        return False, f"Error al exportar a Excel: {str(e)}"

def obtener_reporte_supabase():
    """Generar reporte de respuestas desde Supabase"""
    try:
        # Obtener datos de Supabase
        success, invitados = obtener_invitados_supabase()
        if not success:
            return f"Error al generar reporte: {invitados}"
        
        total = len(invitados)
        confirmados = len([i for i in invitados if i.get('confirmacion', '').lower() == 'sí'])
        rechazados = len([i for i in invitados if i.get('confirmacion', '').lower() == 'no'])
        pendientes = total - confirmados - rechazados
        
        return f"""📊 Reporte de invitados:
- Total: {total}
- Confirmados: {confirmados}
- Rechazados: {rechazados}
- Pendientes: {pendientes}"""
    except Exception as e:
        return f"Error al generar reporte: {str(e)}"

# Historial de conversaciones para el administrador
admin_conversation_history = [
    {"role": "system", "content": """Eres un asistente inteligente para gestionar invitaciones a través de WhatsApp. 
Tu trabajo es ayudar al administrador a utilizar el sistema de gestión de invitaciones.

Información importante:
1. El administrador puede subir un archivo Excel con la lista de invitados
2. Puede usar comandos como !ayuda, !enviar, !reporte
3. El sistema procesa automáticamente respuestas de los invitados usando GPT

Responde de manera concisa y amigable. Si el usuario es nuevo, explícale brevemente cómo funciona el sistema.
"""}
]

def backup_excel():
    """Crear una copia de respaldo del Excel"""
    if os.path.exists(EXCEL_FILE):
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{EXCEL_FILE}"
        os.rename(EXCEL_FILE, backup_name)
        return True
    return False

def process_excel(file_path):
    """Procesar nuevo archivo Excel"""
    try:
        df = pd.read_excel(file_path)
        required_columns = ["Nombre", "Numero", "Confirmacion", "+1", "Restricciones alimenticias"]
        
        # Limpiar nombres de columnas
        df.columns = df.columns.str.strip()
        
        # Verificar columnas requeridas (ignorando espacios)
        current_columns = [col.strip() for col in df.columns]
        required_columns_clean = [col.strip() for col in required_columns]
        
        if not all(col in current_columns for col in required_columns_clean):
            missing_cols = [col for col in required_columns_clean if col not in current_columns]
            return False, f"El Excel debe contener las columnas: {', '.join(missing_cols)}"
        
        # Limpiar y preparar datos
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].fillna("").astype(str).str.strip()
        
        # Limpiar números de teléfono (eliminar espacios y asegurarse que no haya "+" duplicados)
        df["Numero"] = df["Numero"].apply(lambda x: x.strip().replace("++", "+") if isinstance(x, str) else x)
        
        # Guardar Excel procesado
        df.to_excel(EXCEL_FILE, index=False)
        return True, f"Excel procesado con éxito. {len(df)} invitados registrados."
    except Exception as e:
        return False, f"Error al procesar Excel: {str(e)}"

def get_report():
    """Generar reporte de respuestas"""
    try:
        df = pd.read_excel(EXCEL_FILE)
        total = len(df)
        confirmados = len(df[df["Confirmacion"].str.lower() == "sí"])
        rechazados = len(df[df["Confirmacion"].str.lower() == "no"])
        pendientes = total - confirmados - rechazados
        
        return f"""📊 Reporte de invitados:
- Total: {total}
- Confirmados: {confirmados}
- Rechazados: {rechazados}
- Pendientes: {pendientes}"""
    except Exception as e:
        return f"Error al generar reporte: {str(e)}"

def analizar_respuesta(mensaje):
    """Usa GPT para analizar el mensaje y extraer la información relevante"""
    prompt = f"""Analiza este mensaje de respuesta a una invitación y extrae la información solicitada.
Contexto: Es una respuesta a un mensaje que pregunta sobre:
1. Confirmación de asistencia
2. Si llevará acompañante
3. Restricciones alimenticias

Mensaje a analizar: "{mensaje}"

Reglas de interpretación:
- Si menciona que va con alguien (esposa, pareja, amigo, etc.), implica que confirma asistencia Y que lleva acompañante
- Si dice que va solo/sola, implica que confirma asistencia pero NO lleva acompañante
- Cualquier mención a dieta especial o alergias debe registrarse como restricción
- Si no menciona restricciones, usar null

Responde SOLO con este JSON exacto:
{{
    "confirmacion": "sí/no",
    "acompanante": "sí/no",
    "restricciones": "texto de la restricción o null si no hay"
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asistente experto en interpretar respuestas a invitaciones."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        resultado = json.loads(response.choices[0].message.content)
        print(f"DEBUG - Análisis del mensaje: '{mensaje}'")
        print(f"DEBUG - Interpretación: {resultado}")
        return resultado
    except Exception as e:
        print(f"Error al analizar con GPT: {str(e)}")
        return None

def chat_con_gpt(mensaje, conversation_history):
    """Función para mantener una conversación con GPT"""
    print(f"Iniciando chat con GPT. Mensaje: '{mensaje}'")
    
    # Agregar el mensaje del usuario al historial
    conversation_history.append({"role": "user", "content": mensaje})
    
    try:
        # Limitar el historial para evitar tokens excesivos (últimos 10 mensajes)
        limited_history = conversation_history[-10:]
        print(f"Historia de conversación (últimos {len(limited_history)} mensajes)")
        
        # Realizar la llamada a GPT
        print("Llamando a la API de OpenAI...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=limited_history,
            temperature=0.7,
            max_tokens=500
        )
        
        # Obtener la respuesta
        respuesta = response.choices[0].message.content
        print(f"Respuesta recibida de GPT: '{respuesta}'")
        
        # Agregar la respuesta al historial
        conversation_history.append({"role": "assistant", "content": respuesta})
        
        return respuesta
    except Exception as e:
        error_message = f"Error en chat con GPT: {str(e)}"
        print(error_message)
        # Imprimir información de depuración adicional
        import traceback
        print(traceback.format_exc())
        return f"Lo siento, tuve un problema para procesar tu mensaje: {str(e)}"

def download_file(url):
    """Descarga un archivo desde una URL de Twilio"""
    try:
        # Usar autenticación básica con las credenciales de Twilio
        response = requests.get(url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
        response.raise_for_status()
        
        # Guardar temporalmente
        temp_file = "temp_download.xlsx"
        with open(temp_file, "wb") as f:
            f.write(response.content)
        return True, temp_file
    except Exception as e:
        return False, str(e)

def verificar_todas_respuestas():
    """Verifica si todos los invitados han respondido y devuelve un resumen"""
    try:
        # Consultar datos de Supabase
        success, invitados = obtener_invitados_supabase()
        if not success:
            print(f"Error al obtener invitados de Supabase: {invitados}")
            return False, 0, 0, []
            
        total_invitados = len(invitados)
        # Cambiar 'respuesta' por 'confirmacion'
        respondieron = [i for i in invitados if i.get('confirmacion') is not None 
                        and i.get('confirmacion').strip() != '']
        num_respuestas = len(respondieron)
        
        # Cambiar 'respuesta' por 'confirmacion'
        faltantes = [i['nombre'] for i in invitados if i.get('confirmacion') is None 
                    or i.get('confirmacion').strip() == '']
        
        todas_respondieron = (num_respuestas == total_invitados)
        
        return todas_respondieron, num_respuestas, total_invitados, faltantes
    except Exception as e:
        print(f"Error al verificar respuestas: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False, 0, 0, []

def enviar_excel_por_whatsapp(numero):
    """Envía el archivo Excel al organizador por WhatsApp"""
    try:
        # Primero asegurarse que el archivo exista
        if not os.path.exists(EXCEL_FILE):
            whatsapp.send_message(numero, "❌ No se encontró el archivo Excel para enviar")
            return False
            
        # Exportar datos actualizados de Supabase a Excel
        success, result = exportar_supabase_a_excel()
        if not success:
            whatsapp.send_message(numero, f"❌ Error al preparar Excel: {result}")
            return False
            
        # Enviar el archivo directamente por WhatsApp Web JS
        if USE_WHATSAPP_WEB:
            file_path = os.path.abspath(EXCEL_FILE)
            caption = "📊 Aquí está el archivo Excel actualizado con todas las respuestas."
            result = whatsapp.send_file(numero, file_path, caption)
            if result:
                print(f"Excel enviado directamente al organizador ({numero})")
                return True
            else:
                whatsapp.send_message(numero, "❌ Error al enviar el archivo Excel. Por favor contacta al desarrollador.")
                return False
        else:
            # Si usamos Twilio, intentar con Supabase Storage
            # Subir archivo a Supabase Storage
            try:
                # Inicializar Supabase
                supabase = init_supabase()
                if not supabase:
                    raise Exception("No se pudo conectar a Supabase")
                    
                # Generar nombre único para el archivo
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"invitados_{timestamp}.xlsx"
                
                # Subir archivo a Supabase Storage
                with open(EXCEL_FILE, 'rb') as f:
                    file_data = f.read()
                    
                bucket_name = "whatsapp-excel-files"  # El nombre del bucket que creaste
                storage_path = f"{filename}"
                
                # Subir el archivo
                response = supabase.storage.from_(bucket_name).upload(
                    storage_path,
                    file_data,
                    {"content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
                )
                
                # Generar URL pública
                public_url = supabase.storage.from_(bucket_name).get_public_url(storage_path)
                
                # Enviar mensaje con el enlace al archivo
                whatsapp.send_message(
                    numero, 
                    f"📊 Aquí está el archivo Excel actualizado con todas las respuestas: {public_url}"
                )
                print(f"Excel compartido a través de Supabase Storage con el organizador ({numero})")
                return True
                
            except Exception as e:
                print(f"Error al subir archivo a Supabase Storage: {str(e)}")
                import traceback
                print(traceback.format_exc())
                
                # Si falla el envío como adjunto, enviar mensaje alternativo
                whatsapp.send_message(
                    numero,
                    f"📊 El archivo Excel ha sido actualizado y guardado como '{EXCEL_FILE}' en el servidor."
                )
                print(f"Notificación de Excel enviada al organizador ({numero})")
                return True
            
    except Exception as e:
        print(f"Error al enviar Excel por WhatsApp: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        # Informar al organizador sobre el error
        try:
            whatsapp.send_message(numero, f"❌ Error al enviar Excel: {str(e)}")
        except:
            pass
        return False

def subir_archivo_drive(file_path):
    """Sube un archivo a Google Drive y devuelve la URL compartible
    
    Requiere tener configurado el acceso a Google Drive API.
    """
    # 1. Importar dependencias de Google Drive
    try:
        from pydrive.auth import GoogleAuth
        from pydrive.drive import GoogleDrive
        import os
        
        # Obtener ID de carpeta desde variables de entorno
        folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        if not folder_id:
            print("Error: No se encontró GOOGLE_DRIVE_FOLDER_ID en las variables de entorno")
            return None
        
        # 2. Autenticar con Google Drive
        gauth = GoogleAuth()
        # Intentar cargar las credenciales guardadas
        gauth.LoadCredentialsFile("credentials.json")
        if gauth.credentials is None:
            # Si no hay credenciales, usar LocalWebserverAuth
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            # Si las credenciales expiraron, refrescarlas
            gauth.Refresh()
        else:
            # Inicializar con credenciales existentes
            gauth.Authorize()
        # Guardar credenciales actualizadas
        gauth.SaveCredentialsFile("credentials.json")
        
        # 3. Crear instancia de GoogleDrive
        drive = GoogleDrive(gauth)
        
        # 4. Subir archivo a la carpeta específica
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_title = f"invitados_{timestamp}.xlsx"
        
        file1 = drive.CreateFile({
            'title': file_title,
            'parents': [{'id': folder_id}]
        })
        file1.SetContentFile(file_path)
        file1.Upload()
        
        # 5. Establecer permisos (cualquiera con el enlace puede ver)
        file1.InsertPermission({
            'type': 'anyone',
            'value': 'anyone',
            'role': 'reader'
        })
        
        # 6. Obtener URL compartible
        file_id = file1['id']
        share_link = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
        
        print(f"Archivo subido exitosamente a Google Drive: {share_link}")
        return share_link
        
    except ImportError:
        print("Error: Biblioteca pydrive no está instalada.")
        print("Instálala usando: pip install pydrive")
        return None
    except Exception as e:
        print(f"Error al subir archivo a Google Drive: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

def enviar_mensaje_bienvenida(numero):
    """Enviar mensaje de bienvenida al organizador"""
    mensaje = f"""¡Hola! 👋 Soy tu asistente virtual para la gestión de invitaciones.

Puedo ayudarte con:
- Crear eventos para tus celebraciones
- Procesar listas de invitados (envíame un Excel)
- Enviar invitaciones masivas (!enviar)
- Mostrar reportes de estado (!reporte)
- Obtener Excel actualizado (!excel)

📊 Este sistema utiliza:
- Base de datos Supabase para almacenar tu información
- WhatsApp para comunicación directa
- Procesamiento de lenguaje natural para interpretar respuestas

¿En qué puedo ayudarte hoy?"""
    
    return whatsapp.send_message(numero, mensaje)

def enviar_mensaje_nuevo_organizador(numero):
    """Enviar mensaje de bienvenida a nuevo organizador"""
    # Intentar registrar al organizador primero
    success, result = registrar_organizador(numero)
    
    if success:
        print(f"✅ Organizador registrado exitosamente: {result['id']}")
    else:
        print(f"❌ Error al registrar organizador: {result}")
    
    mensaje = """¡Hola! 👋 Bienvenido(a) al sistema de gestión de eventos.

Como organizador(a), puedes:
1️⃣ Crear eventos con el comando !crear
2️⃣ Importar listas de invitados desde Excel
3️⃣ Enviar invitaciones automáticamente
4️⃣ Recibir respuestas y generar reportes

Para comenzar, usa el comando !crear seguido del nombre de tu evento.
Ejemplo: !crear "Boda de Juan y María"

Escribe !ayuda para ver todos los comandos disponibles."""
    
    return whatsapp.send_message(numero, mensaje)

def enviar_mensaje_seleccion_evento(numero, eventos):
    """Envía un mensaje para seleccionar entre varios eventos"""
    mensaje = "Tienes varios eventos registrados. Por favor, selecciona uno para trabajar:\n\n"
    
    for i, evento in enumerate(eventos, 1):
        fecha = evento.get('fecha', 'Sin fecha definida')
        mensaje += f"{i}. {evento['nombre']} - {fecha}\n"
    
    mensaje += "\nResponde con el número del evento que deseas seleccionar."
    
    return whatsapp.send_message(numero, mensaje)

# Función para verificar si un organizador está autorizado
def verificar_organizador_autorizado(numero):
    """Verifica si el número está en la lista de códigos de verificación válidos"""
    print(f"Verificando autorización para el número: {numero}")
    print(f"Estado de codigos_verificacion: {numero in codigos_verificacion}")
    if numero in codigos_verificacion:
        print(f"Estado verificado: {codigos_verificacion[numero].get('verificado', False)}")
    return numero in codigos_verificacion and codigos_verificacion[numero].get('verificado', False)

# Función para borrar un evento
def borrar_evento(evento_id):
    """Borra un evento y todos sus invitados asociados"""
    try:
        supabase = init_supabase()
        if not supabase:
            return False, "No se pudo conectar a Supabase"
        
        # Primero borrar los invitados asociados al evento
        supabase.table('invitados').delete().eq('evento_id', evento_id).execute()
        
        # Luego borrar el evento
        response = supabase.table('eventos').delete().eq('id', evento_id).execute()
        
        return True, "Evento eliminado correctamente"
    except Exception as e:
        print(f"Error al borrar evento: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False, f"Error al borrar evento: {str(e)}"

# Añadir función para resetear un organizador
def resetear_organizador(numero):
    """Borra todos los eventos de un organizador y sus datos para pruebas"""
    try:
        supabase = init_supabase()
        if not supabase:
            return False, "No se pudo conectar a Supabase"
        
        # Obtener el organizador
        success, organizador = obtener_organizador_por_numero(numero)
        if not success:
            return False, "Organizador no encontrado"
        
        organizador_id = organizador['id']
        
        # Obtener todos los eventos del organizador
        success, eventos = obtener_eventos_organizador(organizador_id)
        
        # Borrar invitados y eventos
        if success and eventos:
            for evento in eventos:
                # Borrar invitados asociados al evento
                supabase.table('invitados').delete().eq('evento_id', evento['id']).execute()
                # Borrar evento
                supabase.table('eventos').delete().eq('id', evento['id']).execute()
        
        # Borrar el organizador
        supabase.table('organizadores').delete().eq('id', organizador_id).execute()
        
        # Limpiar estado de sesión
        if numero in sesiones_organizadores:
            del sesiones_organizadores[numero]
        
        # Limpiar código de verificación
        if numero in codigos_verificacion:
            del codigos_verificacion[numero]
        
        return True, "Organizador y todos sus eventos borrados con éxito"
    except Exception as e:
        print(f"Error al resetear organizador: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False, f"Error al resetear organizador: {str(e)}"

# Modificar process_admin_command para incluir el comando de reset
def process_admin_command(numero, comando, media_url=None):
    """Procesar comandos del organizador"""
    comando = comando.lower().strip()
    
    # Obtener información del organizador
    success, organizador = obtener_organizador_por_numero(numero)
    
    # Comando especial para TESTING: !reset - Borrar todos los datos del organizador
    if comando == "!reset":
        success, mensaje = resetear_organizador(numero)
        if success:
            return """✅ Modo de prueba: Se han borrado todos tus datos como organizador.
            
Ahora puedes iniciar el flujo nuevamente como un nuevo usuario. 
Para registrarte como organizador:

1. Visita el landing page y completa el formulario
2. Recibirás un código de verificación
3. Envía !verificar CODIGO para activar tu cuenta"""
        else:
            return f"❌ Error al resetear: {mensaje}"
    
    # Verificar autorización para comandos críticos
    if not verificar_organizador_autorizado(numero) and comando != "!verificar":
        if comando.startswith("!crear") or comando == "!eventos" or comando.startswith("!borrar"):
            return """❌ No estás autorizado como organizador. 
Para registrarte como organizador, debes acceder desde nuestra página web y obtener un código de verificación.
Visita el sitio web y sigue las instrucciones para registrarte."""
    
    # Comandos que no requieren tener un evento activo
    if comando == "!ayuda":
        return """📋 Comandos disponibles:
!crear "Nombre del evento" "Descripción opcional" - Crea un nuevo evento
!eventos - Muestra tus eventos registrados
!borrar (número) - Borra un evento por su número en la lista
!enviar - Inicia el envío de invitaciones
!reporte - Muestra el estado actual de respuestas
!excel - Recibe el archivo Excel actualizado
!reset - (Solo para pruebas) Borra todos tus datos como organizador
!ayuda - Muestra esta ayuda"""
    
    # Comando para verificar un código
    elif comando.startswith("!verificar "):
        codigo = comando[10:].strip()
        print(f"Procesando verificación para {numero} con código: {codigo}")
        print(f"Códigos disponibles: {list(codigos_verificacion.keys())}")
        if numero in codigos_verificacion:
            print(f"Código almacenado: {codigos_verificacion[numero]['codigo']}")
            print(f"¿Coinciden? {codigos_verificacion[numero]['codigo'] == codigo}")
        
        if numero in codigos_verificacion and codigos_verificacion[numero]['codigo'] == codigo:
            print(f"✅ Verificación exitosa para {numero}")
            codigos_verificacion[numero]['verificado'] = True
            
            # Si el organizador no existe, registrarlo automáticamente
            if not success:
                print(f"Registrando organizador automáticamente para {numero}")
                success, organizador = registrar_organizador(numero)
                if not success:
                    return f"❌ Error al registrarte como organizador: {organizador}"
            
            return """✅ ¡Verificación completada con éxito!
Ahora puedes crear y gestionar eventos.
Usa !crear para crear tu primer evento o !ayuda para ver todos los comandos disponibles."""
        else:
            if numero not in codigos_verificacion:
                print(f"❌ No hay código de verificación para {numero}")
                return "❌ No se encontró un código de verificación para tu número. Por favor, genera uno desde la página web."
            else:
                print(f"❌ Código incorrecto para {numero}")
                return "❌ Código de verificación incorrecto. Verifica e intenta nuevamente."
    
    # Verificar si está en proceso de confirmación de borrado
    if numero in sesiones_organizadores and sesiones_organizadores[numero].get('confirmando_borrado') and comando == "!borrar confirmar":
        # Obtener información del evento a borrar
        evento_id = sesiones_organizadores[numero].get('evento_a_borrar_id')
        nombre_evento = sesiones_organizadores[numero].get('evento_a_borrar_nombre')
        
        # Limpiar el estado de confirmación
        sesiones_organizadores[numero]['confirmando_borrado'] = False
        sesiones_organizadores[numero].pop('evento_a_borrar_id', None)
        sesiones_organizadores[numero].pop('evento_a_borrar_nombre', None)
        
        # Borrar el evento
        success, mensaje = borrar_evento(evento_id)
        if success:
            return f"✅ Evento '{nombre_evento}' borrado correctamente."
        else:
            return f"❌ Error al borrar evento: {mensaje}"
    
    # Comando para borrar un evento
    elif comando.startswith("!borrar "):
        if not success:
            return "❌ No estás registrado como organizador. Usa !crear para comenzar."
        
        # Si el usuario ya estaba en modo de confirmación y envía otro comando de borrado
        # cancelamos la confirmación anterior
        if numero in sesiones_organizadores and sesiones_organizadores[numero].get('confirmando_borrado'):
            sesiones_organizadores[numero]['confirmando_borrado'] = False
            sesiones_organizadores[numero].pop('evento_a_borrar_id', None)
            sesiones_organizadores[numero].pop('evento_a_borrar_nombre', None)
        
        try:
            # Obtener el número del evento a borrar
            num_evento = int(comando[8:].strip())
            
            # Obtener la lista de eventos del organizador
            success, eventos = obtener_eventos_organizador(organizador['id'])
            if not success or not eventos:
                return "No tienes eventos registrados para borrar."
            
            if num_evento < 1 or num_evento > len(eventos):
                return f"❌ Número de evento inválido. Debes especificar un número entre 1 y {len(eventos)}."
            
            # Obtener el ID del evento a borrar
            evento_a_borrar = eventos[num_evento - 1]
            
            # Confirmar antes de borrar
            if numero not in sesiones_organizadores:
                sesiones_organizadores[numero] = {}
            
            # Solicitar confirmación
            sesiones_organizadores[numero]['confirmando_borrado'] = True
            sesiones_organizadores[numero]['evento_a_borrar_id'] = evento_a_borrar['id']
            sesiones_organizadores[numero]['evento_a_borrar_nombre'] = evento_a_borrar['nombre']
            
            return f"""⚠️ ¿Estás seguro de borrar el evento "{evento_a_borrar['nombre']}"?
Esta acción no se puede deshacer y eliminará todos los invitados asociados.

Para confirmar, responde con: !borrar confirmar
Para cancelar, responde con cualquier otro comando."""
            
        except ValueError:
            return """❌ Formato incorrecto.
Usa: !borrar (número)
Ejemplo: !borrar 1

Para ver la lista de tus eventos, usa !eventos"""
    
    # Crear un nuevo evento
    elif comando.startswith("!crear "):
        if not success:
            # Registrar nuevo organizador y reportar explícitamente
            success, organizador = registrar_organizador(numero)
            if not success:
                return f"❌ Error al registrarte como organizador: {organizador}"
        
        try:
            # Intentar extraer nombre y descripción del evento
            texto = comando[7:].strip()
            
            # Si usa comillas, intentar separar nombre y descripción
            if texto.startswith('"'):
                partes = texto.split('"')
                if len(partes) >= 3:
                    nombre = partes[1].strip()
                    descripcion = partes[3].strip() if len(partes) >= 5 else ""
                else:
                    nombre = texto
                    descripcion = ""
            else:
                nombre = texto
                descripcion = ""
            
            # Intentar crear el evento
            try:
                success, evento = crear_evento(organizador['id'], nombre, descripcion)
                if not success:
                    return f"❌ Error al crear evento: {evento}"
                
                # Actualizar evento activo del organizador
                if numero not in sesiones_organizadores:
                    sesiones_organizadores[numero] = {}
                
                sesiones_organizadores[numero]['evento_activo_id'] = evento['id']
                sesiones_organizadores[numero]['context'] = {}
                
                return f"""✅ ¡Evento "{nombre}" creado con éxito!

Ahora puedes:
1. Subir tu Excel con la lista de invitados
2. Usar !enviar para mandar invitaciones
3. Consultar el estado con !reporte

¿En qué te puedo ayudar ahora?"""
            except Exception as e:
                error_msg = str(e)
                print(f"Error detallado al crear evento: {error_msg}")
                
                if "relation" in error_msg and "does not exist" in error_msg:
                    return "❌ La tabla 'eventos' no existe. Por favor, créala en el panel de Supabase."
                
                return f"❌ Error al crear evento: {str(e)}"
                
        except Exception as e:
            print(f"Error al procesar comando !crear: {str(e)}")
            return """❌ Formato incorrecto.
Usa: !crear "Nombre del evento" "Descripción opcional"
Ejemplo: !crear "Boda de Juan y María" "15 de diciembre" """
    
    # Listar eventos del organizador
    elif comando == "!eventos":
        if not success:
            return "❌ No estás registrado como organizador. Usa !crear para comenzar."
        
        success, eventos = obtener_eventos_organizador(organizador['id'])
        if not success or not eventos:
            return "No tienes eventos registrados. Usa !crear para comenzar."
        
        mensaje = "📅 Tus eventos registrados:\n\n"
        for i, evento in enumerate(eventos, 1):
            fecha = evento.get('fecha', 'Sin fecha definida')
            mensaje += f"{i}. {evento['nombre']} - {fecha}\n"
        
        mensaje += "\nPara seleccionar un evento, responde con el número correspondiente."
        return mensaje
    
    # Comandos que requieren tener un evento activo
    evento_activo_id = None
    if numero in sesiones_organizadores:
        evento_activo_id = sesiones_organizadores[numero].get('evento_activo_id')
    
    if not evento_activo_id and success:
        # Intentar obtener el evento más reciente
        success, evento = obtener_evento_activo(organizador['id'])
        if success:
            evento_activo_id = evento['id']
            if numero not in sesiones_organizadores:
                sesiones_organizadores[numero] = {}
            sesiones_organizadores[numero]['evento_activo_id'] = evento_activo_id
    
    # Si no hay un evento activo y no es un comando de creación
    if not evento_activo_id and not comando.startswith("!crear") and comando != "!eventos" and comando != "!ayuda":
        return """❌ No tienes un evento activo.
Usa !crear para crear un nuevo evento o !eventos para ver tus eventos existentes."""
    
    if evento_activo_id:
        if comando == "!reporte":
            return obtener_reporte_evento(evento_activo_id)
        
        elif comando == "!enviar":
            try:
                # Exportar datos para envío
                output_file = f"temp_evento_{evento_activo_id}.xlsx"
                success, file_path = exportar_evento_a_excel(evento_activo_id, output_file)
                if not success:
                    return f"❌ Error al preparar datos: {file_path}"
                    
                # Enviar invitaciones
                from send_message import enviar_invitaciones_masivas
                success, result = enviar_invitaciones_masivas(file_path)
                
                # Eliminar archivo temporal
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except:
                    pass
                    
                if success:
                    return result
                else:
                    return f"❌ Error al enviar invitaciones: {result}"
            except Exception as e:
                return f"❌ Error al iniciar envío: {str(e)}"
        
        elif comando == "!excel":
            try:
                # Exportar datos
                output_file = f"evento_{evento_activo_id}.xlsx"
                success, file_path = exportar_evento_a_excel(evento_activo_id, output_file)
                if not success:
                    return f"❌ Error al generar Excel: {file_path}"
                
                # Comprobar si el archivo existe
                if not os.path.exists(file_path):
                    return "❌ No hay datos disponibles para exportar"
                    
                # Enviar mensaje y archivo
                whatsapp.send_message(numero, "💾 Preparando el archivo Excel actualizado...")
                whatsapp.send_file(numero, os.path.abspath(file_path), "📊 Archivo Excel con los datos actualizados de tu evento")
                return None  # Ya enviamos el mensaje, no necesitamos devolver otro
            except Exception as e:
                return f"❌ Error al preparar el Excel: {str(e)}"
    
    return "❌ Comando no reconocido. Usa !ayuda para ver los comandos disponibles."

# Modificar la ruta del webhook para soportar múltiples organizadores
@app.route("/webhook", methods=["POST"])
def recibir_respuesta():
    """Procesa mensajes recibidos desde WhatsApp"""
    global admin_conversation_history
    
    # Diferentes formatos según el proveedor
    if request.is_json and USE_WHATSAPP_WEB:
        # Formato de WhatsApp Web JS
        data = request.json
        numero = data.get("From", "").replace("@c.us", "")
        mensaje = data.get("Body", "").strip()
        media_url = None  # Los medios se manejan en el servidor Node.js
        print(f"Mensaje recibido de WhatsApp Web JS: De={numero}, Mensaje={mensaje}")
    else:
        # Formato de Twilio
        data = request.form
        numero = data.get("From", "").replace("whatsapp:", "").replace("+", "")
        mensaje = data.get("Body", "").strip()
        media_url = data.get("MediaUrl0", "")
        print(f"Mensaje recibido de Twilio: De={numero}, Mensaje={mensaje}")
    
    print(f"\nMensaje recibido:")
    print(f"- Número: {numero}")
    print(f"- Mensaje: {mensaje}")
    
    # Verificar si es un comando de verificación de organizador (procesamiento prioritario)
    if mensaje.lower().startswith("!verificar "):
        respuesta = process_admin_command(numero, mensaje)
        if respuesta:
            whatsapp.send_message(numero, respuesta)
        return "Comando de verificación procesado", 200
    
    # Verificar si es un organizador (existente o potencial)
    is_organizador = False
    success, organizador = obtener_organizador_por_numero(numero)
    
    # Mensajes iniciales y verificación de rol
    if success:
        is_organizador = True
        print(f"- Es organizador: Sí (ID: {organizador['id']})")
    else:
        print(f"- Es organizador: No (verificando si inicia sesión)")
        # Verificar si es un mensaje de inicio como organizador
        if mensaje.lower() in ["hola, soy organizador", "hola soy organizador", "iniciar como organizador"]:
            is_organizador = True
            print("- Iniciando como organizador por mensaje de bienvenida")
            
            # Registrar automáticamente como organizador
            success, resultado = registrar_organizador(numero)
            if success:
                print(f"✅ Organizador registrado automáticamente: {resultado['id']}")
                organizador = resultado
            else:
                print(f"❌ Error al registrar organizador: {resultado}")
    
    # Procesamiento para organizadores
    if is_organizador:
        # Verificar si ya está registrado
        if not success:
            # Es un nuevo organizador, dar la bienvenida
            enviar_mensaje_nuevo_organizador(numero)
            return "Bienvenida a nuevo organizador enviada", 200
        
        # Mensaje inicial de bienvenida a organizador existente
        if mensaje.lower() in ["hola", "hola, soy organizador", "hola soy organizador"]:
            enviar_mensaje_bienvenida(numero)
            
            # Verificar si tiene eventos
            success, eventos = obtener_eventos_organizador(organizador['id'])
            if success and eventos:
                if len(eventos) == 1:
                    # Solo tiene un evento, seleccionarlo automáticamente
                    if numero not in sesiones_organizadores:
                        sesiones_organizadores[numero] = {}
                    sesiones_organizadores[numero]['evento_activo_id'] = eventos[0]['id']
                    whatsapp.send_message(numero, f"Trabajando con tu evento: {eventos[0]['nombre']}")
                elif len(eventos) > 1:
                    # Tiene múltiples eventos, preguntar cuál usar
                    enviar_mensaje_seleccion_evento(numero, eventos)
            
            return "Bienvenida enviada", 200
        
        # Selección de evento por número (respuesta a lista de eventos)
        if numero in sesiones_organizadores and sesiones_organizadores[numero].get('esperando_seleccion'):
            try:
                seleccion = int(mensaje.strip())
                success, eventos = obtener_eventos_organizador(organizador['id'])
                if success and 1 <= seleccion <= len(eventos):
                    evento_seleccionado = eventos[seleccion - 1]
                    sesiones_organizadores[numero]['evento_activo_id'] = evento_seleccionado['id']
                    sesiones_organizadores[numero]['esperando_seleccion'] = False
                    whatsapp.send_message(numero, f"✅ Has seleccionado el evento: {evento_seleccionado['nombre']}")
                    return "Selección de evento procesada", 200
            except ValueError:
                pass  # No es un número, continuar con el procesamiento normal
        
        # Procesar comandos del organizador
        if mensaje.startswith("!"):
            respuesta = process_admin_command(numero, mensaje)
            if respuesta:
                whatsapp.send_message(numero, respuesta)
            return "Comando procesado", 200
            
        # Procesar archivo Excel
        if media_url or (USE_WHATSAPP_WEB and data.get("HasMedia")):
            # Verificar que haya un evento activo
            evento_activo_id = None
            if numero in sesiones_organizadores:
                evento_activo_id = sesiones_organizadores[numero].get('evento_activo_id')
            
            if not evento_activo_id:
                # Intentar obtener el evento más reciente
                success, evento = obtener_evento_activo(organizador['id'])
                if success:
                    evento_activo_id = evento['id']
                    if numero not in sesiones_organizadores:
                        sesiones_organizadores[numero] = {}
                    sesiones_organizadores[numero]['evento_activo_id'] = evento_activo_id
            
            if not evento_activo_id:
                whatsapp.send_message(numero, "❌ No tienes un evento activo. Primero crea un evento usando !crear")
                return "Error: No hay evento activo", 400
            
            print(f"Archivo adjunto detectado para evento ID: {evento_activo_id}")
            
            # Dependiendo del origen, el archivo ya estará guardado o habrá que descargarlo
            if USE_WHATSAPP_WEB:
                # WhatsApp Web JS: el archivo ya está guardado como invitados.xlsx
                file_path = EXCEL_FILE
            else:
                # Twilio: hay que descargar el archivo
                if media_url.lower().endswith(".xlsx") or ".xlsx" in media_url.lower():
                    success, file_path = download_file(media_url)
                    if not success:
                        whatsapp.send_message(numero, f"❌ Error al descargar archivo: {file_path}")
                        return "Error descargando archivo", 500
                else:
                    whatsapp.send_message(numero, "❌ Por favor, envía un archivo Excel (.xlsx)")
                    return "Formato incorrecto", 400
            
            # Importar Excel al evento
            success, message = importar_excel_a_evento(file_path, evento_activo_id)
            
            # Limpieza si es archivo temporal
            if file_path != EXCEL_FILE and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            
            # Enviar resultado
            respuesta = f"✅ {message}" if success else f"❌ {message}"
            whatsapp.send_message(numero, respuesta)
            
            return "Excel procesado", 200
            
        # Conversar con GPT para otros mensajes
        respuesta = chat_con_gpt(mensaje, admin_conversation_history)
        whatsapp.send_message(numero, respuesta)
        
        return "Mensaje procesado", 200
    
    # Procesamiento para invitados normales
    # Primero, buscar en qué evento(s) está invitado este número
    eventos_invitado = []
    
    try:
        supabase = init_supabase()
        if supabase:
            response = supabase.table('invitados').select('*,eventos(*)').eq('numero', numero).execute()
            if response.data:
                for invitado in response.data:
                    if 'eventos' in invitado and invitado['eventos']:
                        eventos_invitado.append({
                            'invitado_id': invitado['id'],
                            'evento_id': invitado['evento_id'],
                            'evento_nombre': invitado['eventos']['nombre'],
                            'organizador_id': invitado['eventos']['organizador_id']
                        })
    except Exception as e:
        print(f"Error al buscar eventos del invitado: {str(e)}")
    
    # Si no está en ningún evento, mensaje genérico
    if not eventos_invitado:
        print(f"Número no registrado como invitado: {numero}")
        
        # Si es un mensaje de verificación, procesar adecuadamente (verificación adicional)
        if mensaje.startswith("!"):
            respuesta = process_admin_command(numero, mensaje)
            if respuesta:
                whatsapp.send_message(numero, respuesta)
                return "Comando procesado", 200
        
        mensaje_error = "¡Hola! Parece que no estás registrado como invitado en ningún evento. Si crees que es un error, contacta al organizador."
        whatsapp.send_message(numero, mensaje_error)
        return "Número no registrado", 400
    
    # Si está en un solo evento, procesar directamente
    if len(eventos_invitado) == 1:
        invitado_data = eventos_invitado[0]
        invitado_id = invitado_data['invitado_id']
        evento_id = invitado_data['evento_id']
        
        # Analizar el mensaje con GPT
        resultados = analizar_respuesta(mensaje)
        
        if resultados:
            cambios = []
            
            # Actualizar datos en Supabase
            success, result = actualizar_respuesta_invitado(
                invitado_id, 
                confirmacion=resultados["confirmacion"].capitalize() if resultados["confirmacion"] in ["sí", "no"] else None,
                acompanante=resultados["acompanante"].capitalize() if resultados["acompanante"] in ["sí", "no"] else None,
                restricciones=resultados["restricciones"] if resultados["restricciones"] else None
            )
            
            if success:
                # Registrar cambios para el log
                if resultados["confirmacion"] in ["sí", "no"]:
                    cambios.append(f"Confirmación: {resultados['confirmacion'].capitalize()}")
                if resultados["acompanante"] in ["sí", "no"]:
                    cambios.append(f"Acompañante: {resultados['acompanante'].capitalize()}")
                if resultados["restricciones"]:
                    cambios.append(f"Restricciones: {resultados['restricciones']}")
                
                print(f"\nMensaje recibido de {numero}: '{mensaje}'")
                print("Cambios realizados:")
                for cambio in cambios:
                    print(f"- {cambio}")
                
                # Verificar si todos han respondido
                todas_respondieron, num_respuestas, total_invitados, faltantes = verificar_todas_respuestas_evento(evento_id)
                
                if todas_respondieron:
                    print(f"¡Todos los invitados ({total_invitados}/{total_invitados}) han respondido!")
                    
                    # Buscar el organizador del evento
                    success, evento = obtener_evento_activo(invitado_data['organizador_id'])
                    if success:
                        # Buscar número del organizador
                        response = supabase.table('organizadores').select('*').eq('id', invitado_data['organizador_id']).execute()
                        if response.data:
                            organizador_numero = response.data[0]['numero']
                            
                            # Enviar notificación al organizador
                            mensaje_notificacion = f"""🎉 ¡Excelente noticia! Todos los invitados ({total_invitados}) han respondido a la invitación para "{invitado_data['evento_nombre']}".

📊 Resumen:
{obtener_reporte_evento(evento_id)}

Te envío el archivo Excel actualizado con todas las respuestas."""
                            
                            # Enviar notificación
                            whatsapp.send_message(organizador_numero, mensaje_notificacion)
                            
                            # Exportar datos actualizados y enviar Excel
                            output_file = f"evento_{evento_id}.xlsx"
                            success, file_path = exportar_evento_a_excel(evento_id, output_file)
                            if success:
                                whatsapp.send_file(organizador_numero, os.path.abspath(file_path), "📊 Archivo Excel con todas las respuestas")
                                print(f"Excel enviado al organizador ({organizador_numero}) con todas las respuestas")
                
                # Enviar confirmación al invitado 
                # Obtener nombre del invitado
                response = supabase.table('invitados').select('nombre').eq('id', invitado_id).execute()
                nombre_invitado = response.data[0]['nombre'] if response.data else ""
                
                confirmacion = f"¡Gracias {nombre_invitado}! Tu respuesta ha sido registrada correctamente para el evento \"{invitado_data['evento_nombre']}\"."
                
                # Solo enviar si no es una confirmación automática (mensajes más largos que "confirmed")
                if len(mensaje) > 10:
                    whatsapp.send_message(numero, confirmacion)
                
                return confirmacion, 200
            else:
                print(f"Error al actualizar respuesta: {result}")
                return "❌ Lo siento, no pudimos procesar tu respuesta", 500
        else:
            print(f"No se pudo interpretar el mensaje: '{mensaje}'")
            return "❌ Lo siento, no pudimos interpretar tu respuesta", 500
    
    # Si está en múltiples eventos, preguntar a cuál responde
    else:
        # TODO: Implementar selección de evento para invitados en múltiples eventos
        # Por ahora, usar el más reciente
        invitado_data = eventos_invitado[0]  # Tomar el primero
        
        # Mismo procesamiento que arriba...
        # [Se omite duplicación por brevedad, pero sería similar al bloque anterior]
        
        return "Invitado en múltiples eventos", 200
        
    return "Mensaje procesado", 200

# Endpoint para procesar archivos Excel recibidos
@app.route("/process-excel", methods=["POST"])
def process_received_excel():
    """Procesa un archivo Excel recibido a través de WhatsApp Web JS"""
    try:
        data = request.json
        numero = data.get("from", "").replace("@c.us", "")
        
        # Verificar si existe el archivo invitados.xlsx
        if not os.path.exists(EXCEL_FILE):
            return jsonify({
                "status": "error",
                "message": f"No se encontró el archivo {EXCEL_FILE}"
            }), 400
            
        # Verificar si es el organizador
        if numero != ADMIN_NUMBER:
            return jsonify({
                "status": "error",
                "message": "Solo el organizador puede enviar archivos Excel"
            }), 403
            
        # Importar Excel a Supabase
        success, message = importar_excel_a_supabase(EXCEL_FILE)
        
        # Notificar al organizador
        respuesta = f"✅ {message}" if success else f"❌ {message}"
        whatsapp.send_message(numero, respuesta)
        
        return jsonify({
            "status": "success" if success else "error",
            "message": message
        }), 200 if success else 400
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Funciones para gestionar organizadores
def registrar_organizador(numero, nombre="Organizador"):
    """Registra un nuevo organizador en el sistema"""
    try:
        supabase = init_supabase()
        if not supabase:
            return False, "No se pudo conectar a Supabase"
        
        # Verificar si ya existe un organizador con ese número
        try:
            response = supabase.table('organizadores').select('*').eq('numero', numero).execute()
            
            if len(response.data) > 0:
                # El organizador ya existe, devolver su ID
                organizador = response.data[0]
                return True, organizador
        except Exception as e:
            print(f"Error al buscar organizador: {str(e)}")
            # Si hay error, es posible que la tabla no exista, crear el organizador de todas formas
        
        # Registrar nuevo organizador
        try:
            organizador_data = {
                'numero': numero,
                'nombre': nombre
            }
            
            response = supabase.table('organizadores').insert(organizador_data).execute()
            if len(response.data) == 0:
                return False, "Error al registrar organizador"
            
            return True, response.data[0]
        except Exception as e:
            error_msg = str(e)
            print(f"Error al insertar organizador: {error_msg}")
            
            # Si el error es que la tabla no existe, recomendar crearla
            if "relation" in error_msg and "does not exist" in error_msg:
                return False, "La tabla 'organizadores' no existe. Por favor, créala en el panel de Supabase."
            
            return False, f"Error al registrar organizador: {error_msg}"
            
    except Exception as e:
        print(f"Error al registrar organizador: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False, f"Error al registrar organizador: {str(e)}"

def obtener_organizador_por_numero(numero):
    """Obtiene un organizador por su número de teléfono"""
    try:
        supabase = init_supabase()
        if not supabase:
            return False, "No se pudo conectar a Supabase"
        
        try:
            response = supabase.table('organizadores').select('*').eq('numero', numero).execute()
            if len(response.data) == 0:
                return False, "Organizador no encontrado"
            
            return True, response.data[0]
        except Exception as e:
            error_msg = str(e)
            print(f"Error detallado al buscar organizador: {error_msg}")
            
            # Si el error es que la tabla no existe
            if "relation" in error_msg and "does not exist" in error_msg:
                return False, "La tabla 'organizadores' no existe"
            
            return False, f"Error al buscar organizador: {error_msg}"
    except Exception as e:
        return False, f"Error al buscar organizador: {str(e)}"

def crear_evento(organizador_id, nombre, descripcion="", fecha=None):
    """Crea un nuevo evento para un organizador"""
    try:
        supabase = init_supabase()
        if not supabase:
            return False, "No se pudo conectar a Supabase"
        
        # Crear datos del evento
        evento_data = {
            'organizador_id': organizador_id,
            'nombre': nombre,
            'descripcion': descripcion
        }
        
        # Añadir fecha si se proporciona
        if fecha:
            evento_data['fecha'] = fecha
        
        # Insertar evento
        try:
            response = supabase.table('eventos').insert(evento_data).execute()
            if len(response.data) == 0:
                return False, "Error al crear evento"
            
            return True, response.data[0]
        except Exception as e:
            error_msg = str(e)
            print(f"Error detallado al crear evento: {error_msg}")
            
            # Si el error es que la tabla no existe
            if "relation" in error_msg and "does not exist" in error_msg:
                return False, "La tabla 'eventos' no existe. Por favor, créala en el panel de Supabase."
            
            return False, f"Error específico al crear evento: {error_msg}"
            
    except Exception as e:
        print(f"Error al crear evento: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False, f"Error al crear evento: {str(e)}"

def obtener_eventos_organizador(organizador_id):
    """Obtiene todos los eventos de un organizador"""
    try:
        supabase = init_supabase()
        if not supabase:
            return False, "No se pudo conectar a Supabase"
        
        response = supabase.table('eventos').select('*').eq('organizador_id', organizador_id).execute()
        return True, response.data
    except Exception as e:
        return False, f"Error al obtener eventos: {str(e)}"

def obtener_evento_activo(organizador_id):
    """Obtiene el evento más reciente (activo) de un organizador"""
    try:
        supabase = init_supabase()
        if not supabase:
            return False, "No se pudo conectar a Supabase"
        
        # Obtener el evento más reciente
        response = supabase.table('eventos').select('*').eq('organizador_id', organizador_id).order('fecha_creacion', desc=True).limit(1).execute()
        
        if len(response.data) == 0:
            return False, "No hay eventos activos"
        
        return True, response.data[0]
    except Exception as e:
        return False, f"Error al obtener evento activo: {str(e)}"

# Funciones para gestionar invitados con la nueva estructura
def obtener_invitados_evento(evento_id):
    """Obtiene todos los invitados de un evento específico"""
    try:
        supabase = init_supabase()
        if not supabase:
            return False, "No se pudo conectar a Supabase"
        
        response = supabase.table('invitados').select('*').eq('evento_id', evento_id).execute()
        return True, response.data
    except Exception as e:
        return False, f"Error al obtener invitados: {str(e)}"

def obtener_invitado_evento(evento_id, numero):
    """Busca un invitado por su número de teléfono en un evento específico"""
    try:
        supabase = init_supabase()
        if not supabase:
            return False, "No se pudo conectar a Supabase"
        
        response = supabase.table('invitados').select('*').eq('evento_id', evento_id).eq('numero', numero).execute()
        if len(response.data) == 0:
            return False, "Invitado no encontrado en este evento"
        
        return True, response.data[0]
    except Exception as e:
        return False, f"Error al buscar invitado: {str(e)}"

def actualizar_respuesta_invitado(invitado_id, confirmacion=None, acompanante=None, restricciones=None):
    """Actualiza la respuesta de un invitado específico"""
    try:
        supabase = init_supabase()
        if not supabase:
            return False, "No se pudo conectar a Supabase"
        
        update_data = {}
        
        # Actualizar solo los campos proporcionados
        if confirmacion is not None:
            update_data['confirmacion'] = confirmacion
        if acompanante is not None:
            update_data['acompanante'] = acompanante
        if restricciones is not None:
            update_data['restricciones_alimenticias'] = restricciones
        
        # Si no hay datos para actualizar, salir
        if not update_data:
            return True, "No hay cambios para actualizar"
        
        # Actualizar en Supabase
        response = supabase.table('invitados').update(update_data).eq('id', invitado_id).execute()
        return True, "Respuesta actualizada correctamente"
    except Exception as e:
        return False, f"Error al actualizar respuesta: {str(e)}"

def verificar_todas_respuestas_evento(evento_id):
    """Verifica si todos los invitados de un evento han respondido"""
    try:
        supabase = init_supabase()
        if not supabase:
            return False, 0, 0, []
        
        # Obtener todos los invitados del evento
        response = supabase.table('invitados').select('*').eq('evento_id', evento_id).execute()
        invitados = response.data
        
        total_invitados = len(invitados)
        if total_invitados == 0:
            return True, 0, 0, []  # No hay invitados, consideramos que todos respondieron
            
        # Contar respondidos
        respondieron = [i for i in invitados if i.get('confirmacion') is not None 
                        and i.get('confirmacion').strip() != '']
        num_respuestas = len(respondieron)
        
        # Listado de faltantes
        faltantes = [i['nombre'] for i in invitados if i.get('confirmacion') is None 
                    or i.get('confirmacion').strip() == '']
        
        todas_respondieron = (num_respuestas == total_invitados)
        
        return todas_respondieron, num_respuestas, total_invitados, faltantes
    except Exception as e:
        print(f"Error al verificar respuestas: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False, 0, 0, []

def importar_excel_a_evento(file_path, evento_id):
    """Importa datos de Excel a un evento específico"""
    try:
        # Leer Excel
        df = pd.read_excel(file_path)
        
        # Limpiar nombres de columnas
        df.columns = df.columns.str.strip()
        
        # Inicializar Supabase
        supabase = init_supabase()
        if not supabase:
            return False, "No se pudo conectar a Supabase"
        
        # Verificar columnas requeridas
        required_columns = ["Nombre", "Numero"]
        current_columns = [col.strip() for col in df.columns]
        required_columns_clean = [col.strip() for col in required_columns]
        
        if not all(col in current_columns for col in required_columns_clean):
            missing_cols = [col for col in required_columns_clean if col not in current_columns]
            return False, f"El Excel debe contener las columnas obligatorias: {', '.join(missing_cols)}"
            
        # Convertir DataFrame a lista de diccionarios
        invitados_formateados = []
        
        for _, row in df.iterrows():
            invitado_formateado = {
                'evento_id': evento_id,
                'nombre': str(row.get('Nombre', '')) if not pd.isna(row.get('Nombre', '')) else '',
                'numero': str(row.get('Numero', '')) if not pd.isna(row.get('Numero', '')) else '',
                'confirmacion': str(row.get('Confirmacion', '')) if not pd.isna(row.get('Confirmacion', '')) else '',
                'acompanante': str(row.get('+1', '')) if not pd.isna(row.get('+1', '')) else '',
                'restricciones_alimenticias': str(row.get('Restricciones alimenticias', '')) if not pd.isna(row.get('Restricciones alimenticias', '')) else ''
            }
            
            # Validar que el número no esté vacío
            if invitado_formateado['nombre'] and invitado_formateado['numero']:
                invitados_formateados.append(invitado_formateado)
        
        if not invitados_formateados:
            return False, "No se encontraron datos válidos para importar"
            
        # Eliminar invitados anteriores del evento (opcional)
        supabase.table('invitados').delete().eq('evento_id', evento_id).execute()
        
        # Insertar nuevos invitados
        response = supabase.table('invitados').insert(invitados_formateados).execute()
        
        print(f"DEBUG: Datos importados a Supabase: {len(invitados_formateados)} invitados para el evento {evento_id}")
        return True, f"Excel importado con éxito. {len(invitados_formateados)} invitados registrados para su evento."
    except Exception as e:
        print(f"ERROR detallado en importar_excel_a_evento: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False, f"Error al importar Excel: {str(e)}"

def exportar_evento_a_excel(evento_id, output_file=None):
    """Exporta los invitados de un evento a Excel"""
    try:
        # Obtener datos del evento
        supabase = init_supabase()
        if not supabase:
            return False, "No se pudo conectar a Supabase"
        
        # Nombre de archivo único para cada evento
        if output_file is None:
            output_file = f"invitados_evento_{evento_id}.xlsx"
        
        # Obtener invitados del evento
        success, invitados = obtener_invitados_evento(evento_id)
        if not success:
            return False, invitados
        
        # Convertir a DataFrame
        df = pd.DataFrame(invitados)
        
        # Renombrar columnas para formato Excel
        df = df.rename(columns={
            'nombre': 'Nombre',
            'numero': 'Numero',
            'confirmacion': 'Confirmacion',
            'acompanante': '+1',
            'restricciones_alimenticias': 'Restricciones alimenticias'
        })
        
        # Seleccionar columnas relevantes
        columns = ['Nombre', 'Numero', 'Confirmacion', '+1', 'Restricciones alimenticias']
        if all(col in df.columns for col in columns):
            df = df[columns]
        
        # Guardar Excel
        df.to_excel(output_file, index=False)
        
        return True, output_file
    except Exception as e:
        print(f"Error al exportar evento a Excel: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False, f"Error al exportar a Excel: {str(e)}"

def obtener_reporte_evento(evento_id):
    """Generar reporte de respuestas para un evento específico"""
    try:
        # Obtener evento
        supabase = init_supabase()
        response_evento = supabase.table('eventos').select('*').eq('id', evento_id).execute()
        if len(response_evento.data) == 0:
            return "Evento no encontrado"
        
        evento = response_evento.data[0]
        
        # Obtener invitados del evento
        success, invitados = obtener_invitados_evento(evento_id)
        if not success:
            return f"Error al generar reporte: {invitados}"
        
        total = len(invitados)
        confirmados = len([i for i in invitados if i.get('confirmacion', '').lower() == 'sí'])
        rechazados = len([i for i in invitados if i.get('confirmacion', '').lower() == 'no'])
        pendientes = total - confirmados - rechazados
        
        return f"""📊 Reporte de "{evento['nombre']}":
- Total invitados: {total}
- Confirmados: {confirmados}
- Rechazados: {rechazados}
- Pendientes: {pendientes}"""
    except Exception as e:
        return f"Error al generar reporte: {str(e)}"

# Añadir rutas para servir el landing page
@app.route('/')
def index():
    """Sirve el landing page"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Sirve archivos estáticos"""
    return send_from_directory('.', filename)

@app.route('/generar-codigo', methods=['POST'])
def generar_codigo():
    """Genera un código de verificación para un número de teléfono"""
    try:
        data = request.json
        numero = data.get('numero', '').strip()
        
        print(f"\n🔑 Generando código para: {numero}")
        
        if not numero:
            print("❌ Número no proporcionado")
            return jsonify({'success': False, 'message': 'Número de teléfono no proporcionado'}), 400
        
        # Generar un código aleatorio de 6 dígitos
        import random
        codigo = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        print(f"🔢 Código generado: {codigo}")
        
        # Almacenar el código para verificación posterior
        codigos_verificacion[numero] = {
            'codigo': codigo,
            'verificado': False,
            'fecha_generacion': datetime.now()
        }
        
        print(f"📝 Código almacenado para {numero}: {codigos_verificacion[numero]}")
        print(f"🗄️ Estado actual de codigos_verificacion: {codigos_verificacion}")
        
        # Enviar el código al número de teléfono
        mensaje = f"""🔐 Tu código de verificación es: {codigo}

Para activar tu cuenta de organizador, envía:
!verificar {codigo}

Este código expirará en 24 horas."""
        
        success = whatsapp.send_message(numero, mensaje)
        print(f"📤 Mensaje enviado: {success}")
        
        return jsonify({'success': True, 'message': 'Código enviado correctamente'})
    except Exception as e:
        print(f"❌ Error al generar código: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

# Iniciar la aplicación
if __name__ == '__main__':
    inicializar_base_de_datos()
    app.run(debug=True)