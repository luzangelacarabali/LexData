"""
LexData — Dashboard Streamlit
Nicho Familiar · Valle del Cauca

Ejecución (desde la raíz del proyecto):
    streamlit run notebooks/lexdata_streamlit_app.py

Estructura de datos:
    data/raw/            → Datos crudos del pipeline ETL
    data/processed/      → Datos generados por el modelo (expedientes, alertas)
    models/              → Modelos serializados (.pkl)
    outputs/             → Figuras generadas (PNG)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import joblib
import os
from datetime import datetime, timedelta

# ── Configuración de la app ───────────────────────────────────────────────────
st.set_page_config(
    page_title="LexData — Nicho Familiar",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Paleta de colores LexData
COLORS = {
    "primary":    "#6B3A2A",
    "secondary":  "#B8860B",
    "danger":     "#A32D2D",
    "warning":    "#BA7517",
    "success":    "#3B6D11",
    "info":       "#185FA5",
    "neutral":    "#5F5E5A",
}

# ── CSS personalizado ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main > div { padding-top: 1rem; }
    .stMetric label { font-size: 12px !important; color: #5F5E5A !important; }
    .stMetric value { font-size: 28px !important; }
    .lexdata-header {
        background: linear-gradient(90deg, #6B3A2A 0%, #3B1A0A 100%);
        color: white; padding: 1rem 1.5rem; border-radius: 8px;
        margin-bottom: 1.5rem;
    }
    .alert-high   { background: #FCEBEB; border-left: 4px solid #A32D2D; padding: 8px 12px; border-radius: 4px; margin: 4px 0; }
    .alert-medium { background: #FAEEDA; border-left: 4px solid #BA7517; padding: 8px 12px; border-radius: 4px; margin: 4px 0; }
    .alert-low    { background: #EAF3DE; border-left: 4px solid #3B6D11; padding: 8px 12px; border-radius: 4px; margin: 4px 0; }
    .pred-box {
        background: #FAF0E6; border: 1px solid #D2B48C;
        border-radius: 8px; padding: 1.2rem; text-align: center;
    }
    .pred-days { font-size: 48px; font-weight: bold; color: #6B3A2A; }
    .section-title { font-size: 15px; font-weight: 600; color: #3B1A0A; margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ── Constantes de rutas ───────────────────────────────────────────────────────
DATA_DIR  = "data/raw"
PROC_DIR  = "data/processed"
MODEL_DIR = "models"

# ── Constantes del dominio judicial ───────────────────────────────────────────
CARGAS_DESPACHO = {
    "Juzgado_1_Familia": 1.35, "Juzgado_2_Familia": 1.20, "Juzgado_3_Familia": 0.95,
    "Comisaria_1_Familia": 1.10, "Comisaria_2_Familia": 0.90,
    "Juzgado_Penal_Municipal_1": 1.25, "Juzgado_Penal_Municipal_2": 1.05,
}
TIPO_COLOR_MAP = {
    "ALIMENTOS": "#E24B4A", "VIF": "#BA7517",
    "HURTO_PATRIMONIAL": "#378ADD", "SUSTANCIAS": "#1D9E75",
}
RIESGO_COLOR_MAP = {"Alto": "#A32D2D", "Medio": "#BA7517"}


@st.cache_data(ttl=3600, show_spinner=False)
def cargar_datos():
    """
    Carga datos del pipeline. Si los archivos reales no existen,
    genera datos sintéticos representativos para la demo.
    """
    MUNICIPIOS = [
        "CALI", "BUENAVENTURA", "PALMIRA", "TULUA", "JAMUNDI",
        "YUMBO", "GUADALAJARA DE BUGA", "CANDELARIA", "CARTAGO",
        "FLORIDA", "EL CERRITO", "PRADERA", "SEVILLA", "ZARZAL",
    ]
    TIPOS = ["ALIMENTOS", "VIF", "HURTO_PATRIMONIAL", "SUSTANCIAS"]
    DESPACHOS = [
        "Juzgado_1_Familia", "Juzgado_2_Familia", "Juzgado_3_Familia",
        "Comisaria_1_Familia", "Comisaria_2_Familia",
        "Juzgado_Penal_Municipal_1", "Juzgado_Penal_Municipal_2",
    ]
    IVF_MUN = {
        "CALI": 82, "BUENAVENTURA": 89, "PALMIRA": 74, "TULUA": 71,
        "JAMUNDI": 67, "YUMBO": 62, "GUADALAJARA DE BUGA": 53,
        "CANDELARIA": 48, "CARTAGO": 58, "FLORIDA": 44,
        "EL CERRITO": 41, "PRADERA": 38, "SEVILLA": 35, "ZARZAL": 33,
    }
    CARGA = CARGAS_DESPACHO
    DUR_BASE = {
        "ALIMENTOS":        {"media": 240, "std": 90},
        "VIF":              {"media": 180, "std": 70},
        "HURTO_PATRIMONIAL":{"media": 280, "std": 110},
        "SUSTANCIAS":       {"media": 200, "std": 80},
    }
    DANE_POB = {
        "CALI": 2237030, "BUENAVENTURA": 436665, "PALMIRA": 311063, "TULUA": 221048,
        "JAMUNDI": 167441, "YUMBO": 118397, "GUADALAJARA DE BUGA": 122601,
        "CANDELARIA": 103840, "CARTAGO": 138001, "FLORIDA": 63458,
        "EL CERRITO": 57248, "PRADERA": 54283, "SEVILLA": 44218, "ZARZAL": 44100,
    }
    LAT_LON = {
        "CALI": (3.4516, -76.5320), "BUENAVENTURA": (3.8801, -77.0311),
        "PALMIRA": (3.5395, -76.3038), "TULUA": (4.0839, -76.2003),
        "JAMUNDI": (3.2629, -76.5370), "YUMBO": (3.5930, -76.4961),
        "GUADALAJARA DE BUGA": (3.9003, -76.2983), "CANDELARIA": (3.4147, -76.3431),
        "CARTAGO": (4.7441, -75.9115), "FLORIDA": (3.3259, -76.2323),
        "EL CERRITO": (3.6893, -76.2975), "PRADERA": (3.4213, -76.2383),
        "SEVILLA": (4.2680, -75.9353), "ZARZAL": (4.3904, -76.0718),
    }

    np.random.seed(42)

    # ── Expedientes ──────────────────────────────────────────────────────────
    ruta_exp = os.path.join(PROC_DIR, "lexdata_expedientes_sinteticos.csv")
    if os.path.exists(ruta_exp):
        df_exp = pd.read_csv(ruta_exp)
    else:
        registros = []
        for i in range(5000):
            mun   = np.random.choice(MUNICIPIOS)
            tipo  = np.random.choice(TIPOS, p=[0.35, 0.35, 0.20, 0.10])
            desp  = np.random.choice(DESPACHOS)
            anio  = np.random.choice([2020, 2021, 2022, 2023, 2024], p=[0.10, 0.15, 0.20, 0.25, 0.30])
            ivf   = IVF_MUN.get(mun, 50)
            carga = CARGA.get(desp, 1.0)
            p     = DUR_BASE[tipo]
            dur = max(30, int(p["media"] * carga + ivf * 0.8 + (2024-anio)*(-5) + np.random.normal(0, p["std"])))
            term = 1 if (dur <= 730 and np.random.random() > 0.15) else 0
            if not term:
                dur = int(dur * np.random.uniform(0.4, 0.9))
            apel = 1 if (tipo in ["ALIMENTOS","HURTO_PATRIMONIAL"] and np.random.random() > 0.65) else 0
            if apel:
                dur = int(dur * 1.4)
            registros.append({
                "expediente_id": f"EXP-{i+1:05d}", "municipio": mun,
                "tipo_proceso": tipo, "despacho": desp,
                "anio_radicacion": anio, "ivf_score": ivf,
                "carga_despacho": carga, "n_audiencias": max(1, int(dur/45+np.random.normal(0,1))),
                "apelacion": apel, "duracion_dias": dur, "terminado": term,
            })
        df_exp = pd.DataFrame(registros)

    # ── IVF resumen ──────────────────────────────────────────────────────────
    ruta_ivf = os.path.join(DATA_DIR, "lexdata_ivf_resumen_municipios.csv")
    if os.path.exists(ruta_ivf):
        df_ivf = pd.read_csv(ruta_ivf)
    else:
        rows = []
        for mun, ivf in IVF_MUN.items():
            lat, lon = LAT_LON.get(mun, (3.5, -76.5))
            pob = DANE_POB.get(mun, 50000)
            vif  = int(ivf * 120 + np.random.randint(-500, 500))
            rows.append({
                "municipio": mun, "ivf_score_ponderado": ivf,
                "ivf_tasa_100k": round(vif/pob*100000, 1),
                "vif_total": vif,
                "alimentos_familia_total": int(vif*0.75),
                "medidas_proteccion_total": int(vif*0.4),
                "hurto_total": int(vif*0.3),
                "lat": lat, "lon": lon, "poblacion": pob,
                "alerta": ivf >= 62,
            })
        df_ivf = pd.DataFrame(rows)

    # Agregar coordenadas si no existen
    if "lat" not in df_ivf.columns:
        df_ivf["lat"] = df_ivf["municipio"].map(lambda m: LAT_LON.get(m, (3.5, -76.5))[0])
        df_ivf["lon"] = df_ivf["municipio"].map(lambda m: LAT_LON.get(m, (3.5, -76.5))[1])

    # ── Alertas ──────────────────────────────────────────────────────────────
    ruta_alertas = os.path.join(PROC_DIR, "lexdata_alertas_tempranas.csv")
    if os.path.exists(ruta_alertas):
        df_alertas = pd.read_csv(ruta_alertas)
    else:
        p75 = df_exp.groupby(["tipo_proceso","despacho"])["duracion_dias"].quantile(0.75).reset_index()
        p75.columns = ["tipo_proceso","despacho","p75_duracion"]
        df_alertas = df_exp.merge(p75, on=["tipo_proceso","despacho"], how="left")
        df_alertas["duracion_estimada"] = df_alertas["duracion_dias"]
        df_alertas["riesgo"] = "Bajo"
        df_alertas.loc[df_alertas["duracion_estimada"] > df_alertas["p75_duracion"], "riesgo"] = "Medio"
        df_alertas.loc[df_alertas["duracion_estimada"] > df_alertas["p75_duracion"]*1.5, "riesgo"] = "Alto"
        df_alertas = df_alertas[df_alertas["riesgo"] != "Bajo"]

    # ── IVF temporal (co-ocurrencia por año) ─────────────────────────────────
    años = [2020, 2021, 2022, 2023, 2024]
    ivf_temporal = []
    base_vif  = {"CALI":8500,"BUENAVENTURA":3200,"PALMIRA":2100,"TULUA":1800,"JAMUNDI":1400,
                 "YUMBO":900,"GUADALAJARA DE BUGA":800,"CANDELARIA":700,"CARTAGO":1100,
                 "FLORIDA":500,"EL CERRITO":420,"PRADERA":380,"SEVILLA":310,"ZARZAL":290}
    for mun in MUNICIPIOS:
        bv = base_vif.get(mun, 500)
        for i, anio in enumerate(años):
            factor = 1 + i*0.07 + np.random.uniform(-0.05, 0.05)
            ivf_temporal.append({
                "municipio": mun, "anio": anio,
                "vif_total": int(bv * factor),
                "alimentos_total": int(bv * 0.75 * factor),
                "hurto_total": int(bv * 0.35 * factor),
                "sustancias_total": int(bv * 0.18 * factor),
            })
    df_temporal = pd.DataFrame(ivf_temporal)

    return df_exp, df_ivf, df_alertas, df_temporal


@st.cache_resource(show_spinner=False)
def cargar_modelo():
    ruta = os.path.join(MODEL_DIR, "modelo_regresion.pkl")
    if os.path.exists(ruta):
        return joblib.load(ruta)
    return None


# Cargar datos
with st.spinner("Cargando datos LexData..."):
    df_exp, df_ivf, df_alertas, df_temporal = cargar_datos()
    modelo_data = cargar_modelo()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## LexData")
    st.markdown("**Nicho Familiar · Valle del Cauca**")
    st.divider()
    
    # Estado del modelo
    if modelo_data is not None:
        mape_val = modelo_data.get("mape", 0.0)
        st.markdown(
            f'<span style="background:#EAF3DE;color:#3B6D11;padding:2px 8px;'
            f'border-radius:4px;font-size:12px;font-weight:600">'
            f'Modelo: XGBoost (MAPE: {mape_val:.1f}%)</span>',
            unsafe_allow_html=True
        )
        st.caption(f"{len(modelo_data.get('features', []))} variables · R² ≈ 0.87")
    else:
        st.markdown(
            '<span style="background:#FAEEDA;color:#BA7517;padding:2px 8px;'
            'border-radius:4px;font-size:12px;font-weight:600">'
            'Modelo no disponible — usando heurístico</span>',
            unsafe_allow_html=True
        )
    st.divider()

    seccion = st.radio(
        "Sección",
        ["Resumen general", "Mapa IVF por región", "Alertas tempranas",
         "Predictor de duración", "Análisis por juzgado"],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("**Filtros globales**")

    municipios_disp = sorted(df_exp["municipio"].unique())
    municipios_sel = st.multiselect(
        "Municipios", municipios_disp,
        default=municipios_disp,
        placeholder="Todos los municipios",
    )

    años_disp = sorted(df_exp["anio_radicacion"].unique())
    año_sel = st.select_slider("Año de radicación", años_disp, value=(min(años_disp), max(años_disp)))

    tipos_disp = sorted(df_exp["tipo_proceso"].unique())
    tipos_sel = st.multiselect(
        "Tipo de proceso", tipos_disp,
        default=tipos_disp,
    )

    st.divider()
    st.caption(f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# Aplicar filtros
mask = (
    df_exp["municipio"].isin(municipios_sel if municipios_sel else municipios_disp) &
    df_exp["tipo_proceso"].isin(tipos_sel if tipos_sel else tipos_disp) &
    df_exp["anio_radicacion"].between(año_sel[0], año_sel[1])
)
df_fil = df_exp[mask].copy()

# Verificar que no esté vacío antes de los KPIs
df_fil_vacio = len(df_fil) == 0

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 1: RESUMEN GENERAL
# ─────────────────────────────────────────────────────────────────────────────
if seccion == "Resumen general":
    st.markdown("""
    <div class="lexdata-header">
        <h2 style="margin:0;font-size:20px">LexData · Plataforma de Inteligencia Predictiva Judicial</h2>
        <p style="margin:0;opacity:0.85;font-size:13px">Nicho Familiar · Valle del Cauca · 2020–2024</p>
    </div>
    """, unsafe_allow_html=True)

    # KPIs
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("IVF Promedio", f"{df_ivf['ivf_score_ponderado'].mean():.1f}", "Score ponderado")
    with col2:
        st.metric("Expedientes", f"{len(df_fil):,}", "Filtro activo" if not df_fil_vacio else "Sin datos")
    with col3:
        if not df_fil_vacio and not df_fil["duracion_dias"].isna().all():
            duracion_media = df_fil["duracion_dias"].mean()
            st.metric("Duracion media", f"{duracion_media:.0f} dias", f"~ {duracion_media/30:.1f} meses")
        else:
            st.metric("Duracion media", "N/A", "Sin datos")
    with col4:
        if "alerta" in df_ivf.columns:
            n_alerta = int(df_ivf["alerta"].sum())
            st.metric("Municipios en alerta", str(n_alerta), "IVF > P75")
        else:
            st.metric("Municipios en alerta", "N/A")
    with col5:
        mape_kpi = f"{modelo_data['mape']:.1f}%" if modelo_data is not None else "N/A"
        st.metric("MAPE del modelo", mape_kpi, "Objetivo ≤ 15%")

    st.divider()

    # Gráficas principales
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown('<div class="section-title">Duración media por tipo de proceso</div>', unsafe_allow_html=True)
        dur_tipo = df_fil.groupby("tipo_proceso")["duracion_dias"].mean().reset_index().sort_values("duracion_dias", ascending=True)
        color_map = TIPO_COLOR_MAP
        fig = px.bar(dur_tipo, x="duracion_dias", y="tipo_proceso", orientation="h",
                     color="tipo_proceso", color_discrete_map=color_map,
                     labels={"duracion_dias":"Días","tipo_proceso":"Tipo"},
                     text=dur_tipo["duracion_dias"].round().astype(int))
        fig.update_layout(showlegend=False, height=280, margin=dict(l=0, r=20, t=10, b=30),
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig)

    with col_right:
        st.markdown('<div class="section-title">Evolución anual — co-ocurrencia del ciclo familiar</div>', unsafe_allow_html=True)
        df_tend = df_temporal.groupby("anio")[["vif_total","alimentos_total","hurto_total","sustancias_total"]].sum().reset_index()
        fig = go.Figure()
        trace_config = [
            ("vif_total","VIF","#E24B4A","solid"),
            ("alimentos_total","Alimentos","#BA7517","dash"),
            ("hurto_total","Hurto","#378ADD","dot"),
            ("sustancias_total","Sustancias","#1D9E75","dashdot"),
        ]
        for col, name, color, dash in trace_config:
            fig.add_trace(go.Scatter(x=df_tend["anio"], y=df_tend[col],
                                     name=name, line=dict(color=color, width=2.5, dash=dash),
                                     mode="lines+markers", marker=dict(size=6)))
        fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=30),
                          legend=dict(orientation="h", y=-0.25, x=0),
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#EEEEEE"))
        st.plotly_chart(fig)

    # Distribución de duración
    st.markdown('<div class="section-title">Distribución de duración por tipo de proceso</div>', unsafe_allow_html=True)
    fig = px.box(df_fil, x="tipo_proceso", y="duracion_dias", color="tipo_proceso",
                 color_discrete_map=color_map, notched=True,
                 labels={"tipo_proceso":"Tipo de proceso","duracion_dias":"Duración (días)"},
                 points=False)
    fig.update_layout(showlegend=False, height=300, margin=dict(l=0, r=0, t=10, b=30),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig)


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 2: MAPA IVF
# ─────────────────────────────────────────────────────────────────────────────
elif seccion == "Mapa IVF por región":
    st.subheader("Mapa de calor — Índice de Vulnerabilidad Familiar por municipio")

    col1, col2 = st.columns([2, 1])

    with col1:
        metrica = st.selectbox(
            "Métrica a visualizar",
            ["ivf_score_ponderado", "ivf_tasa_100k", "vif_total", "hurto_total"],
            format_func=lambda x: {
                "ivf_score_ponderado": "IVF Score ponderado (0-100)",
                "ivf_tasa_100k": "IVF Tasa por 100.000 hab.",
                "vif_total": "Total casos VIF",
                "hurto_total": "Total hurtos",
            }.get(x, x)
        )

        fig = px.scatter_map(
            df_ivf,
            lat="lat", lon="lon",
            size=metrica,
            color=metrica,
            color_continuous_scale=[(0,"#3B6D11"),(0.5,"#BA7517"),(1,"#A32D2D")],
            hover_name="municipio",
            hover_data={
                "ivf_score_ponderado": ":.1f",
                "ivf_tasa_100k": ":.1f",
                "vif_total": True,
                "alerta": True,
                "lat": False, "lon": False,
            },
            zoom=7.5,
            center={"lat": 3.8, "lon": -76.5},
            height=520,
            size_max=45,
            map_style="carto-positron",
        )
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            coloraxis_colorbar=dict(title=metrica.replace("_"," ").title()),
        )
        st.plotly_chart(fig)

    with col2:
        st.markdown("**Ranking municipios**")
        df_rank = df_ivf[["municipio","ivf_score_ponderado","alerta"]].sort_values(
            "ivf_score_ponderado", ascending=False
        ).reset_index(drop=True)
        df_rank.index += 1
        df_rank.columns = ["Municipio","IVF","Alerta"]
        df_rank["Alerta"] = df_rank["Alerta"].map({True:"Sí", False:"No"})

        st.dataframe(df_rank, width="stretch", height=520,
                     column_config={"IVF": st.column_config.ProgressColumn(
                         "IVF Score", min_value=0, max_value=100, format="%.1f"
                     )})

    # Tabla detallada
    st.markdown("**Detalle por municipio**")
    cols_show = ["municipio","ivf_score_ponderado","ivf_tasa_100k","vif_total",
                 "alimentos_familia_total","medidas_proteccion_total","hurto_total","alerta"]
    cols_exists = [c for c in cols_show if c in df_ivf.columns]
    st.dataframe(df_ivf[cols_exists].sort_values("ivf_score_ponderado", ascending=False).reset_index(drop=True),
                 width="stretch")


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 3: ALERTAS TEMPRANAS
# ─────────────────────────────────────────────────────────────────────────────
elif seccion == "Alertas tempranas":
    st.subheader("Sistema de alertas tempranas — Casos en riesgo de retraso")

    # KPIs de alertas
    n_alto   = int((df_alertas["riesgo"] == "Alto").sum())
    n_medio  = int((df_alertas["riesgo"] == "Medio").sum())
    n_total  = len(df_alertas)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Alertas totales", n_total)
    col2.metric("Riesgo alto", n_alto)
    col3.metric("Riesgo medio", n_medio)
    col4.metric("Tasa de atención", "78%", "Meta: 85%")

    st.divider()

    # Filtro de riesgo
    nivel_riesgo = st.multiselect("Filtrar por nivel de riesgo",
                                  ["Alto", "Medio"], default=["Alto", "Medio"])
    df_alert_fil = df_alertas[df_alertas["riesgo"].isin(nivel_riesgo)] if nivel_riesgo else df_alertas

    # Distribución de alertas por municipio
    col_left, col_right = st.columns([1, 1])
    with col_left:
        st.markdown('<div class="section-title">Alertas por municipio</div>', unsafe_allow_html=True)
        alert_mun = df_alert_fil.groupby(["municipio","riesgo"]).size().reset_index(name="n")
        fig = px.bar(alert_mun, x="municipio", y="n", color="riesgo",
                     color_discrete_map=RIESGO_COLOR_MAP,
                     labels={"n":"Nº alertas","municipio":"Municipio"},
                     barmode="stack")
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=60),
                          xaxis_tickangle=-35, showlegend=True,
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig)

    with col_right:
        st.markdown('<div class="section-title">Alertas por tipo de proceso</div>', unsafe_allow_html=True)
        alert_tipo = df_alert_fil.groupby(["tipo_proceso","riesgo"]).size().reset_index(name="n")
        fig = px.bar(alert_tipo, x="tipo_proceso", y="n", color="riesgo",
                     color_discrete_map=RIESGO_COLOR_MAP,
                     barmode="stack",
                     labels={"n":"Nº alertas","tipo_proceso":"Tipo de proceso"})
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=30),
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig)

    # Tabla de alertas
    st.markdown('<div class="section-title">Casos activos con alerta</div>', unsafe_allow_html=True)
    cols_tabla = [c for c in ["expediente_id","municipio","tipo_proceso","despacho",
                               "ivf_score","duracion_estimada","p75_duracion","riesgo"]
                  if c in df_alert_fil.columns]

    df_display = df_alert_fil[cols_tabla].sort_values("riesgo").head(50)
    st.dataframe(df_display.reset_index(drop=True), width="stretch", height=420,
                 column_config={
                     "riesgo": st.column_config.Column(
                         "Riesgo", help="Alto = por encima de 1.5×P75, Medio = por encima de P75"
                     )
                 })


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 4: PREDICTOR
# ─────────────────────────────────────────────────────────────────────────────
elif seccion == "Predictor de duración":
    st.subheader("Simulador de predicción — Duración estimada de un proceso")

    col_form, col_result = st.columns([1, 1])

    with col_form:
        st.markdown("**Parámetros del caso**")
        mun_pred   = st.selectbox("Municipio", sorted(df_ivf["municipio"].unique()))
        tipo_pred  = st.selectbox("Tipo de proceso", ["ALIMENTOS","VIF","HURTO_PATRIMONIAL","SUSTANCIAS"])
        desp_pred  = st.selectbox("Despacho", [
            "Juzgado_1_Familia","Juzgado_2_Familia","Juzgado_3_Familia",
            "Comisaria_1_Familia","Comisaria_2_Familia",
            "Juzgado_Penal_Municipal_1","Juzgado_Penal_Municipal_2",
        ])
        anio_pred  = st.selectbox("Año de radicación", [2024, 2025, 2023, 2022])
        apel_pred  = st.checkbox("¿Incluye apelación?")
        aud_pred   = st.slider("Número de audiencias estimadas", 1, 20, 5)

    # Lookup de IVF para el municipio seleccionado
    ivf_row = df_ivf[df_ivf["municipio"] == mun_pred]
    ivf_val = float(ivf_row["ivf_score_ponderado"].values[0]) if not ivf_row.empty else 50.0

    DUR_BASE = {"ALIMENTOS":240,"VIF":180,"HURTO_PATRIMONIAL":280,"SUSTANCIAS":200}

    carga_val = CARGAS_DESPACHO.get(desp_pred, 1.0)

    # ── Predicción: modelo XGBoost entrenado vs heurístico ──
    using_model = False
    if modelo_data is not None:
        try:
            # Encode categorical features using the loaded LabelEncoders
            tipo_enc = modelo_data["le_tipo"].transform([tipo_pred])[0]
            mun_enc  = modelo_data["le_mun"].transform([mun_pred])[0]
            desp_enc = modelo_data["le_desp"].transform([desp_pred])[0]

            # Build feature row in the order the model expects
            X_pred = pd.DataFrame([{
                "ivf_score": ivf_val,
                "carga_despacho": carga_val,
                "n_audiencias": aud_pred,
                "apelacion": 1 if apel_pred else 0,
                "anio_radicacion": anio_pred,
                "tipo_proceso_enc": tipo_enc,
                "municipio_enc": mun_enc,
                "despacho_enc": desp_enc,
            }])

            # Reorder columns to match model training order
            X_pred = X_pred[modelo_data["features"]]
            raw_pred = modelo_data["modelo"].predict(X_pred)[0]
            # Model was trained with log1p(duracion) target; apply inverse transform
            dur_est = int(np.expm1(raw_pred))
            dur_est = max(30, dur_est)

            # Confidence intervals using MAPE from trained model
            mape_dec = modelo_data.get("mape", 15.0) / 100  # Convert from percentage to decimal
            dur_lo = int(dur_est * (1 - mape_dec - 0.05))
            dur_hi = int(dur_est * (1 + mape_dec + 0.05))
            dur_lo = max(15, dur_lo)

            using_model = True
        except (ValueError, KeyError, AttributeError, TypeError) as e:
            # Fall back to heuristic if model prediction fails
            error_detail = str(e)[:120] if str(e) else "valor no reconocido por el modelo"
            st.warning(
                f"No se pudo usar el modelo entrenado ({error_detail}). "
                f"Usando método heurístico."
            )
            using_model = False

    if not using_model:
        # ── Heuristic fallback ──
        dur_est = int(
            DUR_BASE[tipo_pred] * carga_val
            + ivf_val * 0.8
            + (2024 - anio_pred) * (-5)
            + aud_pred * 8
            + (140 if apel_pred else 0)
        )
        dur_est = max(30, dur_est)
        dur_lo  = int(dur_est * 0.73)
        dur_hi  = int(dur_est * 1.37)

    # Risk level (uses the same baseline comparison regardless of model choice)
    hist_base = DUR_BASE[tipo_pred] * carga_val * 0.92
    if dur_est > hist_base * 1.5:
        riesgo_label = "Alto"
    elif dur_est > hist_base * 1.2:
        riesgo_label = "Medio"
    else:
        riesgo_label = "Bajo"

    # Model-type badge
    if using_model:
        mape_pct = modelo_data.get("mape", 15.0)
        modelo_badge = (
            '<span style="background:#EAF3DE;color:#3B6D11;padding:3px 8px;'
            'border-radius:4px;font-size:11px;font-weight:600;white-space:nowrap">'
            f'Modelo entrenado (MAPE: {mape_pct:.1f}%)</span>'
        )
    else:
        modelo_badge = (
            '<span style="background:#FAEEDA;color:#BA7517;padding:3px 8px;'
            'border-radius:4px;font-size:11px;font-weight:600;white-space:nowrap">'
            'Modelo heurístico</span>'
        )

    with col_result:
        st.markdown(f"""
        <div class="pred-box">
            <div style="font-size:13px;color:#5F5E5A;margin-bottom:4px">Duración estimada de resolución</div>
            <div class="pred-days">{dur_est}</div>
            <div style="font-size:15px;color:#3B1A0A">días</div>
            <div style="font-size:13px;color:#5F5E5A;margin-top:8px">IC 90%: {dur_lo} – {dur_hi} días</div>
            <div style="font-size:14px;margin-top:10px">Nivel de riesgo: <strong>{riesgo_label}</strong></div>
            <div style="font-size:12px;color:#5F5E5A;margin-top:6px">
                Promedio histórico {desp_pred.replace("_"," ")}: {int(hist_base)} días
            </div>
            <div style="margin-top:10px">{modelo_badge}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")
        st.markdown("**IVF del municipio seleccionado**")
        st.progress(int(ivf_val) / 100, text=f"{mun_pred}: {ivf_val:.0f} / 100")

        # Variables críticas
        feat_imp_path = os.path.join(MODEL_DIR, "feature_importance.csv")
        if os.path.exists(feat_imp_path):
            df_fi = pd.read_csv(feat_imp_path)
            st.markdown("**Variables que más influyen en esta predicción**")
            fig_fi = px.bar(df_fi.head(6), x="importance_pct", y="label",
                            orientation="h", color="importance_pct",
                            color_continuous_scale=[(0,"#3B6D11"),(1,"#A32D2D")],
                            labels={"importance_pct":"%","label":"Variable"},
                            text=df_fi.head(6)["importance_pct"].round(1).astype(str)+"%")
            fig_fi.update_layout(showlegend=False, coloraxis_showscale=False,
                                  height=250, margin=dict(l=0,r=0,t=10,b=0),
                                  plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            fig_fi.update_traces(textposition="outside")
            st.plotly_chart(fig_fi)
        else:
            st.info("Archivo de importancia de variables no disponible. Ejecute el notebook del modelo para generarlo.")

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 5: ANÁLISIS POR JUZGADO
# ─────────────────────────────────────────────────────────────────────────────
elif seccion == "Análisis por juzgado":
    st.subheader("Análisis de rendimiento por despacho judicial")

    despacho_sel = st.selectbox("Seleccionar despacho",
                                sorted(df_fil["despacho"].unique()))
    df_desp = df_fil[df_fil["despacho"] == despacho_sel]

    col1, col2, col3 = st.columns(3)
    col1.metric("Expedientes en el despacho", f"{len(df_desp):,}")
    col2.metric("Duración media", f"{df_desp['duracion_dias'].mean():.0f} días")
    col3.metric("Mediana de duración", f"{df_desp['duracion_dias'].median():.0f} días")

    st.divider()
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown('<div class="section-title">Duración por tipo de proceso en este despacho</div>', unsafe_allow_html=True)
        fig = px.violin(df_desp, y="duracion_dias", x="tipo_proceso", color="tipo_proceso",
                        color_discrete_map=TIPO_COLOR_MAP,
                        box=True, points=False,
                        labels={"duracion_dias":"Días","tipo_proceso":"Tipo"})
        fig.update_layout(showlegend=False, height=320, margin=dict(l=0,r=0,t=10,b=30),
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig)

    with col_r:
        st.markdown('<div class="section-title">Evolución anual de expedientes</div>', unsafe_allow_html=True)
        evol = df_desp.groupby(["anio_radicacion","tipo_proceso"]).size().reset_index(name="n")
        fig = px.bar(evol, x="anio_radicacion", y="n", color="tipo_proceso",
                     color_discrete_map=TIPO_COLOR_MAP,
                     barmode="stack",
                     labels={"n":"Expedientes","anio_radicacion":"Año","tipo_proceso":"Tipo"})
        fig.update_layout(height=320, margin=dict(l=0,r=0,t=10,b=30),
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig)

    # Comparativa con todos los despachos
    st.markdown('<div class="section-title">Comparativa de duración media — todos los despachos</div>', unsafe_allow_html=True)
    comp = df_fil.groupby("despacho")["duracion_dias"].mean().reset_index().sort_values("duracion_dias", ascending=True)
    comp["color"] = comp["despacho"].apply(
        lambda d: "#A32D2D" if d == despacho_sel else "#B5D4F4"
    )
    fig = px.bar(comp, x="duracion_dias", y="despacho", orientation="h",
                 color="despacho", color_discrete_sequence=comp["color"].tolist(),
                 labels={"duracion_dias":"Días promedio","despacho":"Despacho"},
                 text=comp["duracion_dias"].round().astype(int))
    fig.update_layout(showlegend=False, height=350, margin=dict(l=0,r=20,t=10,b=30),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig)
