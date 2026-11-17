# Taller de la Entrega 3 (E3): Resiliencia `.dlt`, Administrador de Kafka, Dos Nubes con HTTPS y GitOps (L12A, L12, EP3-Guia y EP3-E3)

Guía técnica y normativa completa de la **Entrega 3 (E3) de la EP3**, consolidando el pre-laboratorio **`L12A-Pre-laboratorio-Taller-de-la-E3`**, el laboratorio **`Lab-L12.pdf`** (57 páginas), el documento **`EP3-Entrega-3.pdf`** y **`EP3-Guia.pdf`**, con el mapeo exacto entre el proyecto de cátedra (`Biblioteca`) y el encargo evaluado **`VidalStore`**.

---

## 1. Mapa de la Entrega 3 (E3), Pauta de 100 Puntos y Mapeo Biblioteca $\leftrightarrow$ VidalStore

### 1.1 Cronograma, Ponderación y Regla del Tope 30%
- **Cierre:** **Viernes 20 de noviembre de 2026, 23:59**.
- **Peso en el encargo EP3:** **35% del encargo** (la EP3 pondera: `Encargo 40% [E1 30% + E2 35% + E3 35%] + Defensa 60%`).
- **División de la E3 (100 puntos):** **50 puntos de Kafka** y **50 puntos de ingeniería/nube/GitOps**.
- **Recuperación (`EP3-Guia.pdf` §4 y `EP3-Entrega-3.pdf` pág. 1):** Lo que no se logró en la E2 se puede recuperar en la E3 con **tope de 60%**; lo que no se logre en la E3 **solo se recupera demostrándolo en la defensa** (y ahí cuenta para la defensa).

| Indicador / Ítem E3 | Tramo L12 | Logro Destacado (100%) | Puntos |
|---|:---:|---|:---:|
| **IE6. Manejo de errores (`.dlt`, validación y reintentos)** | Tramo 1 | Las tres situaciones diferenciadas en código, `.dlt` publicado por la aplicación con `x-motivo` y `x-grupo`, los 34 inválidos del dataset desviados (60 + 8) sin detener ningún consumidor. | **26** |
| **IE3. Endpoints/clases de topics y configs** | Tramo 2 | Las tres rutas de IE3 (`GET /topics`, `POST /topics`, `PATCH /topics/:nombre/config`) en un servicio dedicado (`KafkaAdminService`), con validación DTO y `400`. | **12** |
| **IE9. Operaciones controladas sobre topics y grupos** | Tramo 2 | Las cuatro rutas de IE9 (`POST .../particiones`, `DELETE .../topics/:nombre`, `GET /grupos`, `POST .../offsets`), con protección de borrado (`?confirmar=`) y rebobinado solo si el grupo está detenido (`409` si activo). | **12** |
| **Compila desde clon limpio con 1 comando** | Cierre | `bash levantar.sh` levanta el sistema completo en local desde carpeta vacía. **Si falla, `IE6`, `IE3` e `IE9` quedan con tope del 30%**. | **5** |
| **Git** | Continuo | Igual que E1/E2 (PRs cruzados con review escrita, sin automerge, `main` protegido); los merges a `main` de `vidalstore-plataforma` despliegan. | **5** |
| **Servicios y gateways en las dos nubes con HTTPS** | Tramos 3 y 4 | Recorrido completo Azure $\to$ AWS por HTTPS con Cognito; herramientas (`Kafka UI`, `admin`) accesibles **únicamente por túnel SSM**; evidencias en `docs/despliegue.md`. | **20** |
| **Despliegue continuo con un runner en cada nube** | Tramo 5 | Un cambio en `deploy/versiones.env` llega a AWS y Azure tras merge a `main` sin entrar a ninguna máquina; `vidalstore-plataforma` **privado**; `desplegar.yml` corre **solo con `push` a `main`**; cero credenciales de nube en GitHub. | **20** |

> [!CAUTION]
> **Regla Anti-Mezcla de Dominio (`EP3-Guia.pdf` pág. 6):**
> Se puede reutilizar la arquitectura del proyecto guía de la biblioteca, pero queda **estrictamente prohibido** dejar nombres residuales del dominio de libros (`biblioteca.prestamos`, `biblioteca-panel`, `'biblioteca.'`, `@Roles('bibliotecarios')`) en los repositorios de `VidalStore`.

### 1.2 Tabla de Equivalencia Exacta: `Biblioteca` (L12) $\leftrightarrow$ `VidalStore` (E3)

| Elemento | Caso `Biblioteca` (L12) | Caso `VidalStore` (E3) |
|---|---|---|
| **DLT de actividad** | `biblioteca.lecturas.dlt` (`58` = `29` × `2` grupos) | **`vidalstore.actividad.dlt`** (**`60` = `30` × `2`** grupos: `panel` y `alertas`; categorías `10 · 10 · 10`) |
| **DLT de transacciones** | `biblioteca.prestamos.dlt` (`8` = `4` × `2` grupos) | **`vidalstore.compras.dlt`** (**`8` = `4` × `2`** grupos: `panel` e `historial`; categorías `2 · 1 · 1`) |
| **DLT del catálogo (grupos de 3)** | `biblioteca.catalogo.dlt` | **`vidalstore.catalogo.dlt`** (3 particiones, 3 réplicas, `delete`, 7 días) |
| **Rol exigido en admin y panel** | `@Roles('bibliotecarios')` | **`@Roles('administradores')`** |
| **Prefijo protegido al borrar topic** | `PREFIJO_PROTEGIDO = 'biblioteca.'` | **`PREFIJO_PROTEGIDO = 'vidalstore.'`** (borrar `vidalstore.*` sin `?confirmar=<nombre>` responde `400`) |
| **Rebobinado de historial** | `biblioteca-historial` $\to$ `prestamos_semana` (`380, 18, 362`) | **`vidalstore-historial`** $\to$ **`ventas_semana`** (`380` compras, `15` revocaciones, **`6.032.190 CLP netos`**); `.dlt` crece de `8` a `12` |
| **Servicios en EC2 `servicios` (`10.0.11.10`)** | `libros :3001`, `prestamos :3002`, `eventos :3010` | **`catalogo :3002`**, **`licencias :3003`**, **`eventos :3010`** *(respetando puertos propios en `compose.yml`)* |
| **Herramientas en EC2 `gestion` (`10.0.11.20`)** | `biblioteca-admin :3020`, `kafka-ui :8080`, runner `aws` | **`vidalstore-admin :3020`**, `kafka-ui :8080`, runner `aws` *(Prometheus/Grafana opcionales)* |
| **Secretos en AWS Parameter Store** | `/biblioteca/<maquina>/env` | **`/vidalstore/<maquina>/env`** (o ruta documentada en `deploy/`) |
| **Secretos en VMs de Azure** | `/opt/biblioteca/secretos/<maquina>.env` | **`/opt/vidalstore/secretos/<maquina>.env`** (o Key Vault si se justifica en `deploy/`) |
| **URLs del ecosistema** | `biblioteca-l10.<region>.cloudapp.azure.com` | **`https://<etiqueta>.<region>.cloudapp.azure.com`** y **`https://<elastic-ip-con-guiones>.sslip.io`** |
| **Usuario de prueba de Arturo** | `lector@biblioteca.test` | Usuario real de Cognito en el grupo **`administradores`** |

