"""Gráficos Plotly del dashboard.

Cada función recibe una Serie de Pandas ya calculada (por calculos.py o por
app.py) y devuelve una figura con el estilo común del dashboard.
"""

import plotly.graph_objects as go

# Paleta: una sola serie por gráfico, así que todas las marcas usan el azul.
AZUL = "#2a78d6"
AZUL_SUAVE = "rgba(42, 120, 214, 0.10)"
TEXTO = "#0b0b0b"
TEXTO_SECUNDARIO = "#52514e"
TEXTO_APAGADO = "#898781"
REJILLA = "#e1e0d9"
EJE = "#c3c2b7"

# Paleta del modo oscuro (mismos papeles que la clara, con más luminosidad en el azul)
OSCURO = {
    "azul": "#4f93ec",
    "azul_suave": "rgba(79, 147, 236, 0.16)",
    "fondo": "#1c1f24",
    "texto": "#ececea",
    "texto_secundario": "#b9b8b3",
    "texto_apagado": "#8f8e89",
    "rejilla": "#2e3138",
    "eje": "#454a52",
}
FUENTE = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'

# Símbolo de moneda de los importes (solo presentación: los valores no se convierten).
# Va unido a la cifra con un espacio que no se parte: "80.567,85 €"
MONEDA = "€"
SUFIJO_MONEDA = chr(0xA0) + MONEDA  # espacio de no separación

# Opciones del componente: sin barra de herramientas, solo el tooltip.
CONFIG = {"displayModeBar": False, "responsive": True}

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def etiqueta_mes(periodo):
    """Convierte un Period mensual en un texto corto: 'Ene 2024'."""
    return f"{MESES[periodo.month - 1]} {periodo.year}"


def _recortar(texto, maximo=30):
    """Acorta las etiquetas largas del eje; el nombre completo va en el tooltip."""
    return texto if len(texto) <= maximo else texto[: maximo - 1] + "…"


def _importe(valor):
    """Importe con formato español y dos decimales: 14548.32 -> '14.548,32 €'."""
    texto = f"{valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return texto + SUFIJO_MONEDA


def _estilo_base(fig, alto):
    """Aplica el estilo común: fondo transparente, rejilla discreta y formato español."""
    fig.update_layout(
        height=alto,
        margin=dict(l=8, r=8, t=8, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FUENTE, size=13, color=TEXTO_SECUNDARIO),
        separators=",.",  # decimales con coma y miles con punto
        showlegend=False,
        hoverlabel=dict(
            bgcolor="white", bordercolor=REJILLA,
            font=dict(family=FUENTE, size=13, color=TEXTO),
        ),
        dragmode=False,
    )
    return fig


def grafico_barras_horizontales(serie, alto, formato_valor, nombre_valor,
                                formato_eje=None, info_extra=None, sufijo=""):
    """Barras horizontales ordenadas de mayor a menor, con el valor en el extremo.

    serie: índice = etiquetas, valores = magnitud (ya ordenada de mayor a menor).
    formato_valor: formato d3 del valor, p. ej. ",.2f" o ",d".
    info_extra: Serie opcional con texto adicional para el tooltip.
    sufijo: texto tras cada valor, p. ej. SUFIJO_MONEDA en los importes.
    """
    serie = serie.iloc[::-1]  # Plotly dibuja de abajo arriba: invertimos el orden
    nombres = [str(n) for n in serie.index]
    extra = [info_extra.get(n, "") for n in serie.index] if info_extra is not None else [""] * len(serie)

    fig = go.Figure(go.Bar(
        x=serie.values,
        y=[_recortar(n) for n in nombres],
        orientation="h",
        marker=dict(color=AZUL),
        text=serie.values,
        texttemplate=f"%{{x:{formato_valor}}}{sufijo}",
        textposition="outside",
        textfont=dict(color=TEXTO_SECUNDARIO, size=12),
        cliponaxis=False,
        customdata=list(zip(nombres, extra)),
        hovertemplate=(
            f"<b>%{{customdata[0]}}</b><br>{nombre_valor}: %{{x:{formato_valor}}}{sufijo}"
            "%{customdata[1]}<extra></extra>"
        ),
    ))
    _estilo_base(fig, alto)
    fig.update_layout(margin=dict(r=72))  # sitio para la cifra al final de la barra
    # Barras finas (unos 22 px): el hueco entre barras depende del alto disponible
    alto_banda = (alto - 40) / max(len(serie), 1)
    fig.update_layout(bargap=min(0.85, max(0.25, 1 - 22 / alto_banda)), barcornerradius=4)
    # Sin números en el eje ni rejilla: cada barra ya muestra su valor al final
    fig.update_xaxes(
        showgrid=False, showticklabels=False, zeroline=True,
        zerolinecolor=EJE, tickformat=formato_eje or ",.0f", rangemode="tozero",
        # margen a la derecha para que quepa la etiqueta del extremo
        range=[0, serie.max() * 1.08 if len(serie) else 1],
    )
    fig.update_yaxes(showgrid=False, tickfont=dict(color=TEXTO, size=12), automargin=True)
    return fig


