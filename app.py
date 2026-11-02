"""Dashboard de ventas e-commerce 2024 (Streamlit + Plotly).

Ejecutar desde la carpeta raíz del proyecto:
    python -m streamlit run app.py

Reutiliza leer_csv() de src/lectura.py y las funciones de src/calculos.py.
Los filtros se aplican al DataFrame ANTES de llamar a esas funciones, así que
todas las métricas y gráficos se calculan sobre los datos filtrados.
"""

import sys
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

# Rutas a partir de la ubicación de este archivo: funcionan se ejecute desde donde se ejecute
RAIZ = Path(__file__).resolve().parent
RUTA_CSV = RAIZ / "data" / "online_sales_clean.csv"

# Hacemos visibles los módulos de src/ para poder importarlos
sys.path.insert(0, str(RAIZ / "src"))

from lectura import leer_csv  # noqa: E402
from calculos import (  # noqa: E402
    calcular_ingresos_totales,
    calcular_ticket_medio,
    calcular_transacciones,
    calcular_unidades_vendidas,
    ventas_por_categoria,
    ventas_por_mes,
    ventas_por_producto,
    ventas_por_region,
)
from graficos import (  # noqa: E402
    CONFIG,
    MONEDA,
    SUFIJO_MONEDA,
    etiqueta_mes,
    grafico_barras_horizontales,
    grafico_evolucion_mensual,
)

MESES_LARGOS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

# Nombres que se muestran en pantalla (el dataset está en inglés).
# Solo cambian las etiquetas: los filtros y los cálculos usan los valores originales.
NOMBRES_ES = {
    "North America": "Norteamérica", "Europe": "Europa", "Asia": "Asia",
    "Electronics": "Electrónica", "Home Appliances": "Electrodomésticos",
    "Clothing": "Ropa", "Books": "Libros", "Beauty Products": "Belleza",
    "Sports": "Deportes",
    "Credit Card": "Tarjeta de crédito", "Debit Card": "Tarjeta de débito",
    "PayPal": "PayPal",
}


