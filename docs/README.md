# LexData — Plataforma de Inteligencia Predictiva Judicial

Proyecto de analítica de datos enfocado en el **nicho familiar en el Valle del Cauca**, orientado a la modelación, monitoreo y análisis del comportamiento de los procesos judiciales.

**Asignatura:** Data Thinking — 7.° Semestre  
**Institución:** Universidad Autónoma de Occidente — Cali, Colombia  
**Periodo:** 2025-1

**Autores:** Luz Angela Carabali Mosquera, Nicolas Zapata Ocampo, Laura Daniela Astudillo

---

## Componentes del proyecto

1. **Pipeline ETL** — Extracción de datos desde datos.gov.co (API Socrata) con 6 fuentes de datos
2. **Modelo predictivo** — XGBoost regressor (MAPE: 15.5%, R²: 0.870) para estimar duración de procesos
3. **Índice de Vulnerabilidad Familiar (IVF)** — Score compuesto ponderado para 42 municipios
4. **Sistema de alertas tempranas** — Detección de casos con riesgo de retraso (percentil 75)
5. **Dashboard interactivo** — Streamlit con 5 secciones analíticas
6. **Survival Analysis** — Kaplan-Meier + Cox Proportional Hazards
7. **Paper académico** — Formato Springer LNCS listo para publicación

---

## Estructura del proyecto

```
LexData/
│
├── paper/                           ← Paper académico (Springer LNCS)
│   ├── main.tex                     ← Código LaTeX del paper
│   ├── main.pdf                     ← PDF compilado (9 páginas)
│   ├── biblio.bib                   ← 23 referencias académicas
│   ├── llncs.cls                    ← Clase LaTeX Springer
│   ├── splncs04.bst                 ← Estilo bibliográfico
│   ├── readme.txt / history.txt     ← Documentación de la plantilla
│   └── figures/                     ← Figuras del paper
│       ├── Fig1_eda.png
│       ├── Fig2_evaluacion.png
│       ├── Fig3_importancia.png
│       ├── Fig4_survival.png
│       └── Fig5_cox.png
│
├── data/
│   ├── raw/                         ← Datos crudos del ETL (inmutables)
│   │   ├── lexdata_vif_inmlcf.csv
│   │   ├── lexdata_comisarias_directorio.csv
│   │   ├── lexdata_co_ocurrencia_IVF_v7.csv
│   │   ├── lexdata_co_ocurrencia_IVF_v8.csv
│   │   ├── lexdata_icbf_medidas.csv
│   │   ├── lexdata_inasistencia_alimentaria.csv
│   │   └── lexdata_ivf_resumen_municipios.csv
│   └── processed/                   ← Datos generados por el modelo
│       ├── lexdata_expedientes_sinteticos.csv  (5,000 registros)
│       └── lexdata_alertas_tempranas.csv       (1,097 alertas)
│
├── models/                          ← Modelos serializados
│   ├── modelo_regresion.pkl         ← XGBoost optimizado
│   ├── modelo_cox.pkl               ← Cox Proportional Hazards
│   └── feature_importance.csv       ← Importancia de variables
│
├── outputs/                         ← Figuras generadas
│   ├── eda_duracion_familiar.png
│   ├── evaluacion_modelo_regresion.png
│   ├── feature_importance.png
│   ├── survival_kaplan_meier.png
│   └── cox_hazard_ratios.png
│
├── notebooks/                       ← Código fuente
│   ├── lexdata_streamlit_app.py     ← Dashboard Streamlit (687 líneas)
│   ├── lexdata_modelo_predictivo_demo.ipynb  ← Pipeline ML + Survival
│   └── lexdata_scraping_nicho_familiar_v8.ipynb  ← Pipeline ETL
│
├── docs/                            ← Documentación
│   ├── INFORME_LEXDATA.md           ← Informe técnico completo
│   └── README.md                    ← Este archivo
│
├── Meeting Transcription.txt        ← Transcripción de clases
├── lexdata_nicho_familiar.pdf       ← Propuesta estratégica
└── presentation_lexdata.pdf         ← Presentación académica
```

---

## Instalación

```bash
# Clonar o copiar el proyecto
# Luego instalar dependencias:
pip install streamlit pandas numpy plotly joblib scikit-learn xgboost lifelines
```

---

## Cómo usar

### Dashboard interactivo (Streamlit)
```bash
streamlit run notebooks/lexdata_streamlit_app.py
```
Disponible en: http://localhost:8501

### Compilar el paper (requiere LaTeX)
```bash
cd paper
pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

### Ejecutar el pipeline completo
```bash
# 1. Scraping de datos:
jupyter notebook notebooks/lexdata_scraping_nicho_familiar_v8.ipynb

# 2. Modelo predictivo:
jupyter notebook notebooks/lexdata_modelo_predictivo_demo.ipynb
```

---

## Resultados del modelo

| Métrica | Valor | Objetivo |
|---------|-------|----------|
| MAPE | 15.53% | ≤ 15% |
| MAE | 37 días | — |
| R² | 0.870 | — |

**Variables más influyentes:** Apelación (44.7%), N.° de audiencias (42.3%)

**Alertas generadas:** 50 alto riesgo, 1,047 medio riesgo

---

## Paper académico

El paper sigue el formato **Springer LNCS** (Lecture Notes in Computer Science) e incluye:

- Abstract con resultados cuantitativos
- Introduction con hipótesis del "Ciclo de Vulnerabilidad Familiar"
- Related Works (ML en sistemas judiciales, índices de vulnerabilidad, survival analysis)
- Research Methodology (ETL pipeline, IVF, modelos, alertas)
- Experimental Case (Valle del Cauca, 42 municipios)
- Discussion con 5 figuras (EDA, evaluación, features, survival, Cox)
- Conclusions y Future Work
- 23 referencias académicas (ventana 2022-2026)

---

## Publicación

Este proyecto está preparado para su envío a conferencias y revistas académicas siguiendo las indicaciones del profesor Juan Manuel Núñez. Para someterlo:

1. Subir `paper/` como ZIP a Overleaf
2. Completar ORCIDs de los autores
3. Seleccionar revista o conferencia objetivo
4. Traducir a inglés si es necesario
