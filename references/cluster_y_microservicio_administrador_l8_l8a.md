# Guía Técnica Oficial: Clúster RabbitMQ, Quorum Queues y Microservicio Administrador (L8 y L8A)

Esta guía documenta los fundamentos teóricos, la arquitectura de código, las decisiones de diseño y las preguntas de defensa introducidas en la **Clase Pre-laboratorio L8A ("Clúster y microservicio administrador")** y la guía oficial **Laboratorio L8 (Pulso L8)** del profesor Cristian Calderón (`Umbingelelo`) para la asignatura **DSY1107 - Desarrollo Cloud Native I** (Semana 10 · Unidad 2 · Evaluación Parcial 2).

---

## 1. Encuadre Pedagógico y Rúbrica de la EP2

El Laboratorio L8 cierra la Unidad 2 y cubre **30% del encargo técnico grupal** y **27% de la presentación técnica individual** de la EP2:

| Indicador de la EP2 | Ponderación | Dónde se Construye | Qué Evalúa el Docente |
|---|:---:|:---:|---|
| **IE6. Microservicio administrador con endpoints REST** | **13% Encargo** | Tramo 3 | Verbos y rutas REST coherentes (`POST` crea, `DELETE` borra, nombre del recurso en URL). Protegido por rol (`ADMIN`). |
| **IE7. Lógica encapsulada en un `RabbitAdminService`** | **10% Encargo** | Tramo 3.4 | El controlador no habla con `amqplib`. Cero llamadas directas al broker en controladores. Mapeo semántico a códigos HTTP (400, 404, 409, 503). |
| **IE8. La API valida los parámetros de entrada** | **7% Encargo** | Tramo 3.3 · 3.6 | DTOs con `class-validator` y `ValidationPipe` global con `whitelist: true` y `forbidNonWhitelisted: true`. Rechazo con `400 Bad Request`. |
| **IE9. Dos nodos RabbitMQ** | **5% Defensa** | Tramo 1 | `rabbit1` y `rabbit2` en ejecución, cada uno con su propio puerto y volumen. |
| **IE10. Clúster de RabbitMQ con esos dos nodos** | **8% Defensa** | Tramo 1 · 2 | Clúster formado compartiendo cookie de Erlang y `cluster.conf`. Explicación rigurosa de qué comparten y qué pasa al caer uno. |
| **IE17. Microservicio administrador operativo** | **12% Defensa** | Tramo 3 | Demostración en vivo de operaciones CRUD de colas, exchanges y bindings con errores controlados. |
| **IE18. Métricas de monitoreo del clúster** | **8% Defensa** | Tramo 4 | Explicación fundamentada de las 6 métricas clave: colas activas, `messages_ready`, `messages_unacknowledged`, consumidores y mensajes en DLQ. |
| **IE19. Políticas de retención y limpieza** | **10% Defensa** | Tramo 5 | Políticas versionadas en el repositorio (`politicas.json`): `max-length`, expiración (`message-ttl`) y comportamiento de `overflow` (`drop-head` vs `reject-publish`). |

---

## 2. Tramo 1 · Clúster de Dos Nodos en Docker Compose

### 2.1 Por qué un Solo Nodo no Basta y qué es un Clúster
- **Un nodo suelto**: Si el contenedor muere o se corrompe su disco, todo el sistema de mensajería se paraliza.
- **Dos contenedores sueltos sin clúster**: No comparten nada. Si un productor publica en el puerto 5672 (`rabbit1`) y un consumidor escucha en el 5673 (`rabbit2`), el consumidor jamás recibirá el mensaje porque son dos mundos aislados.
- **Un clúster**: Múltiples nodos de RabbitMQ que operan como una sola entidad lógica unificada. Comparten usuarios, permisos, virtual hosts, definiciones de exchanges, bindings y metadatos de colas. Un cliente conectado a cualquier nodo puede publicar hacia un exchange y el mensaje llegará a la cola correspondiente aunque su líder resida en otro nodo.

### 2.2 La Cookie de Erlang (`.erlang.cookie` / `RABBITMQ_ERLANG_COOKIE`)
- **Propósito**: Es el secreto compartido que permite a dos nodos Erlang comunicarse entre sí. Sin la misma cookie, un nodo rechaza la conexión del otro inmediatamente.
- **Seguridad**: La cookie autentica conversaciones de red entre nodos del runtime; **no cifra ni firma los datos guardados en disco**.
- **Configuración en Compose**: Se inyecta en ambos contenedores mediante la variable de entorno `RABBITMQ_ERLANG_COOKIE: ${RABBITMQ_COOKIE}` en el bloque `environment:` de `rabbit1` y `rabbit2`.
- **Permisos en disco**: Si se manipula el archivo físico (`/var/lib/rabbitmq/.erlang.cookie`), Erlang exige que sea legible **únicamente por su dueño (`chmod 400`)**; de lo contrario, el nodo se niega a arrancar.

### 2.3 Archivo `cluster.conf` y Descubrimiento Automático
Para evitar comandos manuales de unión (`join_cluster`) que violan el requisito de «un solo `docker compose up -d`», la unión se automatiza mediante el archivo de configuración `cluster.conf` montado en ambos nodos:

```ini
# rabbitmq/cluster.conf
cluster_formation.peer_discovery_backend = rabbit_peer_discovery_classic_config
cluster_formation.classic_config.nodes.1 = rabbit@rabbit1
cluster_formation.classic_config.nodes.2 = rabbit@rabbit2
```

