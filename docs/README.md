# LexData ⚖️

**Plataforma de Inteligencia Predictiva para Procesos Judiciales de Familia**  
Valle del Cauca · Colombia · 2025

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.45-red)](https://streamlit.io)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0-orange)](https://xgboost.readthedocs.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## ¿Qué es LexData?

El sistema judicial colombiano tramita más de 3 millones de casos nuevos al año con un índice de congestión del 52.9%. En el nicho de derecho de familia — violencia intrafamiliar (VIF), cuotas alimentarias, medidas de protección ICBF e inasistencia alimentaria — esta congestión es especialmente severa y sus causas están poco comprendidas porque no existe una herramienta analítica que conecte esos cuatro tipos de proceso.

LexData propone que estos casos no son independientes: son manifestaciones de un **Ciclo de Vulnerabilidad Familiar**. Construimos una plataforma que mide ese ciclo, predice la duración de los procesos y genera alertas tempranas para operadores judiciales.

### Componentes

| # | Componente | Descripción |
|---|---|---|
| 1 | Pipeline ETL | Extracción desde datos.gov.co vía API Socrata (6 fuentes) |
| 2 | Índice IVF | Score compuesto ponderado para 42 municipios del Valle del Cauca |
| 3 | Modelo predictivo | XGBoost regressor — MAPE 11.6%, R² 0.54 |
| 4 | Red neuronal | ResidualMLP (PyTorch) — arquitectura con skip connections |
| 5 | Alertas tempranas | Clasificación por percentiles P75 por tipo y despacho |
| 6 | Survival analysis | Kaplan-Meier + Cox Proportional Hazards (lifelines) |
| 7 | Dashboard | Streamlit con 5 secciones interactivas |
| 8 | Paper académico | Formato Springer LNCS — listo para envío |

---

## Resultados del modelo

| Modelo | MAPE | R² | MAE |
|---|---|---|---|
| Ridge | 12.7% | 0.437 | 55.6 días |
| Lasso | 18.9% | -0.020 | 88.1 días |
| GBM | 11.7% | 0.542 | 50.5 días |
| **XGBoost** ✅ | **11.6%** | **0.540** | **50.0 días** |
| ResidualMLP (DL) | 11.7% | 0.520 | 49.8 días |

**Split temporal:** train 2020–2023 / test 2024  
**Variables dominantes:** Apelación (44.7%) + N.° de audiencias (42.3%) = 87% de la importancia  
**Alertas generadas (Cali):** 66 riesgo alto · 1,073 riesgo medio · 22.8% del total

---

## Estructura del proyecto

```
LexData/
│
├── pyproject.toml                   ← Dependencias y configuración del proyecto
├── .env.example                     ← Variables de entorno (copiar a .env)
├── .gitignore
│
├── cuadernos/
│   ├── 01_web_scraping/
│   │   └── lexdata_scraping_nicho_familiar_v9.ipynb   ← Pipeline ETL
│   ├── 02_eda/
│   │   └── eda_nicho_familiar.ipynb                   ← Análisis exploratorio
│   ├── 03_data_judicial/
│   │   └── construccion_ivf.ipynb                     ← Cálculo IVF
│   ├── 04_subir_datos_a_db/
│   │   └── carga_postgres.ipynb                       ← Carga a PostgreSQL
│   ├── 05_modelos_de_prediccion/
│   │   ├── lexdata_modelo_predictivo_cali_v4.ipynb    ← Modelo principal
│   │   ├── models/
│   │   │   ├── modelo_regresion_cali.pkl              ← XGBoost serializado
│   │   │   ├── modelo_nn_cali.pt                      ← ResidualMLP (PyTorch)
│   │   │   └── modelo_cox_cali.pkl                    ← Cox PH (lifelines)
│   │   └── outputs/
│   │       ├── lexdata_expedientes_sinteticos_cali.csv
│   │       ├── lexdata_alertas_cali.csv
│   │       └── feature_importance_cali.csv
│   └── 06_desarrollo_web/
│       └── lexdata_streamlit_app_v2.py                ← Dashboard Streamlit
│
├── data/
│   ├── raw/                         ← Datos crudos del ETL (no modificar)
│   │   ├── lexdata_vif_inmlcf.csv
│   │   ├── lexdata_vif_policia.csv
│   │   ├── lexdata_icbf_medidas.csv
│   │   ├── lexdata_inasistencia_alimentaria.csv
│   │   ├── lexdata_csj_alimentos.csv
│   │   ├── lexdata_comisarias_directorio.csv
│   │   ├── lexdata_co_ocurrencia_IVF_v9.csv
│   │   └── lexdata_ivf_resumen_municipios_v9.csv
│   └── processed/                   ← Generados por los notebooks
│
├── documentos/
│   ├── README.md                    ← Este archivo
│   ├── INFORME_LEXDATA.md           ← Informe técnico completo
│   ├── lexdata_nicho_familiar.pdf   ← Propuesta estratégica
│   └── presentation_lexdata.pdf     ← Presentación académica
│
└── papel/                           ← Paper académico (Springer LNCS)
    ├── main.tex
    ├── main.pdf
    ├── biblio.bib
    ├── llncs.cls
    ├── splncs04.bst
    └── figures/
        ├── Fig1_eda.png
        ├── Fig2_evaluacion.png
        ├── Fig3_importancia.png
        ├── Fig4_survival.png
        └── Fig5_cox.png
```

---

## Instalación

### Opción A — Con `uv` (recomendado)

[`uv`](https://docs.astral.sh/uv/) es el gestor de paquetes moderno para Python. Es 10-100x más rápido que pip y maneja entornos virtuales automáticamente.

```bash
# 1. Instalar uv (una sola vez)
# Windows (PowerShell):
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Mac / Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clonar el repositorio
git clone https://github.com/luzangelcarabali/LexData.git
cd LexData

# 3. Instalar dependencias base
uv sync

# 4. Instalar con extras según lo que necesites:
uv sync --extra notebooks     # Para ejecutar los Jupyter notebooks
uv sync --extra dl            # Para el modelo de deep learning (PyTorch)
uv sync --extra shap          # Para los gráficos SHAP
uv sync --extra dev           # Todo (desarrollo completo)
```

### Opción B — Con pip (clásico)

```bash
git clone https://github.com/luzangelcarabali/LexData.git
cd LexData
pip install -e .

# Con extras:
pip install -e ".[notebooks]"
pip install -e ".[dl]"
pip install -e ".[dev]"
```

### Variables de entorno

```bash
# Copiar el ejemplo y completar con tus credenciales
cp .env.example .env
```

Editar `.env`:
```env
DB_USER=postgres
DB_PASSWORD=tu_contraseña
DB_HOST=localhost
DB_PORT=5432
DB_NAME=lexdata
```

---

## Uso

### Dashboard interactivo

```bash
# Con uv:
uv run streamlit run cuadernos/06_desarrollo_web/lexdata_streamlit_app_v2.py

# Con pip:
streamlit run cuadernos/06_desarrollo_web/lexdata_streamlit_app_v2.py
```

Abre automáticamente en `http://localhost:8501`

**El dashboard tiene 5 secciones:**
- **Resumen general** — KPIs, duración por tipo, evolución anual del ciclo familiar
- **Alertas tempranas** — Casos en riesgo de retraso con filtros por nivel
- **Predictor de duración** — Ingresa parámetros de un caso y obtiene estimación con intervalo de confianza
- **Análisis por despacho** — Comparativa de rendimiento entre juzgados de Cali
- **Comparación de modelos** — Ridge / GBM / XGBoost / ResidualMLP con métricas y gráficos

### Ejecutar los notebooks

```bash
# Con uv (incluye Jupyter):
uv run jupyter notebook

# Orden de ejecución recomendado:
# 1. cuadernos/01_web_scraping/lexdata_scraping_nicho_familiar_v9.ipynb
# 2. cuadernos/04_subir_datos_a_db/carga_postgres.ipynb
# 3. cuadernos/05_modelos_de_prediccion/lexdata_modelo_predictivo_cali_v4.ipynb
# 4. cuadernos/06_desarrollo_web/lexdata_streamlit_app_v2.py
```

### Compilar el paper (requiere LaTeX)

```bash
cd papel
pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

O subir la carpeta `papel/` como ZIP a [Overleaf](https://overleaf.com).

---

## Metodología

### Índice de Vulnerabilidad Familiar (IVF)

El IVF es un score compuesto normalizado por población municipal (escala 0–100):

```
IVF = 0.40 × VIF_norm + 0.30 × Alimentos_norm + 0.20 × ICBF_norm + 0.10 × Inasistencia_norm
```

| Dimensión | Peso | Fuente | Tipo |
|---|---|---|---|
| Violencia intrafamiliar | 40% | INMLCF + Policía SIEDCO | Delito/lesión directa |
| Alimentos familia | 30% | CSJ Rama Judicial | Civil — ruptura económica |
| Medidas ICBF | 20% | ICBF comisarías | Intervención institucional |
| Inasistencia alimentaria | 10% | Fiscalía SPOA | Penal — incumplimiento familiar |

### Modelo predictivo

- **Target:** `log1p(duración_días)` — transformación para reducir skew
- **Split:** train 2020–2023 / test 2024 (temporal, no aleatorio)
- **Features:** IVF score, carga del despacho, número de audiencias, apelación, año de radicación, tipo de proceso (encoded), despacho (encoded)
- **Selección:** grid search sobre 32 combinaciones de hiperparámetros XGBoost

### Sistema de alertas

```
Alto  → duración estimada > 1.5 × P75 (por tipo y despacho)
Medio → duración estimada > P75
Bajo  → resto
```

---

## Hallazgos principales

1. **Apelación y audiencias dominan:** juntas explican el 87% de la importancia del modelo. Una apelación añade ~155 días en promedio. Cada audiencia adicional suma ~9 días.

2. **El IVF predice el patrón territorial:** municipios con IVF > 62 (percentil 75) tienen duraciones consistentemente más largas, confirmado por el análisis de supervivencia Cox PH (HR = 0.85 por desviación estándar de IVF).

3. **VIF se resuelve más rápido que HURTO_PATRIMONIAL:** las curvas Kaplan-Meier muestran que VIF alcanza 50% de resolución al día ~180 vs. ~280 para hurto patrimonial (log-rank p < 0.001).

4. **XGBoost y ResidualMLP empatan:** con datos sintéticos ambos logran MAPE ~11.7%. Con datos reales del CSJ y features adicionales, la red neuronal debería escalar mejor.

---

## Limitaciones

- Los resultados actuales se basan en **10,000 expedientes sintéticos** calibrados con estadísticas del CSJ. Se necesitan datos reales del sistema SIAU para validación definitiva.
- `procesos_alimentos` (CSJ, ID `x5yx-c7vy`) retornó solo 6 filas — la dimensión Alimentos del IVF usa proxy temporal.
- La Policía SIEDCO no retornó resultados para el filtro Valle del Cauca.
- El modelo está focalizado en **Cali**. La expansión a los 42 municipios requiere datos de despachos por municipio.

---

## Trabajo futuro

- [ ] Integrar datos reales del CSJ (sistema SIAU)
- [ ] Modelos especializados por tipo de proceso (VIF, alimentos, custodia)
- [ ] Piloto con 3 organizaciones: comisaría de familia Cali, consultorio jurídico UAO/ICESI, abogado litigante privado
- [ ] Despliegue del análisis de supervivencia en el dashboard (probabilidad de resolución en tiempo real)
- [ ] Expansión geográfica a Bogotá, Medellín y Barranquilla
- [ ] Evaluación formal con actores judiciales

---

## Créditos

**Autores:** Luz Angela Carabali Mosquera · Nicolas Zapata Ocampo · Laura Daniela Astudillo  
**Asignatura:** Data Thinking — 7.° Semestre  
**Institución:** Universidad Autónoma de Occidente · Cali, Colombia  
**Periodo:** 2026-1  
**Asesor:** Prof. Juan Manuel Núñez

---

## Licencia

MIT License — ver archivo [LICENSE](LICENSE) para detalles.

El código es de uso libre para investigación y aplicaciones no comerciales.
Se agradece la atribución si adaptan o extienden LexData.
