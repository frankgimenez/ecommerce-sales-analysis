from pathlib import Path
from lectura import leer_csv
from calculos import calcular_ingresos_totales, calcular_ticket_medio, calcular_unidades_vendidas, calcular_transacciones, ventas_por_categoria, ventas_por_mes, ventas_por_producto, ventas_por_region,calcular_metricas

def main():
    # 1. Leer los pedidos
    datos = leer_csv(Path(__file__).resolve().parent.parent / "data" / "online_sales_clean.csv")
    if datos is None:
        return

    # 2. Calcular métricas
    metricas = calcular_metricas(datos)
    
    # 3. Mostrar resultados
    print("\n========== ANÁLISIS DE VENTAS ==========")

    for metrica, valor in metricas.items():
        print(f"\n{metrica}")
        print("-" * 40)

        if metrica in ["Ingresos Totales", "Ticket Medio"]:
            print(f"{valor:.2f} €")
        else:
            print(valor)

if __name__ == "__main__":
    main()