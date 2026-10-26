import streamlit as st
import pandas as pd

# Configuración visual de la aplicación para Móvil y Web (Ancho completo)
st.set_page_config(
    page_title="Monitor Sourcing | Lili Pink & Yoi",
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

# 📂 Nombre exacto de tu nuevo archivo binario guardado en GitHub
NOMBRE_ARCHIVO_EXCEL = "BD CHINA REAL INTERNACIONAL.xlsb"

# Columnas clave requeridas de tu pestaña "BASE"
COLUMNAS_SELECCIONADAS = [
    "PLAN", "ORDER", "ORDER DETAIL", "REF", 
    "ESTADO FINAL COLOMBIA", "COLOMBIA PAQS", "COLOMBIA PAQS",
    "N. SEGMENTO", "CATEGORIA", "TIPO DE PRODUCTO", "TIPO DE COMPRA", "N. PERFIL"
]

@st.cache_data(ttl=3600) # Caché de 1 hora para archivos locales
def cargar_datos_locales_binarios(nombre_archivo):
    try:
        # Lee el archivo binario (.xlsb) usando el motor pyxlsb
        df = pd.read_excel(nombre_archivo, header=1, sheet_name="BASE", engine="pyxlsb")
        
        # Normalizar nombres de columnas a mayúsculas
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # 🛡️ Eliminar columnas duplicadas automáticamente
        df = df.loc[:, ~df.columns.duplicated()]
        
        # Filtrar solo columnas existentes de las seleccionadas
        cols_presentes = [c for c in COLUMNAS_SELECCIONADAS if c in df.columns]
        df = df[cols_presentes]
        
        # Forzar conversión a texto para evitar errores en las tablas
        for col in df.columns:
            if col not in ["COLOMBIA QTYS", "COLOMBIA PAQS"]:
                df[col] = df[col].astype(str).str.strip().str.upper()
                df[col] = df[col].replace(["NAN", "NONE", "", "NAT"], "SIN ASIGNAR")
        
        # Convertir cantidades a numérico
        cols_numericas = ["COLOMBIA QTYS", "COLOMBIA PAQS"]
        for col_num in cols_numericas:
            if col_num in df.columns:
                df[col_num] = pd.to_numeric(df[col_num], errors="coerce").fillna(0)
                
        return df, None
    except FileNotFoundError:
        return None, f"El archivo '{nombre_archivo}' no se encuentra en el repositorio de GitHub. Por favor, asegúrate de subirlo."
    except Exception as e:
        return None, f"Error al leer la base de datos binaria: {e}"

# --- CARGA CON SPINNER VISUAL ---
with st.spinner("⏳ Procesando base de datos binaria optimizada en el servidor..."):
    df, error = cargar_datos_locales_binarios(NOMBRE_ARCHIVO_EXCEL)

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

    # --- BARRA SUPERIOR DE FILTROS ---
    st.markdown("<div class='section-title'>🎛️ Filtros Globales de Control (Selección Múltiple)</div>", unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3)
    f4, f5, f6 = st.columns(3)
    
    with f1:
        segmentos = sorted([str(x) for x in df["N. SEGMENTO"].unique() if str(x) != "SIN ASIGNAR"]) if "N. SEGMENTO" in df.columns else []
        segmento_sel = st.multiselect("Segmento:", options=segmentos, placeholder="Todos los Segmentos")
    with f2:
        referencias = sorted([str(x) for x in df["REF"].unique() if str(x) != "SIN ASIGNAR"]) if "REF" in df.columns else []
        ref_sel = st.multiselect("Referencia:", options=referencias, placeholder="Todas las Referencias")
    with f3:
        perfiles = sorted([str(x) for x in df["N. PERFIL"].unique() if str(x) != "SIN ASIGNAR"]) if "N. PERFIL" in df.columns else []
        perfil_sel = st.multiselect("Perfil", options=perfiles, placeholder="Todos los Perfiles")
    with f4:
        estados = sorted([str(x) for x in df["ESTADO FINAL COLOMBIA"].unique() if str(x) != "SIN ASIGNAR"]) if "ESTADO FINAL COLOMBIA" in df.columns else []
        estado_sel = st.multiselect("Estado:", options=estados, placeholder="Todos los Estados")
    with f5:
        compras = sorted([str(x) for x in df["TIPO DE COMPRA"].unique() if str(x) != "SIN ASIGNAR"]) if "TIPO DE COMPRA" in df.columns else []
        compra_sel = st.multiselect("Tipo de Compra:", options=compras, placeholder="Todos los Tipos")
    with f6:
        planes = sorted([str(x) for x in df["PLAN"].unique() if str(x) != "SIN ASIGNAR"]) if "PLAN" in df.columns else []
        plan_sel = st.multiselect("Plan:", options=planes, placeholder="Todos los Planes")

    # Aplicar Filtros Dinámicos (Soporta múltiples selecciones simultáneas)
    df_f = df.copy()
    if segmento_sel: df_f = df_f[df_f["N. SEGMENTO"].isin(segmento_sel)]
    if ref_sel: df_f = df_f[df_f["REF"].isin(ref_sel)]
    if perfil_sel: df_f = df_f[df_f["N. PERFIL"].isin(perfil_sel)]
    if estado_sel: df_f = df_f[df_f["ESTADO FINAL COLOMBIA"].isin(estado_sel)]
    if compra_sel: df_f = df_f[df_f["TIPO DE COMPRA"].isin(compra_sel)]
    if plan_sel: df_f = df_f[df_f["PLAN"].isin(plan_sel)]

    # --- BOTÓN DE REFRESCAR EN LA BARRA LATERAL ---
    if st.sidebar.button("🔄 Refrescar Caché Local"):
        st.cache_data.clear()
        st.rerun()

    # --- DISEÑO DEL CONTENIDO PRINCIPAL ---
    col_izquierda, col_derecha = st.columns([5, 7])

    # ================= COLUMNA IZQUIERDA (Métricas y Estatus) =================
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

        # Tabla y Resumen de Estatus
        st.markdown("<div class='section-title'>ESTATUS COLOMBIA</div>", unsafe_allow_html=True)
        if "ESTADO FINAL COLOMBIA" in df_f.columns and "COLOMBIA PAQS" in df_f.columns:
            resumen_status = df_f.groupby("ESTADO FINAL COLOMBIA")["COLOMBIA PAQS"].sum().reset_index()
            total_paqs = resumen_status["COLOMBIA PAQS"].sum()
            resumen_status["%"] = (resumen_status["COLOMBIA PAQS"] / (total_paqs if total_paqs > 0 else 1) * 100).round(1).astype(str) + " %"
            
            # Gráfico de barras de Estatus
            st.bar_chart(resumen_status.set_index("ESTADO FINAL COLOMBIA")["COLOMBIA PAQS"])
            
            # Tabla de datos
            resumen_status["COLOMBIA PAQS"] = resumen_status["COLOMBIA PAQS"].map("{:,.0f}".format)
            st.dataframe(resumen_status, width="stretch", hide_index=True)
        else:
            st.info("No se detectaron las columnas de Estatus o Paquetes.")

    # ================= COLUMNA DERECHA (Gráficos y Métricas de Producto) =================
    with col_derecha:
        st.markdown("<div class='section-title'>ANÁLISIS DE CATEGORÍA Y PRODUCTO</div>", unsafe_allow_html=True)
        
        if 'TIPO DE PRODUCTO' in df_f.columns and 'COLOMBIA PAQS' in df_f.columns:
            st.subheader("🧵 Cantidad de Unidades (QTY) por Tipo de Producto")
            qty_producto = df_f.groupby("TIPO DE PRODUCTO")["COLOMBIA PAQS"].sum().sort_values(ascending=False)
            st.bar_chart(qty_producto)
            
        if 'CATEGORIA' in df_f.columns and 'COLOMBIA PAQS' in df_f.columns:
            st.subheader("📁 Volumen por Categoría")
            qty_categoria = df_f.groupby("CATEGORIA")["COLOMBIA PAQS"].sum().sort_values(ascending=False)
            st.bar_chart(qty_categoria)

    # --- MATRIZ DE DETALLES Y DESCARGA AL FINAL ---
    st.markdown("<div class='section-title'>📋 MATRIZ DETALLADA Y EXPORTACIÓN</div>", unsafe_allow_html=True)
    columnas_vista = [
        "PLAN", "ORDER DETAIL", "REF", "TIPO DE PRODUCTO", "CATEGORIA",
        "", "COLOMBIA PAQS", "ESTADO FINAL COLOMBIA"
    ]
    columnas_vista = list(dict.fromkeys(columnas_vista)) # Eliminar posibles duplicados
    cols_a_mostrar = [c for c in columnas_vista if c in df_f.columns]
    
    if cols_a_mostrar:
        # ⚡ EL TRUCO CLAVE: Mostramos solo las primeras 100 filas para que la web vuele al filtrar
        st.markdown(f"⚠️ *Mostrando las primeras **100 filas** de un total de **{len(df_f):,}** registros filtrados. Descarga el reporte para ver el detalle completo.*")
        st.dataframe(df_f[cols_a_mostrar].head(100), width="stretch", hide_index=True)
        
        # Botón de Descarga (Este SÍ descarga el 100% de los datos filtrados de forma limpia)
        csv_data = df_f[cols_a_mostrar].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar datos filtrados completos (CSV)",
            data=csv_data,
            file_name="reporte_sourcing_filtrado.csv",
            mime="text/csv"
        )
else:
    st.info("No se encontraron registros para mostrar.")