### 1.3 Reglas de Entorno Windows / Git Bash (L12 pág. 2–3)
1. **Conversión de rutas en Docker:** Antes de ejecutar comandos con rutas Linux dentro de contenedores (p. ej. `/opt/kafka/bin/...`), exportar `export MSYS_NO_PATHCONV=1`.
2. **Higiene EOL (`LF` obligatorio):** En VS Code configurar `"files.eol": "\n"` y validar con `sin_crlf` antes de subir scripts a S3/EC2/Azure, evitando `$'\r': command not found`.
3. **Resolución del usuario en minúsculas:** `UM=$(echo "$U" | tr 'A-Z' 'a-z')` porque GHCR rechaza mayúsculas.

---

## 2. Tramo 1 · Resiliencia con `.dlt` y Tope de 3 Reintentos (`IE6` · 26 pts)

### 2.1 Por qué el `.dlt` lo Publica la Aplicación y Qué Topics Exige
- Kafka `4.4` trae DLQ integrada en broker únicamente para *share groups*, pero el curso utiliza **consumer groups** estándar. Por eso **la aplicación (`vidalstore-eventos`) publica al `.dlt`**.
- **Un `.dlt` por cada topic consumido:** En `vidalstore-plataforma/kafka/topics.sh` y `deploy/aws/mq/kafka/topics.sh` deben declararse con **`--partitions 3 --replication-factor 3 --config min.insync.replicas=2 --config cleanup.policy=delete --config retention.ms=604800000` (7 días)**:
  - `vidalstore.compras.dlt`
  - `vidalstore.actividad.dlt`
  - **`vidalstore.catalogo.dlt`** *(obligatorio en grupos de 3: `CatalogoConsumidor` hereda de `ConsumidorKafka` y con `auto.create.topics.enable=false`, un desvío hacia un topic inexistente detiene el consumidor)*.
  - *Por qué `delete` y 7 días en `.dlt` (incluso para `catalogo.dlt`):* el `.dlt` guarda **cada fallo**, no el último estado por clave; y 7 días dan tiempo para diagnosticar y reprocesar.

### 2.2 Las 3 Situaciones Diferenciadas en `vidalstore-eventos/src/streaming/`

| Qué falla | Qué hace el consumidor (`ConsumidorKafka`) | `x-motivo` obligatorio | ¿Va al `.dlt`? |
|---|---|---|:---:|
| **El `value` no es JSON válido** | **No reintenta:** publica en `<topic>.dlt`, registra `WARN` y confirma el offset **después** de que el `.dlt` confirme. | `json-invalido` | **Sí** |
| **Falta campo obligatorio del sobre** (`eventoId`, `tipo`, `version`, `emitidoEn`, etc.) | **Igual:** no reintenta, publica en `<topic>.dlt`, registra y confirma. *(Manda sobre `version`: sin `eventoId` no hay deduplicación posible)*. | `falta-<campo>` *(ej. `falta-eventoId`)* | **Sí** |
| **`version` distinta de `1`** | **Igual:** no reintenta, publica en `<topic>.dlt`, registra y confirma. | `version-desconocida` | **Sí** |
| **JSON válido con campos completos, pero DTO no valida** (UUID inválido, tipo desconocido, `datos` mal formados, o JSON no-objeto como `[1,2]` / `null`) | **Igual:** no reintenta, publica en `<topic>.dlt`, registra y confirma. *(Nota: aceptar `logro.desbloqueado` como tipo válido en `vidalstore.actividad`)*. | `dto-invalido` | **Sí** |
| **Postgres no responde** (`ECONNREFUSED`, timeout, caída del contenedor) | **Hasta 3 reintentos** con espera creciente (**`1000, 2000, 4000` ms**, ~7 s en total). Si el 3.º falla, publica en `<topic>.dlt`, confirma y sigue con el siguiente evento. | `postgres-no-responde` | **Sí (tras 3 fallos)** |
| **Evento duplicado** (`UNIQUE(evento_id)` / `ON CONFLICT DO NOTHING`) | Lo detecta la BD: registra `WARN`, confirma el offset sin volver a sumar. | *—* | **No** |

> [!IMPORTANT]
> **¿Por qué el reintento ante Postgres caído tiene límite (3) y nunca es infinito? (Pregunta 1 de Defensa E3)**
> En Kafka el orden existe dentro de cada partición; mientras el consumidor insiste en un evento, todos los eventos sanos que vienen detrás en esa partición quedan bloqueados y el *consumer lag* sube sin control. Un JSON cortado o DTO inválido jamás se arregla reintentando $\to$ va al `.dlt` al tiro. Postgres caído es un fallo transitorio que puede recuperarse en segundos $\to$ se reintenta un máximo acotado de 3 veces (~7 s); si persiste caído, se resguarda el evento válido en el `.dlt` con `postgres-no-responde` para reprocesarlo luego y el consumidor sigue atendiendo la partición sin colgar el servicio.