Montaje en `compose.yml`:
```yaml
services:
  rabbit1:
    image: rabbitmq:4.3-management
    hostname: rabbit1
    environment:
      RABBITMQ_ERLANG_COOKIE: ${RABBITMQ_COOKIE}
    volumes:
      - datos-rabbit1:/var/lib/rabbitmq
      - ./rabbitmq/cluster.conf:/etc/rabbitmq/conf.d/20-cluster.conf:ro
    ports:
      - "5672:5672"
      - "15672:15672"

  rabbit2:
    image: rabbitmq:4.3-management
    hostname: rabbit2
    environment:
      RABBITMQ_ERLANG_COOKIE: ${RABBITMQ_COOKIE}
    volumes:
      - datos-rabbit2:/var/lib/rabbitmq
      - ./rabbitmq/cluster.conf:/etc/rabbitmq/conf.d/20-cluster.conf:ro
    ports:
      - "5673:5672"
      - "15673:15672"
```

### 2.4 Por qué `rabbit2` NO Lleva `depends_on: { rabbit1: { condition: service_healthy } }`
- Si se configura `depends_on: { condition: service_healthy }` sobre `rabbit1`, Compose retarda el arranque de `rabbit2` hasta que `rabbit1` complete su `healthcheck`.
- Esto introduce una **trampa de arranque en frío**: si en un reinicio `rabbit1` espera encontrar a `rabbit2` para sincronizar metadatos antes de responder a su propio healthcheck, ambos nodos quedan en un bloqueo mutuo (*deadlock*).
- Además, si `rabbit1` se recrea por cambio de configuración o volumen, Compose detecta que `rabbit1` no está `healthy` y cancela el arranque de `rabbit2` con el error: `dependency failed to start: container rabbit1 is unhealthy`.
- Por tanto, `rabbit2` **no lleva `depends_on`** de `rabbit1`. Ambos arrancan en paralelo y `cluster.conf` gestiona el emparejamiento entre pares de forma autónoma.

### 2.5 Interpretación de `rabbitmqctl cluster_status`
Al ejecutar:
```bash
docker compose exec rabbit1 rabbitmqctl cluster_status
```
Se observan dos secciones fundamentales:
1. **`Disk Nodes`**: Lista los nodos que forman parte del clúster registrado en disco (`rabbit@rabbit1`, `rabbit@rabbit2`).
2. **`Running Nodes`**: Lista los nodos que están actualmente encendidos, conectados y operando en el clúster.

#### Comportamiento al Apagar `rabbit2` (`docker compose stop rabbit2`):
- `Disk Nodes`: Permanece con **ambos nodos** (`rabbit@rabbit1` y `rabbit@rabbit2`). El clúster no olvida que `rabbit2` es miembro.
- `Running Nodes`: Muestra **únicamente a `rabbit@rabbit1`**.
- Al ejecutar `docker compose start rabbit2`, `rabbit2` reingresa inmediatamente a `Running Nodes` **sin necesidad de repetir ningún comando `join_cluster` manual**, ya que la unión persiste en el volumen de Docker.

### 2.6 Procedimiento de Rescate de Unión a Mano
Si por carrera al arrancar en una máquina limpia `rabbit2` arrancó antes que `rabbit1`, no lo encontró en la red y formó un clúster solitario de un solo nodo, se rescata ejecutando los 4 comandos estrictamente sobre **`rabbit2`**:

```bash
docker compose exec rabbit2 rabbitmqctl stop_app
docker compose exec rabbit2 rabbitmqctl reset
docker compose exec rabbit2 rabbitmqctl join_cluster rabbit@rabbit1
docker compose exec rabbit2 rabbitmqctl start_app
```

> [!CAUTION]
> **REGLA DE ORO DE SEGURIDAD:**
> Jamás ejecutar `reset` sobre `rabbit1`. Ejecutar `reset` sobre `rabbit1` borraría toda la base de datos Mnesia del nodo maestro, eliminando de inmediato las colas, exchanges y usuarios creados en L7. `reset` se ejecuta **únicamente sobre `rabbit2`**, borrando sus datos temporales para que pueda adoptar limpiamente los metadatos de `rabbit1`.

---

## 3. Tramo 2 · Quorum Queues, Replicación Raft y Mayoría

### 3.1 Colas Clásicas vs Quorum Queues en RabbitMQ 4
| Característica | Cola Clásica (*Classic Queue*) | Cola Quorum (*Quorum Queue*) |
|---|---|---|
| **Almacenamiento** | Vive en un solo nodo (el nodo donde se declaró). | Replicada en múltiples nodos mediante un grupo de consenso Raft. |
| **Rol en el clúster** | Los otros nodos solo actúan como proxies/enrutadores hacia el nodo dueño. | Un nodo es el **Leader** (recibe lecturas y escrituras); los demás son **Followers** (copian el log Raft). |
| **Caída del nodo dueño** | **La cola queda completamente inaccesible** hasta que el nodo reviva. | Si hay mayoría de réplicas vivas, se elige un nuevo Leader de inmediato sin interrupción. |
| **Colas Espejo (`ha-mode: all`)** | Obsoletas. **Eliminadas formalmente en RabbitMQ 4.0**. | El estándar oficial y obligatorio de alta durabilidad en RabbitMQ 4+. |
| **Declaración AMQP** | Argumentos por defecto. | Requiere argumento obligatorio: **`{ 'x-queue-type': 'quorum' }`**. |

