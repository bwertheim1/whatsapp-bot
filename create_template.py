import pandas as pd

# Crear DataFrame de ejemplo
df = pd.DataFrame({
    'Nombre': ['Ejemplo Persona 1', 'Ejemplo Persona 2'],
    'Numero': ['+56912345678', '+56987654321'],
    'Confirmacion': ['', ''],
    '+1': ['', ''],
    'Restricciones alimenticias': ['', '']
})

# Guardar como Excel
df.to_excel('plantilla_invitados.xlsx', index=False)
print("Plantilla creada exitosamente") 