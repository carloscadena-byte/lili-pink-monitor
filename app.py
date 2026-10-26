import streamlit as st
import pandas as pd

# Configuración visual de la aplicación para Móvil y Web (Ancho completo)
st.set_page_config(
    page_title="Monitor Sourcing | Lili Pink & Yoi",
    layout="wide",
    page_icon="🛍️",
)

# --- ESTILIZACIÓN CORPORATIVA LILI PINK & YOI ---
st.markdown(
    """
    <style>
    .main {
        background-color: #fcf8f9;
    }
    .header-box {
        background-color: #d81b60;
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
    }
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
""",
    unsafe_allow_html=True,
)

# 📂 Archivo binario local en GitHub
NOMBRE_ARCHIVO_EXCEL = "BD CHINA REAL INTERNACIONAL.xlsb"

COLUMNAS_SELECCIONADAS = [
    "PLAN",
    "ORDER",
    "ORDER DETAIL",
    "REF",
    "ESTADO FINAL COLOMBIA",
    "COLOMBIA QTY",
    "COLOMBIA PAQS",
    "N. SEGMENTO",
    "CATEGORIA",
    "TIPO DE PRODUCTO",
    "TIPO DE COMPRA",
    "N. PERFIL",
]


@st.cache_data(ttl=3600)
def cargar_datos_locales_binarios(nombre_archivo):
  try:
    df = pd.read_excel(
        nombre_archivo, header=1, sheet_name="BASE", engine="pyxlsb"
    )
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.loc[:, ~df.columns.duplicated()]

    cols_presentes = [c for c in COLUMNAS_SELECCIONADAS if c in df.columns]
    df = df[cols_presentes]

    for col in df.columns:
      if col not in ["COLOMBIA QTY", "COLOMBIA PAQS"]:
        df[col] = df[col].astype(str).str.strip().str.upper()
        df[col] = df[col].replace(["NAN", "NONE", "", "NAT"], "SIN ASIGNAR")

    cols_numericas = ["COLOMBIA QTY", "COLOMBIA PAQS"]
    for col_num in cols_numericas:
      if col_num in df.columns:
        datos_columna = df[col_num]
        if isinstance(datos_columna, pd.DataFrame):
          datos_columna = datos_columna.iloc[:, 0]
        df[col_num] = pd.to_numeric(datos_columna, errors="coerce").fillna(0)

    return df, None
  except FileNotFoundError:
    return (
        None,
        f"El archivo '{nombre_archivo}' no se encuentra en el repositorio.",
    )
  except Exception as e:
    return None, f"Error al leer la base de datos: {e}"


# --- CARGA DE DATOS ---
with st.spinner("⏳ Cargando panel operativo..."):
  df, error = cargar_datos_locales_binarios(NOMBRE_ARCHIVO_EXCEL)

if error:
  st.error(f"⚠️ {error}")
  st.stop()

