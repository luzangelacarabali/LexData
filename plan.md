Ahora el paso a paso detallado para construir esta arquitectura como **Monolito Modular** — la opción correcta para el MVP (piloto con 3 organizaciones, ~300 casos, meses 1–6):

---

## Paso 1 — Definir los módulos y sus responsabilidades

Todos los módulos viven en un único repositorio y se despliegan como una sola aplicación. Se comunican entre sí mediante imports directos (llamadas a funciones) o un bus de eventos interno. Cada módulo tiene su propio paquete Python con límites claros: no se accede a las tablas de otro módulo directamente, sino a través de su interfaz pública. Para LexData se definen seis módulos:

**Módulo de Autenticación** (`app/auth/`) maneja todo lo relacionado con identidad: registro de organizaciones (comisarías, consultorios), login, emisión de tokens JWT, roles (gestor, admin, supervisor ICBF) y revocación de sesiones. Ningún otro módulo gestiona usuarios; los demás importan las dependencias de auth para validar permisos.

**Módulo de Gestión de Casos** (`app/casos/`) es el núcleo transaccional. Almacena los expedientes, sus partes (demandante, demandado, menores), el tipo de proceso (alimentos / VIF / sustancias / hurto patrimonial), el historial de audiencias y el estado procesal. La lógica de vinculación automática entre expedientes del mismo núcleo familiar vive aquí.

**Módulo de Motor IVF** (`app/ivf/`) es el diferenciador competitivo. Recibe llamadas directas desde el módulo de casos o escucha eventos internos de nuevos casos y actualizaciones, calcula el Índice de Vulnerabilidad Familiar (IVF) por expediente y núcleo familiar, y expone sus funciones al resto de la aplicación. Se entrena de manera batch con los datos históricos y sirve predicciones en tiempo real con caché en memoria.

**Módulo de Motor de Alertas** (`app/alertas/`) implementa las reglas procesales: día 12 hábil antes de vencimiento en alimentos, medidas de protección VIF próximas a vencer, audiencias pendientes. Escucha eventos internos y genera notificaciones hacia el módulo de notificaciones.

**Módulo de Panel Analítico** (`app/analytics/`) sirve los dashboards: mapa de calor territorial, KPIs de gestión, evolución del IVF por municipio. Consulta la misma base de datos PostgreSQL usando vistas materializadas o queries optimizadas para no impactar las operaciones transaccionales.

**Módulo de Notificaciones** (`app/notificaciones/`) entrega alertas por email, push y genera reportes PDF para entes de control. Es el consumidor final de los eventos de alerta internos.

---

## Paso 2 — Definir el entry point único (FastAPI con routing interno)

La aplicación tiene un único servidor **FastAPI** que actúa como punto de entrada. Cada módulo registra su propio router con su prefijo de ruta. No hay API Gateway externo ni proxy reverso complejo.

Primero, **enrutamiento por módulo**: cada módulo expone un `APIRouter` que se monta en la app principal. `POST /api/casos` lo resuelve el router del módulo de casos; `GET /api/ivf/{expediente_id}` lo resuelve el router del módulo IVF. Todo dentro del mismo proceso.

Segundo, **validación de JWT como dependencia**: un middleware o dependencia de FastAPI (`Depends(get_current_user)`) valida el token en cada request. No hay servicios internos que necesiten headers reenviados — todo es una llamada a función.

Tercero, **rate limiting**: middleware simple con `slowapi` o similar, por organización (plan básico: 100 req/min; plan pro: ilimitado).

Cuarto, **SSL termination**: un **Nginx** o **Caddy** delante de la app maneja los certificados. La app FastAPI corre en HTTP detrás del proxy.

Herramienta: **FastAPI** con **Uvicorn** como servidor ASGI. Un **Nginx** o **Caddy** como proxy reverso para SSL.

---

## Paso 3 — Configurar el bus de eventos interno

El bus de eventos interno desacopla los módulos sin necesidad de infraestructura externa como RabbitMQ o Kafka. Cuando se crea un nuevo expediente, el módulo de casos emite un evento `caso.creado`. El motor IVF, el motor de alertas y el panel analítico escuchan ese evento y actúan de forma independiente.

La implementación más simple es un **patrón pub/sub en memoria** usando una clase `EventBus` con diccionario de suscriptores. Para tareas que requieren procesamiento en segundo plano (cálculo de IVF, envío de emails), se usa **Celery con Redis** como broker — Redis ya se necesita para caché, así que no agrega complejidad.

Los eventos necesarios para LexData son:

`caso.creado`, `caso.actualizado`, `caso.vinculado` → escuchan Módulo IVF y Módulo de Alertas

`ivf.calculado` → escucha Módulo de Panel Analítico

`alerta.generada` → escucha Módulo de Notificaciones

`reporte.solicitado` → escucha Módulo de Notificaciones

Para el piloto en Cali con ~300 casos, el pub/sub en memoria es más que suficiente. Celery se agrega solo si se necesitan tareas pesadas en background (generación de PDFs, envío masivo de emails).

---

## Paso 4 — Una sola base de datos PostgreSQL

Para el MVP, una única instancia de **PostgreSQL** maneja tanto los datos transaccionales como los analíticos. No hay razón para operar tres bases de datos con ~300 casos. La separación se logra a nivel de esquemas (schemas) dentro de la misma base:

**Schema `core`**: tablas transaccionales — `expediente`, `parte`, `tipo_proceso`, `vinculacion_familiar`, `evento_procesal`, `usuario`, `organizacion`, `sesion`. Cada módulo solo accede a sus propias tablas a través de su capa de repositorio.

