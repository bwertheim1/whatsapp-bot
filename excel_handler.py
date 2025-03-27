import pandas as pd

def leer_invitados(ruta_excel):
    # Cargar el archivo Excel
    df = pd.read_excel(ruta_excel)

    # Convertirlo en una lista de diccionarios
    invitados = df.to_dict(orient="records")

    return invitados

# Prueba leyendo el archivo
if __name__ == "__main__":
    ruta = "invitados.xlsx"  # Asegúrate de que el archivo esté en la misma carpeta
    invitados = leer_invitados(ruta)
    print(invitados)
