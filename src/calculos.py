import pandas as pd


def calcular_ingresos_totales(df):
    return df["Total Revenue"].sum()

def calcular_unidades_vendidas(df):
    return df["Units Sold"].sum()

def calcular_transacciones(df):
    return df["Transaction ID"].nunique()

def calcular_ticket_medio(df):
    total_ingresos = calcular_ingresos_totales(df)
    total_transacciones = calcular_transacciones(df)
    if total_transacciones == 0:
        return 0
    return total_ingresos / total_transacciones

def ventas_por_producto(df):
    return df.groupby("Product Name")["Total Revenue"].sum().sort_values(ascending=False).head(10)

def ventas_por_categoria(df):
    return df.groupby("Product Category")["Total Revenue"].sum().sort_values(ascending=False)

def ventas_por_mes(df):
    fechas = pd.to_datetime(df["Date"])
    return df.groupby(fechas.dt.to_period("M"))["Total Revenue"].sum()

def ventas_por_region(df):
    return df.groupby("Region")["Total Revenue"].sum().sort_values(ascending=False)

def calcular_metricas(df):
    metricas = {
            "Ingresos Totales": calcular_ingresos_totales(df),
            "Ticket Medio": calcular_ticket_medio(df),
            "Unidades Vendidas": calcular_unidades_vendidas(df),
            "Transacciones": calcular_transacciones(df),
            "Ventas por Producto": ventas_por_producto(df),
            "Ventas por Categoría": ventas_por_categoria(df),
            "Ventas por Mes": ventas_por_mes(df),
            "Ventas por Región": ventas_por_region(df)
        }
    return metricas
