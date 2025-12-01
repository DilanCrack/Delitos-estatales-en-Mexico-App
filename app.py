import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(layout="wide")

with open("styles-ppp.css") as css_file:
    st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)

st.markdown(
    """
    <style>
        :root {
            --bg-color: #d6c3c5;      /* rojo claro (fondo) */
            --title-color: #40010D;   /* dark (títulos) */
            --accent-color: #4E342E;  /* acento (botones) */
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Delitos estatales en México")

try:
    df = pd.read_csv("estataldelitos.csv", encoding='latin-1')
    st.markdown(
        '<p class="ok-msg">Datos cargados correctamente</p>',
        unsafe_allow_html=True
    )
except Exception as e:
    st.error(f" Error al cargar los datos: {e}")
    st.stop()  # Detiene la ejecución del dashboard si falla

# Convertir columnas mensuales a numéricas y crear total anual
meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio',
         'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
for mes in meses:
    df[mes] = pd.to_numeric(df[mes], errors='coerce')
df['Total_Anual'] = df[meses].sum(axis=1)


# Métricas generales
st.subheader("Métricas generales")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Registros analizados", f"{len(df):,}")
with col2:
    st.metric("Delitos totales registrados", f"{int(df['Total_Anual'].sum()):,}")
with col3:
    st.metric("Delitos promedio por registro", f"{df['Total_Anual'].mean():.2f}")

# Filtros interactivos
st.subheader("Filtros de análisis")

filter_col1, filter_col2, filter_col3 = st.columns(3)
with filter_col1:
    selected_year = st.selectbox("Selecciona un año", ["Todos los años"] + sorted(df["Año"].unique()))  # Añadido "Todos los años"
with filter_col2:
    selected_entity = st.selectbox("Selecciona una entidad", ["Todas"] + sorted(df["Entidad"].unique()))
with filter_col3:
    selected_metric = st.selectbox("Selecciona un periodo", ["Total_Anual"] + meses)


# Aplicar filtros
if selected_year == "Todos los años":
    filtered_df = df  # Muestra todos los datos si se selecciona "Todos los años"
else:
    filtered_df = df[df["Año"] == selected_year]  # Filtra por el año seleccionado

if selected_entity != "Todas":
    filtered_df = filtered_df[filtered_df["Entidad"] == selected_entity]

# Limitar a los meses que tienen datos
meses_disponibles = [m for m in meses if filtered_df[m].notna().any()]

# Nota si el año no tiene los 12 meses
if len(meses_disponibles) < 12:
    st.caption(f"Nota: {selected_year} tiene datos hasta {meses_disponibles[-1]}. Las cifras mostradas son acumuladas (YTD).")

# Ordenar los meses cronológicamente
orden_meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
               'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

# Pestañas para las visualizaciones
tab1, tab2, tab3 = st.tabs(["Evolución temporal de delitos", "Comparación por tipo de delito", "Total de delitos por entidad"])

# Pestaña 1 - Evolución temporal de delitos
with tab1:
    st.subheader("Evolución temporal de delitos")
    df_line = filtered_df.melt(
        id_vars=["Año", "Entidad"],
        value_vars=meses_disponibles,  # Aquí usamos meses_disponibles
        var_name="Mes",
        value_name="Casos"
    )
    df_line['Mes'] = pd.Categorical(df_line['Mes'], categories=orden_meses, ordered=True)  # Asegurarse de ordenar cronológicamente
    df_line = df_line.sort_values('Mes')  # Ordenar los meses cronológicamente
    
    df_line['Casos'].fillna(0, inplace=True)  # Rellenar los valores nulos con 0

    fig_line = px.line(
        df_line.groupby("Mes")["Casos"].sum().reset_index(),
        x="Mes",
        y="Casos",
        markers=True,
        title=f"Evolución mensual de delitos en {selected_year}"
    )

    fig_line.update_layout(
        plot_bgcolor='#d6b8bc',      # fondo del área de la gráfica
        paper_bgcolor='#d6b8bc',  # deja el “papel” transparente para que se mezcle con la app
        font_color='#40010D',        # textos en DARK
        title_font=dict(color='#40010D')  # título en DARK
    )

    fig_line.update_xaxes(
        title_font=dict(color='#40010D'),   # título eje X ("Mes")
        tickfont=dict(color='#40010D')      # etiquetas de los meses
    )

    fig_line.update_yaxes(
        title_font=dict(color='#40010D'),   # título eje Y ("Casos")
        tickfont=dict(color='#40010D')      # valores numéricos del eje Y
    )

    # Color de la línea
    fig_line.update_traces(
        line=dict(color='#a61929')   # color de la línea
    )

    st.plotly_chart(fig_line, use_container_width=True)

# Pestaña 2 - Comparación por tipo de delito
with tab2:
    st.subheader("Comparación por tipo de delito")

    # Agrupar por tipo de delito y métrica seleccionada
    df_bar = filtered_df.groupby("Tipo de delito")[selected_metric].sum().reset_index()

    # Ordenar y quedarnos con el Top 15
    df_bar = df_bar.sort_values(selected_metric, ascending=False).head(15)

    # Tipo de delito con mayor valor (para resaltarlo)
    max_tipo = df_bar.iloc[0]["Tipo de delito"]

    # Definir color por barra: fuerte para el máximo, claro para el resto
    df_bar["color"] = np.where(
        df_bar["Tipo de delito"] == max_tipo,
        "#a61929",   # rojo fuerte
        "#f4c6cc"    # rojo claro
    )

    # Gráfica de barras HORIZONTAL (mejor para nombres largos)
    fig_bar = px.bar(
        df_bar,
        x=selected_metric,
        y="Tipo de delito",
        orientation="h",
        title=f"Top 15 tipos de delito: {selected_metric} ({selected_year})"
    )

    # Estilo de la gráfica
    fig_bar.update_layout(
        plot_bgcolor='#d6b8bc',
        paper_bgcolor='#d6b8bc',
        font_color='#40010D',
        title_font=dict(color='#40010D'),
        showlegend=False  # ya no usamos leyenda, el color solo indica énfasis
    )

    fig_bar.update_xaxes(
        title_font=dict(color='#40010D'),
        tickfont=dict(color='#40010D')
    )
    fig_bar.update_yaxes(
        title_font=dict(color='#40010D'),
        tickfont=dict(color='#40010D')
    )

    # Aplicar los colores por barra
    fig_bar.update_traces(marker_color=df_bar["color"])

    st.plotly_chart(fig_bar, use_container_width=True)

# Pestaña 3 - Total de delitos por entidad
with tab3:
    st.subheader("Total de delitos por entidad")

    # Base: filtramos por año pero NO por entidad, para poder comparar entre todas
    if selected_year == "Todos los años":
        base_df = df
    else:
        base_df = df[df["Año"] == selected_year]

    # Agrupar según si se eligió métrica mensual o Total_Anual
    if selected_metric in meses:  # Si seleccionamos un mes específico
        df_geo = base_df.groupby("Entidad")[selected_metric].sum().reset_index()
        valor_col = selected_metric
        titulo_geo = f"Top 15 entidades por delitos en {selected_metric} ({selected_year})"
    else:
        df_geo = base_df.groupby("Entidad")["Total_Anual"].sum().reset_index()
        valor_col = "Total_Anual"
        titulo_geo = f"Top 15 entidades por delitos anuales ({selected_year})"

    # Ordenar y quedarnos con el Top 15
    df_geo = df_geo.sort_values(valor_col, ascending=False).head(15)

    # Resaltar siempre la entidad con mayor número de delitos dentro del Top 15
    max_entidad = df_geo.loc[df_geo[valor_col].idxmax(), "Entidad"]

    df_geo["color"] = np.where(
        df_geo["Entidad"] == max_entidad,
        "#a61929",   # entidad con más delitos (rojo fuerte)
        "#f4c6cc"    # resto de entidades (rosa claro)
    )

    # Gráfica de barras HORIZONTAL
    fig_geo = px.bar(
        df_geo,
        x=valor_col,
        y="Entidad",
        orientation="h",
        title=titulo_geo
    )

    # Estilo de la gráfica
    fig_geo.update_layout(
        plot_bgcolor='#d6b8bc',
        paper_bgcolor='#d6b8bc',
        font_color='#40010D',
        title_font=dict(color='#40010D'),
        showlegend=False
    )

    fig_geo.update_xaxes(
        title_font=dict(color='#40010D'),
        tickfont=dict(color='#40010D')
    )
    fig_geo.update_yaxes(
        title_font=dict(color='#40010D'),
        tickfont=dict(color='#40010D')
    )

    # Aplicar los colores por barra
    fig_geo.update_traces(marker_color=df_geo["color"])

    st.plotly_chart(fig_geo, use_container_width=True)
