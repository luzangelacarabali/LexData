## LexData — Arquitectura Simplificada (Enfoque Geográfico)

La unidad de análisis de LexData es la **zona geográfica de comisaría**, no la familia ni el expediente individual. El sistema agrega conteos de casos por zona, calcula un Índice de Vulnerabilidad Familiar (IVF) a nivel territorial, y genera alertas cuando una zona supera umbrales estadísticos. No se gestionan expedientes, partes procesales ni vinculaciones familiares.

Esta arquitectura es un **monolito modular** desplegado como una sola aplicación. Apropiada para el MVP (piloto con 3 comisarías en Cali, meses 1–6).

---

## Paso 1 — Módulos y responsabilidades

Todos los módulos viven en un único repositorio y se despliegan como una sola aplicación. Se comunican mediante imports directos. Cada módulo tiene su propio paquete Python con límites claros.

**Módulo de Autenticación** (`app/auth/`) maneja identidad: registro de organizaciones (comisarías, entes de control), login, tokens JWT, roles (gestor, admin, supervisor ICBF) y revocación de sesiones.

**Módulo de Ingesta de Datos** (`app/ingesta/`) recibe y valida los datos de entrada — archivos CSV o conexiones a fuentes oficiales — y los transforma en conteos agregados por zona geográfica y tipo de proceso (alimentos, VIF, sustancias, hurto patrimonial). No almacena datos individuales de expedientes ni partes.

**Módulo de Motor IVF** (`app/ivf/`) calcula el Índice de Vulnerabilidad Familiar por zona geográfica en modo **batch**. Un job periódico (cron o Celery beat) recalcula los scores usando los conteos agregados más recientes. No hay predicciones en tiempo real ni caché en memoria. El resultado es un score por zona que alimenta alertas y dashboards.

**Módulo de Alertas** (`app/alertas/`) implementa reglas de **umbral geográfico**: cuando una zona supera el percentil 90 en IVF, o cuando el conteo de casos de un tipo específico crece más de X% respecto al período anterior, se genera una alerta. No hay alertas procesales (vencimientos, audiencias).

**Módulo de Panel Analítico** (`app/analytics/`) sirve los dashboards: mapa de calor territorial por zona, ranking de zonas por IVF, evolución temporal de conteos y scores. Consulta PostgreSQL con vistas materializadas.

**Módulo de Notificaciones** (`app/notificaciones/`) entrega alertas por email y genera reportes PDF para entes de control.

---

## Paso 2 — Entry point único (FastAPI)

La aplicación tiene un único servidor **FastAPI**. Cada módulo registra su `APIRouter` con su prefijo: `POST /api/ingesta/upload`, `GET /api/ivf/zonas/{zona_id}`, `GET /api/alertas/activas`.

Validación JWT como dependencia (`Depends(get_current_user)`). Rate limiting con `slowapi`. SSL termination con **Nginx** o **Caddy** delante de la app.

Herramienta: **FastAPI** con **Uvicorn**. **Nginx** como proxy reverso.

---

## Paso 3 — Base de datos PostgreSQL simplificada

Una única instancia de **PostgreSQL** con dos schemas:

**Schema `geo`**: tablas de referencia territorial — `zona_geografica` (id, nombre, polígono, comisaría asignada), `comisaria` (id, nombre, municipio, dirección), `conteo_casos` (zona_id, tipo_proceso, periodo, cantidad). Aquí vive toda la información geográfica y los conteos agregados.

**Schema `ivf`**: tablas del motor — `score_zona` (zona_id, periodo, score_ivf, variables_componentes JSONB), `modelo_version` (id, fecha, parámetros, métricas). Los scores se recalculan en batch; no hay caché Redis.

Las vistas materializadas para dashboards (`mv_calor_territorial`, `mv_ranking_zonas`, `mv_evolucion_temporal`) viven en el schema `ivf` y se refrescan con cron.

No hay schema `core` transaccional. No hay tablas de expedientes, partes, vinculaciones familiares ni eventos procesales.

---

## Paso 4 — Comunicación entre módulos

Al vivir en el mismo proceso, la comunicación es directa:

**Llamadas directas**: el endpoint de analytics importa `ivf_service.obtener_ranking_zonas()` y lo llama. Sin latencia de red.

**Jobs batch**: el recálculo de IVF y el refresco de vistas materializadas corren como tareas periódicas (Celery beat o cron). No hay bus de eventos complejo — el flujo es lineal: ingesta → conteos → IVF batch → alertas → notificaciones.

---

## Paso 5 — Despliegue (Docker Compose en VPS)

El `docker-compose.yml` levanta tres servicios:

- `app`: FastAPI + Uvicorn + Celery worker (mismo contenedor)
- `db`: PostgreSQL
- `nginx`: proxy reverso con SSL (Let's Encrypt)

No se necesita Redis (sin caché, sin broker complejo). Para las tareas batch, Celery puede usar PostgreSQL como broker con `django-db` backend, o se reemplazan por cron jobs simples dentro del contenedor.

VPS básico: 2 vCPU, 4 GB RAM. Costo: **USD $20–40/mes**.

---

## Paso 6 — CI/CD y observabilidad

Un pipeline en **GitHub Actions**: tests → build Docker → push a registry → deploy al VPS vía SSH.

**Logging estructurado** en JSON a stdout. **Métricas básicas** con Prometheus + Grafana (o Grafana Cloud free tier): latencia de endpoints, conteo de alertas generadas, errores HTTP.

Sin tracing distribuido — es un monolito.

---

## Orden de construcción recomendado

1. Módulo de Autenticación (bloquea todo lo demás)
2. Schema `geo` + Módulo de Ingesta (cargar datos de zonas y conteos)
3. Módulo de Motor IVF batch (calcular scores por zona)
4. Módulo de Alertas por umbral geográfico
5. Módulo de Panel Analítico (mapa de calor, rankings)
6. Módulo de Notificaciones y reportes

El sistema entrega valor desde el paso 3: con los conteos y el IVF por zona, las comisarías ya pueden priorizar recursos.

---

## Diferencias con arquitectura original de análisis por familia

| Aspecto | Arquitectura original (por familia) | Arquitectura actual (geográfica) |
|---|---|---|
| **Unidad de análisis** | Expediente individual + núcleo familiar | Zona geográfica de comisaría |
| **Datos almacenados** | Expedientes, partes (demandante, demandado, menores), audiencias, estados procesales | Conteos agregados por zona y tipo de proceso |
| **Vinculación familiar** | Automática entre expedientes del mismo núcleo | Eliminada — no se rastrean familias |
| **Pseudoanonimización** | Requerida para datos personales | No necesaria — solo datos agregados |
| **Motor IVF** | Predicción en tiempo real por expediente, caché Redis | Cálculo batch por zona, sin caché |
| **Alertas** | Procesales (día 12 hábil, vencimientos, audiencias) | Por umbral geográfico (percentil 90, crecimiento anómalo) |
| **Base de datos** | Schema `core` transaccional + schema `ivf` + schema `analytics` | Schema `geo` + schema `ivf` únicamente |
| **Infraestructura** | App + PostgreSQL + Redis + Nginx | App + PostgreSQL + Nginx (sin Redis) |
| **Complejidad** | Alta — gestión de partes, vinculaciones, eventos procesales | Baja — ingesta de conteos, cálculo batch, dashboards |
