import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# Configuración visual de la aplicación para Móvil y Web
st.set_page_config(
    page_title="Control Sourcing - Lili Pink",
    layout="wide",
    page_icon="🛍️"
)

# Estilo personalizado para las tarjetas de indicadores
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

st.title("🛍️ Monitor Operativo y Producción - Lili Pink")
st.caption("Visualización en tiempo real desde la nube (Compatible con Celular 📱)")

# 🔑 El ID real de tu archivo de Google Drive
ID_GOOGLE_DRIVE = "1llhosnqf0zf7FB8bsXgHtNLzbOjio2ro" 

# 🌐 URL de descarga directa base para Google Drive
URL_DESCARGA = f"https://drive.google.com/uc?export=download&id={ID_GOOGLE_DRIVE}"

# Columnas clave requeridas para tu dashboard
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

@st.cache_data(ttl=300)  # Cachea por 5 minutos para que cargue al instante
def cargar_datos_desde_drive(url):
    try:
        session = requests.Session()
        
        # Primera petición para obtener el token de confirmación de Google Drive para archivos > 100MB / pesados
        respuesta = session.get(url, stream=True)
        
        token = None
        for key, value in respuesta.cookies.items():
            if key.startswith('download_warning'):
                token = value
                break
        
        if token:
            # Si hay advertencia de tamaño de Drive, añadimos el token para saltarla directamente
            url_confirmacion = url + f"&confirm={token}"
            respuesta = session.get(url_confirmacion, stream=True)
            
        respuesta.raise_for_status()
        
        # Lee el archivo en memoria usando calamine (Rust) u openpyxl según disponibilidad
        # Se apunta a la pestaña "BASE" y toma los encabezados desde la Fila 2 (header=1)
        try:
            df = pd.read_excel(BytesIO(respuesta.content), header=1, sheet_name="BASE", engine="calamine")
        except Exception:
            df = pd.read_excel(BytesIO(respuesta.content), header=1, sheet_name="BASE", engine="openpyxl")
        
        # Normalizar nombres de columnas a mayúsculas y quitar espacios
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Filtrar solo las columnas seleccionadas existentes
        cols_presentes = [c for c in COLUMNAS_SELECCIONADAS if c in df.columns]
        
        if not cols_presentes:
            return pd.DataFrame(), "No se encontraron las columnas clave. Revisa que la pestaña sea la correcta."
            
        df = df[cols_presentes]
        
        # Convertir identificadores y clasificaciones a texto para evitar errores de PyArrow en Streamlit
        for col in df.columns:
            if col not in ["COLOMBIA QTY", "COLOMBIA PAQS"]:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace(["nan", "NAN", "None", "NONE", "", "nat", "NAT"], "SIN ASIGNAR")
        
        # Convertir cantidades numéricas
        for col_num in ["COLOMBIA QTY", "COLOMBIA PAQS"]:
            if col_num in df.columns:
                df[col_num] = pd.to_numeric(df[col_num], errors="coerce").fillna(0)

        return df, None
        
    except requests.exceptions.HTTPError:
        return None, "Error de red: No se pudo descargar el archivo. Verifica el estado compartido de Google Drive."
    except Exception as e:
        return None, f"Error al procesar la base de datos en la nube: {e}"

# --- BOTÓN DE ACTUALIZACIÓN MANUAL EN LA BARRA LATERAL ---
st.sidebar.header("⚙️ Control")
if st.sidebar.button("🔄 Sincronizar con Google Drive"):
    st.cache_data.clear()
    st.rerun()

# --- CARGA CON SPINNER VISUAL ---
with st.spinner("⏳ Descargando base de datos de 34 MB desde Google Drive..."):
    df, error = cargar_datos_desde_drive(URL_DESCARGA)

if error:
    st.error(f"⚠️ {error}")

