# Guía Técnica Oficial: Diagnóstico, Idempotencia, Clúster RabbitMQ y Políticas (D9 y LA9)

Esta guía documenta los fundamentos teóricos, los ejercicios prácticos de laboratorio y los criterios de evaluación introducidos en la **Clase D9 ("Diagnosticar sin adivinar y clúster RabbitMQ")** y el **Laboratorio A9 ("Actividad: Ack, DLQ e idempotencia, construidos juntos")** del profesor Cristian Calderón (`Umbingelelo`) para la asignatura **DSY1107 - Desarrollo Cloud Native I** (Evaluación Parcial 2).

---

## 1. Laboratorio A9 (Pulso A9): Ack, Idempotencia y Compose

El Laboratorio A9 aborda de forma aislada y experimental (mediante programas de Node.js en módulos ES sin dependencias externas ni RabbitMQ instalado) tres problemas cruciales de la EP2:
1. El comportamiento del `ack` manual y la garantía *at least once*.
2. Por qué la validación en código (`revisoYLuegoInserto`) falla ante concurrencia y solo la restricción `UNIQUE` en base de datos garantiza idempotencia.
3. El diagnóstico de errores de indentación en `compose.yml` en tres capas con `docker compose config`.

---

### 1.1 Ejercicio 1 · Una Cola con ACK Manual (`cola.mjs`)

En RabbitMQ, una cola gestiona internamente dos listas de mensajes:
- **`messages_ready`**: Mensajes que esperan ser entregados a un consumidor disponible.
- **`messages_unacknowledged`**: Mensajes entregados a un consumidor que aún no han recibido confirmación (`ack`).

#### Modos de Consumo y Garantías de Entrega
| Modo | Configuración AMQP | Ciclo de Vida del Mensaje | Garantía de Entrega | Riesgo Crítico |
|---|---|---|---|---|
| **Auto-ACK** | `{ noAck: true }` | El broker elimina el mensaje de la memoria inmediatamente al entregarlo por el socket TCP. | **A lo más una vez (*At most once*)** | Si el consumidor muere a mitad de procesamiento (ej: insertó en base pero falló antes de enviar el correo), **el mensaje se destruye para siempre sin aviso**. |
| **Manual ACK** | `{ noAck: false }` | El mensaje pasa de `ready` a `unacknowledged`. Solo se elimina cuando el consumidor invoca explícitamente `canal.ack(mensaje)`. | **Al menos una vez (*At least once*)** | Si el canal o el consumidor se desconecta sin confirmar, los mensajes en `unacknowledged` vuelven al frente de la cola (`requeue`) para el siguiente consumidor. **Puede duplicar trabajo si no hay idempotencia.** |

#### La Regla del ACK Después del Trabajo
> **¿Por qué el `ack` va DESPUÉS del trabajo y no antes?**  
> Si se envía `ack` antes de realizar las operaciones secundarias (ej. antes de enviar el correo o antes del `INSERT`), y el proceso muere súbitamente, el broker ya olvidó el mensaje y la tarea pendiente **se pierde en silencio**.  
> Al enviar `ack` estrictamente al final, si el proceso se cae a la mitad, el broker conserva el mensaje y lo reentrega a otro consumidor. El costo de esta resiliencia es que las acciones previas se ejecutan dos veces, lo que exige **idempotencia obligatoria** en la persistencia.

---

### 1.2 Ejercicio 2 · Idempotencia y Condición de Carrera (`guardar.mjs`)

Una operación es **idempotente** si ejecutarla $N$ veces produce exactamente el mismo estado final que ejecutarla una sola vez.

#### Comparación de Enfoques de Persistencia
```
1. Sin Control:
   INSERT directo -> DUPLICA SIEMPRE (2 filas en base de datos).

2. Reviso y luego inserto (Anti-patrón TOCTOU):
   SELECT COUNT(*) WHERE evento_id = $1;
   if (count === 0) INSERT INTO ...
   - En serie: Funciona (1 fila).
   - En paralelo (2 llamadas concurrentes / réplicas / prefetch > 1): FALLA ROTUNDAMENTE (2 filas).

3. Clave Única (UNIQUE en base de datos):
   INSERT INTO tabla (...) VALUES (...) 
   ON CONFLICT / Atrapa error SQLSTATE 23505 (unique_violation) -> CONFIRMA CON ACK (1 fila siempre).
```

