#!/usr/bin/env python3
from supabase import create_client
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def configurar_storage():
    print(f"[INFO] Configurando Supabase Storage...")
    
    try:
        # Inicializar cliente
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[OK] ✅ Conexión a Supabase establecida")
        
        # Verificar si existe el bucket 'archivos'
        try:
            # Intentar listar los archivos en el bucket (si existe)
            response = supabase.storage.list_buckets()
            buckets = [bucket['name'] for bucket in response]
            
            print(f"[INFO] Buckets existentes: {buckets}")
            
            if 'archivos' in buckets:
                print("[OK] ✅ El bucket 'archivos' ya existe")
                
                # Verificar políticas de acceso público
                print("[INFO] ✅ Verificando políticas de acceso...")
                
                # Nota: En Supabase-py no hay método directo para verificar políticas,
                # se debe hacer desde el dashboard o a través de la API REST directamente
                
                print("""
[INFO] ⚠️ Para habilitar el acceso público a los archivos, sigue estos pasos manualmente:
1. Ve a la sección Storage del dashboard de Supabase
2. Selecciona el bucket 'archivos'
3. Ve a "Policies" (Políticas)
4. Configura una política para permitir el acceso público de lectura
   - Select type: SELECT (lectura)
   - Define policy: (auth.role() = 'anon') - Permite acceso a usuarios anónimos

Ejemplo de política:
{
  "name": "Acceso público",
  "definition": "auth.role() = 'anon'",
  "allow": "SELECT"
}
""")
                
            else:
                print("[INFO] El bucket 'archivos' no existe, intentando crear...")
                # Crear nuevo bucket - Notar que aquí solo se pasa el nombre como string
                response = supabase.storage.create_bucket("archivos")
                print("[OK] ✅ Bucket 'archivos' creado exitosamente")
                
                print("""
[INFO] ⚠️ Para habilitar el acceso público a los archivos, sigue estos pasos manualmente:
1. Ve a la sección Storage del dashboard de Supabase
2. Selecciona el bucket 'archivos'
3. Ve a "Policies" (Políticas)
4. Configura una política para permitir el acceso público de lectura
   - Select type: SELECT (lectura) 
   - Define policy: (auth.role() = 'anon') - Permite acceso a usuarios anónimos

Ejemplo de política:
{
  "name": "Acceso público",
  "definition": "auth.role() = 'anon'",
  "allow": "SELECT"
}
""")
            
            try:
                # Probar subida de archivo
                print("\n[TEST] Probando subida de archivo a Supabase Storage...")
                
                # Crear archivo temporal para prueba
                test_file_path = "test_storage.txt"
                with open(test_file_path, 'w') as f:
                    f.write("Este es un archivo de prueba para Supabase Storage.")
                
                # Subir archivo
                with open(test_file_path, 'rb') as f:
                    file_content = f.read()
                
                file_name = "test_file.txt"
                response = supabase.storage.from_('archivos').upload(
                    file_name,
                    file_content
                )
                
                # Obtener URL pública
                file_url = supabase.storage.from_('archivos').get_public_url(file_name)
                
                print(f"[OK] ✅ Archivo subido exitosamente")
                print(f"[INFO] URL pública: {file_url}")
                
                # Limpiar archivo de prueba
                os.remove(test_file_path)
                
                # Eliminar archivo de Supabase (opcional)
                # supabase.storage.from_('archivos').remove([file_name])
                # print(f"[INFO] Archivo de prueba eliminado de Supabase")
            except Exception as e:
                print(f"[ERROR] ❌ Error en prueba de subida: {str(e)}")
                
            return True
            
        except Exception as e:
            print(f"[ERROR] ❌ Error al verificar o crear bucket: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
            
    except Exception as e:
        print(f"[ERROR] ❌ Error de conexión a Supabase: {str(e)}")
        return False

if __name__ == "__main__":
    configurar_storage()
    print("\n[INFO] Configuración completada") 