### 3.2 Migración de Colas a Quorum en `topologia.ts`
En `src/mensajeria/topologia.ts` se agrega `'x-queue-type': 'quorum'` en:
1. `argumentosDeCola` para las 3 colas de trabajo (`q.avisos`, `q.auditoria`, `q.correos`).
2. El objeto de configuración de las 3 colas de descarte (`auditoria.dlq`, `notificaciones.dlq`, `correos.dlq`).

#### Error `406 PRECONDITION_FAILED - inequivalent arg 'x-queue-type'`
Si una cola ya existía como `classic` (de L7) y el worker arranca solicitando `quorum`, RabbitMQ lanza `PRECONDITION_FAILED` y detiene el canal, dejando al contenedor en `Exit 1`.
**Solución**: En RabbitMQ los argumentos estructurales de una cola son inmutables. Se deben eliminar las colas existentes antes de relanzar el worker:
```bash
docker compose exec rabbit1 rabbitmqctl delete_queue notificaciones
docker compose exec rabbit1 rabbitmqctl delete_queue notificaciones.dlq
docker compose exec rabbit1 rabbitmqctl delete_queue auditoria
docker compose exec rabbit1 rabbitmqctl delete_queue auditoria.dlq
docker compose exec rabbit1 rabbitmqctl delete_queue correos
docker compose exec rabbit1 rabbitmqctl delete_queue correos.dlq
docker compose restart eventos
```

### 3.3 Qué Pasa de Verdad al Apagar `rabbit2` (El Fenómeno de `minority`)
Cuando `rabbit2` se detiene con `docker compose stop rabbit2`:
1. `cluster_status`: `rabbit2` sale de `Running Nodes`.
2. `quorum_status`: La réplica de `rabbit2` pasa a estado `noconnection`; `rabbit1` permanece como `leader`.
3. `/api/queues`: La propiedad `state` de las colas quorum pasa a **`minority`**.
4. `rabbitmqctl list_queues state`: Sigue respondiendo **`running`**.
   - *¿Por qué no se contradicen?* Porque responden preguntas distintas:
     - `rabbitmqctl list_queues state`: Mide si el proceso local de Erlang de la cola está vivo en `rabbit1` (lo está).
     - `/api/queues state`: Mide si la cola quorum dispone de la **mayoría Raft necesaria para confirmar escrituras** (no la tiene: está en `minority`).

#### La Trampa de `sendToQueue` sin Confirmaciones
Si un productor ejecuta `canal.sendToQueue(...)` mientras la cola está en `minority`:
- `sendToQueue` devuelve **`true`** de inmediato.
- **Ese `true` NO significa que RabbitMQ guardó el mensaje**: solo significa que el mensaje entró al buffer del socket TCP del cliente.
- Sin quórum Raft, el líder `rabbit1` no puede confirmar la escritura. El mensaje **no entra a la cola y se descarta o queda suspendido**.
- **Canal con Confirmaciones (`confirmChannel`)**: Al usar canales confirmados (`publisher-confirms`), el productor espera la respuesta real del broker. Sin mayoría, la llamada entra en espera y termina con un error de timeout (`confirm_timeout`).

### 3.4 La Cuenta de la Mayoría: $\lfloor N / 2 \rfloor + 1$
El consenso distribuido de Raft exige la mayoría estricta de las réplicas para confirmar cualquier cambio en el log:

$$\text{Mayoría Requerida} = \lfloor N / 2 \rfloor + 1$$

| Réplicas ($N$) | Mayoría Requerida | Caídas que Tolera | Diagnóstico Operativo |
|:---:|:---:|:---:|---|
| **1** | 1 | **0** | Sin replicación. Un fallo tumba la cola. |
| **2 (Nuestro Caso)** | **2** | **0** | **Perder 1 nodo es perder la mayoría (queda 1 de 2). Tolera cero caídas.** |
| **3** | 2 | **1** | Si cae 1 nodo, quedan 2 vivos (2 de 3 $\ge$ 2). La cola sigue operando. |
| **5** | 3 | **2** | Soporta la pérdida de hasta 2 nodos simultáneos. |

### 3.5 La Pregunta Decisiva de la Defensa Técnica
> **Pregunta de Examen:** *"Si un clúster de dos nodos tolera cero caídas, ¿para qué sirve? ¿Por qué la pauta pide dos nodos?"*
> 
> **Respuesta Técnica Definitiva:**
> *"Dos nodos me otorgan **durabilidad distribuida y recuperación automática**, no alta disponibilidad.  
> 1. **Cero pérdida de datos**: Los mensajes confirmados residen en dos discos físicos independientes. Si un nodo se quema, los datos sobreviven intactos en el otro.  
> 2. **Recuperación automática sin intervención**: Cuando el nodo caído se levanta, Raft lo resincroniza automáticamente y el servicio se restablece solo sin comandos manuales.  
> 3. **Arquitectura lista para escalar**: La topología en Docker Compose y `cluster.conf` queda armada; pasar a alta disponibilidad real solo requiere agregar un tercer nodo al compose (`rabbit3`), ya que la alta disponibilidad en Raft exige un número impar (mínimo 3 réplicas para tolerar 1 caída)."*

