import pandas as pd 

def leer_csv(ruta):
    try:
        return pd.read_csv(ruta)
    except FileNotFoundError:
        print(f"Error: El archivo {ruta} no se encontró.")
        return None