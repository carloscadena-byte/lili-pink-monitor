from io import StringIO
import altair as alt
import pandas as pd
import streamlit as st

# Configuración visual de la aplicación para Móvil y Web (Ancho completo)
st.set_page_config(
    page_title="Monitor Sourcing | Lili Pink & Yoi",
    layout="wide",
    page_icon="🛍️",
)

# 🔢 Función para formatear números con punto como separador de miles (Estándar Colombia)
def fmt_num(v):
    try:
        return f"{int(round(float(v))):,}".replace(",", ".")
    except Exception:
        return str(v)

# --- ESTILIZACIÓN CORPORATIVA CENTRADA (Fucsia y Blanco) ---
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
    "COLECCIÓN",
    "FECHA DE DESPACHO CHINA COLOMBIA",
]

@st.cache_data(ttl=3600)
def cargar_datos_locales_binarios(nombre_archivo):
    try:
        df = pd.read_excel(
            nombre_archivo, header=1, sheet_name="BASE", engine="pyxlsb"
        )
        df.columns = [str(c).strip().upper() for c in df.columns]
        df = df.loc[:, ~df.columns.duplicated(keep="first")]

        cols_presentes = [c for c in COLUMNAS_SELECCIONADAS if c in df.columns]
        df = df[cols_presentes].copy()

        for col in df.columns:
            if col not in ["COLOMBIA QTY", "COLOMBIA PAQS"]:
                df[col] = df[col].astype(str).str.strip().str.upper()
                df[col] = df[col].replace(["NAN", "NONE", "", "NAT"], "SIN ASIGNAR")

        cols_numericas = ["COLOMBIA QTY", "COLOMBIA PAQS"]
        for col_num in cols_numericas:
            if col_num in df.columns:
                serie_plana = df[col_num].squeeze()
                if isinstance(serie_plana, pd.DataFrame):
                    serie_plana = serie_plana.iloc[:, 0]
                df[col_num] = (
                    pd.to_numeric(serie_plana, errors="coerce").fillna(0).values
                )
        return df, None
    except FileNotFoundError:
        return (
            None,
            f"El archivo '{nombre_archivo}' no se encuentra en el repositorio.",
        )
    except Exception as e:
        return None, f"Error al leer la base de datos: {e}"