elif df is not None and not df.empty:
    # --- FILTROS DINÁMICOS EN LA BARRA LATERAL ---
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filtros de Búsqueda")
    
    # 1. Mes de Despacho
    if "MES DE DESPACHO COLOMBIA" in df.columns:
        meses_disp = sorted(list(set([str(m).strip().upper() for m in df["MES DE DESPACHO COLOMBIA"].dropna().unique() if str(m).strip() != "" and str(m).upper() != "SIN ASIGNAR"])))
    else:
        meses_disp = []
    mes_sel = st.sidebar.multiselect("Mes de Despacho:", options=meses_disp, default=meses_disp)
    
    # 2. Tipo de Producto
    if "TIPO DE PRODUCTO" in df.columns:
        tipos_disp = sorted(list(set([str(t).strip().upper() for t in df["TIPO DE PRODUCTO"].dropna().unique() if str(t).strip() != "" and str(t).upper() != "SIN ASIGNAR"])))
    else:
        tipos_disp = []
    tipo_sel = st.sidebar.multiselect("Tipo de Producto:", options=tipos_disp, default=tipos_disp)
    
    # 3. Estado Final Colombia
    if "ESTADO FINAL COLOMBIA" in df.columns:
        estados_disp = sorted(list(set([str(e).strip().upper() for e in df["ESTADO FINAL COLOMBIA"].dropna().unique() if str(e).strip() != "" and str(e).upper() != "SIN ASIGNAR"])))
    else:
        estados_disp = []
    estado_sel = st.sidebar.multiselect("Estado Final Colombia:", options=estados_disp, default=estados_disp)
    
    # Aplicar filtros
    df_filtrado = df.copy()
    if mes_sel and "MES DE DESPACHO COLOMBIA" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["MES DE DESPACHO COLOMBIA"].astype(str).str.upper().isin(mes_sel)]
    if tipo_sel and "TIPO DE PRODUCTO" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["TIPO DE PRODUCTO"].astype(str).str.upper().isin(tipo_sel)]
    if estado_sel and "ESTADO FINAL COLOMBIA" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["ESTADO FINAL COLOMBIA"].astype(str).str.upper().isin(estado_sel)]

    # 📌 KPIS PRINCIPALES (Indicadores Clave)
    st.subheader("📊 Indicadores Clave")
    k1, k2, k3, k4 = st.columns(4)
    
    col_qty = int(df_filtrado['COLOMBIA QTY'].sum()) if 'COLOMBIA QTY' in df_filtrado.columns else 0
    col_paqs = int(df_filtrado['COLOMBIA PAQS'].sum()) if 'COLOMBIA PAQS' in df_filtrado.columns else 0
    ref_unicas = df_filtrado['REF'].nunique() if 'REF' in df_filtrado.columns else 0
    planes_unicos = df_filtrado['ORDER DETAIL'].nunique() if 'ORDER DETAIL' in df_filtrado.columns else 0

    k1.metric("Total Unidades (COL QTY)", f"{col_qty:,}")
    k2.metric("Total Paquetes (COL PAQS)", f"{col_paqs:,}")
    k3.metric("Referencias Únicas", f"{ref_unicas:,}")
    k4.metric("Órdenes / Planes", f"{planes_unicos:,}")

    st.markdown("---")

    # --- PESTAÑAS DEL DASHBOARD ---
    tab_graficos, tab_tabla = st.tabs(["📈 Gráficos del Negocio", "📋 Matriz Detallada"])

    with tab_graficos:
        # 📈 GRÁFICOS (Se apilan automáticamente en la pantalla de un celular)
        col_izq, col_der = st.columns(2)
        with col_izq:
            st.subheader("🧵 Cantidad por Tipo de Producto")
            if 'TIPO DE PRODUCTO' in df_filtrado.columns and 'COLOMBIA QTY' in df_filtrado.columns:
                qty_producto = df_filtrado.groupby("TIPO DE PRODUCTO")["COLOMBIA QTY"].sum().sort_values(ascending=False)
                st.bar_chart(qty_producto)
                
        with col_der:
            st.subheader("🇨🇳 Avance / Estatus China Colombia")
            if 'ESTATUS CHINA COLOMBIA' in df_filtrado.columns and 'COLOMBIA QTY' in df_filtrado.columns:
                qty_estatus = df_filtrado.groupby("ESTATUS CHINA COLOMBIA")["COLOMBIA QTY"].sum().sort_values(ascending=False)
                st.bar_chart(qty_estatus)

    with tab_tabla:
        # 📋 MATRIZ DETALLADA
        st.subheader("🔎 Matriz Detallada")
        columnas_vista = [
            "PLAN", "ORDER DETAIL", "REF", "TIPO DE PRODUCTO", "CATEGORIA",
            "COLOMBIA QTY", "COLOMBIA PAQS", "ESTATUS CHINA COLOMBIA", 
            "ESTADO FINAL COLOMBIA", "FECHA DE DESPACHO CHINA COLOMBIA"
        ]
        cols_a_mostrar = [c for c in columnas_vista if c in df_filtrado.columns]
        
        if cols_a_mostrar:
            st.dataframe(
                df_filtrado[cols_a_mostrar].sort_values(by="COLOMBIA QTY", ascending=False) if "COLOMBIA QTY" in cols_a_mostrar else df_filtrado[cols_a_mostrar],
                width="stretch",
                hide_index=True
            )
            
            # Botón de Descarga directa para analistas
            csv_data = df_filtrado[cols_a_mostrar].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar datos filtrados (CSV)",
                data=csv_data,
                file_name="reporte_sourcing_filtrado.csv",
                mime="text/csv"
            )
else:
    st.info("No se encontraron registros para mostrar.")
