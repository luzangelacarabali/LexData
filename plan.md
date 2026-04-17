Ahora el paso a paso detallado para construir esta arquitectura:

---

## Paso 1 — Definir los microservicios y sus responsabilidades

Cada servicio es un proceso independiente con su propio repositorio, despliegue y base de datos. Para LexData se definen seis:

**Autenticación** maneja todo lo relacionado con identidad: registro de organizaciones (comisarías, consultorios), login, emisión de tokens JWT, roles (gestor, admin, supervisor ICBF) y revocación de sesiones. Ningún otro servicio gestiona usuarios.

**Gestión de casos** es el núcleo transaccional. Almacena los expedientes, sus partes (demandante, demandado, menores), el tipo de proceso (alimentos / VIF / sustancias / hurto patrimonial), el historial de audiencias y el estado procesal. La lógica de vinculación automática entre expedientes del mismo núcleo familiar vive aquí.

**Motor IVF** es el diferenciador competitivo. Consume eventos de nuevos casos y actualizaciones, calcula el Índice de Vulnerabilidad Familiar (IVF) por expediente y núcleo familiar, y expone predicciones vía API REST interna. Se entrena de manera batch con los datos históricos y sirve predicciones en tiempo real con caché.

**Motor de alertas** implementa las reglas procesales: día 12 hábil antes de vencimiento en alimentos, medidas de protección VIF próximas a vencer, audiencias pendientes. Consume eventos del bus y produce notificaciones hacia el servicio de notificaciones.

**Panel analítico** sirve los dashboards: mapa de calor territorial, KPIs de gestión, evolución del IVF por municipio. Consulta una base de datos analítica separada (no toca la transaccional).

**Notificaciones** entrega alertas por email, push y genera reportes PDF para entes de control. Es el consumidor final de los eventos de alerta.

---

## Paso 2 — Definir el API Gateway

El API Gateway es el único punto de entrada. Tiene cuatro responsabilidades concretas:

Primero, **enrutamiento**: recibe `POST /api/casos` y lo dirige al servicio de gestión de casos; recibe `GET /api/ivf/:expedienteId` y lo dirige al motor IVF. Cada microservicio tiene su prefijo de ruta.

Segundo, **validación de JWT centralizada**: el token se valida una sola vez en el gateway, no en cada servicio. Los servicios internos solo reciben headers con el userId y rol ya verificados.

Tercero, **rate limiting**: por organización (plan básico: 100 req/min; plan pro: ilimitado).

Cuarto, **SSL termination**: el gateway maneja los certificados; los servicios internos se comunican en HTTP plano dentro de la red privada.

Herramienta recomendada: **Kong** o **Nginx** con módulo de auth, según presupuesto. En AWS: **API Gateway + Lambda Authorizer**.

---

## Paso 3 — Configurar el bus de eventos

El bus de eventos desacopla los servicios. Cuando se crea un nuevo expediente, el servicio de casos publica un evento `caso.creado`. El motor IVF, el motor de alertas y el panel analítico subscriben a ese evento y actúan de forma independiente, sin que el servicio de casos sepa quién los escucha.

Los topics (Kafka) o colas (RabbitMQ) necesarios para LexData son:

`caso.creado`, `caso.actualizado`, `caso.vinculado` → consume Motor IVF y Motor de alertas

`ivf.calculado` → consume Panel analítico

`alerta.generada` → consume Notificaciones

`reporte.solicitado` → consume Notificaciones

Para el piloto en Cali con volumen moderado, **RabbitMQ** es suficiente y más simple de operar. Cuando escale a nivel nacional con miles de eventos diarios, migrar a **Kafka**.

---

## Paso 4 — Elegir las bases de datos (una por servicio)

El principio de microservicios exige que ningún servicio lea directamente la base de datos de otro. La comunicación siempre es vía API o vía bus de eventos.