### 2.3 Arquitectura de los 3 Archivos en `vidalstore-eventos/src/streaming/`
1. **`contrato.ts` (`Contrato<T>`, `EventoInvalido`, `MotivoInvalido`)**:
   - `EventoInvalido` recibe `(motivo: MotivoInvalido, detalle: string)`.
   - **Orden estricto de evaluación:**
     1. `JSON.parse(m.value)` falla $\to$ `json-invalido`.
     2. `!crudo || typeof crudo !== 'object' || Array.isArray(crudo)` $\to$ `dto-invalido`.
     3. `validateSync(plainToInstance(this.dto, crudo), { whitelist: true, forbidNonWhitelisted: true })`:
        - Primero busca el primer error con `e.value === undefined || e.value === null` $\to$ `falta-${faltante.property}` *(si falta `eventoId` y además `version` es `99`, gana `falta-eventoId`)*.
        - Luego `errores.some(e => e.property === 'version')` $\to$ `version-desconocida`.
        - Resto $\to$ `dto-invalido` con el detalle de `motivos(errores)` (ej. `datos.desde (matches)`).
2. **`dlt.ts` (`PublicadorDlt`, `cabecerasDlt`, `topicDlt`)**:
   - `Producer` con `acks: ProduceAcks.ALL`, `idempotent: true`, `retries: 10`, `partitioner: compatibilityPartitioner`, `autocreateTopics: false`.
   - Publica en `topicDlt(m.topic)` (`${topic}.dlt`) el **`value` original intacto** con la **misma `key` original** (como tiene 3 particiones y mismo particionador, el mensaje desviado cae exactamente en la misma partición que el original!).
   - **`cabecerasDlt`:** Copia todos los headers originales (`x-evento-id`, `x-correlation-id`, `content-type`) y suma:
     - `x-motivo`: motivo exacto (`json-invalido`, `falta-eventoId`, `version-desconocida`, `dto-invalido`, `postgres-no-responde`)
     - `x-grupo`: el `groupId` del consumidor que lo desvió (permite comprobar cuánto desvió cada grupo)
     - `x-topic-origen`: `m.topic`
     - `x-particion`: `String(m.partition)`
     - `x-offset`: `String(m.offset)`
     - `x-detalle`: error truncado a 500 caracteres
   - **Si Kafka falla al publicar en `.dlt`, `desviar()` lanza excepción** y el consumidor **no confirma el offset del mensaje original**.
3. **`consumidor-kafka.ts` (`ConsumidorKafka<T>`)**:
   - Constante `ESPERAS_REINTENTO_MS = [1000, 2000, 4000]`.
   - Si `contrato.validar(m)` lanza `EventoInvalido` $\to$ `await this.desviar(...)` $\to$ `await m.commit()` $\to$ `continue`.
   - Si no $\to$ `procesarConReintentos(evento, donde)`: intenta `this.negocio.procesar(evento)` hasta `ESPERAS_REINTENTO_MS.length` reintentos (3 esperas de 1, 2 y 4 s); si en medio del cierre (`this.cerrando`) retorna `undefined` **sale sin hacer commit** para que otro consumidor retome; si agota los 3 reintentos retorna `causa: Error` $\to$ `await this.desviar(m, donde, 'postgres-no-responde', resultado.message)` $\to$ `await m.commit()`.
   - Resumen periódico cada 10 s (`desde el arranque: X nuevos, Y duplicados, Z ignorados, W al .dlt (A invalidos, B sin Postgres)`).
   - `onModuleDestroy()` cierra flujo, consumidor y `this.dlt.cerrar()`.

### 2.4 Cifras Exactas del Dataset y Pruebas de Comprobación en VidalStore (`IE6`)
- **Inválidos del dataset VidalStore (`34` inválidos totales):**
  - En `vidalstore.actividad`: **30 inválidos** (`10` JSON cortado, `10` `version: 99`, `10` falta un campo). Leídos por **`vidalstore-panel`** y **`vidalstore-alertas`** $\Rightarrow$ **`60` mensajes en `vidalstore.actividad.dlt`**.
  - En `vidalstore.compras`: **4 inválidos** (`2` JSON cortado, `1` `version: 99`, `1` falta un campo). Leídos por **`vidalstore-panel`** y **`vidalstore-historial`** $\Rightarrow$ **`8` mensajes en `vidalstore.compras.dlt`**.
  - Con `x-grupo` se verifica que cada grupo desvió exactamente `30` y `4`.
  - **Eventos sin `eventoId` (Pregunta 5 de Defensa E3):** Hay 4 eventos sin `eventoId` en el dataset. Sin `eventoId` no existe clave para asegurar idempotencia (`UNIQUE(evento_id)`) en Postgres, así que **no se escriben**; `contrato.ts` los detecta primero con `x-motivo: falta-eventoId` (sin reintentar) y los desvía al `.dlt` conservando su `x-correlation-id`, `x-particion` y `x-offset` originales para rastrearlos, confirmando el offset para seguir leyendo.
- **Rebobinado y `.dlt`:** Si se rebobina `vidalstore-historial` desde el inicio, vuelve a leer los 4 inválidos de `compras` y los desvía nuevamente $\Rightarrow$ `vidalstore.compras.dlt` pasa de `8` a `12` mensajes (en nuevos offsets del `.dlt`, pero con los mismos `x-topic-origen`, `x-particion`, `x-offset` — por eso quien reprocesa desde `.dlt` agrupa por esa tupla de origen).
- **Prueba unitaria (`contrato.spec.ts`):** Obligatoria en `vidalstore-eventos` para probar todos los motivos y `cabecerasDlt` (y que pase `npm test` en el pipeline CI).
- **Script `herramientas/eventos-malos.mjs`:** Publica 1 caso de cada clase (`json-invalido`, `falta-eventoId`, `version-desconocida`, `dto-invalido`) + 1 válido + 1 duplicado para comprobar en vivo que los 4 malos llegan al `.dlt` por cada grupo que lee ese topic y el duplicado no va al `.dlt`.
- **Prueba en vivo con Postgres detenido:** Simulador corriendo (`--velocidad 60`), ejecutar `docker compose stop postgres` ~25 s y luego `start postgres` $\to$ ver en logs los 3 reintentos (`1, 2 y 4s`), `AL .DLT (postgres-no-responde)`, servicio vivo y eventos posteriores procesados normal (`GET /salud` ok).

