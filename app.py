import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# Configuración visual moderna
st.set_page_config(
    page_title="Dashboard Sourcing & Producción | Lili Pink",
    layout="wide",
    page_icon="👙"
)

# --- ESTILOS PERSONALIZADOS ---
st.markdown("""
    <style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        border-left: 5px solid #e83e8c;
    }
    </style>
""", unsafe_allow_html=True)

# 🔑 CONFIGURACIÓN DRIVE
ID_GOOGLE_DRIVE = "1llhosnqf0zf7FB8bsXgHtNLzbOjio2ro"
URL_DESCARGA = f"https://drive.google.com/uc?export=download&id={ID_GOOGLE_DRIVE}"

COLUMNAS_SELECCIONADAS = [
    "PLAN", "ORDER DETAIL", "REF", 
    "ESTATUS CHINA COLOMBIA", "ESTADO FINAL COLOMBIA",
    "FECHA DE DESPACHO CHINA COLOMBIA", "MES DE DESPACHO COLOMBIA",
    "COLOMBIA QTY", "COLOMBIA PAQS",
    "UNIDAD DE NEGOCIO", "N. MARCA", "CLASIFICACION DE PRODUCTO",
    "N. SEGMENTO", "CATEGORIA", "SUBCATEGORIA", "LÍNEAS DE PRODUCTO",
    "N. PERFIL", "TIPO DE PRODUCTO", "TIPO DE SILUETA",
    "PRESENTACION DEL PRODUCTO", "TIPO DE REALCE", "N. MATERIALES",
    "ACABADO", "TECNOLOGIA", "N. BENEFICIOS", "FRAGANCIA",
    "COPA", "N. EMPAQUE", "TIPO DE REFERENCIA", "TIPO DE COMPRA"
]

@st.cache_data(ttl=300)
def cargar_datos_optimizados(url):
    try:
        respuesta = requests.get(url)
        respuesta.raise_for_status()
        
        # Lectura con calamine (si está disponible) u openpyxl
        try:
            df = pd.read_excel(BytesIO(respuesta.content), header=1, sheet_name="BASE", engine="calamine")
        except Exception:
            df = pd.read_excel(BytesIO(respuesta.content), header=1, sheet_name="BASE", engine="openpyxl")
        
        df.columns = [str(c).strip().upper() for c in df.columns]
        cols_presentes = [c for c in COLUMNAS_SELECCIONADAS if c in df.columns]
        df = df[cols_presentes]
        
        # Estandarización de textos
        for col in df.columns:
            if col not in ["COLOMBIA QTY", "COLOMBIA PAQS"]:
                df[col] = df[col].astype(str).str.strip().str.upper()
                df[col] = df[col].replace(["NAN", "NONE", "", "NAT"], "SIN ASIGNAR")
        
        # Cantidades numéricas
        for col_num in ["COLOMBIA QTY", "COLOMBIA PAQS"]:
            if col_num in df.columns:
                df[col_num] = pd.to_numeric(df[col_num], errors="coerce").fillna(0)

        return df, None
    except Exception as e:
        return None, f"Error cargando base: {e}"

# --- CARGA DE DATOS ---
with st.spinner("🔄 Conectando con Google Drive..."):
    df, error = cargar_datos_optimizados(URL_DESCARGA)

if error:
    st.error(f"⚠️ {error}")
    st.stop()

# --- BARRA LATERAL: FILTROS DINÁMICOS ---
st.sidebar.title("🎛️ Filtros de Control")