#### ¿Por qué Falla «Reviso y Luego Inserto»? (Ventana TOCTOU)
Entre la consulta (`SELECT existe`) y la escritura (`INSERT`) transcurre una ventana de tiempo (latencia de red, tiempo de ejecución en PostgreSQL). Si dos workers o dos promesas concurrentes consultan antes de que la primera haya completado su inserción, **ambas reciben `false` (no existe) y ambas proceden a insertar**.
- Achicar la latencia (incluso a $0$ ms) no cierra la ventana; solo la hace invisible en desarrollo y letal en producción con réplicas.
- La atomicidad solo se garantiza si la validación y la inserción ocurren en el mismo paso dentro del motor relacional mediante un índice **`UNIQUE (evento_id)`**.

#### ¿Por qué el Duplicado (Error `23505`) se Confirma con `ACK` y NO va a la DLQ?
Cuando PostgreSQL rechaza una inserción con el error SQLSTATE `23505` (`unique_violation`):
1. **El trabajo ya fue realizado con éxito**: La fila ya existe en la tabla con los datos requeridos debido a una entrega previa.
2. **Hacer `nack` con requeue provocaría un bucle infinito**: El mensaje volvería a la cola para rebotar perpetuamente contra el índice único.
3. **Mandar el duplicado a la DLQ saturaría la cola de cartas muertas**: La DLQ es un depósito forense para mensajes corruptos o fallos irrecuperables de procesamiento, no para mensajes válidos que RabbitMQ reentregó legítimamente bajo su garantía *at least once*.
4. **Acción requerida**: El consumidor atrapa el código `23505`, registra un log informativo (`"Mensaje duplicado ya procesado"`) y envía **`canal.ack(mensaje)`**.

---

### 1.3 Ejercicio 3 · Las 3 Capas de Diagnóstico de `compose.yml`

El comando `docker compose config` lee, valida sintácticamente y normaliza el archivo `compose.yml` **sin instanciar contenedores, redes ni volúmenes**. Permite detectar errores de indentación que en YAML alteran la jerarquía de las claves.

Compose se detiene en el primer error encontrado. Los tres tipos de error pertenecen a tres capas distintas:

| Capa de Error | Mensaje Típico de Error | Causa Raíz | Cómo Interpretar y Corregir |
|---|---|---|---|
| **1. Parser Léxico/Sintáctico YAML** | `yaml: while parsing a block mapping at line 4, column 5: line 7, column ...` | Indentación rota (espacios dispares entre claves hermanas). | El lector ni siquiera pudo armar el árbol. **Ojo con el conteo de líneas base 0**: en mensajes `while parsing`, la línea reportada $N$ corresponde a la línea $N+1$ en el editor (ej. línea 7 en el error = línea 8 del archivo). |
| **2. Constructor Semántico YAML** | `yaml: construct errors: line 1: line 18: mapping key "image" already defined at line 5` | Una clave de servicio quedó indentada dentro de otro servicio vecino (ej. `rabbit1:` con 4 espacios en vez de 2). | El árbol YAML se parseó, pero `rabbit1` pasó a ser un atributo hijo de `postgres`, duplicando la propiedad `image`. El conteo de líneas coincide exactamente con el editor. |
| **3. Validador de Esquema Docker Compose** | `validating .../compose.yml: volumes.name must be a mapping or null` | YAML válido sintácticamente, pero viola las especificaciones de esquema de Docker Compose (ej. `name:` con 2 espacios en vez de 4 dentro de `volumes:`). | Compose interpreta `name` como un tercer volumen independiente con valor de cadena, en vez de un atributo del volumen nombrado anterior. |

---

### 1.4 Respuestas Oficiales de la Caja de Pulso A9