def grafico_evolucion_mensual(ingresos, dias, mes_incompleto=None, alto=360):
    """Línea con la evolución mensual de los ingresos.

    ingresos: Serie con índice Period mensual y los ingresos de cada mes.
    dias: Serie con el número de días con ventas de cada mes (para el tooltip).
    mes_incompleto: Period del último mes si los datos no lo cubren entero.
    alto: altura del gráfico en píxeles.
    """
    etiquetas = [etiqueta_mes(p) for p in ingresos.index]
    media_diaria = [
        ingresos[p] / dias[p] if dias.get(p, 0) else 0 for p in ingresos.index
    ]

    fig = go.Figure(go.Scatter(
        x=etiquetas,
        y=ingresos.values,
        mode="lines+markers",
        line=dict(color=AZUL, width=2, shape="linear"),
        marker=dict(size=9, color=AZUL, line=dict(color="white", width=2)),
        fill="tozeroy",
        fillcolor=AZUL_SUAVE,
        customdata=list(zip(dias.reindex(ingresos.index, fill_value=0).values, media_diaria)),
        hovertemplate=(
            f"<b>%{{x}}</b><br>Ingresos: %{{y:,.2f}}{SUFIJO_MONEDA}"
            "<br>Días con ventas: %{customdata[0]}"
            f"<br>Media diaria: %{{customdata[1]:,.2f}}{SUFIJO_MONEDA}<extra></extra>"
        ),
    ))
    _estilo_base(fig, alto)
    fig.update_layout(hovermode="x")
    fig.update_xaxes(
        showgrid=False, showline=True, linecolor=EJE,
        tickfont=dict(color=TEXTO_APAGADO, size=11), fixedrange=True,
        # en el eje basta el mes abreviado; el año completo aparece en el tooltip
        tickvals=etiquetas, ticktext=[e.split()[0] for e in etiquetas],
        showspikes=True, spikemode="across", spikethickness=1,
        spikecolor=EJE, spikedash="solid",
    )
    fig.update_yaxes(
        showgrid=True, gridcolor=REJILLA, zeroline=False, rangemode="tozero",
        tickformat=",.0f", ticksuffix=SUFIJO_MONEDA,
        tickfont=dict(color=TEXTO_APAGADO, size=11), fixedrange=True,
    )

    # Etiqueta directa solo en el máximo, no en cada punto
    if len(ingresos):
        pos_max = int(ingresos.values.argmax())
        fig.add_annotation(
            x=etiquetas[pos_max], y=ingresos.values[pos_max],
            text=f"Máximo · {_importe(ingresos.values[pos_max])}",
            showarrow=False, yshift=18, font=dict(color=TEXTO, size=12),
        )
    if mes_incompleto is not None and mes_incompleto in ingresos.index:
        fig.add_annotation(
            x=etiqueta_mes(mes_incompleto), y=0, yref="y",
            text=f"{dias[mes_incompleto]} días", showarrow=False,
            yshift=12, font=dict(color=TEXTO_APAGADO, size=11),
        )
    return fig


def aplicar_modo_oscuro(fig):
    """Recolorea una figura ya creada con la paleta oscura (los datos no cambian)."""
    c = OSCURO
    fig.update_layout(
        font_color=c["texto_secundario"],
        hoverlabel=dict(bgcolor=c["fondo"], bordercolor=c["rejilla"], font_color=c["texto"]),
    )
    fig.update_xaxes(gridcolor=c["rejilla"], zerolinecolor=c["eje"], linecolor=c["eje"],
                     spikecolor=c["eje"], tickfont_color=c["texto_apagado"])
    fig.update_yaxes(gridcolor=c["rejilla"], zerolinecolor=c["eje"], linecolor=c["eje"],
                     tickfont_color=c["texto_apagado"])
    for traza in fig.data:
        if traza.type == "bar":
            traza.marker.color = c["azul"]
            traza.textfont.color = c["texto_secundario"]
            # En las barras, el eje vertical lleva los nombres: van con el texto principal
            fig.update_yaxes(tickfont_color=c["texto"])
        else:
            traza.line.color = c["azul"]
            traza.marker.color = c["azul"]
            traza.marker.line.color = c["fondo"]
            traza.fillcolor = c["azul_suave"]
    for anotacion in fig.layout.annotations:
        es_maximo = anotacion.text.startswith("Máximo")
        anotacion.font.color = c["texto"] if es_maximo else c["texto_apagado"]
    return fig