if st.sidebar.button("🔄 Refrescar Datos (Drive)"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")

# Filtros principales
meses = sorted([m for m in df["MES DE DESPACHO COLOMBIA"].unique() if m != "SIN ASIGNAR"]) if "MES DE DESPACHO COLOMBIA" in df.columns else []
mes_sel = st.sidebar.multiselect("📅 Mes Despacho Colombia:", options=meses, default=meses)

marcas = sorted([m for m in df["N. MARCA"].unique() if m != "SIN ASIGNAR"]) if "N. MARCA" in df.columns else []
marca_sel = st.sidebar.multiselect("🏷️ Marca:", options=marcas, default=marcas)

categorias = sorted([c for c in df["CATEGORIA"].unique() if c != "SIN ASIGNAR"]) if "CATEGORIA" in df.columns else []
cat_sel = st.sidebar.multiselect("📂 Categoría:", options=categorias, default=categorias)

tipos = sorted([t for t in df["TIPO DE PRODUCTO"].unique() if t != "SIN ASIGNAR"]) if "TIPO DE PRODUCTO" in df.columns else []
tipo_sel = st.sidebar.multiselect("👙 Tipo de Producto:", options=tipos, default=tipos)

# Buscador de Referencia individual
busqueda_ref = st.sidebar.text_input("🔍 Buscar Referencia específica:", "").strip().upper()

# Aplicación de filtros
df_f = df.copy()
if mes_sel: df_f = df_f[df_f["MES DE DESPACHO COLOMBIA"].isin(mes_sel)]
if marca_sel: df_f = df_f[df_f["N. MARCA"].isin(marca_sel)]
if cat_sel: df_f = df_f[df_f["CATEGORIA"].isin(cat_sel)]
if tipo_sel: df_f = df_f[df_f["TIPO DE PRODUCTO"].isin(tipo_sel)]
if busqueda_ref: df_f = df_f[df_f["REF"].str.contains(busqueda_ref, na=False)]

# --- CABECERA Y KPIS ---
st.title("📊 Panel Ejecutivo de Sourcing & Producción")
st.caption(f"Visualizando **{len(df_f):,}** registros filtrados")

col1, col2, col3, col4 = st.columns(4)
total_qty = int(df_f["COLOMBIA QTY"].sum())
total_paqs = int(df_f["COLOMBIA PAQS"].sum())
total_refs = df_f["REF"].nunique()
total_ops = df_f["ORDER DETAIL"].nunique()

col1.metric("📦 Unidades Totales (QTY)", f"{total_qty:,}")
col2.metric("📦 Paquetes Totales (PAQS)", f"{total_paqs:,}")
col3.metric("🔖 Referencias Únicas", f"{total_refs:,}")
col4.metric("📑 Planes / Órdenes", f"{total_ops:,}")

st.markdown("---")

# --- NAVEGACIÓN EN PESTAÑAS (TABS) ---
tab_resumen, tab_estatus, tab_detalle = st.tabs([
    "📈 Distribución por Producto", 
    "🚢 Estatus Logístico & China", 
    "📋 Detalle de Datos & Descarga"
])

with tab_resumen:
    c_izq, c_der = st.columns(2)
    with c_izq:
        st.subheader("Top 10 Tipos de Producto (Unidades)")
        top_prod = df_f.groupby("TIPO DE PRODUCTO")["COLOMBIA QTY"].sum().nlargest(10)
        st.bar_chart(top_prod)
    
    with c_der:
        st.subheader("Volumen por Categoría")
        cat_vol = df_f.groupby("CATEGORIA")["COLOMBIA QTY"].sum().sort_values(ascending=False)
        st.bar_chart(cat_vol)

with tab_estatus:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Estatus China Colombia")
        estatus_china = df_f.groupby("ESTATUS CHINA COLOMBIA")["COLOMBIA QTY"].sum().sort_values(ascending=False)
        st.bar_chart(estatus_china)
        
    with c2:
        st.subheader("Estado Final Colombia")
        estado_col = df_f.groupby("ESTADO FINAL COLOMBIA")["COLOMBIA QTY"].sum().sort_values(ascending=False)
        st.bar_chart(estado_col)

with tab_detalle:
    st.subheader("Tabla de Registros Filtrados")
    cols_grid = [
        "PLAN", "ORDER DETAIL", "REF", "N. MARCA", "CATEGORIA", 
        "TIPO DE PRODUCTO", "COLOMBIA QTY", "COLOMBIA PAQS",
        "ESTATUS CHINA COLOMBIA", "ESTADO FINAL COLOMBIA", "MES DE DESPACHO COLOMBIA"
    ]
    cols_exist = [c for c in cols_grid if c in df_f.columns]
    
    st.dataframe(
        df_f[cols_exist].sort_values(by="COLOMBIA QTY", ascending=False),
        width="stretch",
        hide_index=True
    )
    
    # Botón de Descarga directa para analistas
    csv_data = df_f[cols_exist].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar datos filtrados (CSV)",
        data=csv_data,
        file_name="reporte_sourcing_filtrado.csv",
        mime="text/csv"
    )