**DB Expedientes (PostgreSQL)**: datos relacionales con integridad referencial. Las tablas clave son `expediente`, `parte`, `tipo_proceso`, `vinculacion_familiar` y `evento_procesal`. PostgreSQL permite las consultas relacionales que necesita la vinculación automática de núcleos familiares.

**DB Predicción (MongoDB + Redis)**: MongoDB almacena los feature vectors y el historial de predicciones IVF (documentos semiestructurados que cambian con cada versión del modelo). Redis cachea las últimas predicciones por expediente para respuesta en milisegundos.

**DB Analytics (ClickHouse o Redshift)**: base de datos columnar optimizada para consultas analíticas sobre millones de filas. Las queries del mapa de calor territorial (`GROUP BY municipio, tipo_proceso, mes`) son el caso de uso exacto para el que fue diseñado ClickHouse.

---

## Paso 5 — Definir la comunicación entre servicios

Hay dos patrones de comunicación y cada uno tiene su uso correcto:

**Comunicación síncrona (REST/gRPC)**: el API Gateway llama al servicio de gestión de casos, que a su vez puede llamar al motor IVF para obtener el IVF actual de un expediente antes de responder al cliente. Es síncrono porque el cliente está esperando la respuesta.

**Comunicación asíncrona (bus de eventos)**: cuando un caso se actualiza, el servicio de casos publica el evento y responde al cliente de inmediato. El motor IVF recalcula el índice en segundo plano. Las alertas se evalúan sin bloquear la respuesta. Esta es la comunicación que desacopla el sistema y lo hace resiliente.

La regla práctica para LexData: si el cliente necesita el resultado ahora → síncrono. Si es procesamiento posterior → asíncrono vía bus.

---

## Paso 6 — Contenerizar y orquestar (Docker + Kubernetes)

Cada microservicio vive en su propio contenedor Docker con su `Dockerfile`. El `docker-compose.yml` sirve para desarrollo local con todos los servicios corriendo en la misma máquina.

En producción, **Kubernetes** (o AWS ECS como alternativa más simple para el piloto) orquesta los contenedores. Cada microservicio tiene su propio `Deployment`, `Service` y `HorizontalPodAutoscaler`. El motor IVF y el servicio de casos pueden escalar de forma independiente según carga, sin afectar a los demás.

Para el piloto de Cali (3 organizaciones, ~300 casos), un clúster de 3 nodos en AWS EKS o Google GKE es suficiente. El costo estimado es de USD $150–250/mes en infraestructura cloud.

---

## Paso 7 — CI/CD y observabilidad

Cada servicio tiene su propio pipeline de CI/CD (GitHub Actions recomendado): tests → build de imagen Docker → push a registry → deploy automático al entorno de staging → deploy manual a producción.

Para observabilidad, tres herramientas cubren el 90% de lo que necesita LexData:

**Logging centralizado**: todos los servicios envían logs estructurados (JSON) a **ELK Stack** o **Loki**. Permite correlacionar eventos entre servicios usando el `expedienteId` como campo de búsqueda.

**Métricas y alertas operativas**: **Prometheus + Grafana** para latencia de predicciones IVF, tasa de alertas generadas vs. atendidas, y errores por servicio.

**Tracing distribuido**: **Jaeger** para rastrear una solicitud del cliente a través de gateway → casos → IVF → respuesta, midiendo dónde se consume el tiempo.

---

## Orden de construcción recomendado

Dado que el MVP del mes 1–3 es gestión básica + alertas + vinculación, el orden de desarrollo es:

1. Autenticación (bloquea todo lo demás)
2. Gestión de casos (núcleo del producto)
3. Motor de alertas (valor inmediato para las comisarías)
4. Panel analítico básico
5. Motor IVF (requiere datos históricos del piloto para entrenar)
6. Notificaciones y reportes

El motor IVF se construye a partir del mes 5 usando los datos reales del piloto. Antes de eso, el sistema ya entrega valor con la gestión de expedientes y las alertas de vencimiento.

Haz clic en cualquier bloque del diagrama para profundizar en ese servicio específico.