st.set_page_config(
    page_title="Ventas e-commerce 2024",
    page_icon="📊",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Formato de números (estilo español: 80.567,85)
# ---------------------------------------------------------------------------

def formato_numero(valor, decimales=2):
    """Devuelve el número con punto de miles y coma decimal."""
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def formato_euros(valor):
    """80567.85 -> '80.567,85 €' (solo cambia la presentación, no el valor)."""
    return formato_numero(valor) + SUFIJO_MONEDA


def formato_porcentaje(valor, decimales=1):
    """0.434 -> '43,4 %'"""
    return f"{formato_numero(valor * 100, decimales)} %"


def en_espanol(nombre):
    """Traduce una región, categoría o método de pago para mostrarlo."""
    return NOMBRES_ES.get(nombre, nombre)


def nombre_mes(periodo):
    """Period mensual -> 'enero de 2024'."""
    return f"{MESES_LARGOS[periodo.month - 1]} de {periodo.year}"


# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------

@st.cache_data
def cargar_datos(ruta):
    """Lee el CSV limpio con leer_csv() y añade columnas de fecha auxiliares."""
    df = leer_csv(ruta)
    if df is None:
        return None
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["Mes"] = df["Date"].dt.to_period("M")
    return df


def filtrar(df, regiones, categorias, mes_inicio, mes_fin):
    """Devuelve solo las filas que cumplen los tres filtros."""
    mascara = (
        df["Region"].isin(regiones)
        & df["Product Category"].isin(categorias)
        & df["Mes"].between(mes_inicio, mes_fin)
    )
    return df[mascara]


# ---------------------------------------------------------------------------
# Cálculos adicionales (los que no están en calculos.py)
# ---------------------------------------------------------------------------

def unidades_por_categoria(df):
    """Unidades vendidas por categoría, de mayor a menor."""
    return df.groupby("Product Category")["Units Sold"].sum().sort_values(ascending=False)


def dias_con_ventas_por_mes(df):
    """Número de días distintos con ventas en cada mes."""
    return df.groupby("Mes")["Date"].nunique()


def ventas_mensuales_completas(df, mes_inicio, mes_fin):
    """ventas_por_mes() con todos los meses del periodo (0 si un mes no tiene ventas)."""
    meses = pd.period_range(mes_inicio, mes_fin, freq="M")
    return ventas_por_mes(df).reindex(meses, fill_value=0)


def cuota(serie):
    """Peso del primer elemento de una serie ordenada sobre el total."""
    total = serie.sum()
    return serie.iloc[0] / total if total else 0


# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    /* Ancho del contenido: ~88 % de la pantalla en escritorio, centrado.
       En pantallas grandes se limita para que las líneas no queden demasiado largas. */
    [data-testid="stMainBlockContainer"], .block-container {
        width: 100%;
        max-width: min(88vw, 2000px);
        margin-inline: auto;
        padding: 2.2rem 1.5rem 3rem 1.5rem;
    }
    /* Tablet: se aprovecha todo el ancho con un margen fijo */
    @media (max-width: 1024px) {
        [data-testid="stMainBlockContainer"], .block-container {
            max-width: 100%;
            padding-left: 1.5rem; padding-right: 1.5rem;
        }
    }
    /* Móvil: márgenes más estrechos */
    @media (max-width: 640px) {
        [data-testid="stMainBlockContainer"], .block-container {
            padding: 1.5rem 1rem 2.5rem 1rem;
        }
    }
    /* Valores comunes a todas las tarjetas: mismo borde, radio y espaciado */
    :root {
        --radio: 12px;
        --borde: 1px solid #e1e0d9;
        --hueco: 1rem;
        --texto: #0b0b0b;
        --texto-2: #52514e;
        --texto-3: #898781;
        --azul: #2a78d6;
    }
    h1, h2, h3 { letter-spacing: -0.01em; }

    /* Contenedores con borde de Streamlit (filtros y gráficos) */
    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stExpander"] details { border-radius: var(--radio) !important; }

    /* En móvil, los botones de los filtros pasan a la línea siguiente en vez de desplazarse */
    [data-testid="stButtonGroup"] > div { flex-wrap: wrap; overflow-x: visible; row-gap: 0.4rem; }

    /* ---- Cabecera ---- */
    .cabecera {
        display: flex; flex-wrap: wrap; align-items: flex-end;
        justify-content: space-between; gap: 0.75rem 2rem;
        margin-bottom: 1.25rem;
    }
    .encabezado-etiqueta {
        font-size: 0.75rem; font-weight: 600; letter-spacing: 0.06em;
        text-transform: uppercase; color: var(--azul); margin-bottom: 0.3rem;
    }
    .encabezado-titulo {
        font-size: clamp(1.7rem, 3vw, 2.25rem); font-weight: 700;
        color: var(--texto); line-height: 1.15; margin: 0;
    }
    .encabezado-sub { color: var(--texto-2); font-size: 0.95rem; margin: 0.35rem 0 0 0; }
    .aviso-demo {
        display: flex; gap: 0.5rem; align-items: flex-start;
        max-width: 24rem; font-size: 0.78rem; line-height: 1.4; color: var(--texto-2);
        background: #ffffff; border: var(--borde); border-radius: var(--radio);
        padding: 0.55rem 0.8rem;
    }
    .aviso-demo b { color: var(--texto); font-weight: 600; }
    .aviso-icono {
        flex: none; width: 1.1rem; height: 1.1rem; border-radius: 50%;
        background: rgba(42,120,214,0.12); color: var(--azul);
        font-size: 0.72rem; font-weight: 700; text-align: center; line-height: 1.1rem;
    }

    /* ---- Filtros (compactos) ---- */
    .st-key-filtros { padding: 0.75rem 1rem !important; gap: 0.5rem; }
    .st-key-filtros [data-testid="stWidgetLabel"] p {
        font-size: 0.78rem; font-weight: 600; color: var(--texto-2);
    }
    /* El botón se alinea con los controles, no con las etiquetas */
    .st-key-restablecer { margin-top: 1.7rem; }
    .st-key-restablecer button { width: 100%; white-space: nowrap; }
    @media (max-width: 640px) { .st-key-restablecer { margin-top: 0; } }

    /* ---- KPIs ---- */
    .kpis {
        display: grid; gap: var(--hueco); margin: var(--hueco) 0;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    }
    .kpi {
        background: #ffffff; border: var(--borde); border-radius: var(--radio);
    }
    .kpi { padding: 1rem 1.25rem; }
    .kpi-etiqueta {
        font-size: 0.75rem; font-weight: 600; letter-spacing: 0.05em;
        text-transform: uppercase; color: var(--texto-2);
    }
    .kpi-valor {
        font-size: clamp(1.75rem, 2.6vw, 2.2rem); font-weight: 700;
        color: var(--texto); margin-top: 0.4rem; line-height: 1.1;
        font-variant-numeric: tabular-nums; letter-spacing: -0.02em;
    }
    .kpi-unidad {
        font-size: 0.9rem; font-weight: 500; color: var(--texto-3);
        margin-left: 0.3rem; letter-spacing: 0;
    }
    .kpi-nota { font-size: 0.78rem; color: var(--texto-3); margin-top: 0.4rem; }

    /* ---- Gráficos ---- */
    .titulo-grafico { font-size: 1.1rem; font-weight: 600; color: var(--texto); margin: 0; }
    .sub-grafico { font-size: 0.82rem; color: var(--texto-3); margin: 0.1rem 0 0 0; }

    /* ---- Conclusiones ---- */
    .titulo-seccion { font-size: 1.45rem; font-weight: 650; color: var(--texto); margin: 1.75rem 0 0 0; }
    .sub-seccion { font-size: 0.92rem; color: var(--texto-3); margin: 0.2rem 0 0.85rem 0; }
    .insights {
        display: grid; gap: var(--hueco);
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    }
    /* Las cuatro tarjetas comparten el mismo acento azul (fondo claro, borde e icono) */
    .insight {
        --acento: #2a78d6; --acento-texto: #1f5fae; --fondo-acento: #f5f9fe;
        --borde-acento: #d6e5f7; --chip: #e2edfb;
        padding: 1rem 1.15rem 1.05rem 1.15rem; border-radius: var(--radio);
        background: var(--fondo-acento); border: 1px solid var(--borde-acento);
    }
    .insight-cabecera { display: flex; align-items: center; gap: 0.55rem; }
    .insight-icono {
        flex: none; width: 1.9rem; height: 1.9rem; border-radius: 8px;
        background: var(--chip); color: var(--acento);
        display: flex; align-items: center; justify-content: center;
    }
    .insight-icono svg { width: 1.05rem; height: 1.05rem; }
    .insight-titulo { font-size: 0.78rem; font-weight: 600; color: var(--acento-texto); }
    .insight-dato {
        font-size: 1.35rem; font-weight: 700; color: var(--texto); line-height: 1.2;
        letter-spacing: -0.01em; margin: 0.7rem 0 0.3rem 0;
    }
    .insight-texto { font-size: 0.8rem; color: var(--texto-2); line-height: 1.5; }

    /* En escritorio, las cuatro tarjetas siempre en una fila */
    @media (min-width: 1100px) {
        .kpis, .insights { grid-template-columns: repeat(4, 1fr); }
    }

    .nota-datos {
        font-size: 0.82rem; color: var(--texto-2); background: #f0efec;
        border-radius: var(--radio); padding: 0.75rem 1rem; margin-top: var(--hueco); line-height: 1.5;
    }
    .pie {
        font-size: 0.78rem; color: var(--texto-3); margin-top: 2.5rem;
        padding-top: 1rem; border-top: var(--borde); line-height: 1.6;
    }
    .pie a { color: var(--texto-2); }
    </style>
    """,
    unsafe_allow_html=True,
)


def titulo_grafico(titulo, subtitulo):
    st.markdown(
        f'<div class="titulo-grafico">{titulo}</div><div class="sub-grafico">{subtitulo}</div>',
        unsafe_allow_html=True,
    )


def tarjeta_kpi(etiqueta, valor, unidad, nota):
    unidad_html = f'<span class="kpi-unidad">{unidad}</span>' if unidad else ""
    return (
        f'<div class="kpi"><div class="kpi-etiqueta">{etiqueta}</div>'
        f'<div class="kpi-valor">{valor}{unidad_html}</div>'
        f'<div class="kpi-nota">{nota}</div></div>'
    )


# Iconos de las conclusiones (SVG en línea, sin dependencias): trazos de 24x24
ICONOS = {
    "categoria": '<path d="M3 12V4a1 1 0 0 1 1-1h8l9 9-9 9z"/><circle cx="7.5" cy="7.5" r="1.5"/>',
    "region": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
    "mes": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "sube": '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
    "baja": '<path d="M3 7l6 6 4-4 8 8"/><path d="M15 17h6v-6"/>',
}


def tarjeta_insight(titulo, dato, texto, icono):
    """icono: clave de ICONOS."""
    svg = (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONOS[icono]}</svg>'
    )
    return (
        f'<div class="insight">'
        f'<div class="insight-cabecera"><span class="insight-icono">{svg}</span>'
        f'<span class="insight-titulo">{titulo}</span></div>'
        f'<div class="insight-dato">{dato}</div><div class="insight-texto">{texto}</div></div>'
    )


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------

datos = cargar_datos(RUTA_CSV)
if datos is None:
    st.error(f"No se encontró el archivo de datos: `{RUTA_CSV}`")
    st.stop()

meses_disponibles = sorted(datos["Mes"].unique())
fecha_min = datos["Date"].min()
fecha_max = datos["Date"].max()
ultimo_mes = meses_disponibles[-1]
# Si el último mes no tiene datos hasta su último día, lo marcamos como incompleto
mes_incompleto = ultimo_mes if fecha_max < ultimo_mes.end_time.normalize() else None

# ---------------------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------------------

st.markdown(
    f"""
    <div class="cabecera">
        <div>
            <div class="encabezado-etiqueta">Análisis de ventas · E-commerce</div>
            <div class="encabezado-titulo">Ventas del marketplace 2024</div>
            <div class="encabezado-sub">
                {formato_numero(len(datos), 0)} transacciones entre el
                {fecha_min.day} de {MESES_LARGOS[fecha_min.month - 1]} y el
                {fecha_max.day} de {MESES_LARGOS[fecha_max.month - 1]} de {fecha_max.year}
            </div>
        </div>
        <div class="aviso-demo">
            <span class="aviso-icono">i</span>
            <span><b>Proyecto demostrativo.</b> Datos de ejemplo: no representan
            ventas reales de una empresa.</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Filtros
# ---------------------------------------------------------------------------

regiones_todas = sorted(datos["Region"].unique())
categorias_todas = sorted(datos["Product Category"].unique())

# Para restablecer los filtros cambiamos su clave: Streamlit los vuelve a crear
# con los valores por defecto (todas las regiones, categorías y meses)
st.session_state.setdefault("version_filtros", 0)


def restablecer_filtros():
    st.session_state["version_filtros"] += 1


version = st.session_state["version_filtros"]

with st.container(border=True, key="filtros"):
    col_region, col_categoria, col_periodo, col_boton = st.columns(
        [1.2, 2.4, 1.6, 0.8], gap="medium",
    )
    with col_region:
        regiones = st.pills(
            "Región", regiones_todas, selection_mode="multi",
            default=regiones_todas, format_func=en_espanol,
            key=f"filtro_regiones_{version}",
        )
    with col_categoria:
        categorias = st.pills(
            "Categoría", categorias_todas, selection_mode="multi",
            default=categorias_todas, format_func=en_espanol,
            key=f"filtro_categorias_{version}",
        )
    with col_periodo:
        mes_inicio, mes_fin = st.select_slider(
            "Periodo", options=meses_disponibles,
            value=(meses_disponibles[0], meses_disponibles[-1]),
            format_func=etiqueta_mes, key=f"filtro_periodo_{version}",
        )
    with col_boton:
        st.button("Restablecer", key="restablecer", on_click=restablecer_filtros,
                  icon=":material/restart_alt:", help="Volver a mostrar todos los datos")

if not regiones or not categorias:
    st.info("Selecciona al menos una región y una categoría para ver los resultados.")
    st.stop()

df = filtrar(datos, regiones, categorias, mes_inicio, mes_fin)

if df.empty:
    st.warning(
        "No hay ventas para esta combinación de filtros. En este dataset cada "
        "categoría se vende en una única región, así que algunas combinaciones "
        "de región y categoría no tienen datos."
    )
    st.stop()

# ---------------------------------------------------------------------------
# KPIs (funciones de calculos.py sobre los datos filtrados)
# ---------------------------------------------------------------------------

ingresos = calcular_ingresos_totales(df)
ticket = calcular_ticket_medio(df)
unidades = calcular_unidades_vendidas(df)
transacciones = calcular_transacciones(df)

st.markdown(
    '<div class="kpis">'
    + tarjeta_kpi("Ingresos totales", formato_numero(ingresos), MONEDA,
                  f"{formato_numero(df['Date'].nunique(), 0)} días con ventas")
    + tarjeta_kpi("Ticket medio", formato_numero(ticket), MONEDA,
                  "ingresos por transacción")
    + tarjeta_kpi("Unidades vendidas", formato_numero(unidades, 0), "uds.",
                  f"{formato_numero(df['Product Name'].nunique(), 0)} productos distintos")
    + tarjeta_kpi("Transacciones", formato_numero(transacciones, 0), "",
                  f"{formato_numero(unidades / transacciones, 1)} unidades por transacción")
    + "</div>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------

mensual = ventas_mensuales_completas(df, mes_inicio, mes_fin)
dias = dias_con_ventas_por_mes(df)
# Las etiquetas se traducen solo para mostrarlas; los valores salen de calculos.py
por_region = ventas_por_region(df).rename(index=en_espanol)
por_categoria = ventas_por_categoria(df).rename(index=en_espanol)
unidades_categoria = unidades_por_categoria(df).rename(index=en_espanol)
top_productos = ventas_por_producto(df)

col_mes, col_region = st.columns([2, 1], gap="medium")

with col_mes:
    with st.container(border=True):
        subtitulo = f"Ingresos por mes, en {MONEDA}"
        if mes_incompleto is not None and mes_incompleto in mensual.index:
            subtitulo += (f" · {etiqueta_mes(mes_incompleto)} solo incluye datos hasta el día "
                          f"{fecha_max.day}")
        titulo_grafico("Evolución mensual", subtitulo)
        st.plotly_chart(
            grafico_evolucion_mensual(mensual, dias, mes_incompleto, alto=400),
            config=CONFIG, width="stretch",
        )

with col_region:
    with st.container(border=True):
        titulo_grafico("Ventas por región", f"Ingresos en {MONEDA} y peso sobre el total")
        cuotas_region = (por_region / por_region.sum()).map(
            lambda c: f"<br>Peso: {formato_porcentaje(c)}"
        )
        st.plotly_chart(
            grafico_barras_horizontales(
                por_region, 400, ",.2f", "Ingresos", info_extra=cuotas_region,
                sufijo=SUFIJO_MONEDA,
            ),
            config=CONFIG, width="stretch",
        )

col_cat, col_top = st.columns(2, gap="medium")

with col_cat:
    with st.container(border=True):
        titulo_grafico("Ventas por categoría", "Ordenadas de mayor a menor")
        medida = st.segmented_control(
            "Medida", ["Ingresos", "Unidades"], default="Ingresos",
            label_visibility="collapsed", key="medida_categoria",
        )
        if medida == "Unidades":
            extra = por_categoria.map(lambda v: f"<br>Ingresos: {formato_euros(v)}")
            fig_categoria = grafico_barras_horizontales(
                unidades_categoria, 360, ",d", "Unidades", info_extra=extra,
            )
        else:
            extra = unidades_categoria.map(lambda v: f"<br>Unidades: {formato_numero(v, 0)}")
            fig_categoria = grafico_barras_horizontales(
                por_categoria, 360, ",.2f", "Ingresos", info_extra=extra,
                sufijo=SUFIJO_MONEDA,
            )
        st.plotly_chart(fig_categoria, config=CONFIG, width="stretch")

with col_top:
    with st.container(border=True):
        titulo_grafico("Top 10 productos", f"Productos con más ingresos, en {MONEDA}")
        categoria_producto = (
            df.drop_duplicates("Product Name").set_index("Product Name")["Product Category"]
            .map(lambda c: f"<br>Categoría: {en_espanol(c)}")
        )
        st.plotly_chart(
            grafico_barras_horizontales(
                top_productos, 412, ",.2f", "Ingresos", info_extra=categoria_producto,
                sufijo=SUFIJO_MONEDA,
            ),
            config=CONFIG, width="stretch",
        )

# ---------------------------------------------------------------------------
# Conclusiones (se recalculan con los filtros)
# ---------------------------------------------------------------------------

st.markdown(
    '<div class="titulo-seccion">Conclusiones</div>'
    '<div class="sub-seccion">Se recalculan con los filtros aplicados. '
    'Describen los datos; no explican sus causas.</div>',
    unsafe_allow_html=True,
)

tarjetas = []

texto_cat = f"{formato_porcentaje(cuota(por_categoria))} de los ingresos del periodo."
if unidades_categoria.index[0] != por_categoria.index[0]:
    texto_cat += (f" En unidades lidera {escape(unidades_categoria.index[0])}: más volumen "
                  f"no implica más facturación.")
tarjetas.append(tarjeta_insight("Categoría que más factura",
                                escape(por_categoria.index[0]), texto_cat,
                                "categoria"))

tarjetas.append(tarjeta_insight(
    "Región con más ingresos", escape(por_region.index[0]),
    f"{formato_porcentaje(cuota(por_region))} del total, "
    f"{formato_euros(por_region.iloc[0])} en ingresos.",
    "region",
))

mes_max = mensual.idxmax()
tarjetas.append(tarjeta_insight(
    "Mes con mayor facturación", nombre_mes(mes_max).capitalize(),
    f"{formato_euros(mensual[mes_max])} en ingresos, "
    f"{formato_porcentaje(mensual[mes_max] / mensual.sum())} del periodo.",
    "mes",
))

# Evolución: comparamos la media diaria del primer y último mes, para no
# penalizar a un mes incompleto (agosto solo tiene datos hasta el día 27)
meses_con_ventas = [m for m in mensual.index if dias.get(m, 0) > 0]
if len(meses_con_ventas) >= 2:
    primero, ultimo = meses_con_ventas[0], meses_con_ventas[-1]
    media_primero = mensual[primero] / dias[primero]
    media_ultimo = mensual[ultimo] / dias[ultimo]
    variacion = media_ultimo / media_primero - 1
    tendencia = "baja" if variacion < 0 else "sube"
    tarjetas.append(tarjeta_insight(
        "Evolución del periodo",
        f"{'−' if variacion < 0 else '+'}{formato_porcentaje(abs(variacion))} en ingreso diario",
        f"La media diaria {tendencia} de {formato_euros(media_primero)} "
        f"({MESES_LARGOS[primero.month - 1]}) a {formato_euros(media_ultimo)} "
        f"({MESES_LARGOS[ultimo.month - 1]}).",
        "baja" if variacion < 0 else "sube",
    ))
else:
    tarjetas.append(tarjeta_insight(
        "Evolución del periodo", "—",
        "Selecciona al menos dos meses con ventas para ver la evolución.",
        "sube",
    ))

st.markdown(f'<div class="insights">{"".join(tarjetas)}</div>', unsafe_allow_html=True)

# Nota sobre la estructura del dataset (se calcula sobre los datos completos)
una_region_por_categoria = datos.groupby("Product Category")["Region"].nunique().max() == 1
una_venta_por_dia = datos["Date"].is_unique
if una_region_por_categoria or una_venta_por_dia:
    partes = []
    if una_venta_por_dia:
        partes.append("hay exactamente una transacción por día")
    if una_region_por_categoria:
        partes.append(
            "cada categoría se vende en una única región, por lo que las diferencias "
            "entre regiones reflejan sobre todo la mezcla de categorías y no se pueden "
            "separar de ellas"
        )
    st.markdown(
        f'<div class="nota-datos"><b>Sobre los datos.</b> En este dataset '
        f'{" y ".join(partes)}. Es una estructura típica de datos sintéticos.</div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Tabla con los datos filtrados
# ---------------------------------------------------------------------------

st.write("")
with st.expander(f"Ver las {formato_numero(len(df), 0)} transacciones filtradas"):
    tabla = df.drop(columns=["Mes"]).sort_values("Date")
    # Solo cambia cómo se muestran: textos en español e importes como 1.234,56
    tabla[["Product Category", "Region", "Payment Method"]] = (
        tabla[["Product Category", "Region", "Payment Method"]].map(en_espanol)
    )
    tabla_formateada = tabla.style.format({
        "Date": lambda fecha: fecha.strftime("%d/%m/%Y"),
        "Unit Price": formato_numero,
        "Total Revenue": formato_numero,
    })
    st.dataframe(
        tabla_formateada,
        hide_index=True,
        width="stretch",
        height=420,
        column_order=["Transaction ID", "Date", "Product Name", "Product Category",
                      "Units Sold", "Unit Price", "Total Revenue", "Region",
                      "Payment Method"],
        column_config={
            "Transaction ID": st.column_config.NumberColumn("ID", format="%d", width="small"),
            "Date": st.column_config.Column("Fecha", width="small"),
            "Product Name": st.column_config.Column("Producto", width="large"),
            "Product Category": "Categoría",
            "Units Sold": st.column_config.NumberColumn("Unidades", width="small"),
            "Unit Price": f"Precio unitario ({MONEDA})",
            "Total Revenue": f"Ingresos ({MONEDA})",
            "Region": "Región",
            "Payment Method": "Método de pago",
        },
    )

# ---------------------------------------------------------------------------
# Pie
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="pie">
        Fuente: <a href="https://www.kaggle.com/datasets/shreyanshverma27/online-sales-dataset-popular-marketplace-data"
        target="_blank">Online Sales Dataset — Popular Marketplace Data</a> (Kaggle).
        El dataset no indica la divisa: los importes se muestran en euros (€) solo a efectos de presentación.<br>
        Proyecto de portfolio con fines demostrativos. Los datos parecen sintéticos y no
        representan necesariamente las ventas reales de ninguna empresa.<br>
        Hecho con Python, Pandas, Plotly y Streamlit.
    </div>
    """,
    unsafe_allow_html=True,
)