---

## 3. Tramo 2 · Administrador de Kafka en `vidalstore-admin` (`IE3` 12 pts + `IE9` 12 pts)

### 3.1 Arquitectura y Reglas Obligatorias (`vidalstore-admin/src/kafka/`)
- Se amplía el microservicio **`vidalstore-admin`** existente (`:3020`), **no se crea un repo aparte**.
- Protección idéntica a RabbitMQ: `@UseGuards(JwtGuard, RolGuard)` y **`@Roles('administradores')`** en `KafkaController` (`@Controller('v1/admin/kafka')`).
- **Aislamiento obligatorio de controlador (`IE3`/`IE9`):** **`KafkaController` jamás importa ni conoce `@platformatic/kafka`**. Solo valida DTOs con `class-validator` (`ValidationPipe` con `whitelist: true`, `forbidNonWhitelisted: true`) y delega en **`KafkaAdminService`**.
- **No expuestas en el API Gateway:** Las rutas `/v1/admin/kafka/*` corren en la instancia `gestion` (`127.0.0.1:3020`) y se consumen únicamente a través del túnel de Session Manager (`localhost:13020`).
- **Configuración de entorno:** Agregar `@platformatic/kafka@2.14.0`, añadir `KAFKA_BROKERS` en `vidalstore-admin/.env` y `.env.example`, inyectar `KAFKA_BROKERS: broker-1:19092,broker-2:19092,broker-3:19092` y `depends_on` `broker-1..3` (`condition: service_healthy`) en `vidalstore-plataforma/compose.yml`, y añadir `comprobar 401 http://localhost:3020/v1/admin/kafka/topics` en `levantar.sh`.

### 3.2 Las 7 Rutas Oficiales de `/v1/admin/kafka`

| Ruta | Método Admin (`@platformatic/kafka`) | Qué hace y validaciones clave | Indicador |
|---|---|---|:---:|
| **`GET /v1/admin/kafka/topics`** | `listTopics`, `describeConfigs`, `metadata` | Lista todos los topics con particiones, réplicas, ISR y configs propias (`DYNAMIC_TOPIC_CONFIG`). | **IE3** |
| **`POST /v1/admin/kafka/topics`** | `createTopics` | Crea un topic (`nombre`, `particiones` 1..50, `replicas` 1..3, `configs` opcional). **Filtrar `!== undefined` en `configs`** (con `target: ES2023`, propiedades opcionales viajan como `undefined` y causan `INVALID_CONFIG`) + polling de hasta 5 s (`20 × 250ms`) para evitar `404` por latencia de propagación en controller. | **IE3** |
| **`PATCH /v1/admin/kafka/topics/:nombre/config`** | `incrementalAlterConfigs` | Modifica configs permitidas en lista cerrada (`ConfigsTopicDto`: `retention.ms`, `cleanup.policy`, `min.insync.replicas`, `retention.bytes`, `segment.ms`, `max.message.bytes`). Rechaza con `400` cualquier otra clave o body vacío (`forbidNonWhitelisted`). | **IE3** |
| **`POST /v1/admin/kafka/topics/:nombre/particiones`** | `createPartitions` (`@HttpCode(200)`) | Aumenta particiones. **Si `particiones < actuales` o `=== actuales`, responde `400 Bad Request`** explicando el motivo (nunca `500`). Al aumentar, incluye `aviso` advirtiendo que las nuevas keys pueden cambiar de partición. | **IE9** |
| **`DELETE /v1/admin/kafka/topics/:nombre`** | `deleteTopics` | Elimina topic. **Si el nombre empieza con `'vidalstore.'` (`PREFIJO_PROTEGIDO`), exige `?confirmar=<nombre exacto>`**; si falta o difiere, responde **`400 Bad Request`**. Rechaza topics internos `__*` con `400`. | **IE9** |
| **`GET /v1/admin/kafka/grupos`** | `listGroups`, `describeGroups`, `listConsumerGroupOffsets`, `listOffsets` | Lista consumer groups con `estado`, `miembros`, `lagTotal` y detalle de lag por topic y partición. | **IE9** |
| **`POST /v1/admin/kafka/grupos/:id/offsets`** | `alterConsumerGroupOffsets` (`@HttpCode(200)`) | Rebobina offsets del grupo a `principio` (`-2n`), `final` (`-1n`) o `fecha` (`ISO 8601`), opcionalmente filtrado por `topic`. **Si el grupo tiene `miembros > 0`, responde `409 Conflict`** indicando detener el consumidor primero (jamás `500`). | **IE9** |

> [!IMPORTANT]
> **¿Por qué el administrador responde `400` si se piden menos particiones? (Pregunta 2 de Defensa E3)**
> Kafka no tiene operación para quitar particiones (`createPartitions` solo aumenta). Si se redujeran, los mensajes ya escritos en la partición eliminada quedarían huérfanos sin destino, y la función de hash $\text{murmur2}(\text{key}) \bmod N$ enviaría los nuevos eventos de un mismo `usuarioSub` o `juegoId` a otra partición distinta de sus eventos históricos, rompiendo el orden garantizado por clave (como `compra.realizada` antes de `licencia.revocada`).