### 3.6 Diagnóstico Preventivo con `rabbitmq-diagnostics`
RabbitMQ permite verificar si un nodo es crítico para el quórum sin necesidad de apagarlo:
```bash
docker compose exec rabbit1 rabbitmq-diagnostics check_if_node_is_quorum_critical
```
En un clúster de dos nodos, la salida confirma por escrito:
```text
Checking if node rabbit@rabbit1 is critical for quorum of any queues/streams ...
queue 'notificaciones' in vhost '/' will become unavailable if node rabbit@rabbit1 stops
queue 'notificaciones.dlq' in vhost '/' will become unavailable if node rabbit@rabbit1 stops
queue 'auditoria' in vhost '/' will become unavailable if node rabbit@rabbit1 stops
queue 'auditoria.dlq' in vhost '/' will become unavailable if node rabbit@rabbit1 stops
queue 'correos' in vhost '/' will become unavailable if node rabbit@rabbit1 stops
queue 'correos.dlq' in vhost '/' will become unavailable if node rabbit@rabbit1 stops
rabbitmq_metadata will become unavailable if node rabbit@rabbit1 stops
```
- El comando finaliza con **código de salida 69** a propósito, alertando que el nodo es crítico.
- **`rabbitmq_metadata`**: También es un grupo de consenso Raft. Por eso, con un nodo caído tampoco se pueden crear colas ni exchanges nuevos; el intento tarda 30 segundos y falla con: `Could not declare quorum queue ... because the metadata store operation timed out`.

---

## 4. Tramo 3 · Microservicio Administrador (`vidalstore-admin`)

### 4.1 Arquitectura de Dos Protocolos
`vidalstore-admin` (puerto `3020`) utiliza dos protocolos diferenciados para hablar con el broker:
1. **AMQP (`amqp://rabbit1:5672`)**: Para **operaciones mutativas** (crear colas, borrar colas, crear exchanges, borrar exchanges, crear bindings, desvincular bindings). Utiliza la librería nativa `amqplib`.
2. **HTTP Management API (`http://rabbit1:15672/api`)**: Para **operaciones de lectura e inspección** (listar colas, listar métricas de overview y nodos). Utiliza llamadas HTTP con autenticación Basic (`Authorization: Basic <base64(user:pass)>`).

```
                    ┌────────────────────────┐
                    │    AdminController     │ (:3020)
                    └───────────┬────────────┘
                                │ invoca métodos de alto nivel
                    ┌───────────▼────────────┐
                    │   RabbitAdminService   │
                    └─────┬────────────┬─────┘
                          │ AMQP       │ HTTP
                          │ (:5672)    │ (:15672)
                          │            │
                          ▼            ▼
                   ┌──────────────────────────┐
                   │   RabbitMQ (rabbit1)     │
                   └──────────────────────────┘
```

### 4.2 Recorrido de una Petición de Afuera hacia Adentro
Cada capa de la arquitectura valida y corta la petición con su propio código de estado HTTP antes de que la capa siguiente sea invocada:

```
Petición Entrante (curl con Bearer token y JSON body)
  │
  ▼
[ 1. JwtGuard ] ─────────► Firma inválida o sin token? ──► 401 Unauthorized
  │
  ▼
[ 2. RolGuard ] ─────────► Rol distinto de ADMIN? ───────► 403 Forbidden
  │
  ▼
[ 3. ValidationPipe ] ───► Body con campos inválidos? ───► 400 Bad Request
  │
  ▼
[ 4. AdminController ] ──► Puro enrutamiento HTTP y DTOs (cero amqplib)
  │
  ▼
[ 5. RabbitAdminService ]► Mapeo de errores de RabbitMQ:
                           • Recurso inexistente (NOT_FOUND) ──────► 404 Not Found
                           • Conflicto parámetros (PRECONDITION) ──► 409 Conflict
                           • Broker caído / sin mayoría Raft ─────► 503 Service Unavailable
```

### 4.3 DTOs y Validación de Parámetros (`class-validator`)
Prohibido permitir que datos corruptos alcancen el broker:
- **`CrearColaDto`**:
  ```typescript
  export const TIPOS_DE_COLA = ['quorum', 'classic'] as const;
  export type TipoDeCola = (typeof TIPOS_DE_COLA)[number];

  const NOMBRE_VALIDO = /^[a-zA-Z0-9._-]+$/;

  export class CrearColaDto {
    @IsString({ message: 'nombre tiene que ser string' })
    @IsNotEmpty({ message: 'nombre no puede estar vacio' })
    @Matches(NOMBRE_VALIDO, {
      message: 'nombre solo puede tener letras, numeros, puntos, guiones y guiones bajos',
    })
    nombre!: string;

    @IsOptional()
    @IsIn(TIPOS_DE_COLA, { message: 'tipo tiene que ser quorum o classic' })
    tipo?: TipoDeCola;
  }
  ```
- **`CrearExchangeDto`**:
  ```typescript
  export const TIPOS_DE_EXCHANGE = ['topic', 'direct', 'fanout', 'headers'] as const;
  export type TipoDeExchange = (typeof TIPOS_DE_EXCHANGE)[number];

  export class CrearExchangeDto {
    @IsString()
    @IsNotEmpty()
    @Matches(NOMBRE_VALIDO)
    nombre!: string;

    @IsIn(TIPOS_DE_EXCHANGE)
    tipo!: TipoDeExchange;
  }
  ```