1. **Salida de `cola.mjs` (modo auto vs manual)**:
   - Modo `auto`: Al caer el consumidor A procesando el mensaje 2, la cola queda en `cola=[3] pendientes=[]`. El consumidor B solo procesa el 3. Filas en base: `[1, 2, 3]`; correos enviados: `[1, 3]` (el correo 2 se perdió para siempre).
   - Modo `manual`: Al caer A, `pendientes=[2]`. Tras cortar el canal, el mensaje vuelve: `cola=[2, 3] pendientes=[]`. B procesa 2 y 3. Filas en base: `[1, 2, 2, 3]`; correos enviados: `[1, 2, 3]` (ningún correo se perdió; la persistencia requirió deduplicación).
2. **Salida de `guardar.mjs`**:
   - `sinControl`: serie $\rightarrow$ 2 filas; a la vez $\rightarrow$ 2 filas.
   - `revisoYLuegoInserto`: serie $\rightarrow$ 1 fila; a la vez $\rightarrow$ 2 filas (falla por carrera).
   - `conClaveUnica`: serie $\rightarrow$ 1 fila; a la vez $\rightarrow$ 1 fila (idempotencia absoluta).
3. **¿Por qué el `ack` va después del trabajo y no antes?**:
   - Porque si se confirma antes y el proceso muere durante el trabajo posterior (como el envío de correo en el mensaje 2), el broker descarta el mensaje y la tarea pendiente se pierde sin rastro ni posibilidad de reintento.
4. **¿Por qué `revisoYLuegoInserto` deja 2 filas cuando las llamadas llegan a la vez y `conClaveUnica` no?**:
   - Porque entre el `SELECT existe` y el `INSERT` hay una ventana de tiempo en la cual ninguna llamada ha insertado aún, por lo que ambas reciben `false` e insertan. Con `UNIQUE`, la verificación y la escritura son un paso atómico interno del motor de base de datos.

---

## 2. Clase Magistral D9: Diagnosticar sin Adivinar y Clúster RabbitMQ

La clase D9 establece el protocolo metodológico de depuración para evitar el tanteo a ciegas ("adivinar"), detalla la resiliencia en consumidores y formaliza la arquitectura de clúster RabbitMQ requerida para la EP2.

---

### 2.1 Método de Diagnóstico en 4 Pasos

El diagnóstico técnico profesional consiste en **reducir el espacio de lo posible mediante evidencia**:
1. **Síntoma**: Definido con sus palabras técnicas exactas y mensajes literales (ej. `connect ECONNREFUSED 172.25.0.2:5432`), nunca afirmaciones vagas como "no conecta" o "se cayó".
2. **Hipótesis**: Explicación concreta y **falsable** (ej. "Postgres está en ejecución pero aún no acepta conexiones porque `initdb` sigue corriendo").
3. **Comando**: Ejecutar el comando exacto que **confirma o descarta** la hipótesis (ej. `docker compose ps` para revisar el estado del healthcheck). Si el comando descarta la hipótesis, **se regresa al paso 2**; jamás se modifica código basándose en una hipótesis refutada.
4. **Cambio**: Modificar **una sola cosa a la vez**, la que la hipótesis confirmada señala, y volver a probar para evaluar si la tendencia o síntoma cambió.

#### Reglas de Lectura de Logs y Stack Traces
- **Los logs se leen de ARRIBA hacia ABAJO**: La última línea suele ser una consecuencia secundaria (ej. `exited with code 1`). El error raíz siempre es la **primera línea anómala** del registro.
- **Saltarse lo ajeno en el Stack Trace**: Las trazas contienen decenas de líneas internas del motor de Node (`node:net`, `node:events`) o librerías externas (`node_modules/amqplib`, `node_modules/pg-pool`). **El diagnóstico se detiene en la primera línea que apunte al código propio (`src/...`)**, la cual señala exactamente qué función invocó la operación fallida.

---

### 2.2 Caso 1: `ECONNREFUSED` al 5432 y la Condición `service_healthy`

- **Causa Raíz**: En Docker Compose, `depends_on: [postgres]` solo espera que el contenedor pase a estado `running`. Cuando el volumen está vacío o se inicializa por primera vez, PostgreSQL ejecuta `initdb`, demorando varios segundos en abrir el socket TCP 5432. El consumidor de eventos arranca de inmediato, intenta conectar y es rechazado (`ECONNREFUSED`).
- **Solución en Compose**:
  ```yaml
  services:
    postgres:
      image: postgres:18
      healthcheck:
        test: ["CMD-SHELL", "pg_isready -U biblioteca -d biblioteca"]
        interval: 5s
        retries: 10
    eventos:
      depends_on:
        postgres:
          condition: service_healthy # Espera confirmación activa de pg_isready
  ```