### 3.3 Traducción de Errores de Protocolo (`traducir()` y `errorDeProtocolo()`)
- `@platformatic/kafka` envuelve fallos en estructuras anidadas (`MultipleErrors` $\to$ `ResponseError` con `apiId`). `errorDeProtocolo()` recorre recursivamente `errors`/propiedades buscando `apiId`:
  - `TOPIC_ALREADY_EXISTS`, `NON_EMPTY_GROUP`, `UNKNOWN_MEMBER_ID`, `REBALANCE_IN_PROGRESS` $\to$ `409 ConflictException`
  - `UNKNOWN_TOPIC_OR_PARTITION`, `UNKNOWN_TOPIC_ID`, `GROUP_ID_NOT_FOUND` $\to$ `404 NotFoundException`
  - `INVALID_PARTITIONS`, `INVALID_REPLICATION_FACTOR`, `INVALID_REPLICA_ASSIGNMENT`, `INVALID_CONFIG`, `INVALID_TOPIC_EXCEPTION`, `POLICY_VIOLATION`, `INVALID_REQUEST` $\to$ `400 BadRequestException`
  - Otros o timeout de clúster (`retries: 2, timeout: 5000` en `Admin`) $\to$ `503 ServiceUnavailableException`.

---

## 4. Tramos 3 y 4 · Dos Nubes Completas con HTTPS (`20 pts`)

### 4.1 Recorrido Completo de Peticiones en la Arquitectura Final E3
```text
Navegador (Usuario / Arturo)
   │ HTTPS (:443)  https://<etiqueta>.<region>.cloudapp.azure.com
   ▼
[Azure · gw-azure · 10.1.1.4 · IP pública estática + DNS]
   ├── Caddy (:443 y :80) + Frontend Angular (una sola imagen, network_mode: host, vol /data)
   │     └── /v1/* ──> 127.0.0.1:8080 (vidalstore-gateway en gw-azure)
   └── Gateway en gw-azure (:8080)
         ├── /v1/panel/en-vivo ──> [Azure · bff · 10.1.2.4 · sin IP pública] (:3001)
         │                             └── sale por NAT de gw-azure (IP estática gw-azure)
         └── /v1/catalogo, /v1/compras, /v1/licencias, /v1/auditoria ──┐
                                                                       ▼
                                             HTTPS :443 (solo desde IP pública de gw-azure)
                                             https://<elastic-ip-con-guiones>.sslip.io
[AWS · gw-aws · 10.0.1.20 · Elastic IP]
   ├── Caddy (:443 y :80 con network_mode: host, vol /data)
   └── vidalstore-gateway (:8080 con network_mode: host)
         └── [AWS · servicios · 10.0.11.10 · subred aplicacion]
               ├── vidalstore-catalogo (:3002)
               ├── vidalstore-licencias (:3003)
               └── vidalstore-eventos (:3010) ──> [mq-1..3 Kafka/Rabbit] + [datos Postgres :5432]

[AWS · gestion · 10.0.11.20 · subred aplicacion · SIN puertos entrantes abiertos]
   ├── Kafka UI (127.0.0.1:8080 ── túnel SSM ──> localhost:18085)
   ├── vidalstore-admin (127.0.0.1:3020 ── túnel SSM ──> localhost:13020)
   └── Runner self-hosted 'aws'
```

### 4.2 Tramo 3 · AWS Completo (`deploy/aws/`)
1. **8 Instancias EC2 (Atención al Límite de 9 en Learner Lab):**
   - `nat` (10.0.1.10), `mq-1..3` (10.0.21.11, 10.0.22.12, 10.0.21.13), `datos` (10.0.21.30), `gestion` (10.0.11.20), más las 2 nuevas de E3:
     - **`servicios` (`10.0.11.10`, `t3.medium`, `sg-servicios`)**: `deploy/aws/servicios/compose.yml` con `catalogo`, `licencias` y `eventos`, leyendo `deploy/versiones.env` y `/opt/vidalstore/secretos/servicios.env` (de Parameter Store `/vidalstore/servicios/env`).
     - **`gw-aws` (`10.0.1.20`, `t3.small`, `sg-gw`, con Elastic IP tag `Name=gw-aws`)**: `deploy/aws/gw-aws/compose.yml` + `Caddyfile`, corriendo `caddy:2.11.7` y `gateway`, ambos con **`network_mode: host`**.
   - Si hay instancias extra en la misma cuenta (>9), EC2 apaga la novena con `Client.UserInitiatedShutdown`.
2. **Seguridad de `sg-gw` (`443` vs `80`, cero `22`) — *(Pregunta 3 de Defensa E3)*:**
   - **Puerto `443`**: acepta **únicamente `${IP_GW_AZURE}/32`** (porque tanto el gateway de `gw-azure` como `bff` detrás del NAT salen a AWS con la IP pública de `gw-azure`). Desde el PC del estudiante devuelve **timeout** (el SG descarta en silencio).
   - **Puerto `80`**: queda abierto **`0.0.0.0/0`** exclusivamente para el desafío **HTTP-01 de Let's Encrypt** (cuyos servidores de validación no tienen IPs fijas y renuevan cada ~60 días); Caddy responde el desafío y redirige `308` hacia `443` (por el `80` jamás pasa tráfico de la API).
   - **Puerto `22`**: cerrado en toda la VPC (acceso por Session Manager).
3. **Caddy y `sslip.io` en `gw-aws`:**
   - Nombre TLS: `<elastic-ip-con-guiones>.sslip.io` (ej. `100-51-99-43.sslip.io`).
   - **Primero `ACME_CA` de staging** (`https://acme-staging-v02.api.letsencrypt.org/directory`); una vez obtenido el certificado de prueba, pasar a producción (`https://acme-v02.api.letsencrypt.org/directory`), subir parámetros (`03-subir.sh`) y redesplegar `gw-aws`.
   - **NUNCA ejecutar `docker compose down -v` en `gw-aws`**: el volumen `/data` conserva los certificados; `sslip.io` comparte límite semanal de certificados entre todos los usuarios.
