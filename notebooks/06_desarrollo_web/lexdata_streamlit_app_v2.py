"""
LexData — Dashboard Streamlit v2
Nicho Familiar · Cali (modelo predictivo v4)

Cambios v2:
- Scope ajustado a CALI (modelo v4)
- Predictor usa modelo_regresion_cali.pkl real (XGBoost + encoders)
- Despachos actualizados a los 10 de Cali del modelo v4
- feature_importance lee feature_importance_cali.csv
- Alertas lee lexdata_alertas_cali.csv
- Expedientes lee lexdata_expedientes_sinteticos_cali.csv
- IVF fallback calibrado para Cali (70.0)
- Métricas del modelo actualizadas (MAPE 11.6%)
- Sección "Análisis por juzgado" con despachos de Cali
- Sección "Modelo" nueva: curva de comparación de modelos

Instalación:
    pip install streamlit pandas numpy plotly joblib scikit-learn xgboost

Ejecución:
    streamlit run lexdata_streamlit_app_v2.py

Estructura esperada:
    lexdata_streamlit_app_v2.py
    outputs/
        lexdata_expedientes_sinteticos_cali.csv
        lexdata_alertas_cali.csv
        feature_importance_cali.csv
    models/
        modelo_regresion_cali.pkl
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import joblib
import os
from datetime import datetime

# ── Configuración ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LexData — Cali",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLORS = {
    "primary":   "#6B3A2A",
    "secondary": "#B8860B",
    "danger":    "#A32D2D",
    "warning":   "#BA7517",
    "success":   "#3B6D11",
    "info":      "#185FA5",
    "neutral":   "#5F5E5A",
}

COLOR_TIPO = {
    "ALIMENTOS":        "#E24B4A",
    "VIF":              "#BA7517",
    "HURTO_PATRIMONIAL":"#378ADD",
    "SUSTANCIAS":       "#1D9E75",
}

st.markdown("""
<style>
    .main > div { padding-top: 1rem; }
    .stMetric label { font-size: 12px !important; color: #5F5E5A !important; }
    .lexdata-header {
        background: linear-gradient(90deg, #6B3A2A 0%, #3B1A0A 100%);
        color: white; padding: 1rem 1.5rem; border-radius: 8px;
        margin-bottom: 1.5rem;
    }
    .pred-box {
        background: #FAF0E6; border: 1px solid #D2B48C;
        border-radius: 8px; padding: 1.4rem; text-align: center;
    }
    .pred-days { font-size: 52px; font-weight: bold; color: #6B3A2A; line-height: 1.1; }
    .section-title { font-size: 14px; font-weight: 600; color: #3B1A0A; margin-bottom: 0.4rem; }
    .tag-alto   { background:#FCEBEB; color:#791F1F; padding:2px 8px; border-radius:4px; font-size:12px; }
    .tag-medio  { background:#FAEEDA; color:#633806; padding:2px 8px; border-radius:4px; font-size:12px; }
    .tag-bajo   { background:#EAF3DE; color:#2B5007; padding:2px 8px; border-radius:4px; font-size:12px; }
</style>
""", unsafe_allow_html=True)

# ── Constantes del modelo v4 ──────────────────────────────────────────────────
MUNICIPIO_OBJETIVO = "CALI"
IVF_CALI_FALLBACK  = 70.0

DESPACHOS_CALI = [
    "Juzgado_1_Familia_Cali",
    "Juzgado_2_Familia_Cali",
    "Juzgado_3_Familia_Cali",
    "Juzgado_4_Familia_Cali",
    "Juzgado_5_Familia_Cali",
    "Comisaria_1_Familia_Cali",
    "Comisaria_2_Familia_Cali",
    "Comisaria_3_Familia_Cali",
    "Juzgado_Penal_Municipal_1_Cali",
    "Juzgado_Penal_Municipal_2_Cali",
]

CARGA_DESPACHO = {
    "Juzgado_1_Familia_Cali":          1.45,
    "Juzgado_2_Familia_Cali":          1.30,
    "Juzgado_3_Familia_Cali":          1.20,
    "Juzgado_4_Familia_Cali":          1.10,
    "Juzgado_5_Familia_Cali":          0.95,
    "Comisaria_1_Familia_Cali":        1.25,
    "Comisaria_2_Familia_Cali":        1.10,
    "Comisaria_3_Familia_Cali":        0.90,
    "Juzgado_Penal_Municipal_1_Cali":  1.35,
    "Juzgado_Penal_Municipal_2_Cali":  1.15,
}

DUR_BASE_CALI = {
    "ALIMENTOS":         260,
    "VIF":               190,
    "HURTO_PATRIMONIAL": 300,
    "SUSTANCIAS":        210,
}

TIPOS = ["ALIMENTOS", "VIF", "HURTO_PATRIMONIAL", "SUSTANCIAS"]

# Comparación de modelos del notebook v4
RESULTADOS_MODELOS = {
    "Ridge":          {"MAPE": 12.7, "R2": 0.437, "MAE": 55.6},
    "Lasso":          {"MAPE": 18.9, "R2": -0.020, "MAE": 88.1},
    "GBM":            {"MAPE": 11.7, "R2": 0.542, "MAE": 50.5},
    "XGBoost":        {"MAPE": 11.6, "R2": 0.540, "MAE": 50.0},
    "ResidualMLP(DL)":{"MAPE": 11.7, "R2": 0.520, "MAE": 49.8},
}

# ── Paths ─────────────────────────────────────────────────────────────────────
# ── Rutas absolutas relativas a este script ──────────────────────────────────
# Funciona sin importar desde qué carpeta se ejecute streamlit
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODELS_05  = os.path.join(BASE_DIR, "..", "05_modelos_de_prediccion", "models")
OUTPUTS_05 = os.path.join(BASE_DIR, "..", "05_modelos_de_prediccion", "outputs")

# MODEL_DIR: busca primero en 05_modelos, luego en carpeta local
MODEL_DIR  = MODELS_05  if os.path.isdir(MODELS_05)  else os.path.join(BASE_DIR, "models")
# OUTPUT_DIR: busca primero en 05_modelos, luego en carpeta local
OUTPUT_DIR = OUTPUTS_05 if os.path.isdir(OUTPUTS_05) else os.path.join(BASE_DIR, "outputs")

os.makedirs(os.path.join(BASE_DIR, "models"),  exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "outputs"), exist_ok=True)


# ── Carga de datos ────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def cargar_datos():
    # ── Expedientes sintéticos Cali ───────────────────────────────────────────
    ruta_exp = os.path.join(OUTPUT_DIR, "lexdata_expedientes_sinteticos_cali.csv")
    if os.path.exists(ruta_exp):
        df_exp = pd.read_csv(ruta_exp)
    else:
        # Generar sintéticos si no existe el CSV
        np.random.seed(42)
        registros = []
        for i in range(10_000):
            tipo     = np.random.choice(TIPOS, p=[0.40, 0.35, 0.15, 0.10])
            despacho = np.random.choice(DESPACHOS_CALI)
            anio     = np.random.choice([2020,2021,2022,2023,2024], p=[0.10,0.15,0.20,0.25,0.30])
            carga    = CARGA_DESPACHO[despacho]
            n_aud    = max(1, int(np.random.gamma(2.5, 2.2)))
            apelacion= 1 if np.random.random() < {"ALIMENTOS":0.38,"VIF":0.20,"HURTO_PATRIMONIAL":0.35,"SUSTANCIAS":0.22}[tipo] else 0
            dur = max(30, int(
                DUR_BASE_CALI[tipo] * carga
                + IVF_CALI_FALLBACK * 2.5
                + n_aud * 9
                + apelacion * 155
                + (2024 - anio) * (-4)
                + np.random.normal(0, DUR_BASE_CALI[tipo] * 0.07)
            ))
            terminado = 1 if (dur <= 730 and np.random.random() > 0.12) else 0
            registros.append({
                "expediente_id":   f"CAL-{i+1:05d}",
                "municipio":       MUNICIPIO_OBJETIVO,
                "tipo_proceso":    tipo,
                "despacho":        despacho,
                "anio_radicacion": anio,
                "ivf_score":       IVF_CALI_FALLBACK,
                "carga_despacho":  carga,
                "n_audiencias":    n_aud,
                "apelacion":       apelacion,
                "duracion_dias":   dur,
                "terminado":       terminado,
            })
        df_exp = pd.DataFrame(registros)

    # ── Alertas ───────────────────────────────────────────────────────────────
    ruta_alertas = os.path.join(OUTPUT_DIR, "lexdata_alertas_cali.csv")
    if os.path.exists(ruta_alertas):
        df_alertas = pd.read_csv(ruta_alertas)
    else:
        p75 = (df_exp.groupby(["tipo_proceso","despacho"])["duracion_dias"]
               .quantile(0.75).reset_index()
               .rename(columns={"duracion_dias":"p75_duracion"}))
        df_alertas = df_exp.merge(p75, on=["tipo_proceso","despacho"], how="left")
        df_alertas["duracion_estimada"] = df_alertas["duracion_dias"]
        df_alertas["riesgo"] = "Bajo"
        df_alertas.loc[df_alertas["duracion_estimada"] > df_alertas["p75_duracion"],       "riesgo"] = "Medio"
        df_alertas.loc[df_alertas["duracion_estimada"] > df_alertas["p75_duracion"] * 1.5, "riesgo"] = "Alto"
        df_alertas = df_alertas[df_alertas["riesgo"] != "Bajo"]

    # ── Feature importance ────────────────────────────────────────────────────
    ruta_fi = os.path.join(OUTPUT_DIR, "feature_importance_cali.csv")
    df_fi = pd.read_csv(ruta_fi) if os.path.exists(ruta_fi) else pd.DataFrame()

    # ── Evolución temporal sintética ──────────────────────────────────────────
    base_vif = 8500
    años = [2020, 2021, 2022, 2023, 2024]
    rows = []
    np.random.seed(7)
    for i, anio in enumerate(años):
        factor = 1 + i * 0.07 + np.random.uniform(-0.03, 0.03)
        rows.append({
            "anio":              anio,
            "vif_total":         int(base_vif * factor),
            "alimentos_total":   int(base_vif * 0.75 * factor),
            "hurto_total":       int(base_vif * 0.35 * factor),
            "sustancias_total":  int(base_vif * 0.18 * factor),
        })
    df_temporal = pd.DataFrame(rows)

    return df_exp, df_alertas, df_fi, df_temporal


@st.cache_resource(show_spinner=False)
def cargar_modelo():
    ruta = os.path.join(MODEL_DIR, "modelo_regresion_cali.pkl")
    if os.path.exists(ruta):
        return joblib.load(ruta)
    return None


# Cargar
with st.spinner("Cargando LexData..."):
    df_exp, df_alertas, df_fi, df_temporal = cargar_datos()
    modelo_data = cargar_modelo()

modelo_ok = modelo_data is not None

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚖️ LexData")
    st.markdown("**Nicho Familiar · Cali**")
    st.divider()

    seccion = st.radio(
        "Sección",
        [
            "📊 Resumen general",
            "⚠️ Alertas tempranas",
            "🔮 Predictor de duración",
            "📈 Análisis por despacho",
            "🤖 Comparación de modelos",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("**Filtros globales**")

    años_disp = sorted(df_exp["anio_radicacion"].unique())
    año_sel   = st.select_slider(
        "Año de radicación", años_disp,
        value=(min(años_disp), max(años_disp))
    )

    tipos_sel = st.multiselect(
        "Tipo de proceso", TIPOS, default=TIPOS
    )

    st.divider()
    if modelo_ok:
        st.success(f"Modelo cargado ✅\nMAPE: {modelo_data.get('mape_test', 11.6):.1f}%")
    else:
        st.warning("Modelo no encontrado\nEjecuta el notebook v4 primero")
    st.caption(f"Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# Filtro base
mask = (
    df_exp["tipo_proceso"].isin(tipos_sel if tipos_sel else TIPOS) &
    df_exp["anio_radicacion"].between(año_sel[0], año_sel[1])
)
df_fil = df_exp[mask].copy()


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 1 — RESUMEN GENERAL
# ─────────────────────────────────────────────────────────────────────────────
if seccion == "📊 Resumen general":

    st.markdown("""
    <div class="lexdata-header">
        <h2 style="margin:0;font-size:20px">LexData · Inteligencia Predictiva Judicial</h2>
        <p style="margin:0;opacity:0.85;font-size:13px">
            Nicho Familiar · Cali, Valle del Cauca · 2020–2024
        </p>
    </div>
    """, unsafe_allow_html=True)

    # KPIs
    c1, c2, c3, c4, c5 = st.columns(5)
    dur_media = df_fil["duracion_dias"].mean()
    n_alto    = int((df_alertas["riesgo"] == "Alto").sum())
    mape_val  = modelo_data.get("mape_test", 11.6) if modelo_ok else 11.6

    c1.metric("Expedientes (filtro)", f"{len(df_fil):,}")
    c2.metric("Duración media", f"{dur_media:.0f} días", f"≈ {dur_media/30:.1f} meses")
    c3.metric("Alertas riesgo alto", f"{n_alto:,}", "casos activos")
    c4.metric("IVF Cali", f"{IVF_CALI_FALLBACK:.0f} / 100", "score ponderado")
    c5.metric("MAPE del modelo", f"{mape_val:.1f}%", "objetivo ≤ 15% ✅")

    st.divider()

    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown('<div class="section-title">Duración media por tipo de proceso</div>', unsafe_allow_html=True)
        dur_tipo = (df_fil.groupby("tipo_proceso")["duracion_dias"]
                    .mean().reset_index()
                    .sort_values("duracion_dias", ascending=True))
        fig = px.bar(
            dur_tipo, x="duracion_dias", y="tipo_proceso", orientation="h",
            color="tipo_proceso", color_discrete_map=COLOR_TIPO,
            text=dur_tipo["duracion_dias"].round().astype(int),
            labels={"duracion_dias": "Días", "tipo_proceso": "Tipo"},
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            showlegend=False, height=280,
            margin=dict(l=0, r=30, t=10, b=30),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, width='stretch')

    with col_r:
        st.markdown('<div class="section-title">Evolución anual del ciclo familiar en Cali</div>', unsafe_allow_html=True)
        fig = go.Figure()
        trazas = [
            ("vif_total",        "VIF",               "#E24B4A", "solid"),
            ("alimentos_total",  "Alimentos",          "#BA7517", "dash"),
            ("hurto_total",      "Hurto patrimonial",  "#378ADD", "dot"),
            ("sustancias_total", "Sustancias",         "#1D9E75", "dashdot"),
        ]
        for col, name, color, dash in trazas:
            fig.add_trace(go.Scatter(
                x=df_temporal["anio"], y=df_temporal[col],
                name=name,
                line=dict(color=color, width=2.5, dash=dash),
                mode="lines+markers", marker=dict(size=7),
            ))
        fig.update_layout(
            height=280, margin=dict(l=0, r=0, t=10, b=30),
            legend=dict(orientation="h", y=-0.28, x=0),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#EEEEEE"),
        )
        st.plotly_chart(fig, width='stretch')

    # Distribución de duración
    st.markdown('<div class="section-title">Distribución de duración por tipo (boxplot)</div>', unsafe_allow_html=True)
    fig = px.box(
        df_fil, x="tipo_proceso", y="duracion_dias",
        color="tipo_proceso", color_discrete_map=COLOR_TIPO,
        notched=True, points=False,
        labels={"tipo_proceso": "Tipo de proceso", "duracion_dias": "Duración (días)"},
    )
    fig.update_layout(
        showlegend=False, height=300,
        margin=dict(l=0, r=0, t=10, b=30),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, width='stretch')

    # Distribución por despacho
    st.markdown('<div class="section-title">Volumen de expedientes por despacho</div>', unsafe_allow_html=True)
    vol_desp = (df_fil.groupby(["despacho","tipo_proceso"]).size()
                .reset_index(name="n"))
    fig = px.bar(
        vol_desp, x="despacho", y="n", color="tipo_proceso",
        color_discrete_map=COLOR_TIPO, barmode="stack",
        labels={"n": "Expedientes", "despacho": "Despacho"},
    )
    fig.update_layout(
        height=320, margin=dict(l=0, r=0, t=10, b=80),
        xaxis_tickangle=-35,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, width='stretch')


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 2 — ALERTAS TEMPRANAS
# ─────────────────────────────────────────────────────────────────────────────
elif seccion == "⚠️ Alertas tempranas":
    st.subheader("Sistema de alertas tempranas — Casos en riesgo de retraso")

    n_alto  = int((df_alertas["riesgo"] == "Alto").sum())
    n_medio = int((df_alertas["riesgo"] == "Medio").sum())
    n_total = len(df_alertas)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Alertas totales",  f"{n_total:,}")
    c2.metric("🔴 Riesgo alto",  f"{n_alto:,}")
    c3.metric("🟡 Riesgo medio", f"{n_medio:,}")
    c4.metric("% sobre total",   f"{n_total/len(df_exp)*100:.1f}%", "expedientes en alerta")

    st.divider()

    nivel_sel = st.multiselect(
        "Filtrar por nivel", ["Alto", "Medio"], default=["Alto", "Medio"]
    )
    df_af = df_alertas[df_alertas["riesgo"].isin(nivel_sel)] if nivel_sel else df_alertas

    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown('<div class="section-title">Alertas por tipo de proceso</div>', unsafe_allow_html=True)
        at = df_af.groupby(["tipo_proceso","riesgo"]).size().reset_index(name="n")
        fig = px.bar(
            at, x="tipo_proceso", y="n", color="riesgo",
            color_discrete_map={"Alto":"#A32D2D","Medio":"#BA7517"},
            barmode="stack",
            labels={"n":"Nº alertas","tipo_proceso":"Tipo de proceso"},
        )
        fig.update_layout(
            height=300, margin=dict(l=0, r=0, t=10, b=30),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, width='stretch')

    with col_r:
        st.markdown('<div class="section-title">Alertas por despacho</div>', unsafe_allow_html=True)
        ad = df_af.groupby(["despacho","riesgo"]).size().reset_index(name="n")
        fig = px.bar(
            ad, x="despacho", y="n", color="riesgo",
            color_discrete_map={"Alto":"#A32D2D","Medio":"#BA7517"},
            barmode="stack",
            labels={"n":"Nº alertas","despacho":"Despacho"},
        )
        fig.update_layout(
            height=300, margin=dict(l=0, r=0, t=10, b=60),
            xaxis_tickangle=-35,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, width='stretch')

    # Tabla
    st.markdown('<div class="section-title">Casos activos con alerta (top 100)</div>', unsafe_allow_html=True)
    cols_tabla = [c for c in
                  ["expediente_id","tipo_proceso","despacho","n_audiencias",
                   "apelacion","duracion_estimada","p75_duracion","riesgo"]
                  if c in df_af.columns]
    st.dataframe(
        df_af[cols_tabla].sort_values("riesgo").head(100).reset_index(drop=True),
        width='stretch', height=400,
    )

    # Descarga
    csv = df_af[cols_tabla].to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ Descargar alertas CSV",
        data=csv, file_name="lexdata_alertas_cali.csv", mime="text/csv",
    )


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 3 — PREDICTOR
# ─────────────────────────────────────────────────────────────────────────────
elif seccion == "🔮 Predictor de duración":
    st.subheader("Predictor de duración — Proceso judicial en Cali")

    col_form, col_res = st.columns([1, 1])

    with col_form:
        st.markdown("**Parámetros del caso**")
        tipo_pred  = st.selectbox("Tipo de proceso", TIPOS)
        desp_pred  = st.selectbox("Despacho", DESPACHOS_CALI)
        anio_pred  = st.selectbox("Año de radicación", [2025, 2024, 2023, 2022])
        aud_pred   = st.slider("Número de audiencias estimadas", 1, 20, 4)
        apel_pred  = st.checkbox("¿Incluye apelación?")

    # ── Predicción ────────────────────────────────────────────────────────────
    carga_val = CARGA_DESPACHO.get(desp_pred, 1.0)

    if modelo_ok:
        # Usar modelo XGBoost real
        le_tipo = modelo_data["le_tipo"]
        le_desp = modelo_data["le_desp"]
        features = modelo_data["features"]

        try:
            tipo_enc = le_tipo.transform([tipo_pred])[0]
            desp_enc = le_desp.transform([desp_pred])[0]
            X_pred   = pd.DataFrame([{
                "ivf_score":        IVF_CALI_FALLBACK,
                "carga_despacho":   carga_val,
                "n_audiencias":     aud_pred,
                "apelacion":        int(apel_pred),
                "anio_radicacion":  anio_pred,
                "tipo_proceso_enc": tipo_enc,
                "despacho_enc":     desp_enc,
            }])[features]
            dur_est = int(np.expm1(modelo_data["modelo"].predict(X_pred)[0]))
            fuente_pred = "🤖 XGBoost (modelo real)"
        except Exception as e:
            st.warning(f"Error en modelo: {e} — usando fórmula de referencia")
            dur_est = None

        if dur_est is None:
            dur_est = int(
                DUR_BASE_CALI[tipo_pred] * carga_val
                + IVF_CALI_FALLBACK * 2.5
                + aud_pred * 9
                + (155 if apel_pred else 0)
                + (2024 - anio_pred) * (-4)
            )
            fuente_pred = "📐 Fórmula de referencia"
    else:
        # Sin modelo — fórmula de referencia
        dur_est = int(
            DUR_BASE_CALI[tipo_pred] * carga_val
            + IVF_CALI_FALLBACK * 2.5
            + aud_pred * 9
            + (155 if apel_pred else 0)
            + (2024 - anio_pred) * (-4)
        )
        fuente_pred = "📐 Fórmula de referencia (modelo no cargado)"

    dur_est = max(30, dur_est)

    # Intervalo de confianza aproximado (±MAPE del modelo)
    mape_val = modelo_data.get("mape_test", 11.6) if modelo_ok else 12.0
    dur_lo   = int(dur_est * (1 - mape_val / 100))
    dur_hi   = int(dur_est * (1 + mape_val / 100))

    hist_base = DUR_BASE_CALI[tipo_pred] * carga_val
    if   dur_est > hist_base * 1.5: riesgo_tag = "🔴 Alto"
    elif dur_est > hist_base * 1.2: riesgo_tag = "🟡 Medio"
    else:                           riesgo_tag = "🟢 Bajo"

    with col_res:
        st.markdown(f"""
        <div class="pred-box">
            <div style="font-size:13px;color:#5F5E5A;margin-bottom:6px">
                Duración estimada de resolución — Cali
            </div>
            <div class="pred-days">{dur_est}</div>
            <div style="font-size:16px;color:#3B1A0A;margin-top:2px">días</div>
            <div style="font-size:13px;color:#5F5E5A;margin-top:8px">
                IC ±{mape_val:.0f}%: {dur_lo} – {dur_hi} días
            </div>
            <hr style="border:none;border-top:1px solid #D2B48C;margin:10px 0">
            <div style="font-size:14px">
                Nivel de riesgo: <strong>{riesgo_tag}</strong>
            </div>
            <div style="font-size:12px;color:#5F5E5A;margin-top:6px">
                Promedio histórico {desp_pred.replace("_"," ")}: {int(hist_base)} días
            </div>
            <div style="font-size:11px;color:#888;margin-top:6px">
                {fuente_pred}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("&nbsp;")

        # IVF
        st.markdown("**IVF Cali**")
        st.progress(int(IVF_CALI_FALLBACK) / 100,
                    text=f"Cali: {IVF_CALI_FALLBACK:.0f} / 100")

    # Feature importance
    if not df_fi.empty:
        st.markdown("---")
        st.markdown('<div class="section-title">Variables más influyentes en la predicción</div>', unsafe_allow_html=True)

        # Detectar columna de label e importancia
        label_col = "label" if "label" in df_fi.columns else df_fi.columns[0]
        imp_col   = "importance_pct" if "importance_pct" in df_fi.columns else df_fi.columns[-1]

        df_fi_top = df_fi.sort_values(imp_col, ascending=False).head(7)
        fig = px.bar(
            df_fi_top.sort_values(imp_col, ascending=True),
            x=imp_col, y=label_col, orientation="h",
            color=imp_col,
            color_continuous_scale=[(0,"#3B6D11"),(1,"#A32D2D")],
            text=df_fi_top.sort_values(imp_col, ascending=True)[imp_col].round(1).astype(str) + "%",
            labels={imp_col: "Importancia (%)", label_col: "Variable"},
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            showlegend=False, coloraxis_showscale=False,
            height=280, margin=dict(l=0, r=40, t=10, b=20),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, width='stretch')


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 4 — ANÁLISIS POR DESPACHO
# ─────────────────────────────────────────────────────────────────────────────
elif seccion == "📈 Análisis por despacho":
    st.subheader("Análisis de rendimiento por despacho — Cali")

    desp_sel = st.selectbox("Seleccionar despacho", sorted(df_fil["despacho"].unique()))
    df_desp  = df_fil[df_fil["despacho"] == desp_sel]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Expedientes",    f"{len(df_desp):,}")
    c2.metric("Duración media", f"{df_desp['duracion_dias'].mean():.0f} días")
    c3.metric("Mediana",        f"{df_desp['duracion_dias'].median():.0f} días")
    c4.metric("Carga relativa", f"{CARGA_DESPACHO.get(desp_sel, 1.0):.2f}",
              "vs media 1.0")

    st.divider()

    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown('<div class="section-title">Duración por tipo de proceso</div>', unsafe_allow_html=True)
        fig = px.violin(
            df_desp, x="tipo_proceso", y="duracion_dias",
            color="tipo_proceso", color_discrete_map=COLOR_TIPO,
            box=True, points=False,
            labels={"duracion_dias": "Días", "tipo_proceso": "Tipo"},
        )
        fig.update_layout(
            showlegend=False, height=320,
            margin=dict(l=0, r=0, t=10, b=30),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, width='stretch')

    with col_r:
        st.markdown('<div class="section-title">Evolución anual de expedientes</div>', unsafe_allow_html=True)
        evol = (df_desp.groupby(["anio_radicacion","tipo_proceso"])
                .size().reset_index(name="n"))
        fig = px.bar(
            evol, x="anio_radicacion", y="n", color="tipo_proceso",
            color_discrete_map=COLOR_TIPO, barmode="stack",
            labels={"n": "Expedientes", "anio_radicacion": "Año"},
        )
        fig.update_layout(
            height=320, margin=dict(l=0, r=0, t=10, b=30),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, width='stretch')

    # Comparativa todos los despachos
    st.markdown('<div class="section-title">Comparativa de duración media — todos los despachos</div>', unsafe_allow_html=True)
    comp = (df_fil.groupby("despacho")["duracion_dias"]
            .agg(["mean","median","count"]).reset_index()
            .sort_values("mean", ascending=True))
    comp.columns = ["despacho","media","mediana","n_exp"]
    comp["color"] = comp["despacho"].map(
        lambda d: "#A32D2D" if d == desp_sel else "#B5D4F4"
    )
    fig = px.bar(
        comp, x="media", y="despacho", orientation="h",
        color="despacho",
        color_discrete_sequence=comp["color"].tolist(),
        text=comp["media"].round().astype(int),
        labels={"media": "Días promedio", "despacho": "Despacho"},
        hover_data={"mediana": True, "n_exp": True},
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        showlegend=False, height=380,
        margin=dict(l=0, r=40, t=10, b=30),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, width='stretch')

    # Tabla resumen
    st.markdown('<div class="section-title">Resumen estadístico por despacho</div>', unsafe_allow_html=True)
    resumen = (df_fil.groupby("despacho")["duracion_dias"]
               .agg(n="count", media="mean", mediana="median",
                    p25=lambda x: x.quantile(0.25),
                    p75=lambda x: x.quantile(0.75))
               .round(0).astype(int).reset_index()
               .sort_values("media", ascending=False))
    st.dataframe(resumen, width='stretch')


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 5 — COMPARACIÓN DE MODELOS
# ─────────────────────────────────────────────────────────────────────────────
elif seccion == "🤖 Comparación de modelos":
    st.subheader("Comparación de modelos — LexData Cali v4")

    st.markdown("""
    Resultados del entrenamiento con 10,000 expedientes sintéticos de Cali.
    Split temporal: **train 2020–2023 / test 2024**.
    Target: `log1p(duración_días)` — XGBoost y ResidualMLP con HuberLoss.
    """)

    df_mod = pd.DataFrame(RESULTADOS_MODELOS).T.reset_index()
    df_mod.columns = ["Modelo", "MAPE (%)", "R²", "MAE (días)"]
    df_mod = df_mod.sort_values("MAPE (%)")
    df_mod["Mejor"] = df_mod["MAPE (%)"] == df_mod["MAPE (%)"].min()

    # Tabla resumen
    st.dataframe(
        df_mod[["Modelo","MAPE (%)","R²","MAE (días)"]].reset_index(drop=True),
        width='stretch',
        column_config={
            "MAPE (%)": st.column_config.ProgressColumn(
                "MAPE (%)", min_value=0, max_value=25, format="%.1f%%"
            ),
            "R²": st.column_config.NumberColumn("R²", format="%.3f"),
            "MAE (días)": st.column_config.NumberColumn("MAE (días)", format="%.0f d"),
        }
    )

    st.divider()

    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown('<div class="section-title">MAPE por modelo (menor = mejor)</div>', unsafe_allow_html=True)
        mejor_mape = df_mod["MAPE (%)"].min()
        colores = ["#C44E52" if m == mejor_mape else "#4C72B0" for m in df_mod["MAPE (%)"]]
        fig = go.Figure(go.Bar(
            x=df_mod["Modelo"], y=df_mod["MAPE (%)"],
            marker_color=colores,
            text=[f"{v:.1f}%" for v in df_mod["MAPE (%)"]],
            textposition="outside",
        ))
        fig.add_hline(y=15, line_dash="dash", line_color="green",
                      annotation_text="Objetivo 15%", annotation_position="top right")
        fig.update_layout(
            height=320, margin=dict(l=0, r=0, t=20, b=30),
            yaxis_title="MAPE (%)",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, width='stretch')

    with col_r:
        st.markdown('<div class="section-title">R² por modelo (mayor = mejor)</div>', unsafe_allow_html=True)
        mejor_r2 = df_mod["R²"].max()
        colores_r2 = ["#C44E52" if r == mejor_r2 else "#4C72B0" for r in df_mod["R²"]]
        fig = go.Figure(go.Bar(
            x=df_mod["Modelo"], y=df_mod["R²"],
            marker_color=colores_r2,
            text=[f"{v:.3f}" for v in df_mod["R²"]],
            textposition="outside",
        ))
        fig.update_layout(
            height=320, margin=dict(l=0, r=0, t=20, b=30),
            yaxis_title="R²",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, width='stretch')

    st.divider()

    # Interpretación
    st.markdown("**Interpretación de resultados**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**XGBoost ← modelo en producción**\nMAPE 11.6% · R² 0.540\nMejor MAPE con arquitectura simple y entrenamiento rápido.")
    with col2:
        st.info("**ResidualMLP (Deep Learning)**\nMAPE 11.7% · R² 0.520\nPerformance equivalente a XGBoost. Escala mejor con datos reales y features de texto.")
    with col3:
        st.warning("**Lasso — excluido**\nMAPE 18.9% · R² -0.02\nPerformance por debajo del objetivo. La penalización L1 es demasiado agresiva para este dataset.")

    st.markdown("""
    **Siguiente paso:** cuando el CSJ exporte duraciones reales de SICOF, reentrenar con
    `retrain_model_42municipios.py` — se espera que R² suba a ~0.75 con features adicionales
    (juez asignado, tipo de demandante, historial de audiencias reales).
    """)
