import pandas as pd

df = pd.read_excel("invitados.xlsx")
print(df["Numero"].astype(str).tolist())  # Imprime los números en formato string