- **Comando de Arranque**: `docker compose up -d --wait` garantiza que la terminal no retorne hasta que todos los servicios cumplan su healthcheck.

---

### 2.3 Caso 2: Pérdida de Colas al Recrear Contenedores y `hostname` Fijo

- **Causa Raíz**: RabbitMQ almacena su base de datos interna Mnesia en una carpeta cuyo nombre contiene el Erlang Node Name: `/var/lib/rabbitmq/mnesia/rabbit@<hostname>`.
- Si no se define un hostname fijo en Docker Compose, Docker asigna el ID aleatorio del contenedor como hostname (ej. `rabbit@a1b2c3d4e5f6`). Al ejecutar `docker compose down` y volver a levantar, el nuevo contenedor nace con otro ID aleatorio, **creando una base Mnesia nueva y vacía**. El volumen nombrado preserva los datos anteriores, pero RabbitMQ los ignora porque busca una carpeta con el nuevo nombre.
- **Verificación**: `docker exec rabbit1 rabbitmqctl eval 'node().'` debe devolver `rabbit@rabbit1`.
- **Solución**: Fijar obligatoriamente `hostname: rabbit1` en la definición del servicio en `compose.yml`.

---

### 2.4 Matriz de las Cuatro Salidas del Consumidor (IE5 · 20% del Encargo)

Un consumidor resiliente no se limita a un `try/catch` genérico; implementa cuatro salidas diferenciadas según la naturaleza del evento y del error:

| Situación | Ejemplo en VidalStore | Decisión Técnica | Destino del Mensaje | Justificación |
|---|---|---|---|---|
| **1. Éxito de Negocio** | `licencia.revocada` guardada en `eventos_auditoria`. | `canal.ack(mensaje)` | Fuera de la cola (procesado). | El broker elimina el mensaje tras la persistencia confirmada. |
| **2. Mensaje Ya Procesado (Duplicado)** | Reentrega por reinicio; inserción falla con SQLSTATE `23505` en `evento_id`. | `canal.ack(mensaje)` + log `WARN` ("duplicado detectado"). | Fuera de la cola (sin duplicar fila). | La fila ya existe en base de datos. Hacer `nack` ciclaría el mensaje; mandarlo a DLQ contaminaría cartas muertas con datos válidos. |
| **3. Error Permanente (Mensaje Envenenado / Dato Corrupto)** | JSON inválido (`SyntaxError`), falta `usuarioSub`, o error SQLSTATE `22...`/`23...` (ej. `22P02 invalid input syntax for type uuid`). | `canal.nack(mensaje, false, false)` sin reintentar. | **DLX $\rightarrow$ DLQ $\rightarrow$ `mensajes_muertos`**. | El dato está mal estructurado. Reintentar fallará infinitamente y bloqueará la cola. Va a DLQ para auditoría forense. |
| **4. Error Transitorio (Infraestructura / Conexión)** | PostgreSQL caído, timeout, o `ECONNREFUSED` al puerto 5432. | Función `conReintentos` (hasta 3 veces con backoff y jitter). Si se agotan los intentos: `canal.nack(mensaje, false, false)`. | Permanece en procesamiento durante reintentos; si agota intentos va a DLQ. | El mensaje es válido pero el entorno falló temporalmente. Si el fallo persiste, se aparta para no congelar la cola. |

> [!CAUTION]
> **Prohibido republicar al exchange para «reintentar»**:  
> Si un consumidor publica el mensaje de vuelta en `vidalstore.eventos` para simular un reintento, y la cola de auditoría está suscrita con `#`, en cada iteración la cola recibirá copias adicionales que desencadenarán una tormenta de mensajes duplicados.

