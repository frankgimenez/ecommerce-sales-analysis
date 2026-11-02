"""Limpieza del dataset "online_sales_raw.csv".

Carga el CSV original, lo inspecciona, corrige los problemas de formato
y guarda una versión limpia en data/.
"""

# Paso 1: importar librerías

import pandas as pd

# Paso 2: cargar el CSV

from pathlib import Path

ruta = Path(__file__).resolve().parent.parent / "data" / "online_sales_raw.csv"

df = pd.read_csv(ruta)

# Paso 3: primer vistazo a los datos

print(df.head())
print(df.shape)

# Paso 4: comprobar valores nulos

print(df.isnull().sum())

# Mostrar las filas con valores nulos

print(df[df.isnull().any(axis=1)])


# Paso 5: investigar la fila problemática

print(df.loc[15, "Transaction ID"])


# Paso 6: comprobar registros duplicados

print("Filas duplicadas:", df.duplicated().sum())

# Comprobar IDs repetidos
print("IDs duplicados:", df["Transaction ID"].duplicated().sum())

# Comprobar que los ingresos están bien calculados
diferencia = (
    df["Units Sold"] * df["Unit Price"] - df["Total Revenue"]
).abs()

print("Ventas con importes incorrectos:", (diferencia > 0.01).sum())

#Guardar el dataset limpio
df.to_csv(ruta.parent / "online_sales_clean.csv", index=False)