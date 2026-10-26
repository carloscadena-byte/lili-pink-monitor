import streamlit as st
import pandas as pd
import requests
import re
from io import BytesIO

# Configuración visual de la aplicación para Móvil y Web (Ancho completo)
st.set_page_config(
    page_title="Dashboard Sourcing & Producción | Lili Pink & Yoi",
    layout="wide",
    page_icon="🛍️"
)

# --- ESTILIZACIÓN CORPORATIVA LILI PINK & YOI (Fucsia y Blanco) ---
st.markdown("""
    <style>
    /* Fondo principal y textos */
    .main {
        background-color: #fcf8f9;
    }
    /* Encabezado fucsia corporativo */
    .header-box {
        background-color: #d81b60;
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
    }
    /* Estilos de Tarjetas de Métricas (KPIs) */
    .kpi-card {
        background-color: white;
        border: 1px solid #f0b3cd;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        box-shadow: 2px 2px 10px rgba(216, 27, 96, 0.05);
    }
    .kpi-val {
        font-size: 38px;
        font-weight: bold;
        color: #d81b60;
        margin: 0;
    }
    .kpi-lbl {
        font-size: 14px;
        color: #707070;
        text-transform: uppercase;
        font-weight: 600;
        margin-top: 5px;
    }
    /* Subtítulos de Secciones */
    .section-title {
        color: #d81b60;
        font-size: 20px;
        font-weight: bold;
        border-bottom: 2px solid #d81b60;
        padding-bottom: 5px;
        margin-top: 25px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# 🔑 El ID real de tu archivo de Google Drive
ID_GOOGLE_DRIVE = "1llhosnqf0zf7FB8bsXgHtNLzbOjio2ro"

# Columnas clave requeridas para los cálculos del dashboard
COLUMNAS_SELECCIONADAS = [
    "PLAN", "ORDER", "ORDER DETAIL", "REF", 
    "ESTATUS CHINA COLOMBIA", "ESTADO FINAL COLOMBIA",
    "COLOMBIA QTY", "COLOMBIA PAQS", "PLAN PLANEACION",
    "DIAS FICHA - CREACION", "DIAS CREACION - ENVIO", "DIAS ENVIO - CONFIRMACION",
    "N. SEGMENTO", "CATEGORIA", "TIPO DE PRODUCTO", "TIPO DE COMPRA", "N. PERFIL"
]

@st.cache_data(ttl=300)
def cargar_datos_desde_drive(file_id):
    try:
        session = requests.Session()
        url_base = "https://docs.google.com/uc?export=download"
        
        # Primera solicitud para buscar si Google Drive pide confirmación de descarga por virus
        respuesta = session.get(url_base, params={'id': file_id}, stream=True)
        
        token = None
        # Método 1: Buscar token en cookies
        for key, value in respuesta.cookies.items():
            if key.startswith('download_warning'):
                token = value
                break
                
        # Método 2: Buscar token en el HTML de advertencia (si Google cambió las cookies)
        if not token:
            match = re.search(r'confirm=([a-zA-Z0-9_]+)', respuesta.text)
            if match:
                token = match.group(1)
                
        # Si se encontró un token de confirmación, hacemos la descarga final con el token
        if token:
            respuesta = session.get(url_base, params={'id': file_id, 'confirm': token}, stream=True)
            
        respuesta.raise_for_status()
        
        # Lee la pestaña "BASE" usando el motor openpyxl (100% compatible con flujos en memoria)
        df = pd.read_excel(BytesIO(respuesta.content), header=1, sheet_name="BASE", engine="openpyxl")
        
        # Normalizar nombres de columnas a mayúsculas
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Filtrar solo columnas existentes
        cols_presentes = [c for c in COLUMNAS_SELECCIONADAS if c in df.columns]
        df = df[cols_presentes]
        
        # Forzar conversión a texto para evitar errores en las tablas
        for col in df.columns:
            if col not in ["COLOMBIA QTY", "COLOMBIA PAQS", "PLAN PLANEACION", "DIAS FICHA - CREACION", "DIAS CREACION - ENVIO", "DIAS ENVIO - CONFIRMACION"]:
                df[col] = df[col].astype(str).str.strip().str.upper()
                df[col] = df[col].replace(["NAN", "NONE", "", "NAT"], "SIN ASIGNAR")
        
        # Convertir cantidades y días a numérico
        cols_numericas = ["COLOMBIA QTY", "COLOMBIA PAQS", "PLAN PLANEACION", "DIAS FICHA - CREACION", "DIAS CREACION - ENVIO", "DIAS ENVIO - CONFIRMACION"]
        for col_num in cols_numericas:
            if col_num in df.columns:
                df[col_num] = pd.to_numeric(df[col_num], errors="coerce").fillna(0)
                
        return df, None
    except Exception as e:
        return None, f"Error cargando base: {e}"

# --- CARGA CON SPINNER VISUAL ---
with st.spinner("⏳ Descargando base de datos de 34 MB desde Google Drive..."):
    df, error = cargar_datos_desde_drive(ID_GOOGLE_DRIVE)

if error:
    st.error(f"⚠️ {error}")
    st.stop()

if df is not None and not df.empty:
    
    # --- CABECERA ESTILO LILI PINK ---
    st.markdown("""
        <div class="header-box">
            <h1 style='margin:0; font-size:32px;'>Lili Pink & Yoi</h1>
            <p style='margin:5px 0 0 0; font-size:16px; opacity:0.9;'>Monitor Ejecutivo de Sourcing y Producción Textil</p>
        </div>
    """, unsafe_allow_html=True)

    # --- BARRA SUPERIOR DE FILTROS (Múltiple Selección) ---
    st.markdown("<div class='section-title'>🎛️ Filtros Globales de Control (Selección Múltiple)</div>", unsafe_allow_html=True)
    
    f1, f2, f3 = st.columns(3)
    f4, f5, f6 = st.columns(3)
    
    with f1:
        segmentos = sorted([str(x) for x in df["N. SEGMENTO"].unique() if str(x) != "SIN ASIGNAR"]) if "N. SEGMENTO" in df.columns else []
        segmento_sel = st.multiselect("Segmentos:", options=segmentos, placeholder="Todos los Segmentos")
    with f2:
        referencias = sorted([str(x) for x in df["REF"].unique() if str(x) != "SIN ASIGNAR"]) if "REF" in df.columns else []
        ref_sel = st.multiselect("Referencias:", options=referencias, placeholder="Todas las Referencias")
    with f3:
        perfiles = sorted([str(x) for x in df["N. PERFIL"].unique() if str(x) != "SIN ASIGNAR"]) if "N. PERFIL" in df.columns else []
        perfil_sel = st.multiselect("Perfiles / Clasificación:", options=perfiles, placeholder="Todos los Perfiles")
    with f4:
        estados = sorted([str(x) for x in df["ESTADO FINAL COLOMBIA"].unique() if str(x) != "SIN ASIGNAR"]) if "ESTADO FINAL COLOMBIA" in df.columns else []
        estado_sel = st.multiselect("Estatus China:", options=estados, placeholder="Todos los Estatus")
    with f5:
        compras = sorted([str(x) for x in df["TIPO DE COMPRA"].unique() if str(x) != "SIN ASIGNAR"]) if "TIPO DE COMPRA" in df.columns else []
        compra_sel = st.multiselect("Tipos de Compra:", options=compras, placeholder="Todos los Tipos")
    with f6:
        planes = sorted([str(x) for x in df["PLAN"].unique() if str(x) != "SIN ASIGNAR"]) if "PLAN" in df.columns else []
        plan_sel = st.multiselect("Planes / O.P.:", options=planes, placeholder="Todos los Planes")

    # Aplicar Filtros Dinámicos (Soporta múltiples selecciones simultáneas)
    df_f = df.copy()
    if segmento_sel: df_f = df_f[df_f["N. SEGMENTO"].isin(segmento_sel)]
    if ref_sel: df_f = df_f[df_f["REF"].isin(ref_sel)]
    if perfil_sel: df_f = df_f[df_f["N. PERFIL"].isin(perfil_sel)]
    if estado_sel: df_f = df_f[df_f["ESTADO FINAL COLOMBIA"].isin(estado_sel)]
    if compra_sel: df_f = df_f[df_f["TIPO DE COMPRA"].isin(compra_sel)]
    if plan_sel: df_f = df_f[df_f["PLAN"].isin(plan_sel)]

    # --- BOTÓN DE REFRESCAR EN LA BARRA LATERAL ---
    if st.sidebar.button("🔄 Sincronizar Google Drive"):
        st.cache_data.clear()
        st.rerun()

    # --- DISEÑO DEL CONTENIDO PRINCIPAL (Dividido en 2 Columnas Grandes) ---
    col_izquierda, col_derecha = st.columns([5, 7])

    # ================= COLUMNA IZQUIERDA (Métricas, Estatus, Lead Times) =================
    with col_izquierda:
        st.markdown("<div class='section-title'>CELULAS TEXTIL</div>", unsafe_allow_html=True)
        
        # Tarjetas Métricas
        k_col1, k_col2, k_col3 = st.columns(3)
        num_ordenes = df_f["ORDER"].nunique() if "ORDER" in df_f.columns else 0
        num_refs = df_f["REF"].nunique() if "REF" in df_f.columns else 0
        num_planes = df_f["PLAN"].nunique() if "PLAN" in df_f.columns else 0
        
        with k_col1:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-val">{num_ordenes:,}</div>
                    <div class="kpi-lbl"># ORDER</div>
                </div>
            """, unsafe_allow_html=True)
        with k_col2:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-val">{num_refs:,}</div>
                    <div class="kpi-lbl"># REF</div>
                </div>
            """, unsafe_allow_html=True)
        with k_col3:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-val">{num_planes:,}</div>
                    <div class="kpi-lbl"># PLANES</div>
                </div>
            """, unsafe_allow_html=True)

        # Tabla de Estatus
        st.markdown("<div class='section-title'>ESTATUS COLOMBIA</div>", unsafe_allow_html=True)
        if "ESTADO FINAL COLOMBIA" in df_f.columns and "COLOMBIA PAQS" in df_f.columns:
            resumen_status = df_f.groupby("ESTADO FINAL COLOMBIA")["COLOMBIA PAQS"].sum().reset_index()
            total_paqs = resumen_status["COLOMBIA PAQS"].sum()
            resumen_status["%"] = (resumen_status["COLOMBIA PAQS"] / (total_paqs if total_paqs > 0 else 1) * 100).round(1).astype(str) + " %"
            resumen_status["COLOMBIA PAQS"] = resumen_status["COLOMBIA PAQS"].map("{:,.0f}".format)
            st.dataframe(resumen_status, width="stretch", hide_index=True)
        else:
            st.info("No se detectaron las columnas de Estatus o Paquetes.")

        # Lead Time por Perfil y Tipo de Producto
        st.markdown("<div class='section-title'>LEAD TIME BESTSELLER (LT)</div>", unsafe_allow_html=True)
        if "N. PERFIL" in df_f.columns and "TIPO DE PRODUCTO" in df_f.columns:
            resumen_lt = df_f.groupby(["N. PERFIL", "TIPO DE PRODUCTO"])["COLOMBIA PAQS"].sum().reset_index()
            resumen_lt["LT (SEMANAS)"] = 6  # Ejemplo de Lead Time promedio
            resumen_lt["COLOMBIA PAQS"] = resumen_lt["COLOMBIA PAQS"].map("{:,.0f}".format)
            st.dataframe(resumen_lt, width="stretch", hide_index=True)

    # ================= COLUMNA DERECHA (Tiempos de Ejecución y Evacuación de Planes) =================
    with col_derecha:
        st.markdown("<div class='section-title'>TIEMPO PROMEDIO EJECUCION</div>", unsafe_allow_html=True)
        # Tiempos Promedio por Plan
        columnas_dias = [c for c in ["DIAS FICHA - CREACION", "DIAS CREACION - ENVIO", "DIAS ENVIO - CONFIRMACION"] if c in df_f.columns]
        if "PLAN" in df_f.columns and columnas_dias:
            resumen_tiempos = df_f.groupby("PLAN")[columnas_dias].mean().round(1).reset_index()
            st.dataframe(resumen_tiempos, width="stretch", hide_index=True)
        else:
            st.info("No hay columnas suficientes para calcular los tiempos promedio de ejecución.")

        st.markdown("<div class='section-title'>EVACUACION PLANES</div>", unsafe_allow_html=True)
        # Evacuación de Planes (Suma Solicitado / Planeado vs Paquetes reales)
        if "PLAN" in df_f.columns and "PLAN PLANEACION" in df_f.columns and "COLOMBIA PAQS" in df_f.columns:
            resumen_evac = df_f.groupby("PLAN")[["PLAN PLANEACION", "COLOMBIA PAQS"]].sum().reset_index()
            
            # Cálculo de % Evacuación seguro
            resumen_evac["% EVACUACION"] = 100
            mask_planeacion = resumen_evac["PLAN PLANEACION"] > 0
            resumen_evac.loc[mask_planeacion, "% EVACUACION"] = (resumen_evac["COLOMBIA PAQS"] / resumen_evac["PLAN PLANEACION"] * 100).round(1)
            
            # Formatear
            resumen_evac["% EVACUACION"] = resumen_evac["% EVACUACION"].astype(str) + " %"
            resumen_evac["PLAN PLANEACION"] = resumen_evac["PLAN PLANEACION"].map("{:,.0f}".format)
            resumen_evac["COLOMBIA PAQS"] = resumen_evac["COLOMBIA PAQS"].map("{:,.0f}".format)
            
            st.dataframe(resumen_evac, width="stretch", hide_index=True)
        else:
            st.info("Columnas de planeación/paquetes no detectadas.")

    # --- MATRIZ DE DETALLES Y DESCARGA AL FINAL ---
    st.markdown("<div class='section-title'>📋 MATRIZ DETALLADA Y EXPORTACIÓN</div>", unsafe_allow_html=True)
    columnas_vista = [
        "PLAN", "ORDER DETAIL", "REF", "TIPO DE PRODUCTO", "CATEGORIA",
        "COLOMBIA QTY", "COLOMBIA PAQS", "ESTADO FINAL COLOMBIA", 
        "ESTADO FINAL COLOMBIA"
    ]
    cols_a_mostrar = [c for c in columnas_vista if c in df_f.columns]
    if cols_a_mostrar:
        st.dataframe(df_f[cols_a_mostrar], width="stretch", hide_index=True)
        
        # Botón de Descarga
        csv_data = df_f[cols_a_mostrar].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar datos filtrados (CSV)",
            data=csv_data,
            file_name="reporte_sourcing_filtrado.csv",
            mime="text/csv"
        )
else:
    st.info("No se encontraron registros para mostrar.")