#### Backoff Exponencial y Jitter en Reintentos
```javascript
const dormir = (ms) => new Promise(r => setTimeout(r, ms));

async function conReintentos(tarea, intentos = 3) {
  for (let i = 0; i < intentos; i++) {
    try {
      return await tarea();
    } catch (error) {
      if (i === intentos - 1) throw error; // Límite obligatorio: permite desviar a DLQ
      // Backoff exponencial (1s, 2s, 4s...) + Jitter aleatorio
      const espera = (2 ** i) * 1000 + Math.random() * 300;
      await dormir(espera);
    }
  }
}
```
- **Backoff Exponencial**: Da tiempo al servicio saturado (Postgres) para recuperarse en vez de machacarlo continuamente.
- **Jitter (`Math.random()`)**: Desfasa temporalmente los reintentos de múltiples consumidores simultáneos, evitando tormentas sincronizadas (*thundering herd problem*).

---

### 2.5 Clúster RabbitMQ de Dos Nodos (IE9, IE10, IE11)

Un clúster de RabbitMQ agrupa múltiples nodos que comparten metadatos globales (usuarios, virtual hosts, exchanges, bindings y políticas) y coordinan conexiones entre sí.

#### Configuración del Clúster
- Nodos: `rabbit1` (puertos `5672` y `15672`) y `rabbit2` (puertos `5673` y `15673`).
- **`RABBITMQ_ERLANG_COOKIE`**: Secreto compartido indispensable montado desde el archivo `.env`. Sin coincidencia exacta de este cookie, los nodos se rechazan criptográficamente.
- **Auto-unión**: Se configura en `rabbitmq.conf` o scripts de arranque sin intervención manual:
  ```ini
  cluster_formation.peer_discovery_backend = rabbit_peer_discovery_classic_config
  cluster_formation.classic_config.nodes.1 = rabbit@rabbit1
  cluster_formation.classic_config.nodes.2 = rabbit@rabbit2
  ```

#### Colas Clásicas vs Quorum Queues
| Característica | Colas Clásicas (*Classic Queues*) | Quorum Queues (*Quorum Queues*) |
|---|---|---|
| **Replicación en Clúster** | **NO SE REPLICAN**. Viven en un solo nodo (el que las declaró). Los demás nodos solo actúan como proxies reenviando tráfico. | **REPLICADAS**. Distribuyen copias en múltiples nodos del clúster bajo el algoritmo Raft. |
| **Declaración en amqplib** | `{ durable: true }` | `{ durable: true, arguments: { 'x-queue-type': 'quorum' } }` |
| **Tolerancia a Fallos** | Si el nodo donde vive la cola cae, la cola queda inaccesible hasta que el nodo se recupere. | Si el líder cae, las réplicas eligen un nuevo líder transparente para productores y consumidores. |
| **Estado en RabbitMQ 4** | Activas. | **Estándar mandatorio para alta disponibilidad**. (*Nota*: Las antiguas `mirrored queues` / `ha-mode` fueron completamente eliminadas en RabbitMQ 4). |

#### La Regla del Quórum de Mayoría en Raft
Una Quorum Queue exige la confirmación de la **mayoría estricta** de sus miembros para confirmar una escritura:
$$\text{Mayoría} = \left\lfloor \frac{N}{2} \right\rfloor + 1$$

| Nodos ($N$) | Mayoría Necesaria | Caídas Toleradas sin Perder Quórum |
|:---:|:---:|:---:|
| **2 (EP2)** | **2** | **0** |
| **3** | **2** | **1** |
| **4** | **3** | **1** |
| **5** | **3** | **2** |

> [!WARNING]
> **Comportamiento en la Defensa (Caída de `rabbit2` con 2 Nodos)**:  
> En un clúster de 2 nodos, la mayoría requerida es 2. Si se detiene `rabbit2`, queda 1 solo nodo activo ($1 < 2$), por lo que el clúster entra en estado `minority`.  
> **Las Quorum Queues suspenden la aceptación y confirmación de nuevas escrituras hasta que el segundo nodo vuelva a levantarse**. Afirmar en la defensa que un clúster de 2 nodos tolera la caída de un nodo y sigue operando con normalidad es un error conceptual grave sancionado por la rúbrica (IE10).

---

### 2.6 Métricas Operativas de RabbitMQ (IE18)