if df is not None and not df.empty:

  # --- CABECERA ---
  st.markdown(
      """
        <div class="header-box">
            <h1 style='margin:0; font-size:32px;'>Lili Pink & Yoi</h1>
            <p style='margin:5px 0 0 0; font-size:16px; opacity:0.9;'>Monitor Ejecutivo de Sourcing y Producción Textil</p>
        </div>
    """,
      unsafe_allow_html=True,
  )

  # --- FILTROS GLOBALES ---
  st.markdown(
      "<div class='section-title'>🎛️ Filtros Globales de Control (Selección"
      " Múltiple)</div>",
      unsafe_allow_html=True,
  )
  f1, f2, f3 = st.columns(3)
  f4, f5, f6 = st.columns(3)

  with f1:
    segmentos = (
        sorted([
            str(x)
            for x in df["N. SEGMENTO"].unique()
            if str(x) != "SIN ASIGNAR"
        ])
        if "N. SEGMENTO" in df.columns
        else []
    )
    segmento_sel = st.multiselect(
        "Segmentos:", options=segmentos, placeholder="Todos los Segmentos"
    )
  with f2:
    referencias = (
        sorted([str(x) for x in df["REF"].unique() if str(x) != "SIN ASIGNAR"])
        if "REF" in df.columns
        else []
    )
    ref_sel = st.multiselect(
        "Referencias:", options=referencias, placeholder="Todas las Referencias"
    )
  with f3:
    perfiles = (
        sorted([
            str(x) for x in df["N. PERFIL"].unique() if str(x) != "SIN ASIGNAR"
        ])
        if "N. PERFIL" in df.columns
        else []
    )
    perfil_sel = st.multiselect(
        "Perfiles / Clasificación:",
        options=perfiles,
        placeholder="Todos los Perfiles",
    )
  with f4:
    estados = (
        sorted([
            str(x)
            for x in df["ESTADO FINAL COLOMBIA"].unique()
            if str(x) != "SIN ASIGNAR"
        ])
        if "ESTADO FINAL COLOMBIA" in df.columns
        else []
    )
    estado_sel = st.multiselect(
        "Estado Final Colombia:",
        options=estados,
        placeholder="Todos los Estados",
    )
  with f5:
    compras = (
        sorted([
            str(x)
            for x in df["TIPO DE COMPRA"].unique()
            if str(x) != "SIN ASIGNAR"
        ])
        if "TIPO DE COMPRA" in df.columns
        else []
    )
    compra_sel = st.multiselect(
        "Tipos de Compra:", options=compras, placeholder="Todos los Tipos"
    )
  with f6:
    planes = (
        sorted([
            str(x) for x in df["PLAN"].unique() if str(x) != "SIN ASIGNAR"
        ])
        if "PLAN" in df.columns
        else []
    )
    plan_sel = st.multiselect(
        "Planes / O.P.:", options=planes, placeholder="Todos los Planes"
    )

  # Aplicar filtros
  df_f = df.copy()
  if segmento_sel:
    df_f = df_f[df_f["N. SEGMENTO"].isin(segmento_sel)]
  if ref_sel:
    df_f = df_f[df_f["REF"].isin(ref_sel)]
  if perfil_sel:
    df_f = df_f[df_f["N. PERFIL"].isin(perfil_sel)]
  if estado_sel:
    df_f = df_f[df_f["ESTADO FINAL COLOMBIA"].isin(estado_sel)]
  if compra_sel:
    df_f = df_f[df_f["TIPO DE COMPRA"].isin(compra_sel)]
  if plan_sel:
    df_f = df_f[df_f["PLAN"].isin(plan_sel)]

  if st.sidebar.button("🔄 Refrescar Caché Local"):
    st.cache_data.clear()
    st.rerun()

  # --- INDICADORES Y DISTRIBUCIÓN ---
  col_izquierda, col_derecha = st.columns([5, 7])

  # ================= COLUMNA IZQUIERDA =================
  with col_izquierda:
    st.markdown(
        "<div class='section-title'>CELULAS TEXTIL</div>",
        unsafe_allow_html=True,
    )

    k_col1, k_col2, k_col3 = st.columns(3)
    num_ordenes = df_f["ORDER"].nunique() if "ORDER" in df_f.columns else 0
    num_refs = df_f["REF"].nunique() if "REF" in df_f.columns else 0
    num_planes = df_f["PLAN"].nunique() if "PLAN" in df_f.columns else 0

    with k_col1:
      st.markdown(
          f"""<div class="kpi-card"><div class="kpi-val">{num_ordenes:,}</div><div class="kpi-lbl"># ORDER</div></div>""",
          unsafe_allow_html=True,
      )
    with k_col2:
      st.markdown(
          f"""<div class="kpi-card"><div class="kpi-val">{num_refs:,}</div><div class="kpi-lbl"># REF</div></div>""",
          unsafe_allow_html=True,
      )
    with k_col3:
      st.markdown(
          f"""<div class="kpi-card"><div class="kpi-val">{num_planes:,}</div><div class="kpi-lbl"># PLANES</div></div>""",
          unsafe_allow_html=True,
      )

    # Estatus Colombia en PAQS
    st.markdown(
        "<div class='section-title'>ESTATUS COLOMBIA (PAQS)</div>",
        unsafe_allow_html=True,
    )
    if (
        "ESTADO FINAL COLOMBIA" in df_f.columns
        and "COLOMBIA PAQS" in df_f.columns
    ):
      resumen_status = (
          df_f.groupby("ESTADO FINAL COLOMBIA")["COLOMBIA PAQS"]
          .sum()
          .reset_index()
      )
      suma_paqs_raw = resumen_status["COLOMBIA PAQS"].sum()
      total_paqs = (
          float(suma_paqs_raw.iloc[0])
          if isinstance(suma_paqs_raw, pd.Series)
          else float(suma_paqs_raw)
      )
      divisor = total_paqs if total_paqs > 0 else 1.0

      resumen_status["%"] = (
          (resumen_status["COLOMBIA PAQS"] / divisor * 100)
          .round(1)
          .astype(str)
          + " %"
      )
      st.bar_chart(
          resumen_status.set_index("ESTADO FINAL COLOMBIA")["COLOMBIA PAQS"]
      )

      resumen_status["COLOMBIA PAQS"] = resumen_status["COLOMBIA PAQS"].map(
          "{:,.0f}".format
      )
      st.dataframe(resumen_status, width="stretch", hide_index=True)

  # ================= COLUMNA DERECHA =================
  with col_derecha:
    # 1. Gráfica Vertical por N. PERFIL
    st.markdown(
        "<div class='section-title'>DISTRIBUCIÓN POR PERFIL (PAQS)</div>",
        unsafe_allow_html=True,
    )
    if "N. PERFIL" in df_f.columns and "COLOMBIA PAQS" in df_f.columns:
      resumen_perfil = (
          df_f.groupby("N. PERFIL")["COLOMBIA PAQS"].sum().reset_index()
      )
      resumen_perfil = resumen_perfil.sort_values(
          by="COLOMBIA PAQS", ascending=False
      )

      # Gráfica vertical de columnas
      st.bar_chart(resumen_perfil.set_index("N. PERFIL")["COLOMBIA PAQS"])

      # Tabla resumen de perfiles
      total_perfil = resumen_perfil["COLOMBIA PAQS"].sum()
      div_p = total_perfil if total_perfil > 0 else 1.0
      resumen_perfil["%"] = (
          (resumen_perfil["COLOMBIA PAQS"] / div_p * 100).round(1).astype(str)
          + " %"
      )
      resumen_perfil["COLOMBIA PAQS"] = resumen_perfil["COLOMBIA PAQS"].map(
          "{:,.0f}".format
      )
      st.dataframe(resumen_perfil, width="stretch", hide_index=True)

    # 2. Gráfica Horizontal por Tipo de Producto (PAQS)
    st.markdown(
        "<div class='section-title'>PAQUETES POR TIPO DE PRODUCTO</div>",
        unsafe_allow_html=True,
    )
    if "TIPO DE PRODUCTO" in df_f.columns and "COLOMBIA PAQS" in df_f.columns:
      paqs_prod = (
          df_f.groupby("TIPO DE PRODUCTO")["COLOMBIA PAQS"]
          .sum()
          .sort_values(ascending=True)
      )  # Orden ascendente para lectura natural de abajo hacia arriba

      # Gráfica horizontal
      st.bar_chart(paqs_prod, horizontal=True)

  # --- MATRIZ DETALLADA ---
  st.markdown(
      "<div class='section-title'>📋 MATRIZ DETALLADA Y EXPORTACIÓN</div>",
      unsafe_allow_html=True,
  )
  columnas_vista = [
      "PLAN",
      "ORDER DETAIL",
      "REF",
      "N. PERFIL",
      "TIPO DE PRODUCTO",
      "CATEGORIA",
      "COLOMBIA PAQS",
      "ESTADO FINAL COLOMBIA",
  ]
  columnas_vista = list(dict.fromkeys(columnas_vista))
  cols_a_mostrar = [c for c in columnas_vista if c in df_f.columns]

  if cols_a_mostrar:
    st.markdown(
        f"⚠️ *Mostrando las primeras **100 filas** de un total de"
        f" **{len(df_f):,}** registros filtrados. Descarga el reporte para ver"
        " el detalle completo.*"
    )
    st.dataframe(
        df_f[cols_a_mostrar].head(100), width="stretch", hide_index=True
    )

    csv_data = df_f[cols_a_mostrar].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Descargar datos filtrados completos (CSV)",
        data=csv_data,
        file_name="reporte_sourcing_filtrado.csv",
        mime="text/csv",
    )
else:
  st.info("No se encontraron registros para mostrar.")