4. **Herramientas Privadas y Túneles SSM (`05-tunel.sh`):**
   - En `gestion` (`deploy/aws/gestion/compose.yml`): `kafka-ui` (`127.0.0.1:8080:8080`) y `admin` (`127.0.0.1:3020:3020`) escuchan solo en loopback.
   - `05-tunel.sh` abre `localhost:18085` (Kafka UI) y `localhost:13020` (`vidalstore-admin`).
   - Para abrir servicios de otras máquinas privadas pasando por `gestion` (Postgres en `datos:5432` o RabbitMQ UI en `mq-1:15672`): usar `AWS-StartPortForwardingSessionToRemoteHost` con `--parameters "host=10.0.21.30,portNumber=5432,localPortNumber=15432"`.
5. **Despliegue sin llaves SSH (directo en `.github/workflows/desplegar.yml`, job `aws` — SIN script `.sh` de despliegue):**
   - La pauta E3 prohíbe scripts `.sh` de despliegue continuo: toda la lógica vive en el job `aws` de `desplegar.yml` (usando la variable `BUCKET`).
   - Sube `deploy/` a `s3://$BUCKET/deploy/` excluyendo secretos y envía por `aws ssm send-command` a `servicios`, `gestion` y `gw-aws`:
     - **`aws s3 sync ... --exact-timestamps`** *(CRÍTICO: reemplazar un SHA en `versiones.env` mantiene el tamaño exacto del archivo; sin `--exact-timestamps`, `s3 sync` no descarga el cambio!)*.
     - Escribe `/opt/vidalstore/secretos/<maquina>.env` desde Parameter Store (`--with-decryption`).
     - Ejecuta `docker compose --env-file ../../versiones.env pull && up -d --wait --remove-orphans` e imprime **`docker compose ps --format '{{.Name}} {{.Image}} {{.Status}}'`** para probar qué SHA quedó corriendo.

### 4.3 Tramo 4 · Azure Completo (`deploy/azure/` y `vidalstore-frontend`)
1. **Frontend + Caddy en una sola imagen (`vidalstore-frontend/Dockerfile` + `Caddyfile`):**
   - Etapa 1 (`FROM node:24-slim AS build`): `npm ci && npx ng build`.
   - Etapa 2 (`FROM caddy:2`): copia `Caddyfile` a `/etc/caddy/Caddyfile` y los estáticos compilados a `/srv/`. *(Reemplaza `nginx.conf`)*.
   - `Caddyfile` (`{$DOMINIO::80}`): `handle /v1/* { reverse_proxy {$GATEWAY:127.0.0.1:8080} }` y `handle { root * /srv; try_files {path} /index.html; file_server }`. En local (sin `DOMINIO`) sirve HTTP en `:80`; en `gw-azure` con `DOMINIO=<etiqueta>.<region>.cloudapp.azure.com` obtiene certificado TLS automático (~5s). **Nunca `docker compose down -v` en `gw-azure`** para no borrar `/data`.
2. **Mismo origen = Cero CORS en Frontend:**
   - Constante dinámica: `export const GATEWAY = globalThis.location?.hostname === 'localhost' ? 'http://localhost:8080' : '';`
   - Interceptor HTTP y servicios Angular usan `${GATEWAY}/v1/...` (relativo `/v1/...` en Azure, absoluto `:8080/v1/...` en local).
3. **Cognito HTTPS (obligatorio para login en Azure):**
   - En `vidalstore-frontend/src/main.ts`, `redirectSignIn` y `redirectSignOut` mantienen `http://localhost:4200/...` y añaden `https://<etiqueta>.<region>.cloudapp.azure.com/callback` y `https://<etiqueta>.<region>.cloudapp.azure.com/`.
   - En consola AWS Cognito $\to$ App client $\to$ Login pages: agregar exactamente las mismas URLs (carácter por carácter; una `/` de más provoca `redirect_mismatch`).
4. **Secretos y Compose en VMs de Azure:**
   - Secretos en `/opt/vidalstore/secretos/gw-azure.env` y `bff.env` (`chmod 700`/`600`, fuera de Git; o Key Vault justificado en `deploy/`).
   - `deploy/azure/gw-azure/compose.yml`: `frontend` y `gateway` con `network_mode: host`.
   - `deploy/azure/bff/compose.yml`: `bff` en `:3001` (o `:3000`) llamando a AWS `https://<elastic-ip-con-guiones>.sslip.io` saliendo por NAT de `gw-azure`.
5. **Despliegue y prueba de humo directos en `.github/workflows/desplegar.yml` (jobs `azure` y `humo` — SIN scripts `.sh` de despliegue):**
   - El job `azure` corre en `bff` posicionándose en **`deploy/`** (`cd deploy` — si apunta a la raíz falla con `couldn't find env file: .../versiones.env`), levanta `bff` local (`docker compose pull && up -d`) y por SSH dentro de la VNet (`10.1.1.4`, llave `id_ed25519` generada en `bff` y autorizada en `gw-azure`) copia `versiones.env` + `gw-azure/compose.yml` y levanta `gw-azure`.
   - El job `humo` corre en `bff` después de `aws` y `azure` usando las variables `FRONTEND_URL` y `AWS_URL`: verifica `200` en `$FRONTEND_URL/`, `200` en `$FRONTEND_URL/callback`, y `401` en `$AWS_URL/v1/catalogo` sin token. *(Desde `bff` con token del navegador también se verifica `200` / `403` si se usa CLI `USER_PASSWORD_AUTH` sin scope).*

---

## 5. Tramo 5 · GitOps y Despliegue Continuo con Self-Hosted Runners (`20 pts`)