# --- FUNCIÓN GENERADORA DE TABLAS CENTRADAS CON FILA TOTAL ---
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

    # --- FILTROS GLOBALES (Diseño Simétrico de 4 columnas) ---
    st.markdown(
        "<div class='section-title'>🎛️ Filtros Globales de Control (Selección Múltiple)</div>",
        unsafe_allow_html=True,
    )
    f1, f2, f3, f4 = st.columns(4)
    f5, f6, f7, f8 = st.columns(4)
    
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
    with f7:
        colecciones = (
            sorted([
                str(x) for x in df["COLECCIÓN"].unique() if str(x) != "SIN ASIGNAR"
            ])
            if "COLECCIÓN" in df.columns
            else []
        )
        coleccion_sel = st.multiselect(
            "Colección:", options=colecciones, placeholder="Todas las Colecciones"
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
    if coleccion_sel:
        df_f = df_f[df_f["COLECCIÓN"].isin(coleccion_sel)]

    if st.sidebar.button("🔄 Refrescar Caché Local"):
        st.cache_data.clear()
        st.rerun()

    # --- DISTRIBUCIÓN EN 2 COLUMNAS ---
    col_izquierda, col_derecha = st.columns([5, 7])

    # ================= COLUMNA IZQUIERDA =================
    with col_izquierda:
        st.markdown(
            "<div class='section-title'>CELULAS TEXTIL</div>",
            unsafe_allow_html=True,
        )
        k_col1, k_col2, k_col3 = st.columns(3)
        
        # 🔢 Conteo único estricto excluyendo "SIN ASIGNAR"
        num_ordenes = df_f[df_f["ORDER DETAIL"] != "SIN ASIGNAR"]["ORDER DETAIL"].nunique() if "ORDER DETAIL" in df_f.columns else 0
        num_refs = df_f[df_f["REF"] != "SIN ASIGNAR"]["REF"].nunique() if "REF" in df_f.columns else 0
        num_planes = df_f[df_f["PLAN"] != "SIN ASIGNAR"]["PLAN"].nunique() if "PLAN" in df_f.columns else 0
        
        with k_col1:
            st.markdown(
                f"""<div class="kpi-card"><div class="kpi-val">{fmt_num(num_ordenes)}</div><div class="kpi-lbl"># ORDER</div></div>""",
                unsafe_allow_html=True,
            )
        with k_col2:
            st.markdown(
                f"""<div class="kpi-card"><div class="kpi-val">{fmt_num(num_refs)}</div><div class="kpi-lbl"># REF</div></div>""",
                unsafe_allow_html=True,
            )
        with k_col3:
            st.markdown(
                f"""<div class="kpi-card"><div class="kpi-val">{fmt_num(num_planes)}</div><div class="kpi-lbl"># PLANES</div></div>""",
                unsafe_allow_html=True,
            )

        # Gráfica de Torta / Donut y Tabla de Estatus
        st.markdown(
            "<div class='section-title'>ESTATUS COLOMBIA</div>",
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
            resumen_status = resumen_status.sort_values(
                by="COLOMBIA PAQS", ascending=False
            )
            total_paqs = float(resumen_status["COLOMBIA PAQS"].sum())
            divisor = total_paqs if total_paqs > 0 else 1.0
            resumen_status["PORC_NUM"] = (
                resumen_status["COLOMBIA PAQS"] / divisor * 100
            ).round(1)
            resumen_status["%"] = resumen_status["PORC_NUM"].astype(str) + " %"

            # 🍰 Gráfica de Torta / Donut con paleta corporativa
            try:
                import plotly.express as px
                fig = px.pie(
                    resumen_status,
                    values="COLOMBIA PAQS",
                    names="ESTADO FINAL COLOMBIA",
                    hole=0.55,
                    color_discrete_sequence=[
                        "#d81b60",
                        "#f06292",
                        "#ba68c8",
                        "#ff80ab",
                        "#ad1457",
                        "#f48fb1",
                    ],
                )
                fig.update_traces(
                    textposition="inside",
                    textinfo="percent",
                    hovertemplate=(
                        "<b>%{label}</b><br>Paquetes: %{value:,.0f}<br>Porcentaje:"
                        " %{percent}<extra></extra>"
                    ),
                )
                fig.update_layout(
                    margin=dict(t=10, b=10, l=10, r=10),
                    showlegend=True,
                    legend=dict(
                        orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5
                    ),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                # Fallback nativo Altair
                chart_donut = (
                    alt.Chart(resumen_status)
                    .mark_arc(innerRadius=50)
                    .encode(
                        theta=alt.Theta(field="COLOMBIA PAQS", type="quantitative"),
                        color=alt.Color(
                            field="ESTADO FINAL COLOMBIA",
                            type="nominal",
                            scale=alt.Scale(
                                range=[
                                    "#d81b60",
                                    "#f06292",
                                    "#ba68c8",
                                    "#ff80ab",
                                    "#ad1457",
                                    "#f48fb1",
                                ]
                            ),
                            legend=alt.Legend(orient="bottom", title=None),
                        ),
                        tooltip=["ESTADO FINAL COLOMBIA", "COLOMBIA PAQS", "%"],
                    )
                    .properties(height=260)
                )
                st.altair_chart(chart_donut, use_container_width=True)

            # 📋 Tabla de Estatus con fila de Total
            tabla_status = resumen_status.copy()
            fila_total_s = pd.DataFrame([{
                "ESTADO FINAL COLOMBIA": "Total",
                "COLOMBIA PAQS": total_paqs,
                "PORC_NUM": 100.0,
                "%": "100 %",
            }])
            tabla_status = pd.concat([tabla_status, fila_total_s], ignore_index=True)
            tabla_status["PAQS_FMT"] = tabla_status["COLOMBIA PAQS"].apply(fmt_num)

            st.markdown(
                render_tabla_centrada(
                    tabla_status,
                    {
                        "ESTADO FINAL COLOMBIA": "ESTADO",
                        "PAQS_FMT": "PAQS",
                        "%": "%",
                    },
                    "ESTADO FINAL COLOMBIA",
                ),
                unsafe_allow_html=True,
            )

    # ================= COLUMNA DERECHA =================
    with col_derecha:
        # 1. Tabla y Gráfica Vertical por N. PERFIL con Total
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
            total_perf = float(resumen_perfil["COLOMBIA PAQS"].sum())
            div_perf = total_perf if total_perf > 0 else 1.0
            resumen_perfil["PORC_NUM"] = (
                resumen_perfil["COLOMBIA PAQS"] / div_perf * 100
            ).round(1)
            resumen_perfil["%"] = resumen_perfil["PORC_NUM"].astype(str) + " %"

            # Gráfica vertical de columnas
            st.bar_chart(resumen_perfil.set_index("N. PERFIL")["COLOMBIA PAQS"])

            # Tabla centrada con Total
            tabla_perfil = resumen_perfil.copy()
            fila_total_p = pd.DataFrame([{
                "N. PERFIL": "Total",
                "COLOMBIA PAQS": total_perf,
                "PORC_NUM": 100.0,
                "%": "100 %",
            }])
            tabla_perfil = pd.concat([tabla_perfil, fila_total_p], ignore_index=True)
            tabla_perfil["PAQS_FMT"] = tabla_perfil["COLOMBIA PAQS"].apply(fmt_num)

            st.markdown(
                render_tabla_centrada(
                    tabla_perfil,
                    {"N. PERFIL": "PERFIL", "PAQS_FMT": "PAQS", "%": "%"},
                    "N. PERFIL",
                ),
                unsafe_allow_html=True,
            )

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
            )
            st.bar_chart(paqs_prod, horizontal=True)

    # --- MATRIZ DETALLADA Y EXPORTACIÓN ---
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
        df_preview = df_f[cols_a_mostrar].head(100).copy()
        if "COLOMBIA PAQS" in df_preview.columns:
            df_preview["COLOMBIA PAQS"] = df_preview["COLOMBIA PAQS"].apply(fmt_num)

        st.markdown(
            f"<p style='text-align: center; color: #707070;'>⚠️ Mostrando las"
            f" primeras <b>100 filas</b> de un total de <b>{fmt_num(len(df_f))}</b>"
            " registros filtrados.</p>",
            unsafe_allow_html=True,
        )
        st.dataframe(df_preview, width="stretch", hide_index=True)

        # Descarga completa
        csv_data = df_f[cols_a_mostrar].to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Descargar datos filtrados completos (CSV)",
            data=csv_data,
            file_name="reporte_sourcing_filtrado.csv",
            mime="text/csv",
        )
else:
    st.info("No se encontraron registros para mostrar.")