- **`BindingDto`**:
  ```typescript
  const ROUTING_KEY_VALIDA = /^[a-zA-Z0-9._#*-]+$/;

  export class BindingDto {
    @IsString()
    @IsNotEmpty()
    @Matches(NOMBRE_VALIDO)
    exchange!: string;

    @IsString()
    @IsNotEmpty()
    @Matches(NOMBRE_VALIDO)
    cola!: string;

    @IsString()
    @Matches(ROUTING_KEY_VALIDA, {
      message: 'routingKey solo admite letras, numeros, puntos, guiones, # y *',
    })
    routingKey!: string;
  }
  ```

#### Configuración de `ValidationPipe` en `main.ts`:
```typescript
app.useGlobalPipes(
  new ValidationPipe({
    whitelist: true, // Descarta campos sobrantes
    forbidNonWhitelisted: true, // Responde 400 Bad Request si envían propiedades no declaradas
    transform: true, // Convierte el payload a la instancia real del DTO
    transformOptions: { enableImplicitConversion: false },
  }),
);
```

### 4.4 Las Tres Decisiones Clave del `RabbitAdminService`
1. **Conexión Persistente Única vs Canal Efímero por Operación**:
   - Abrir una conexión TCP AMQP es costoso (handshake de red, credenciales, negociación de heartbeat). Se abre una sola vez al arrancar el servicio.
   - Los canales AMQP son ligeros y económicos. **Se abre un canal nuevo por cada operación** y se cierra al terminar (`await canal.close()`).  
     *¿Por qué?* Porque cuando RabbitMQ rechaza un comando (ej. cola inexistente o conflicto de argumentos), **cierra el canal AMQP entero**. Si el canal fuera compartido, el error de un usuario destruiría las peticiones de todos los demás.
   - **Oyente de error obligatorio**: Cada canal efímero registra `canal.on('error', () => undefined)` para evitar que el evento de cierre de canal se propague como excepción no controlada que tumbe el proceso de Node.js.
2. **Función `traducir()` (Mapeo Semántico de AMQP a Códigos HTTP)**:
   ```typescript
   private traducir(error: unknown): never {
     const mensaje = error instanceof Error ? error.message : String(error);

     if (mensaje.includes('NOT_FOUND')) {
       throw new NotFoundException(mensaje); // 404
     }
     if (mensaje.includes('PRECONDITION_FAILED')) {
       throw new ConflictException(mensaje); // 409
     }
     // Broker caído, timeout de metadata o clúster sin quórum
     throw new ServiceUnavailableException(
       `RabbitMQ no esta disponible o no tiene mayoria de cluster: ${mensaje}`, // 503
     );
   }
   ```
3. **Borrado Idempotente**:
   - Si se solicita eliminar una cola o exchange que no existe, `RabbitAdminService` retorna éxito (`200 OK`) en lugar de fallar con 404. Es idempotente y consistente con los principios REST para operaciones `DELETE`.

### 4.5 Las 8 Pruebas Obligatorias de la API del Administrador
| N° | Prueba | Comando de Entrada | Código HTTP Esperado | Qué Demuestra |
|:---:|---|---|:---:|---|
| **1** | Sin token | `curl -i http://localhost:3020/v1/admin/colas` | `401 Unauthorized` | El perímetro corta en el Guard. |
| **2** | Token de rol insuficiente | `curl -i -H "Authorization: Bearer <token_jugador>" http://localhost:3020/v1/admin/colas` | `403 Forbidden` | `RolGuard` protege las rutas administrativas. |
| **3** | Body con campo inventado | `curl -i -H "Authorization: Bearer <token_admin>" -d '{"nombre":"test","campo_fantasma":"x"}' ...` | `400 Bad Request` | `forbidNonWhitelisted: true` activo en ValidationPipe. |
| **4** | Nombre inválido o vacío | `curl -i -H "Authorization: Bearer <token_admin>" -d '{"nombre":""}' ...` | `400 Bad Request` | `class-validator` valida formato y strings no vacíos. |
| **5** | Crear cola válida | `curl -i -H "Authorization: Bearer <token_admin>" -d '{"nombre":"ensayo.cola","tipo":"quorum"}' ...` | `201 Created` | Creación exitosa en el broker con tipo quorum. |
| **6** | Redeclarar con tipo distinto | `curl -i -H "Authorization: Bearer <token_admin>" -d '{"nombre":"ensayo.cola","tipo":"classic"}' ...` | `409 Conflict` | `traducir()` mapea `PRECONDITION_FAILED` a 409 Conflict. |
| **7** | Binding a cola inexistente | `curl -i -H "Authorization: Bearer <token_admin>" -d '{"exchange":"ensayo","cola":"no_existe","routingKey":"#"}' ...` | `404 Not Found` | `traducir()` mapea `NOT_FOUND` a 404 Not Found. |
| **8** | Broker caído o sin quórum | Detener `rabbit1` y consultar cualquier endpoint | `503 Service Unavailable` | Resiliencia limpia sin arrojar 500 ciego. |

---

## 5. Tramo 4 · Métricas del Clúster y Observabilidad

### 5.1 Dónde se Leen las Métricas
1. **Management UI (`http://localhost:15672`)**:
   - Pestaña **Overview**: Totales del clúster (tasas de mensajes/segundo, conexiones, canales, descriptores de archivos, memoria y disco de cada nodo en el bloque *Nodes*).
   - Pestaña **Queues and Streams**: Tabla con nombre, tipo, estado (`running` / `minority`), nodo líder, `messages_ready`, `messages_unacknowledged` y número de consumidores activos.