**Schema `ivf`**: tablas del motor de predicción — `feature_vector`, `prediccion_ivf`, `modelo_version`. Los feature vectors se almacenan como JSONB (PostgreSQL maneja documentos semiestructurados sin necesidad de MongoDB). Las predicciones recientes se cachean con **Redis** para respuesta en milisegundos.

**Schema `analytics`**: vistas materializadas para dashboards — `mv_calor_territorial`, `mv_kpi_gestion`, `mv_evolucion_ivf`. Se refrescan periódicamente con un cron job. Con ~300 casos, las queries analíticas corren en milisegundos directamente sobre las tablas transaccionales; las vistas materializadas son una optimización anticipada para cuando crezca el volumen.

La regla de disciplina: cada módulo accede solo a las tablas de su schema. Si necesita datos de otro módulo, llama a la función pública de ese módulo, no hace un JOIN cruzado.

---

## Paso 5 — Comunicación entre módulos

Al vivir todos en el mismo proceso, la comunicación es directa y simple:

**Llamadas directas (imports)**: cuando el endpoint de casos necesita el IVF actual de un expediente para responder al cliente, importa la función `ivf_service.obtener_ivf(expediente_id)` y la llama directamente. No hay latencia de red, no hay serialización JSON, no hay manejo de timeouts. Es una llamada a función normal de Python.

**Eventos internos (para desacoplamiento)**: cuando un caso se actualiza, el módulo de casos emite un evento interno y responde al cliente de inmediato. El motor IVF recalcula el índice en segundo plano (vía Celery task o handler asíncrono). Las alertas se evalúan sin bloquear la respuesta. El desacoplamiento se mantiene, pero sin infraestructura de mensajería externa.

La regla práctica para LexData: si el cliente necesita el resultado ahora → llamada directa a función. Si es procesamiento posterior → evento interno o tarea Celery.

---

## Paso 6 — Despliegue simple (Docker Compose en VPS)

La aplicación completa corre en un único contenedor Docker (o dos si se usa Celery como worker separado). El `Dockerfile` empaqueta toda la app FastAPI. Un `docker-compose.yml` levanta la app, PostgreSQL, Redis y Nginx como proxy reverso.

En producción, un **VPS básico** (DigitalOcean, Hetzner o Linode) con 2 vCPU y 4 GB de RAM es más que suficiente para 3 organizaciones y ~300 casos. No se necesita Kubernetes, ni ECS, ni orquestación de contenedores.

El `docker-compose.yml` de producción tiene cuatro servicios: `app` (FastAPI + Uvicorn), `db` (PostgreSQL o PostgreSQL gestionado externo), `redis` (caché y broker de Celery), `nginx` (proxy reverso con SSL vía Let's Encrypt).

Costo estimado: **USD $30–50/mes** — un VPS de $20–30 + PostgreSQL gestionado de $10–20 (o PostgreSQL en el mismo VPS para ahorrar más).

---

## Paso 7 — CI/CD simplificado y observabilidad

Un solo pipeline de CI/CD (GitHub Actions) para todo el proyecto: tests → build de imagen Docker → push a registry → deploy automático al VPS vía SSH o webhook. No hay coordinación entre múltiples pipelines ni versionado independiente de servicios.

Para observabilidad, lo mínimo necesario para el MVP:

**Logging estructurado**: la app escribe logs en JSON a stdout. Docker los captura. Se consultan con `docker logs` o se envían a un servicio gratuito como **Better Stack** o **Papertrail**. El `expediente_id` se incluye en cada log para trazabilidad.

**Métricas básicas**: **Prometheus + Grafana** en el mismo VPS (o un servicio gratuito como Grafana Cloud) para latencia de endpoints, tasa de alertas generadas vs. atendidas, y errores HTTP.

**Sin tracing distribuido**: al ser un monolito, no hay llamadas entre servicios que rastrear. Un middleware de FastAPI que mide el tiempo de cada request es suficiente.

---

## Orden de construcción recomendado

Dado que el MVP del mes 1–3 es gestión básica + alertas + vinculación, el orden de desarrollo es:

1. Módulo de Autenticación (bloquea todo lo demás)
2. Módulo de Gestión de Casos (núcleo del producto)
3. Módulo de Motor de Alertas (valor inmediato para las comisarías)
4. Módulo de Panel Analítico básico
5. Módulo de Motor IVF (requiere datos históricos del piloto para entrenar)
6. Módulo de Notificaciones y reportes

El motor IVF se construye a partir del mes 5 usando los datos reales del piloto. Antes de eso, el sistema ya entrega valor con la gestión de expedientes y las alertas de vencimiento.

---

## Cuándo migrar a microservicios

El monolito modular es la arquitectura correcta mientras se cumplan estas condiciones:

- Menos de **100,000 registros** concurrentes en la base de datos
- Menos de **10 organizaciones** activas
- Un solo equipo de desarrollo (hasta ~5 personas)
- El VPS no supera el 70% de uso de CPU/RAM de forma sostenida

**Señales de que es momento de separar**:

- PostgreSQL se convierte en cuello de botella y se necesitan bases especializadas (columnar para analytics, documento para ML features)
- El motor IVF necesita GPUs o infraestructura de ML dedicada que no puede compartir con la app transaccional
- Múltiples equipos trabajan en paralelo y se bloquean mutuamente en el mismo repositorio
- Se necesita escalar un módulo específico de forma independiente (ej: notificaciones en picos de alertas masivas)

La migración es gradual: se extrae primero el módulo que más presión genera (típicamente Motor IVF o Notificaciones), se convierte en servicio independiente con su propia base de datos, y se conecta vía API REST o bus de eventos externo. Los demás módulos siguen en el monolito hasta que haya razón concreta para separarlos.




