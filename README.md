# ⚖️ LexData — Plataforma de Inteligencia Predictiva Judicial

Proyecto de analítica de datos enfocado en el **nicho familiar en el Valle del Cauca**, orientado a la modelación, monitoreo y análisis del comportamiento de los procesos judiciales.

El sistema integra técnicas de **machine learning, análisis exploratorio y visualización interactiva** para apoyar la toma de decisiones en el contexto judicial.

Principales líneas de trabajo:

* Predicción de duración de procesos judiciales
* Sistema de alertas tempranas para identificación de retrasos
* Identificación de variables críticas que afectan la duración
* Visualización analítica por región y despacho judicial

---

## 🚀 Componentes del proyecto

### 1. Modelo predictivo

* Tipo: Modelo de regresión supervisada

* Objetivo: Estimar la duración de procesos judiciales (en días)

* Variable objetivo: `duracion_dias`

* Variables relevantes:

  * Tipo de proceso
  * Municipio
  * Carga del despacho
  * Número de audiencias
  * Índice de vulnerabilidad familiar (IVF)
  * Presencia de apelación

* Métrica de evaluación:

  * MAPE ≈ 12.4%
  * Nivel de error dentro del rango aceptable para modelos predictivos aplicados

---

### 2. Sistema de alertas tempranas

Módulo orientado a la detección de procesos con alta probabilidad de retraso.

* Clasificación de riesgo:

  * Alto: duración superior a 1.5 * P75
  * Medio: duración superior a P75
  * Bajo: comportamiento esperado

* Metodología:

  * Cálculo de percentiles (P75) por tipo de proceso y despacho
  * Comparación con duración estimada o histórica
  * Generación de alertas sobre casos activos

---

### 3. Dashboard interactivo

Aplicación desarrollada en **Streamlit** para la exploración y análisis de los datos.

Incluye:

* Visualización de indicadores clave (KPIs)
* Mapa geográfico del índice de vulnerabilidad familiar (IVF)
* Panel de alertas tempranas
* Simulador predictivo de duración de procesos
* Análisis de desempeño por despacho judicial

---

## 📁 Estructura del proyecto


```
LexData/
│
├── notebooks/
│   ├── lexdata_modelo_predictivo_demo.ipynb
│   ├── lexdata_scraping_nicho_familiar_v8.ipynb
│   └── problema_de_regresión_IA_1.ipynb
│
├── data_judicial/
│   ├── lexdata_co_ocurrencia_IVF_v6.csv
│   ├── lexdata_expedientes_sinteticos.csv
│   ├── lexdata_alertas_tempranas.csv
│   └── lexdata_ivf_resumen_municipios.csv
│
├── models/
│   ├── modelo_regresion.pkl
│   └── feature_importance.csv
│
└── lexdata_streamlit_app.py
```

---

## ⚙️ Instalación

Instalar las dependencias necesarias:

```
pip install streamlit pandas numpy plotly joblib scikit-learn
```

---

## ▶️ Ejecución del dashboard

Ejecutar el siguiente comando desde la raíz del proyecto:

```
python -m streamlit run lexdata_streamlit_app.py
```

Una vez iniciado, el sistema estará disponible en:

* Local: http://localhost:8501

---

## 📊 Funcionalidades principales

### Resumen general

* Visualización de indicadores clave del sistema
* Análisis de duración promedio de procesos
* Evolución temporal de variables asociadas

---

### Mapa IVF

* Representación geográfica del índice de vulnerabilidad familiar
* Identificación de zonas con mayor riesgo
* Comparación entre municipios

---

### Alertas tempranas

* Identificación de procesos en riesgo de retraso
* Clasificación por nivel de riesgo
* Filtros por municipio, tipo de proceso y despacho

---

### Predictor

* Simulación de duración de procesos judiciales
* Ajuste dinámico de variables de entrada
* Estimación con intervalos de confianza

---

### Análisis por juzgado

* Evaluación de desempeño por despacho
* Distribución de duración por tipo de proceso
* Comparativa entre juzgados

---

## 🔍 Fuente y procesamiento de datos

* Integración de datos mediante scraping y consolidación estructurada
* Generación de datasets analíticos para entrenamiento y evaluación
* Limpieza, transformación y normalización de variables
* Generación de datos sintéticos para pruebas y visualización

---

## 🎯 Objetivo del proyecto

Apoyar la toma de decisiones en el sistema judicial mediante:

* Anticipación de congestión en despachos
* Priorización de casos críticos
* Identificación de patrones territoriales
* Optimización en la gestión de procesos

---

## 👥 Equipo

Proyecto desarrollado para la materia **Data Thinking**
Entrega académica — Segunda fase