2. **API HTTP de RabbitMQ**: Consultas programáticas que devuelven JSON normalizado.
   - `/api/overview`: Tasas globales y versiones.
   - `/api/nodes`: Salud, memoria y espacio libre de cada nodo.
   - `/api/queues/%2F`: Listado detallado de todas las colas en el vhost `/`. *(Nota: `%2F` es la codificación URL obligatoria para `/`)*.
3. **CLI (`rabbitmqctl`)**: Consultas locales de terminal (`rabbitmqctl list_queues name type messages_ready messages_unacknowledged consumers`).

### 5.2 Las Seis Métricas Clave y Decisiones Operativas
| Métrica | Dónde se Lee | Qué Significa | Decisión Operativa que se Toma |
|---|---|---|---|
| **`messages_ready`** | `/api/queues/%2F`<br>columna *Ready* | Mensajes acumulados en la cola esperando ser entregados a un consumidor. | **La alerta más crítica**. Si sube sin bajar: los consumidores están caídos o no dan abasto ante la tasa de llegada. **Decisión**: Escalar consumidores horizontalmente o reiniciar el worker caído. |
| **`messages_unacknowledged`** | `/api/queues/%2F`<br>columna *Unacked* | Mensajes entregados a un worker pero que aún no reciben `ack`. | Si el número coincide exactamente con el valor del `prefetch` (ej. 1) y permanece congelado: el consumidor está colgado o no ejecutó `canal.ack(mensaje)`. **Decisión**: Revisar timeouts de base de datos o stack trace del worker. |
| **`disk_free` / `disk_alarm`** | `/api/nodes`<br>recuadro *Nodes* | Espacio libre en disco del volumen de RabbitMQ. | Si baja del umbral crítico (`disk_free_limit`), RabbitMQ activa una **alarma de disco y bloquea todas las publicaciones del broker**. **Decisión**: Limpiar logs, purgar colas muertas o expandir volumen físico. |
| **`mem_used` / `mem_alarm`** | `/api/nodes`<br>recuadro *Nodes* | Memoria RAM utilizada respecto al límite (*watermark*). | Si supera el límite de memoria, RabbitMQ suspende el tráfico de red de entrada. **Decisión**: Aplicar políticas de `max-length` o reducir retención en memoria. |
| **`running_nodes` / `partitions`** | `cluster_status`<br>`/api/nodes` | Nodos activos y estado de particiones de red (*network partitions*). | Si falta un nodo en `running_nodes`: hay fallo de contenedor o corte de red. Si `partitions` reporta nodos: ocurrió un *split-brain*. **Decisión**: Reiniciar el nodo aislado y validar resolución DNS. |
| **`object_totals.queues`** | `/api/overview` | Total de colas declaradas en el broker. | Si supera las 6 colas de la arquitectura oficial: alguien creó colas temporales a mano o tests sin limpiar. **Decisión**: Auditar y purgar colas no versionadas. |

### 5.3 Diagnóstico de Escenarios Críticos (Preguntas de Pulso L8)
1. **Escenario: `messages_ready` en 4200 y subiendo, con `consumers: 0`**:
   - *¿Qué pasó?* El worker se cayó o nunca arrancó; los productores siguen publicando normalmente.
   - *¿Qué NO hacer?* Jamás reiniciar RabbitMQ (el broker está haciendo su trabajo perfecto guardando los mensajes) ni purgar la cola (se destruirían mensajes legítimos de negocio).
   - *¿Qué hacer?* Inspeccionar los logs del worker (`docker compose logs eventos`), corregir la causa de la caída y levantarlo (`docker compose start eventos`).
2. **Escenario: `messages_unacknowledged` congelado en el valor de `prefetch` (ej. 1) y `consumers: 1`**:
   - *¿Qué pasó?* El consumidor está vivo pero bloqueado en una llamada sincrónica externa (ej. query lento a Postgres, conexión caída sin timeout) o tiene un error de código donde olvidó invocar `canal.ack(mensaje)`.
   - *¿Qué hacer?* Depurar la función de consumo en el worker y asegurar que las transacciones y llamadas externas tengan timeouts configurados.

---

## 6. Tramo 5 · Políticas de Retención, Límites y Desborde (`policies`)

### 6.1 Por qué una Cola sin Límite Rompe el Sistema Entero
Una cola sin límite crece de manera indefinida. Si el consumidor de cartas muertas se detiene durante un fin de semana y los fallos se acumulan, la DLQ puede acumular millones de mensajes. Al llenarse el disco, RabbitMQ levanta la alarma de disco y **bloquea la publicación en todo el broker: ninguna compra, pago ni evento puede ser procesado por ningún microservicio**. Una sola cola desatendida se lleva por delante la plataforma completa.

### 6.2 Parámetros de una Política
Se aplican mediante patrones regex sobre los nombres de las colas:
- **`max-length`**: Límite estricto de cantidad de mensajes en la cola.
- **`message-ttl`**: Tiempo de vida del mensaje en milisegundos.
- **`overflow`**: Estrategia de desborde cuando la cola alcanza su límite.

### 6.3 Estrategias de Desborde: `drop-head` vs `reject-publish`
En colas Quorum existen dos comportamientos:

| Estrategia | Comportamiento al Saturarse | Confirmación al Productor | Cuándo se Utiliza |
|---|---|---|---|
| **`drop-head`** | **Descarta el mensaje más antiguo** de la cola para hacerle espacio al nuevo. | El productor recibe confirmación exitosa (`ack`) y no se entera del descarte. | Cuando la información reciente tiene mayor valor que la histórica: colas de **Avisos** (`notificaciones`), telemetría, métricas o posiciones. |
| **`reject-publish`** | **Rechaza el mensaje entrante nuevo** y no permite su entrada a la cola. | El productor recibe un rechazo explícito (`basic.nack` / *publish confirm negative*). | Cuando no se puede perder información en silencio: colas de trabajo críticas, **Auditoría** (`auditoria`) y transacciones financieras. |

> [!NOTE]
> **Detalle técnico de Quorum Queues con `reject-publish`:**
> Una cola quorum admite exactamente un mensaje adicional sobre el límite antes de comenzar a rechazar publicaciones. Si `max-length` es 3, almacena hasta 4 mensajes antes de emitir el nack.

### 6.4 Caducidad y la Regla del TTL
- **`message-ttl`**: El tiempo de caducidad **se asigna al mensaje en el instante en que entra a la cola**.
- Si se aplica una política con `message-ttl` a una cola que ya contenía mensajes previos, dichos mensajes **no caducan de forma retroactiva**; solo caducarán los mensajes que ingresen con posterioridad a la definición de la política.

### 6.5 Versionamiento de Políticas en el Repositorio (`politicas.json`)
Las políticas definidas manualmente en la terminal con `rabbitmqctl set_policy` se pierden al recrear volúmenes (`docker compose down -v`). Por ello, las políticas oficiales deben versionarse en el repositorio `vidalstore-plataforma` en el archivo `rabbitmq/politicas.json` y montarse en `rabbit1`:

```json
{
  "policies": [
    {
      "vhost": "/",
      "name": "retencion-dlq",
      "pattern": "\\.dlq$",
      "apply-to": "quorum_queues",
      "definition": {
        "max-length": 1000,
        "message-ttl": 604800000,
        "overflow": "reject-publish"
      },
      "priority": 1
    },
    {
      "vhost": "/",
      "name": "retencion-avisos",
      "pattern": "^notificaciones$",
      "apply-to": "quorum_queues",
      "definition": {
        "max-length": 10000,
        "message-ttl": 259200000,
        "overflow": "drop-head"
      },
      "priority": 1
    },
    {
      "vhost": "/",
      "name": "retencion-trabajo",
      "pattern": "^(auditoria|correos)$",
      "apply-to": "quorum_queues",
      "definition": {
        "max-length": 50000,
        "overflow": "reject-publish"
      },
      "priority": 1
    }
  ]
}
```

Carga en Compose mediante el comando:
```bash
docker compose exec rabbit1 rabbitmqctl import_definitions /etc/rabbitmq/politicas.json
```

### 6.6 El Debate Técnico de la DLQ: `reject-publish` vs `drop-head`
En la presentación se exige fundamentar la política asignada a la DLQ:
- **Postura 1 (`reject-publish`)**: Si la DLQ llega a 1000 mensajes, el sistema lleva horas o días fallando gravemente. El problema no es dónde almacenar el mensaje 1001, sino forzar que el fallo se haga visible ruidosamente en los logs de los productores en lugar de continuar ocultando el desastre en silencio.
- **Postura 2 (`drop-head`)**: Prefiere descartar los mensajes más viejos para conservar siempre los 1000 fallos más recientes, que son los que contienen la traza y el contexto temporal útil para diagnosticar la causa raíz actual.

Ambas posturas son plenamente válidas y evaluables con 100% de logro siempre que el estudiante exponga los argumentos técnicos de ambas y justifique la adoptada por su equipo.

---

## 7. Tabla Maestra de Errores Frecuentes de L8