Las métricas del broker se inspeccionan por tres vías:
1. **Management UI**: Web en `http://localhost:15672` (usuario/clave de `.env`).
2. **Línea de Comandos (CLI)**: `docker exec rabbit1 rabbitmqctl list_queues name messages_ready messages_unacknowledged consumers`.
3. **HTTP API**: `GET /api/queues/%2f` (utilizada por `vidalstore-admin`).

#### Catálogo de Decisiones Operativas por Métrica
| Métrica | Qué Mide | Valor Normal | Anomalía Típica | Causa y Acción Correctiva |
|---|---|---|---|---|
| **Colas Activas** | Número de colas declaradas. | 6 (3 trabajo + 3 DLQ) | Menor a 6 | El worker falló al arrancar y no completó la declaración de topología. Revisar logs con `docker compose logs --tail 50 eventos`. |
| **`messages_ready`** | Mensajes esperando ser entregados. | Cero o buffer bajo estable | Crecimiento sostenido con tendencia alcista | Productor publica más rápido de lo que el worker procesa. Escalar cantidad de réplicas de consumidores. |
| **`consumers`** | Cantidad de workers conectados a la cola. | $\ge 1$ | **0 con mensajes en ready** | El servicio consumidor está caído o desconectado del broker. Diagnóstico más rápido de corte de servicio. |
| **`messages_unacknowledged`** | Mensajes entregados al worker sin `ack`. | Bajo y oscilante (acotado por prefetch) | **Fijo en el tope del prefetch (ej: 1 o 3) y no baja** | **Bug de código en el consumidor**: el proceso olvidó ejecutar `ack` o se quedó esperando una promesa colgada sin timeout. RabbitMQ bloquea la entrega de nuevos mensajes. |
| **Mensajes en DLQ** | Mensajes rechazados enviados a cartas muertas. | **0** | $> 0$ | Hay mensajes envenenados o errores de datos. Abrir `mensajes_muertos` en Postgres o consultar `/v1/admin/mensajes-muertos` para depurar el payload. |

---

### 2.7 Políticas de Retención, Limpieza y Estrategias de Desborde (IE19)

Si una cola no tiene límites y el productor publica sin control, la cola crece hasta **agotar la memoria RAM del nodo**. RabbitMQ activa su alarma global de memoria (`vm_memory_high_watermark`) y **bloquea todas las publicaciones en todas las colas del broker**.

#### Declaración en Código vs Políticas del Broker
- **En Código (`arguments` en `assertQueue`)**: Parámetros fijos. Para modificarlos se requiere eliminar la cola (`rabbitmqctl delete_queue`) y reiniciar el servicio, arriesgando error `406 PRECONDITION_FAILED`.
- **Por Política (`rabbitmqctl set_policy`)**: Regla dinámica aplicada por patrón regex a colas existentes sin alterar código ni reiniciar servicios:
  ```bash
  # Política para limitar la cola de avisos a 100.000 mensajes con drop-head
  docker exec rabbit1 rabbitmqctl set_policy tope-avisos '^avisos$' '{"max-length":100000,"overflow":"drop-head"}' --apply-to queues
  ```

#### Decisión de Negocio: `drop-head` vs `reject-publish`
| Estrategia de Overflow | Comportamiento al Llegar al Límite | Caso de Uso en VidalStore | Justificación de Arquitectura |
|---|---|---|---|
| **`drop-head`** | Descarta silenciosamente los mensajes más antiguos del frente de la cola para admitir los nuevos. | **Cola de Avisos** | Las notificaciones son efímeras (un aviso de juego o compra de hace días pierde relevancia ante novedades inmediatas). |
| **`reject-publish`** | Rechaza las nuevas publicaciones devolviendo un `basic.nack` al productor. | **Cola de Auditoría** | La auditoría es la evidencia legal de las operaciones. Descartar registros silenciosamente es inaceptable; el productor debe enterarse del fallo para reaccionar. |

> [!WARNING]
> **Trampa Crítica en la DLQ**:  
> Configurar `drop-head` o un `message-ttl` agresivo en las colas DLQ destruye la evidencia de los fallos, contradiciendo el requerimiento fundamental de trazabilidad del caso. Las DLQs deben tener políticas calibradas para no perder mensajes de error antes de su análisis y reprocesamiento.