### 5.1 Flujo Completo del Commit a las Dos Nubes
```text
[Repo de servicio] push a main ──> imagen.yml:
   Job 1: pruebas (ubuntu-latest: npm ci, lint, test, build)
     └── needs: pruebas ──> Job 2: imagen (platforms: linux/amd64 ──> GHCR :sha)
                                      │
                                      ▼ (actualizar SHA en deploy/versiones.env)
[vidalstore-plataforma (PRIVADO)] merge PR dev -> main (push a main) ──> desplegar.yml:
   Job 1: validar (ubuntu-latest: regex 40-hex en versiones.env + docker manifest inspect)
     ├── needs: validar ──> Job 2: aws   [self-hosted, aws]   (en gestion: S3 + SSM)
     └── needs: validar ──> Job 3: azure [self-hosted, azure] (en bff: local + SSH VNet)
                              └── needs: [aws, azure] ──> Job 4: humo [self-hosted, azure]
```

### 5.2 Reglas Críticas de `imagen.yml` en los 7 Servicios
1. **Dos jobs obligatorios (`pruebas` $\to$ `imagen` con `needs: pruebas`):** si fallan pruebas, lint o build, jamás se construye ni publica imagen en GHCR.
2. **`platforms: linux/amd64` obligatorio:** las EC2 y VMs de Azure son x86_64; sin esto, un build o push multi-arch/ARM puede fallar en la nube.
3. **Arreglos de pruebas reales (sin borrar tests):**
   - Repositorios sin `*.spec.ts` (ej. si algún servicio no tuviera specs): usar `npm test --if-present -- --passWithNoTests`.
   - En `vidalstore-gateway` (Jest + `jose` ESM): incluir `transformIgnorePatterns: ['/node_modules/(?!jose)']`, pasar `COGNITO_ISSUER` y `COGNITO_CLIENT_ID` en `env:` del paso `npm test` (porque el verificador arma la URL JWKS al importarse) y verificar que ningún test antiguo mande `Bearer holaquetal` esperando `200` en lugar de `401 Unauthorized`.

### 5.3 Reglas Críticas de `vidalstore-plataforma`, `versiones.env`, `desplegar.yml` y Runners
1. **`vidalstore-plataforma` debe ser `Private`:**
   - Un repositorio público con *self-hosted runners* expone workflows y estructura interna a terceros (GitHub desaconseja runners en repos públicos). Cambiar en `Settings → Danger Zone → Change visibility → Private` (si viene de un fork público y GitHub no deja hacerlo privado, crear repo privado nuevo con `git push --mirror` e invitar al docente como colaborador).
   - Configurar 3 **Variables** (no Secrets) en `Settings → Secrets and variables → Actions → Variables`: `BUCKET`, `FRONTEND_URL` y `AWS_URL`. **La pestaña `Secrets` queda vacía** de credenciales AWS/Azure.
   - En `gestion` (Amazon Linux), instalar antes del runner: `sudo dnf install -y git libicu tar` (sin `libicu` el runner no arranca).
2. **`deploy/versiones.env`:**
   - Declara las 7 imágenes por **SHA completo de 40 caracteres hexadecimales en minúsculas** (nunca `:latest`): `GATEWAY`, `CATALOGO`, `LICENCIAS`, `EVENTOS`, `ADMIN`, `BFF`, `FRONTEND`.
   - **Por qué SHA y por qué runners dentro de la nube (Pregunta 4 de Defensa E3):** El SHA ata exactamente el código desplegado y permite rollback revirtiendo una línea en Git; `:latest` es mutable. Los runners viven dentro de las subredes privadas (`gestion` y `bff`) abriendo solo conexiones salientes `:443` hacia GitHub: llegan por SSM/rol IAM y VNet sin abrir puertos entrantes ni guardar credenciales de AWS/Azure en GitHub (donde además las llaves del Learner Lab vencen cada 4 horas).
3. **`.github/workflows/desplegar.yml`:**
   - **`on: push: branches: [main]` + `workflow_dispatch:` — PROHIBIDO usar `pull_request`:** un evento `pull_request` permitiría ejecutar código de ramas externas/no aprobadas en tus VMs privadas.
   - `concurrency: { group: desplegar, cancel-in-progress: false }` para encolar merges sucesivos sin pisarse.
   - El runner `aws` en `gestion` (etiqueta `--labels aws`, servicio `./svc.sh`) despliega mientras la **sesión del Learner Lab está abierta** (si está cerrada, el job queda en cola y falla tras 24h).
   - El runner `azure` en `bff` (etiqueta `--labels azure`, usuario `azureuser` en grupo `docker`, servicio `sudo ./svc.sh install azureuser`).

---

## 6. Salidas de `docs/despliegue.md`, Entregable AVA, 5 Preguntas de Defensa y Troubleshooting L12

### 6.1 Las 5 Salidas Obligatorias en `docs/despliegue.md` para la E3
```bash
# 1 · Frontend en Azure con su certificado TLS válido
curl -sI https://<etiqueta>.<region>.cloudapp.azure.com | head -1

# 2 · Desde bff: AWS responde y el gateway recibe el token
curl -s -H "Authorization: Bearer <token>" \
  https://<elastic-ip-con-guiones>.sslip.io/v1/<una-ruta-del-gateway>

# 3 · Desde el equipo del grupo: la misma URL no responde (timeout)
curl -s --max-time 8 https://<elastic-ip-con-guiones>.sslip.io/ || echo sin-respuesta

# 4 · El SHA que corre en cada máquina (AWS y Azure), después de un despliegue
sudo docker ps --format '{{.Names}} {{.Image}}'

# 5 · Lo que desviaron los consumidores en mq-1 tras una reproducción (60 y 8)
$K/kafka-get-offsets.sh --bootstrap-server 10.0.21.11:9092 --topic vidalstore.actividad.dlt
$K/kafka-get-offsets.sh --bootstrap-server 10.0.21.11:9092 --topic vidalstore.compras.dlt
```
Además, incluir el **enlace al run verde de `desplegar.yml`** en GitHub Actions que ejecutó el despliegue.