| Síntoma en Terminal o Log | Causa Raíz Exacta | Solución Inmediata |
|---|---|---|
| `dependency failed to start: container rabbit1 is unhealthy` | `rabbit2` tiene `depends_on: { condition: service_healthy }` hacia `rabbit1`. | Eliminar el `depends_on` de `rabbit2` en `compose.yml` y arrancar ambos en paralelo. |
| `Running Nodes` con un solo nodo en `cluster_status` | `rabbit2` arrancó antes y no encontró a `rabbit1`. | Ejecutar el procedimiento de unión a mano sobre `rabbit2`: `stop_app` -> `reset` -> `join_cluster rabbit@rabbit1` -> `start_app`. |
| Las colas de L7 y las tablas de Postgres desaparecieron | Al bloque `volumes:` de `compose.yml` le faltan los nombres explícitos (`name:`). Compose creó volúmenes temporales nuevos. | Declarar `name: datos-rabbit1` y `name: datos-postgres` en los volúmenes del compose. |
| `406 PRECONDITION_FAILED - inequivalent arg 'x-queue-type'` | La cola existía como `classic` y ahora se pide `quorum`. | Los argumentos son inmutables. Eliminar la cola con `rabbitmqctl delete_queue <nombre>` y reiniciar el worker. |
| Cola quorum reporta una sola réplica | La cola fue declarada antes de unir el clúster. | Replicar la cola al segundo nodo con: `docker compose exec rabbit1 rabbitmq-queues grow <nombre_cola> rabbit@rabbit2`. |
| `state: minority` en `/api/queues` | `rabbit2` está apagado y falta la mayoría de réplicas ($2$ de $2$). | Comportamiento esperado de Raft con 2 nodos. Levantar el nodo con `docker compose start rabbit2`. |
| `state: running` en `list_queues` con un nodo apagado | Mide el proceso local de Erlang en `rabbit1`, no el quórum distribuido. | No es un error. La salud de mayoría Raft se consulta en `/api/queues`. |
| `the metadata store operation timed out` | El clúster sin quórum Raft tampoco puede crear colas ni exchanges nuevos. | Restablecer el segundo nodo para recuperar mayoría antes de mutar la topología. |
| `Channel ended, no reply will be forthcoming` en un `503` del admin | El microservicio administrador intentó crear una cola mientras el clúster carecía de mayoría. | El timeout de 30s de Mnesia cortó el canal; `traducir()` arrojó `503 Service Unavailable` limpiamente. |
| `container eventos is unhealthy` en el segundo up | El worker quedó colgado de la conexión TCP previa con el `rabbit1` recreado. | Ejecutar `docker compose restart eventos` para que renegocie la conexión AMQP limpia. |
| `rejected: Unable to publish message. Check queue limits` | La política de la cola tiene `overflow: reject-publish` y la cola alcanzó su límite. | La política operó correctamente rechazando el desborde con un nack. |
| `error TS2307: Cannot find module 'jose'` | Falta la dependencia de validación criptográfica JWT en el microservicio administrador. | Ejecutar `npm install jose` en `vidalstore-admin`. |
| `Relative import paths need explicit file extensions` | El proyecto NestJS está configurado con módulos ES (`"type": "module"` en `package.json`). | Agregar la extensión `.js` a todos los imports relativos (ej. `import ... from './rabbit-admin.service.js'`). |
| `Nest can't resolve dependencies of the RabbitAdminService (?)` | Falta `ConfigModule.forRoot({ isGlobal: true })` en `app.module.ts`. | Importar `ConfigModule` global en el módulo raíz de NestJS. |
| `EADDRINUSE :::3020` | Otro proceso anterior de Node.js o NestJS sigue corriendo en segundo plano ocupando el puerto. | Buscar y matar el proceso (`lsof -ti:3020 | xargs kill -9`), jamás cambiar el puerto 3020 asignado. |
| El microservicio administrador muere solo al pedir un recurso inexistente | Falta el oyente `canal.on('error', () => undefined)` en el canal efímero. | Registrar siempre el oyente de error para que el cierre del canal no tumbe a Node.js. |
| Responde `200 OK` con token de jugador a rutas del administrador | `RolGuard` no está leyendo la metadata `@Roles('ADMIN')` del decorador de la clase/método. | Inyectar `Reflector` en el guard y validar `getAllAndOverride<string[]>('roles', [context.getHandler(), context.getClass()]) ?? []`. |
| `Could not parse JSON document` al aplicar política | Problema de escape de comillas en terminal Windows PowerShell. | Usar `\"` en PowerShell 5.1 o escribir la política en `politicas.json` para importarla con `import_definitions`. |
| Error `404 Not Found` en la API HTTP de Management sin explicación | Se escribió `/api/queues//` con barra suelta. | El vhost `/` debe codificarse obligatoriamente como `%2F` (`/api/queues/%2F`). |
| `message-ttl` no borra los mensajes antiguos | El TTL no es retroactivo; se asigna únicamente al momento de ENTRAR a la cola. | Los mensajes previos deben ser consumidos o purgados; los nuevos respetarán el TTL. |
| Un tutorial sugiere poner `ha-mode: all` | Las colas espejo (*mirrored queues*) pertenecían a RabbitMQ 3.x y fueron **eliminadas en la versión 4.0**. | Usar Quorum Queues (`'x-queue-type': 'quorum'`). |

---

## 8. Diagrama de Red y Mapa de Puertos de la Unidad 2

```text
  FRONTEND ANGULAR (:4200)
         │ HTTP Bearer
         ▼
  API GATEWAY (:8080)
         │ HTTP Bearer
         ▼
  BFF (:3001) ───► Microservicio Licencias (:3004)
                          │ Persistencia SQL        │ AMQP (:5672)
                          ▼                         ▼
                 PostgreSQL (:5432)        rabbit1 (:5672 / :15672)
                          ▲                         ║ Raft
                          │ Persistencia            ║
                 Worker Eventos (:3010)    rabbit2 (:5673 / :15673)
                          │ AMQP (:5672)            ▲
                          └─────────────────────────┘
                                       ▲
                                       │ AMQP (:5672) & HTTP (:15672)
                          Admin Service (:3020)
```

| Componente | Puerto AMQP / DB | Puerto HTTP / UI | Repositorio | Cómo se Levanta |
|---|:---:|:---:|---|---|
| **rabbit1** | `5672` | `15672` (Management UI) | `vidalstore-plataforma` | `docker compose up -d` |
| **rabbit2** | `5673` | `15673` (Management UI) | `vidalstore-plataforma` | `docker compose up -d` |
| **postgres** | `5432` | — | `vidalstore-plataforma` | `docker compose up -d` |
| **vidalstore-eventos** | — | `3010` (Healthcheck) | `vidalstore-eventos` | `docker compose up -d` |
| **vidalstore-admin** | — | `3020` (REST API) | `vidalstore-admin` | `npm run start:dev` |
