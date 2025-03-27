#!/usr/bin/env python3

import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from dotenv import load_dotenv

"""
Script para configurar el acceso a Google Drive API
Este script debe ejecutarse una sola vez para configurar las credenciales.

Pasos previos:
1. Crear un proyecto en Google Cloud Platform (https://console.cloud.google.com/)
2. Habilitar la API de Google Drive
3. Crear credenciales OAuth2 (Tipo: Aplicación de escritorio)
4. Descargar el archivo client_secrets.json y colocarlo en este directorio
"""

# Cargar variables de entorno
load_dotenv()

def configurar_google_drive():
    """Configura la autenticación con Google Drive"""
    print("[INFO] Configurando Google Drive API...")
    
    # Verificar si existe el archivo client_secrets.json
    if not os.path.exists('client_secrets.json'):
        print("[ERROR] ❌ No se encontró el archivo client_secrets.json")
        print("""
[INFO] Para configurar Google Drive API, sigue estos pasos:
1. Ve a https://console.cloud.google.com/
2. Crea un proyecto nuevo
3. Habilita la API de Google Drive para tu proyecto
4. Crea credenciales OAuth2 (Tipo: Aplicación de escritorio)
5. Descarga el archivo client_secrets.json y colócalo en este directorio
""")
        return False
    
    try:
        # Inicializar la autenticación
        gauth = GoogleAuth()
        
        # Intentar autenticar por LocalWebserverAuth
        # Esto abrirá una ventana del navegador para autenticar
        print("[INFO] Abriendo navegador para autenticación con Google...")
        gauth.LocalWebserverAuth()
        
        # Guardar las credenciales para uso futuro
        gauth.SaveCredentialsFile("credentials.json")
        
        # Probar la conexión a Google Drive
        drive = GoogleDrive(gauth)
        
        # Crear una carpeta de prueba
        folder_name = "WhatsApp Bot Excel Storage"
        folder_exists = False
        
        # Buscar si la carpeta ya existe
        file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
        for file in file_list:
            if file['title'] == folder_name and file['mimeType'] == 'application/vnd.google-apps.folder':
                folder_exists = True
                folder_id = file['id']
                print(f"[INFO] La carpeta '{folder_name}' ya existe en Google Drive (ID: {folder_id})")
                break
        
        # Si no existe, crear la carpeta
        if not folder_exists:
            folder = drive.CreateFile({
                'title': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            })
            folder.Upload()
            folder_id = folder['id']
            print(f"[INFO] Carpeta '{folder_name}' creada exitosamente en Google Drive (ID: {folder_id})")
            
            # Dar permiso de solo lectura a cualquier persona con el enlace
            folder.InsertPermission({
                'type': 'anyone',
                'value': 'anyone',
                'role': 'reader'
            })
            
        # Crear un archivo de prueba en la carpeta
        test_file = drive.CreateFile({
            'title': 'test_file.txt',
            'parents': [{'id': folder_id}]
        })
        test_file.SetContentString('Este es un archivo de prueba para verificar la configuración de Google Drive API.')
        test_file.Upload()
        
        # Establecer permisos para el archivo
        test_file.InsertPermission({
            'type': 'anyone',
            'value': 'anyone',
            'role': 'reader'
        })
        
        # Obtener el enlace compartible
        file_id = test_file['id']
        share_link = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
        
        print(f"[OK] ✅ Archivo de prueba creado exitosamente")
        print(f"[INFO] URL compartible: {share_link}")
        
        # Guardar el ID de la carpeta en el archivo .env
        has_folder_id = False
        with open('.env', 'r') as env_file:
            env_content = env_file.read()
            if 'GOOGLE_DRIVE_FOLDER_ID=' in env_content:
                has_folder_id = True
        
        if not has_folder_id:
            with open('.env', 'a') as env_file:
                env_file.write(f"\n# Google Drive configuration\nGOOGLE_DRIVE_FOLDER_ID={folder_id}\n")
                print("[INFO] ID de carpeta añadido al archivo .env")
        
        print("[OK] ✅ Google Drive API configurado exitosamente")
        print("[INFO] Las credenciales se han guardado en 'credentials.json'")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] ❌ Error al configurar Google Drive: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    configurar_google_drive() 