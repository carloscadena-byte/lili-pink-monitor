from io import StringIO
import altair as alt
import pandas as pd
import streamlit as st
import unicodedata

# Configuración visual de la aplicación para Móvil y Web (Ancho completo)
st.set_page_config(
    page_title="Monitor Sourcing | Lili Pink & Yoi",
    layout="wide",
    page_icon="🛍️",
)

# 🔢 Formateo con punto como separador de miles
def fmt_num(v):
    try:
        if pd.isna(v) or v == 0:
            return "0"
        return f"{int(round(float(v))):,}".replace(",", ".")
    except Exception:
        return str(v)

# 🕵️‍♂️ Buscador flexible de columnas (inmune a tildes o codificación)
def buscar_columna_flexible(columnas_df, nombre_buscado):
    def normalizar(texto):
        return ''.join(
            c for c in unicodedata.normalize('NFD', str(texto).upper().strip())
            if unicodedata.category(c) != 'Mn'
        )
    buscado_clean = normalizar(nombre_buscado)
    for col in columnas_df:
        if normalizar(col) == buscado_clean:
            return col
    return None

# --- ESTILIZACIÓN CORPORATIVA ---
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
        text-align: center;
    }
    .kpi-lbl {
        font-size: 14px;
        color: #707070;
        text-transform: uppercase;
        font-weight: 600;
        margin-top: 5px;
        text-align: center;
    }
    .section-title {
        color: #d81b60;
        font-size: 20px;
        font-weight: bold;
        border-bottom: 2px solid #d81b60;
        padding-bottom: 5px;
        margin-top: 25px;
        margin-bottom: 15px;
        text-align: center;
    }
    </style>
