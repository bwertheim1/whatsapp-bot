#!/usr/bin/env python3
from supabase import create_client
import os
from dotenv import load_dotenv
import pandas as pd
import json

# Cargar variables de entorno
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def verificar_supabase():
    print(f"[INFO] Verificando conexión a Supabase...")
    print(f"[INFO] URL: {SUPABASE_URL}")
    print(f"[INFO] KEY: {SUPABASE_KEY[:10]}...{SUPABASE_KEY[-10:]}")
    
    try:
        # Inicializar cliente
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[OK] ✅ Conexión a Supabase establecida")
        
        # Verificar tabla invitados
        try:
            response = supabase.table('invitados').select('id').limit(1).execute()
            print(f"[OK] ✅ Tabla 'invitados' existe")
            print(f"[INFO] Estructura de la respuesta: {type(response)}")
            
            # Ver esquema de la tabla
            try:
                # Intentamos obtener solo una fila para ver la estructura
                response = supabase.table('invitados').select('*').limit(1).execute()
                if response.data:
                    print(f"[INFO] Estructura de la tabla 'invitados':")
                    for key, value in response.data[0].items():
                        print(f"  - {key}: {type(value).__name__}")
                else:
                    print(f"[INFO] Tabla 'invitados' está vacía")
                
                # Intentar insertar un registro de prueba
                print("\n[TEST] Probando inserción...")
                test_data = {
                    'nombre': 'Usuario de Prueba',
                    'numero': '123456789',
                    'confirmacion': '',
                    'acompanante': '',
                    'restricciones_alimenticias': ''
                }
                
                print(f"[INFO] Datos a insertar: {json.dumps(test_data)}")
                
                response = supabase.table('invitados').insert(test_data).execute()
                print(f"[OK] ✅ Inserción exitosa")
                print(f"[INFO] Respuesta: {response.data}")
                
                # Limpiar dato de prueba
                if response.data and len(response.data) > 0:
                    test_id = response.data[0].get('id')
                    if test_id:
                        supabase.table('invitados').delete().eq('id', test_id).execute()
                        print(f"[OK] ✅ Datos de prueba eliminados")
                
            except Exception as e:
                print(f"[ERROR] ❌ Error al consultar estructura: {str(e)}")
                
        except Exception as e:
            print(f"[ERROR] ❌ Error al verificar tabla 'invitados': {str(e)}")
            print("[INFO] Intentando crear la tabla...")
            # Aquí podríamos añadir código para crear la tabla si no existe
            
    except Exception as e:
        print(f"[ERROR] ❌ Error de conexión a Supabase: {str(e)}")

def probar_importacion_excel():
    print("\n[TEST] Probando importación de Excel a Supabase...")
    
    # Crear un DataFrame de prueba
    data = {
        'Nombre': ['Juan Pérez', 'María López', 'Carlos Gómez'],
        'Numero': ['1234567890', '0987654321', '1122334455'],
        'Confirmacion': ['', '', ''],
        '+1': ['', '', ''],
        'Restricciones alimenticias': ['', '', '']
    }
    
    df = pd.DataFrame(data)
    
    # Guardar a Excel temporal
    temp_excel = "test_import.xlsx"
    df.to_excel(temp_excel, index=False)
    print(f"[INFO] Excel de prueba creado: {temp_excel}")
    
    # Importar a Supabase
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Leer Excel
        df = pd.read_excel(temp_excel)
        print(f"[INFO] DataFrame leído: {len(df)} filas")
        
        # Convertir DataFrame a lista de diccionarios con manejo adecuado de valores nulos
        invitados = []
        
        for _, row in df.iterrows():
            # Crear diccionario con valores convertidos a string
            invitado = {
                'nombre': str(row['Nombre']) if not pd.isna(row['Nombre']) else '',
                'numero': str(row['Numero']) if not pd.isna(row['Numero']) else '',
                'confirmacion': str(row['Confirmacion']) if not pd.isna(row['Confirmacion']) else '',
                'acompanante': str(row['+1']) if not pd.isna(row['+1']) else '',
                'restricciones_alimenticias': str(row['Restricciones alimenticias']) if not pd.isna(row['Restricciones alimenticias']) else ''
            }
            invitados.append(invitado)
        
        print(f"[INFO] Datos procesados: {invitados}")
        
        # Insertar en Supabase
        response = supabase.table('invitados').insert(invitados).execute()
        print(f"[OK] ✅ Importación exitosa")
        print(f"[INFO] Respuesta: {response.data}")
        
        # Limpiar datos de prueba
        for item in response.data:
            supabase.table('invitados').delete().eq('id', item['id']).execute()
        print(f"[OK] ✅ Datos de prueba eliminados")
        
        # Limpiar archivo
        os.remove(temp_excel)
        print(f"[INFO] Archivo Excel de prueba eliminado")
        
    except Exception as e:
        print(f"[ERROR] ❌ Error en prueba de importación: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    verificar_supabase()
    probar_importacion_excel()
    print("\n[INFO] Pruebas completadas") 