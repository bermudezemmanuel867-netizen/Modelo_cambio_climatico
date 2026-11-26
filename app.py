import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Impacto del Cambio Climático", layout="wide")
st.title("🌍 Dashboard de Impacto del Cambio Climático")


# 1. Cargar datos
@st.cache_data
def cargar_datos():
    # Cambia "tus_datos.csv" por el nombre real de tu archivo (o pd.read_json)
    return pd.read_csv("Dataset_Climatico_Mexico_2013_2030.csv")


df_raw = cargar_datos()

# Lista exacta de tus columnas climáticas
COLUMNAS_CLIMA = [
    "Hectareas_Cultivo_Perdidas",
    "Desplazados_Climaticos",
    "Emisiones_CO2_ton",
    "Temperatura_C",
    "Almacenamiento_Presas_Porcentaje",
    "Presion_Atmosferica_hPa",
]

# --- SECCIÓN 1: LIMPIEZA DE DATOS (NULOS Y DUPLICADOS) ---
with st.expander("🧹 Diagnóstico de Calidad de Datos (Nulos y Duplicados)"):
    total_filas = len(df_raw)
    duplicados = df_raw.duplicated().sum()
    nulos_total = df_raw.isnull().sum().sum()

    q1, q2, q3 = st.columns(3)
    q1.metric("Registros originales", f"{total_filas:,}")
    q2.metric("Filas duplicadas", f"{duplicados:,}")
    q3.metric("Celdas nulas totales", f"{nulos_total:,}")

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.write("**Nulos por columna:**")
        df_nulos = pd.DataFrame({
            "Columna": df_raw.columns,
            "Nulos": df_raw.isnull().sum().values,
            "%": (df_raw.isnull().sum().values / total_filas * 100).round(2),
        })
        st.dataframe(df_nulos, use_container_width=True, hide_index=True)

    with col_t2:
        st.write("**Registros duplicados:**")
        if duplicados > 0:
            st.dataframe(
                df_raw[df_raw.duplicated(keep=False)], use_container_width=True
            )
        else:
            st.success("Sin filas duplicadas.")

# Controles de limpieza en la barra lateral
st.sidebar.header("⚙️ Limpieza de Datos")
quitar_duplicados = st.sidebar.checkbox("Eliminar duplicados", value=True)
manejo_nulos = st.sidebar.radio(
    "Tratamiento de valores nulos:",
    [
        "Mantener original",
        "Eliminar filas con nulos",
        "Rellenar con la media",
    ],
)

df = df_raw.copy()
if quitar_duplicados:
    df = df.drop_duplicates()

if manejo_nulos == "Eliminar filas con nulos":
    df = df.dropna()
elif manejo_nulos == "Rellenar con la media":
    cols_num = df.select_dtypes(include="number").columns
    df[cols_num] = df[cols_num].fillna(df[cols_num].mean())

# --- SECCIÓN 2: INDICADORES CLAVE DE IMPACTO (KPIs) ---
st.header("📌 Resumen General de Impacto")
k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Cultivos Perdidos (Total)",
    f"{df['Hectareas_Cultivo_Perdidas'].sum():,.0f} ha",
)
k2.metric(
    "Desplazados Climáticos", f"{df['Desplazados_Climaticos'].sum():,.0f}"
)
k3.metric("Temperatura Promedio", f"{df['Temperatura_C'].mean():.2f} °C")
k4.metric(
    "Almacenamiento Presas (Prom.)",
    f"{df['Almacenamiento_Presas_Porcentaje'].mean():.1f} %",
)

st.divider()

# --- SECCIÓN 3: GRÁFICAS DE DISPERSIÓN (CAUSA Y EFECTO) ---
st.header("📈 Análisis de Dispersión y Correlación")

# Filtrar solo las columnas que realmente existen en el dataframe
cols_disponibles = [c for c in COLUMNAS_CLIMA if c in df.columns]
cols_extra = [
    c
    for c in df.columns
    if c not in COLUMNAS_CLIMA and df[c].dtype == "object"
]

c_x, c_y, c_color = st.columns(3)
with c_x:
    eje_x = st.selectbox(
        "Variable Causa (Eje X):",
        cols_disponibles,
        index=cols_disponibles.index("Temperatura_C"),
    )
with c_y:
    eje_y = st.selectbox(
        "Variable Efecto (Eje Y):",
        cols_disponibles,
        index=cols_disponibles.index("Hectareas_Cultivo_Perdidas"),
    )
with c_color:
    opciones_color = ["Ninguno"] + cols_extra + cols_disponibles
    color_var = st.selectbox(
        "Color / Tercera variable:", opciones_color
    )

color_seleccionado = None if color_var == "Ninguno" else str(color_var)

fig_scatter = px.scatter(
    df,
    x=eje_x,
    y=eje_y,
    color=color_seleccionado,
    trendline="ols",
    title=f"Relación: {eje_x} vs. {eje_y}",
    opacity=0.75,
    color_continuous_scale="RdYlBu_r",
)

st.plotly_chart(fig_scatter, use_container_width=True)

# --- SECCIÓN 4: MATRIZ DE CORRELACIÓN Y COMPARATIVAS RÁPIDAS ---
col_izq, col_der = st.columns(2)

with col_izq:
    st.subheader("🔥 Matriz de Correlación")
    corr = df[cols_disponibles].corr().round(2)
    fig_corr = px.imshow(
        corr,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title="Correlación entre variables climáticas",
    )
    st.plotly_chart(fig_corr, use_container_width=True)

with col_der:
    st.subheader("💧 Presas vs. Desplazamiento")
    fig_presas = px.scatter(
        df,
        x="Almacenamiento_Presas_Porcentaje",
        y="Desplazados_Climaticos",
        size="Hectareas_Cultivo_Perdidas",
        color="Temperatura_C",
        color_continuous_scale="OrRd",
        title="Nivel de Presas vs. Desplazados (Tamaño = Cultivos Perdidos)",
    )
    st.plotly_chart(fig_presas, use_container_width=True)

# --- SECCIÓN 5: DATOS LIMPIOS ---
with st.expander("📋 Ver tabla de datos procesados"):
    st.dataframe(df, use_container_width=True)