""",
    unsafe_allow_html=True,
)

NOMBRE_ARCHIVO_EXCEL = "BD CHINA REAL INTERNACIONAL.xlsb"

COLUMNAS_SELECCIONADAS = [
    "PLAN", "ORDER", "ORDER DETAIL", "REF",
    "ESTADO FINAL COLOMBIA", "COLOMBIA QTY", "COLOMBIA PAQS",
    "N. SEGMENTO", "CATEGORIA", "TIPO DE PRODUCTO", "TIPO DE COMPRA",
    "N. PERFIL", "COLECCIÓN", "COLECCION", "FECHA DE DESPACHO CHINA COLOMBIA"
]

@st.cache_data(ttl=3600)
def cargar_datos_locales_binarios(nombre_archivo):
    try:
        df = pd.read_excel(
            nombre_archivo, header=1, sheet_name="BASE", engine="pyxlsb"
        )
        df.columns = [str(c).strip().upper() for c in df.columns]
        df = df.loc[:, ~df.columns.duplicated(keep="first")]

        cols_presentes = []
        for col_req in COLUMNAS_SELECCIONADAS:
            col_encontrada = buscar_columna_flexible(df.columns, col_req)
            if col_encontrada and col_encontrada not in cols_presentes:
                cols_presentes.append(col_encontrada)
                
        df = df[cols_presentes].copy()

        # Estandarización de texto
        for col in df.columns:
            if col not in ["COLOMBIA QTY", "COLOMBIA PAQS"]:
                df[col] = df[col].astype(str).str.strip().str.upper()
                df[col] = df[col].replace(["NAN", "NONE", "", "NAT"], "SIN ASIGNAR")

        # Conversión numérica de 1 dimensión
        cols_numericas = ["COLOMBIA QTY", "COLOMBIA PAQS"]
        for col_num in cols_numericas:
            if col_num in df.columns:
                serie_plana = df[col_num].squeeze()
                if isinstance(serie_plana, pd.DataFrame):
                    serie_plana = serie_plana.iloc[:, 0]
                df[col_num] = pd.to_numeric(serie_plana, errors="coerce").fillna(0).values

        # 📅 Extracción de Mes a partir de FECHA DE DESPACHO CHINA COLOMBIA
        col_fecha = buscar_columna_flexible(df.columns, "FECHA DE DESPACHO CHINA COLOMBIA")
        if col_fecha:
            # Intento de parseo de fecha estándar o serial de Excel
            fecha_dt = pd.to_datetime(df[col_fecha], errors="coerce")
            
            # Mapeo a nombres de meses en español
            meses_dict = {
                1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
                5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
                9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
            }
            df["MES_NUM"] = fecha_dt.dt.month.fillna(0).astype(int)
            df["MES_DESPACHO"] = df["MES_NUM"].map(meses_dict).fillna("SIN FECHA")
        else:
            df["MES_DESPACHO"] = "SIN FECHA"
            df["MES_NUM"] = 0

        return df, None
    except FileNotFoundError:
        return None, f"El archivo '{nombre_archivo}' no se encuentra en el repositorio."
    except Exception as e:
        return None, f"Error al leer la base de datos: {e}"

# --- FUNCIÓN GENERADORA DE TABLAS CENTRADAS ---
def render_tabla_centrada(df_data, mapeo_columnas, nombre_col_total=None):
    html = """
    <div style="overflow-x: auto; margin-bottom: 20px;">
    <table style="width: 100%; border-collapse: collapse; text-align: center; font-family: sans-serif; font-size: 14px; background-color: white; color: #212121; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <thead>
            <tr style="background-color: #d81b60; color: white;">
    """
    for _, col_disp in mapeo_columnas.items():
        html += f'<th style="padding: 10px; text-align: center; font-weight: 600; color: white;">{col_disp}</th>'
    html += """
            </tr>
        </thead>
        <tbody>
    """
    for idx, row in df_data.iterrows():
        es_total = (
            nombre_col_total
            and str(row[nombre_col_total]).strip().lower() == "total"
        )
        if es_total:
            row_style = "background-color: #fce4ec; font-weight: bold; color: #d81b60; border-top: 2px solid #d81b60;"
            text_color = "#d81b60"
        else:
            bg = "#ffffff" if idx % 2 == 0 else "#fdf7f9"
            row_style = f"background-color: {bg}; border-bottom: 1px solid #f3e5f5;"
            text_color = "#212121"
            
        html += f'<tr style="{row_style}">'
        for col_orig in mapeo_columnas.keys():
            val = row[col_orig]
            html += f'<td style="padding: 8px; text-align: center; color: {text_color};">{val}</td>'
        html += "</tr>"
        
    html += """
        </tbody>
    </table>
    </div>
    """
    return html

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
        "<div class='section-title'>🎛️ Filtros Globales de Control (Selección Múltiple)</div>",
        unsafe_allow_html=True,
    )
    f1, f2, f3, f4 = st.columns(4)
    f5, f6, f7, f8 = st.columns(4)
    
    with f1:
        col_seg = buscar_columna_flexible(df.columns, "N. SEGMENTO")
        segmentos = sorted([str(x) for x in df[col_seg].unique() if str(x) != "SIN ASIGNAR"]) if col_seg else []
        segmento_sel = st.multiselect("Segmentos:", options=segmentos, placeholder="Todos los Segmentos")
    with f2:
        col_ref = buscar_columna_flexible(df.columns, "REF")
        referencias = sorted([str(x) for x in df[col_ref].unique() if str(x) != "SIN ASIGNAR"]) if col_ref else []
        ref_sel = st.multiselect("Referencias:", options=referencias, placeholder="Todas las Referencias")
    with f3:
        col_perf = buscar_columna_flexible(df.columns, "N. PERFIL")
        perfiles = sorted([str(x) for x in df[col_perf].unique() if str(x) != "SIN ASIGNAR"]) if col_perf else []
        perfil_sel = st.multiselect("Perfiles / Clasificación:", options=perfiles, placeholder="Todos los Perfiles")
    with f4:
        col_est = buscar_columna_flexible(df.columns, "ESTADO FINAL COLOMBIA")
        estados = sorted([str(x) for x in df[col_est].unique() if str(x) != "SIN ASIGNAR"]) if col_est else []
        estado_sel = st.multiselect("Estado Final Colombia:", options=estados, placeholder="Todos los Estados")
    with f5:
        col_comp = buscar_columna_flexible(df.columns, "TIPO DE COMPRA")
        compras = sorted([str(x) for x in df[col_comp].unique() if str(x) != "SIN ASIGNAR"]) if col_comp else []
        compra_sel = st.multiselect("Tipos de Compra:", options=compras, placeholder="Todos los Tipos")
    with f6:
        col_plan = buscar_columna_flexible(df.columns, "PLAN")
        planes = sorted([str(x) for x in df[col_plan].unique() if str(x) != "SIN ASIGNAR"]) if col_plan else []
        plan_sel = st.multiselect("Planes / O.P.:", options=planes, placeholder="Todos los Planes")
    with f7:
        col_col = buscar_columna_flexible(df.columns, "COLECCIÓN")
        colecciones = sorted([str(x) for x in df[col_col].unique() if str(x) != "SIN ASIGNAR"]) if col_col else []
        coleccion_sel = st.multiselect("Colección:", options=colecciones, placeholder="Todas las Colecciones")      
    with f8:
        meses_disp = [m for m in ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre", "SIN FECHA"] if m in df["MES_DESPACHO"].unique()]
        mes_sel = st.multiselect("Mes Despacho:", options=meses_disp, placeholder="Todos los Meses")

    # Aplicar filtros
    df_f = df.copy()
    if segmento_sel and col_seg: df_f = df_f[df_f[col_seg].isin(segmento_sel)]
    if ref_sel and col_ref: df_f = df_f[df_f[col_ref].isin(ref_sel)]
    if perfil_sel and col_perf: df_f = df_f[df_f[col_perf].isin(perfil_sel)]
    if estado_sel and col_est: df_f = df_f[df_f[col_est].isin(estado_sel)]
    if compra_sel and col_comp: df_f = df_f[df_f[col_comp].isin(compra_sel)]
    if plan_sel and col_plan: df_f = df_f[df_f[col_plan].isin(plan_sel)]
    if coleccion_sel and col_col: df_f = df_f[df_f[col_col].isin(coleccion_sel)]
    if mes_sel: df_f = df_f[df_f["MES_DESPACHO"].isin(mes_sel)]

    if st.sidebar.button("🔄 Refrescar Caché Local"):
        st.cache_data.clear()
        st.rerun()

    # --- DISTRIBUCIÓN EN 2 COLUMNAS ---
    col_izquierda, col_derecha = st.columns([5, 7])

    # ================= COLUMNA IZQUIERDA =================
    with col_izquierda:
        st.markdown("<div class='section-title'>CELULAS TEXTIL</div>", unsafe_allow_html=True)
        k_col1, k_col2, k_col3 = st.columns(3)
        
        num_ordenes = df_f[df_f["ORDER"] != "SIN ASIGNAR"]["ORDER"].nunique() if "ORDER" in df_f.columns else 0
        num_refs = df_f[df_f["REF"] != "SIN ASIGNAR"]["REF"].nunique() if "REF" in df_f.columns else 0
        num_planes = df_f[df_f["PLAN"] != "SIN ASIGNAR"]["PLAN"].nunique() if "PLAN" in df_f.columns else 0
        
        with k_col1:
            st.markdown(f"""<div class="kpi-card"><div class="kpi-val">{fmt_num(num_ordenes)}</div><div class="kpi-lbl"># ORDER</div></div>""", unsafe_allow_html=True)
        with k_col2:
            st.markdown(f"""<div class="kpi-card"><div class="kpi-val">{fmt_num(num_refs)}</div><div class="kpi-lbl"># REF</div></div>""", unsafe_allow_html=True)
        with k_col3:
            st.markdown(f"""<div class="kpi-card"><div class="kpi-val">{fmt_num(num_planes)}</div><div class="kpi-lbl"># PLANES</div></div>""", unsafe_allow_html=True)

        # Gráfica de Donut y Tabla de Estatus
        st.markdown("<div class='section-title'>ESTATUS COLOMBIA</div>", unsafe_allow_html=True)
        col_paqs = buscar_columna_flexible(df.columns, "COLOMBIA PAQS")
        col_est_final = buscar_columna_flexible(df.columns, "ESTADO FINAL COLOMBIA")
        
        if col_est_final and col_paqs:
            resumen_status = (
                df_f.groupby(col_est_final)[col_paqs].sum().reset_index()
            )
            resumen_status = resumen_status.sort_values(by=col_paqs, ascending=False)
            total_paqs = float(resumen_status[col_paqs].sum())
            divisor = total_paqs if total_paqs > 0 else 1.0
            resumen_status["PORC_NUM"] = (resumen_status[col_paqs] / divisor * 100).round(1)
            resumen_status["%"] = resumen_status["PORC_NUM"].astype(str) + " %"

            try:
                import plotly.express as px
                fig = px.pie(
                    resumen_status,
                    values=col_paqs,
                    names=col_est_final,
                    hole=0.55,
                    color_discrete_sequence=["#d81b60", "#f06292", "#ba68c8", "#ff80ab", "#ad1457", "#f48fb1"],
                )
                fig.update_traces(
                    textposition="inside",
                    textinfo="percent",
                    hovertemplate="<b>%{label}</b><br>Paquetes: %{value:,.0f}<br>Porcentaje: %{percent}<extra></extra>"
                )
                fig.update_layout(
                    margin=dict(t=10, b=10, l=10, r=10),
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                chart_donut = (
                    alt.Chart(resumen_status)
                    .mark_arc(innerRadius=50)
                    .encode(
                        theta=alt.Theta(field=col_paqs, type="quantitative"),
                        color=alt.Color(
                            field=col_est_final, type="nominal",
                            scale=alt.Scale(range=["#d81b60", "#f06292", "#ba68c8", "#ff80ab", "#ad1457", "#f48fb1"]),
                            legend=alt.Legend(orient="bottom", title=None),
                        ),
                        tooltip=[col_est_final, col_paqs, "%"],
                    )
                    .properties(height=260)
                )
                st.altair_chart(chart_donut, use_container_width=True)

            tabla_status = resumen_status.copy()
            fila_total_s = pd.DataFrame([{
                col_est_final: "Total",
                col_paqs: total_paqs,
                "PORC_NUM": 100.0,
                "%": "100 %",
            }])
            tabla_status = pd.concat([tabla_status, fila_total_s], ignore_index=True)
            tabla_status["PAQS_FMT"] = tabla_status[col_paqs].apply(fmt_num)

            st.markdown(
                render_tabla_centrada(
                    tabla_status,
                    {col_est_final: "ESTADO", "PAQS_FMT": "PAQS", "%": "%"},
                    col_est_final,
                ),
                unsafe_allow_html=True,
            )

    # ================= COLUMNA DERECHA =================
    with col_derecha:
        # 1. Tabla y Gráfica Vertical por N. PERFIL
        st.markdown("<div class='section-title'>DISTRIBUCIÓN POR PERFIL (PAQS)</div>", unsafe_allow_html=True)
        col_perf = buscar_columna_flexible(df_f.columns, "N. PERFIL")
        
        if col_perf and col_paqs:
            resumen_perfil = df_f.groupby(col_perf)[col_paqs].sum().reset_index()
            resumen_perfil = resumen_perfil.sort_values(by=col_paqs, ascending=False)
            total_perf = float(resumen_perfil[col_paqs].sum())
            div_perf = total_perf if total_perf > 0 else 1.0
            resumen_perfil["PORC_NUM"] = (resumen_perfil[col_paqs] / div_perf * 100).round(1)
            resumen_perfil["%"] = resumen_perfil["PORC_NUM"].astype(str) + " %"

            st.bar_chart(resumen_perfil.set_index(col_perf)[col_paqs])

            tabla_perfil = resumen_perfil.copy()
            fila_total_p = pd.DataFrame([{
                col_perf: "Total",
                col_paqs: total_perf,
                "PORC_NUM": 100.0,
                "%": "100 %",
            }])
            tabla_perfil = pd.concat([tabla_perfil, fila_total_p], ignore_index=True)
            tabla_perfil["PAQS_FMT"] = tabla_perfil[col_paqs].apply(fmt_num)

            st.markdown(
                render_tabla_centrada(
                    tabla_perfil,
                    {col_perf: "PERFIL", "PAQS_FMT": "PAQS", "%": "%"},
                    col_perf,
                ),
                unsafe_allow_html=True,
            )

        # 2. 📊 NUEVA TABLA DINÁMICA: MES DE DESPACHO VS ESTADO FINAL (COLOMBIA PAQS)
        st.markdown("<div class='section-title'>PAQUETES POR MES DE DESPACHO Y ESTADO</div>", unsafe_allow_html=True)
        
        if col_est_final and col_paqs and "MES_DESPACHO" in df_f.columns:
            # Crear la tabla dinámica
            pivot = pd.pivot_table(
                df_f,
                index=col_est_final,
                columns="MES_DESPACHO",
                values=col_paqs,
                aggfunc="sum",
                fill_value=0
            )

            # Ordenar columnas cronológicamente según el año
            orden_meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre", "SIN FECHA"]
            cols_ordenadas = [m for m in orden_meses if m in pivot.columns]
            pivot = pivot[cols_ordenadas]

            # Agregar columna Total General
            pivot["Total"] = pivot.sum(axis=1)

            # Agregar fila Total General
            fila_total_pivot = pd.DataFrame(pivot.sum(axis=0)).T
            fila_total_pivot.index = ["Total"]
            pivot_con_totales = pd.concat([pivot, fila_total_pivot])

            # Reset index para formatear
            pivot_display = pivot_con_totales.reset_index()
            col_index_name = col_est_final
            pivot_display.rename(columns={"index": col_index_name}, inplace=True)

            # Diccionario de columnas y formateo con punto
            mapeo_piv = {col_index_name: "ESTADO"}
            for c in pivot_con_totales.columns:
                col_fmt = f"{c}_FMT"
                pivot_display[col_fmt] = pivot_display[c].apply(fmt_num)
                mapeo_piv[col_fmt] = c.upper()

            # Render de la tabla dinámica
            st.markdown(
                render_tabla_centrada(
                    pivot_display,
                    mapeo_piv,
                    col_index_name
                ),
                unsafe_allow_html=True
            )

    # --- MATRIZ DETALLADA Y EXPORTACIÓN ---
    st.markdown("<div class='section-title'>📋 MATRIZ DETALLADA Y EXPORTACIÓN</div>", unsafe_allow_html=True)
    columnas_vista = [
        "PLAN", "ORDER DETAIL", "REF", "N. PERFIL", "TIPO DE PRODUCTO",
        "CATEGORIA", "COLOMBIA PAQS", "MES_DESPACHO", "ESTADO FINAL COLOMBIA"
    ]
    columnas_vista = list(dict.fromkeys(columnas_vista))
    cols_a_mostrar = [c for c in columnas_vista if c in df_f.columns]
    
    if cols_a_mostrar:
        df_preview = df_f[cols_a_mostrar].head(100).copy()
        if "COLOMBIA PAQS" in df_preview.columns:
            df_preview["COLOMBIA PAQS"] = df_preview["COLOMBIA PAQS"].apply(fmt_num)

        st.markdown(
            f"<p style='text-align: center; color: #707070;'>⚠️ Mostrando las primeras <b>100 filas</b> de un total de <b>{fmt_num(len(df_f))}</b> registros filtrados.</p>",
            unsafe_allow_html=True,
        )
        st.dataframe(df_preview, width="stretch", hide_index=True)

        csv_data = df_f[cols_a_mostrar].to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Descargar datos filtrados completos (CSV)",
            data=csv_data,
            file_name="reporte_sourcing_filtrado.csv",
            mime="text/csv",
        )
else:
    st.info("No se encontraron registros para mostrar.")