### 6.2 Qué se Sube al AVA en la E3 (`EP3-Entrega-3.pdf` págs. 10–11)
**Dos archivos** subidos por un integrante al AVA, con copia al correo `cr.calderons@profesor.duoc.cl` (sin `.zip` ni `.env`; la nube debe estar **ya encendida** al comenzar el turno de defensa, o `IE6`, `IE3` e `IE9` quedan topados al 30%):
1. **El PDF con imágenes:**
   - Integrantes, sección, número de grupo, y quién aloja AWS y quién Azure.
   - Capturas con 1 línea descriptiva: frontend en Azure con el panel, ejecución de `imagen.yml` y de `desplegar.yml` con sus 4 jobs en verde, Kafka UI por el túnel y los `.dlt`.
   - Enlace a `docs/despliegue.md` (con pasos para re-levantar en nueva sesión del Learner Lab + las 5 salidas de la E3) y **cuál de los dos órdenes del Paso 1 eligió el grupo** (*Validar antes de mirar el tipo* → `60`/`8` vs *Filtrar por tipo primero* → `45`/`8`).
   - El contenido exacto de `deploy/versiones.env` en ese commit de entrega.
2. **El `.md` de entrega:**
   - Enlace de cada repositorio (indicando el nombre del de plataforma si no es `vidalstore-plataforma`).
   - URL públicas: `https://<etiqueta>.<region>.cloudapp.azure.com` y `https://<elastic-ip-con-guiones>.sslip.io` (que solo responde a `gw-azure`).
   - **Dos usuarios de prueba de Cognito con su contraseña:** uno en `administradores` y un `jugador`.

### 6.3 Las 5 Preguntas Oficiales de Defensa de la E3 (`EP3-Entrega-3.pdf` pág. 8)
1. **¿Qué va al `.dlt` y qué se reintenta, y por qué no se reintenta para siempre?**
2. **¿Por qué no se pueden disminuir las particiones de un topic?**
3. **¿Por qué `gw-aws` acepta el `443` solo desde `gw-azure`, y para qué está abierto el `80`?**
4. **¿Por qué el tag de la imagen es el `sha`, y por qué el runner vive dentro de la nube?**
5. **¿Qué hace el sistema con un evento que no trae `eventoId`?**

### 6.4 Tabla Maestra de Diagnóstico «Si algo te falló» de L12 (14 Fallos Reales)

| Lo que ves | Causa raíz | Solución exacta |
|---|---|---|
| El consumidor se detuvo en el log de `eventos` | Falta un `.dlt` con `autocreateTopics: false` (p. ej. `vidalstore.catalogo.dlt`) | Agregar el `.dlt` faltante y correr `sh kafka/topics.sh` antes de levantar `eventos`. |
| `.dlt` tiene la mitad de mensajes (`30` y `4` en vez de `60` y `8`) | Solo un grupo desvía; el desvío no quedó en la clase base `ConsumidorKafka` | Mover `desviar()` a `ConsumidorKafka<T>` para que todos los grupos desvíen lo que leen. |
| `npm ci` falla con `EBADENGINE` | Node 22 en host; el proyecto exige Node 24 | Cambiar a Node 24 (`nvm use 24`, verificar `node -v`). |
| `500` en una ruta de `/v1/admin/kafka/*` | El controlador llama al cliente Kafka directo, o el error no pasa por `traducir()` | Delegar 100% en `KafkaAdminService` y envolver con `conKafka()` + `errorDeProtocolo()`. |
| `INVALID_CONFIG: Invalid value undefined for configuration segment.ms` | Con `target: ES2023` las props opcionales del DTO viajan como `undefined` | Filtrar `Object.entries(dto.configs ?? {}).filter(([, v]) => v !== undefined)` en `crearTopic()`. |
| `Client.UserInitiatedShutdown` al crear `gw-aws` | Más de 9 instancias EC2 en la misma cuenta Learner Lab | Revisar EC2 y apagar/terminar instancias sobrantes de otros ramos o pruebas. |
| `gw-aws: no hay una instancia corriendo con Name=gw-aws` | `gw-aws` está detenida o no se creó | Ejecutar `bash deploy/aws/02-maquinas.sh gw-aws` (o `05-instancias.sh`). |
| Job `aws` en verde, pero la EC2 sigue con la imagen anterior | `aws s3 sync` sin `--exact-timestamps` no bajó `versiones.env` porque un SHA tiene el mismo tamaño que otro | Añadir `--exact-timestamps` al `aws s3 sync` dentro del job `aws` de `.github/workflows/desplegar.yml`. |
| `AADSTS530036` al correr comandos `az` | Expiró el refresh token de Azure CLI | Ejecutar `az logout` y `az login`. |
| `Permission denied (publickey)` al saltar a `bff` | No se está pasando el archivo SSH config con `ProxyJump` / `ProxyCommand` y llave | Usar `ProxyCommand` con `-i` en ambos tramos o `ssh -F ~/.ssh/<config-azure> bff`. |
| `couldn't find env file .../versiones.env` en job `azure` | El job `azure` de `desplegar.yml` corre desde la raíz del repo en vez de `deploy/` | Posicionarse en `deploy/` (`cd deploy`) antes de correr `docker compose`. |
| `MAL frontend ...: 000` en job `humo` | `FRONTEND` en `versiones.env` aún apunta a imagen con `nginx` o Caddy no obtuvo certificado | Actualizar SHA de `FRONTEND` con imagen Caddy y verificar puertos 80/443 y `DOMINIO`. |
| `redirect_mismatch` en login Cognito | URL de Azure en Cognito y en `main.ts` difieren en un carácter (ej. `/` final) | Hacer que coincidan carácter por carácter en ambos sitios. |
| `403 te falta el permiso ...` al probar desde `bff` | El token usado salió por CLI (`USER_PASSWORD_AUTH`) sin el scope de aplicación | Usar el access token obtenido del login Hosted UI en el navegador. |
| `No test files found, exiting with code 1` en `pruebas` | Vitest falla si un servicio aún no tiene archivos `*.spec.ts` | Usar `npm test --if-present -- --passWithNoTests`. |
| Job `aws` queda en cola para siempre | Sesión del Learner Lab cerrada y máquina `gestion` detenida | Abrir sesión del Learner Lab y encender máquinas con `02-maquinas.sh` / `05-instancias.sh`. |
