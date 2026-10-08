# Banco de Preguntas y Respuestas Modelo · Defensa Individual EP1 y EP2

La defensa técnica individual representa el **60% de la nota final** (tanto en EP1 como en EP2). El docente Cristian Calderón (`Umbingelelo`) realiza preguntas profundas sobre las decisiones de arquitectura, los tokens, los flujos criptográficos, la mensajería asíncrona, Docker Compose, DLQ y las pruebas en vivo.

Este documento consolida:
1. **Las 8 preguntas oficiales de `Pulso.pdf` (Tramo 12.2)** (Bloque A).
2. **Las preguntas complementarias de rúbrica EP1 (IE1 a IE10)** (Bloques B, C, D y E).
3. **El guion oficial de defensa técnica de la clase D6**: reloj de 15 minutos, 5 flujos y método de 4 pasos.
4. **Las 15 preguntas oficiales de D8, L7A y L7 (Mensajería, Compose, DLQ y Persistencia)** (Bloque F).
5. **Las preguntas de defensa del Microservicio Administrador (Oscar · IE6, IE7, IE8, IE14, IE17, IE18)** (Bloque G: G.1 a G.10).
6. **Diagnóstico, Idempotencia, Clúster y Políticas (D9 y LA9)** (Bloque H: H.1 a H.14).
7. **Las 13 Preguntas Oficiales del Enunciado EP2 (EP2-Caso-VidalStore.pdf §5.3)** (Bloque I: I.1 a I.13).

---

## Bloque A: Las 8 Preguntas Oficiales de `Pulso.pdf` (§12.2)

### 1. ¿Por qué el BFF vuelve a validar el token si el gateway ya lo validó?
* **Referencia**: *Pulso Tramo 5.2 (Página 37)*.
* **Respuesta Técnica**:
  > "Por tres razones de arquitectura y seguridad, ninguna de las cuales es desconfianza hacia el gateway:
  > 1. **Defensa en profundidad y Zero Trust**: Nadie garantiza que la petición provino exclusivamente del gateway. Si un servicio dentro de la red interna o un contenedor mal configurado habla directo al puerto del BFF, el BFF no puede asumir ciegamente que la petición 'viene de adentro'.
  > 2. **El BFF necesita los claims, no solo el veredicto**: El gateway responde un veredicto binario (pasa / no pasa), pero el BFF necesita saber quién es el usuario (`sub`) para filtrar sus datos en el service. Ya que tiene que abrir el token para leerlo, verificar la firma criptográfica con `jwtVerify` tiene un costo computacional casi nulo.
  > 3. **Múltiples canales de entrada futuros**: En la evolución del sistema (ej. consumo de mensajes desde una cola RabbitMQ o SQS), las peticiones no pasan por ningún gateway. Si la validación viviera solo en el borde, cualquier entrada alternativa quedaría desprotegida."
  * **Frase clave**: *«El gateway protege el perímetro; el BFF protege al servicio, incluso de dentro del perímetro.»*

---

### 2. ¿Qué decide un scope y qué decide un grupo, y por qué son cosas distintas?
* **Referencia**: *Pulso L3 §7.1, Tramo 6 (Página 42)*.
* **Respuesta Técnica**:
  > "* **El Scope (`vidalstore/catalogo.leer`) decide qué operaciones puede pedir la aplicación cliente** (el frontend web o móvil) ante la API. Limita el alcance técnico del cliente. Cualquier persona que entre por ese cliente recibirá un token con esos mismos scopes.
  > * **El Grupo (`cognito:groups`) decide qué rol tiene la persona humana** que está detrás del teclado (`jugadores`, `editores`, `administradores`).
  > El Gateway autoriza por **scope** en el perímetro; el BFF autoriza por **grupo** en las rutas protegidas (ej. revocar licencias con `@Roles('administradores')`)."

---

### 3. ¿Cuándo respondes 401 y cuándo 403?
* **Referencia**: *Pulso Página 3, Tramo 9*.
* **Respuesta Técnica**:
  > "* **401 Unauthorized**: Significa **«No sé quién eres»**. Ocurre cuando no hay token, la firma criptográfica no cuadra, expiró (`exp`), no está vigente (`nbf`), o el token no es de tipo acceso (`token_use !== 'access'`).
  > * **403 Forbidden**: Significa **«Sé perfectamente quién eres, pero tu rol o permiso no te alcanza»**. Ocurre cuando el token es 100% válido, pero al usuario le falta el scope requerido o no pertenece al grupo necesario (`cognito:groups`).
  > *Confundir 401 con 403 crea un bucle infinito de login*, porque un 401 le dice al navegador 'vuelve a autenticarte', y el usuario volverá a ingresar las mismas credenciales fallando indefinidamente."

---

### 4. ¿Qué pregunta de autorización no puede responder un guard, y dónde va esa comprobación?
* **Referencia**: *Pulso Tramo 7 (Páginas 45–46)*.
* **Respuesta Técnica**:
  > "La pregunta que ningún guard puede responder es: **«¿Este recurso le pertenece a este usuario?»**.
  > Un guard de NestJS solo inspecciona la cabecera HTTP, la URL y las anotaciones de la clase/método antes de ejecutar la lógica; **no ve los datos persistidos**.
  > Para saber si una licencia le pertenece al usuario que llama, hay que mirar el registro en la base de datos. Por eso esa comprobación vive exclusivamente en la capa de **Service**, filtrando los registros por `usuarioSub === sub`.
  > Si el usuario no posee registros propios, el servicio responde **`200 OK` con un arreglo vacío `[]`**, jamás 403 ni 404 (evitando ataques de enumeración)."

---

### 5. ¿Por qué el `client_id` del access token no sirve para autorizar al usuario?
* **Referencia**: *Pulso L3 §7.1, Tramo 5.3 (Página 39)*.
* **Respuesta Técnica**:
  > "Porque el `client_id` identifica a la **aplicación cliente** (el software SPA registrado en Cognito) y no al sujeto o usuario humano.
  > Solo sirve para validar que el token fue emitido específicamente para nuestro frontend de VidalStore y no para otra aplicación distinta dentro del mismo User Pool. Autorizar privilegios de usuario usando el `client_id` asumiría erróneamente que todos los usuarios de la web tienen los mismos derechos."

---

### 6. ¿Qué gana el frontend con que exista el BFF? Da el número que mediste
* **Referencia**: *Pulso Tramo 1.1, Tramo 4.3 (Páginas 10 y 35)*.
* **Respuesta Técnica**:
  > "El frontend gana tres beneficios fundamentales:
  > 1. **Una sola llamada HTTP en lugar de múltiples peticiones**: Reduce drásticamente la latencia en redes móviles.
  > 2. **Concurrencia en servidor**: Gracias a `Promise.all`, las llamadas internas a los microservicios se ejecutan en paralelo. En la medición con 300 ms de latencia por servicio, la llamada en serie tardaba ~600 ms ($300 + 300$), mientras que en paralelo tardó **~300 ms** ($\max(300, 300)$).
  > 3. **Agregación $O(N)$ y Zero Fuga de Datos**: El cruce de datos se hace en servidor mediante un `Map` por ID, enviando al navegador un DTO que contiene exclusivamente lo que la vista necesita mostrar."

---

### 7. Un usuario se registra solo y no puede entrar a nada. ¿Qué pasó y cómo lo resolviste?
* **Referencia**: *Pulso Tramo 10 (Páginas 54–57)*.
* **Respuesta Técnica**:
  > "Ocurrió la **«trampa de Cognito»**: cuando un usuario se registra por autoservicio en Cognito Managed Login / Hosted UI, Cognito **no le asigna ningún grupo por omisión**. Por lo tanto, el claim `cognito:groups` viene vacío y el usuario recibe 403 Forbidden en todas las rutas protegidas.
  > Se resuelve con fallback seguro en el guard: si el token no trae grupos, el backend asume en memoria el rol de menor privilegio (`jugadores`). En producción, la solución en nube es un trigger Lambda *Post Confirmation* que ejecuta `AdminAddUserToGroup`."

---

### 8. Al crear o revocar un recurso, ¿de dónde sacas el usuario, y por qué no del cuerpo de la petición?
* **Referencia**: *Pulso Tramo 11.3 (Páginas 62–64)*.
* **Respuesta Técnica**:
  > "El identificador del usuario (`usuarioSub`) se obtiene **estrictamente de `req.user.sub`**, el cual fue extraído del token JWT verificado criptográficamente por el `JwtGuard`.
  > **Nunca se lee del cuerpo (`@Body()`)** porque lo que envía el cliente es manipulable. Si aceptáramos el `usuarioSub` en el JSON de la petición, un atacante podría enviar el ID de otra persona y comprar o revocar licencias a nombre de un tercero (vulnerabilidad BOLA / OWASP API #1)."

---

## Bloque F: Mensajería, Docker Compose, DLQ y Persistencia Relacional (D8, L7A y L7)

### F.1. ¿Por qué se necesitan las Tres Durabilidades indispensables para no perder datos en RabbitMQ?
* **Respuesta Técnica (D8 Slides 22-24)**:
  > "Se necesitan tres elementos combinados:
  > 1. **Volumen nombrado de Docker** (`-v datos-rabbit:/var/lib/rabbitmq`): Preserva la base de datos Mnesia al recrear el contenedor.
  > 2. **Cola durable** (`{ durable: true }`): Preserva la metadata y definición de la cola si el broker se reinicia.
  > 3. **Mensaje persistent** (`{ persistent: true }` o `deliveryMode: 2` en el productor): Obliga al broker a escribir el contenido en disco y no retenerlo únicamente en memoria RAM. Si falta cualquiera de las tres, ante un reinicio o caída forzada los mensajes se pierden."

---

### F.2. ¿Para qué sirve `prefetch(1)` y por qué debe configurarse antes de consumir?
* **Respuesta Técnica (L7A Slide 18 y L7 Tramo 2.4)**:
  > "`prefetch(1)` limita a 1 la cantidad de mensajes sin confirmar (`unacked`) que el broker puede entregar a la vez a un consumidor. Sin prefetch (`prefetch(0)`), RabbitMQ vuelca en la memoria del proceso todos los mensajes de la cola de golpe. Si la base de datos de persistencia se cae, el worker acumularía miles de mensajes en memoria y, si muere, todos vuelven a `ready` saturando la infraestructura. Con `prefetch(1)`, el worker procesa uno, persiste, envía `ack`, y recién recibe el siguiente."

---

### F.3. ¿Por qué la columna `payload` en la tabla `mensajes_muertos` es `text` y JAMÁS `jsonb`?
* **Respuesta Técnica (L7 Tramo 4.4 y 5.1)**:
  > "Porque la causa más común de descarte de un mensaje envenenado es que venga corrupto, malformado o no cumpla sintaxis JSON (por ejemplo el caso de prueba `emitir.mjs --roto`). Si definiéramos la columna como `jsonb`, PostgreSQL arrojaría un error de sintaxis al intentar hacer el `INSERT`, el consumidor de DLQ fallaría, y el mensaje envenenado no podría guardarse ni registrarse para auditoría forense. Con `text`, cualquier cadena de bytes rota se almacena íntegra."

---

### F.4. ¿Por qué el consumidor confirma con `ack` cuando detecta el error SQL `23505` (`unique_violation`)?
* **Respuesta Técnica (L7 Tramo 4.8 y L7A Slide 23)**:
  > "El código SQLSTATE `23505` indica violación de clave única (idempotencia en `evento_id`). Significa que el evento **ya fue procesado y persistido con éxito en una entrega previa**, y volvió a entregarse debido a un reinicio de red o caída antes del ack original. Como el trabajo ya está hecho en la base de datos, el consumidor debe confirmar con `canal.ack(mensaje)` y registrar una advertencia. Mandarlo a la DLQ con `nack` sería un error grave porque contaminaría la cola de cartas muertas con eventos válidos ya procesados."

---

## Bloque G: Microservicio Administrador (`vidalstore-admin` · Oscar · IE6, IE7, IE8, IE17, IE18)

### G.1. ¿Cuál es la responsabilidad del microservicio `vidalstore-admin` (:3020) y cómo se integra en la arquitectura?
* **Respuesta Técnica**:
  > "Es el microservicio de observabilidad, control y auditoría operativa de la plataforma de mensajería (dueño: Oscar). Se comunica con la **RabbitMQ Management HTTP API** (:15672) para inspeccionar métricas de colas, exchanges, bindings y salud del clúster, y se conecta a **PostgreSQL** para auditar y depurar la tabla `mensajes_muertos`. Está protegido perimetralmente con Cognito JWT y expone los contratos REST administrativos bajo `/v1/admin`."

---

### G.2. ¿Cómo responde `GET /v1/admin/queues` y qué métricas normaliza para cumplir con IE18?
* **Respuesta Técnica**:
  > "Consulta la Management API en `/api/queues/%2f`. Si RabbitMQ responde 200, normaliza cada cola a la interfaz `RabbitQueueSummary`:
  > * `name`: nombre canónico (ej. `q.avisos`, `q.auditoria`, `q.correos` y sus DLQ).
  > * `messages`: mensajes totales encolados.
  > * `messages_ready`: mensajes listos para entrega inmediata.
  > * `messages_unacknowledged`: mensajes apartados en procesamiento por workers sin confirmar.
  > * `consumers`: cantidad de procesos workers suscritos activamente.
  > * `state`: estado operativo (`running`, `idle`).
  > Si la Management API está caída o inaccesible, captura el error de red o timeout y lanza `ServiceUnavailableException` (HTTP 503), cumpliendo con la tolerancia a fallos de IE17."

---

### G.3. ¿Cómo implementa `GET /v1/admin/queues/:name` el manejo de recursos inexistentes (404 vs 503)?
* **Respuesta Técnica**:
  > "Invoca `/api/queues/%2f/:name`. Si RabbitMQ responde `404 Not Found`, el servicio lanza explícitamente `NotFoundException('Cola no encontrada en RabbitMQ')`, retornando HTTP 404 limpio al cliente. Si la API de RabbitMQ no contesta o hay error de socket (`ECONNREFUSED`), responde `503 Service Unavailable`. Esto previene respuestas engañosas y cumple con la semántica REST estricta de IE7."

---

### G.4. ¿Por qué `GET /v1/admin/exchanges` distingue entre exchanges de negocio y exchanges internos del broker?
* **Respuesta Técnica**:
  > "Porque RabbitMQ incluye por omisión exchanges amq.* (`amq.direct`, `amq.topic`, `amq.fanout`, etc.). El endpoint lista todos los exchanges declarados mapeando su tipo (`topic` para `vidalstore.eventos`, `direct` para `vidalstore.comandos` y `vidalstore.dlx`) y su durabilidad (`durable: true`), permitiendo auditar si la topología fue creada conforme a los requerimientos de la evaluación."

---

### G.5. En `POST /v1/admin/publicar`, ¿de dónde se obtiene la identidad del administrador y por qué?
* **Respuesta Técnica**:
  > "La identidad se extrae estrictamente del claim `sub` mediante el decorador `@ReqUserSub()` inyectado desde `req.user.sub` (token firmado por Cognito). El controlador inyecta programáticamente este identificador dentro del payload del evento (`adminSub: sub`), garantizando trazabilidad y no-repudio absoluto en la auditoría. Si viniera en el `@Body()`, un operador podría falsificar la autoría del evento."

---

### G.6. ¿Qué función cumple `GET /v1/admin/bindings` y cómo valida las rutas de enrutamiento?
* **Respuesta Técnica**:
  > "Consulta `/api/bindings/%2f` y retorna la matriz de enlaces entre exchanges y colas. Permite verificar en vivo:
  > 1. Que las colas de trabajo estén vinculadas a `vidalstore.eventos` y `vidalstore.comandos` con los routing keys correspondientes (`compra.realizada`, `licencia.revocada`, `correo.enviar`).
  > 2. Que cada cola de trabajo tenga su binding hacia `vidalstore.dlx` con routing key idéntico al nombre de la cola."

---

### G.7. ¿Cómo reporta `GET /v1/admin/cluster` la salud y qué información expone?
* **Respuesta Técnica**:
  > "Consulta `/api/overview` y `/api/nodes`. Expone el nombre del nodo Erlang activo (`rabbit@rabbitmq1`), la versión de RabbitMQ (`4.3.6`), el estado del socket y las métricas acumuladas de mensajes procesados, confirmados y descartados."

---

### G.8. ¿Cómo implementa `GET /v1/admin/mensajes-muertos` la persistencia y qué ocurre si PostgreSQL se cae?
* **Respuesta Técnica (IE7, IE8, IE17)**:
  > "Se conecta a PostgreSQL mediante un pool resiliente (`pg.Pool`) utilizando variables de entorno (`POSTGRES_*`). Antes de consultar, ejecuta un DDL auto-sanador `CREATE TABLE IF NOT EXISTS mensajes_muertos (...)` con los tipos oficiales de L7 (`payload text`, `recibido_en timestamptz`).
  > Si la tabla está vacía, devuelve `200 OK` con un arreglo vacío `[]`.
  > Si PostgreSQL no está disponible (`ECONNREFUSED`, timeout o caída del contenedor), captura la excepción y arroja `ServiceUnavailableException('Base de datos de eventos no disponible o fuera de servicio')` (HTTP 503), evitando jamás generar un 500 ciego ni botar el proceso de Node.js."

---

### G.9. ¿Cómo opera `DELETE /v1/admin/mensajes-muertos/:id` y cómo valida los códigos 400, 404 y 503?
* **Respuesta Técnica (IE6, IE7, IE8, IE17)**:
  > "Permite a un administrador purgar físicamente un mensaje muerto de la base de datos tras su análisis forense o resolución manual:
  > 1. **Validación Sintáctica (HTTP 400)**: Utiliza `@Param('id', new ParseUUIDPipe({ version: '4' }))`. Si el cliente envía una cadena que no sea un UUID v4 válido, NestJS corta de inmediato con `400 Bad Request` (`Validation failed (uuid v 4 is expected)`).
  > 2. **Autenticación (HTTP 401)**: Protegido con `@UseGuards(AuthGuard)` validando el token de acceso de Cognito.
  > 3. **Existencia en BD (HTTP 404)**: Ejecuta `DELETE FROM mensajes_muertos WHERE id = $1`. Si `resultado.rowCount === 0`, significa que el ID no existe o ya fue eliminado, arrojando `NotFoundException('Mensaje muerto con ID ... no encontrado')` (HTTP 404).
  > 4. **Tolerancia a Fallos (HTTP 503)**: Si PostgreSQL está fuera de servicio o pierde la conexión, captura el error y lanza `ServiceUnavailableException` (HTTP 503).
  > 5. **Éxito (HTTP 200)**: Si `rowCount === 1`, confirma con `{ id, mensaje: 'Mensaje muerto eliminado exitosamente', eliminado: true }`."

---

### G.10. ¿Cómo funciona el flujo de reprocesamiento de DLQ (`POST /v1/admin/dlq/:id/reproceso`) y cómo garantiza idempotencia y trazabilidad? (Requisito Grupos de 3 · IE14, IE17)
* **Respuesta Técnica**:
  > "Es la capacidad operativa avanzada de remediación para grupos de 3 (dueño: Oscar):
  > 1. **Identidad y No-Repudio**: Extrae el `adminSub` del JWT autenticado para auditar qué administrador disparó la remediación.
  > 2. **Verificación en BD e Idempotencia (400 vs 404)**: Consulta la tabla `mensajes_muertos`. Si el registro no existe, arroja `NotFoundException` (404). Si ya tiene `reprocesada = true`, arroja `BadRequestException('El mensaje muerto con ID ... ya fue reprocesado previamente')` (400), impidiendo inundar el broker con reintentos duplicados no deseados.
  > 3. **Republicación Atómica**: Invoca `republicarMensaje` hacia `vidalstore.dlx` con routing key `dlq.reprocesar` con entrega persistente (`persistent: true`). Inyecta la metadata forense (`reprocesoId`, `colaOrigen`, `routingKeyOriginal`, `motivoOriginal`, `intentosPrevios`, `payload`, `reprocesadoPor`, `reprocesadoEn`).
  > 4. **Persistencia del Estado**: Ejecuta `UPDATE mensajes_muertos SET reprocesada = true WHERE id = $1` en PostgreSQL.
  > 5. **Tolerancia a Fallos**: Si RabbitMQ o PostgreSQL están caídos (`ECONNREFUSED` o timeout), captura la excepción y retorna `503 Service Unavailable`, evitando estados inconsistentes y sin botar el proceso."

---

## Bloque H: Diagnóstico, Idempotencia, Clúster y Políticas (D9 y LA9)

### H.1. ¿Por qué el `ack` va después del trabajo y no antes? (LA9 Ejercicio 1 / Pulso A9)
* **Respuesta Técnica**:
  > "Porque si se envía `ack` antes de completar el trabajo (como guardar en base de datos o enviar un correo) y el proceso muere a mitad de camino, el broker ya eliminó el mensaje de su memoria y la tarea pendiente se pierde para siempre en silencio (*at most once*). Al enviar `ack` estrictamente después del trabajo, si el proceso muere, el broker mantiene el mensaje en `unacknowledged` y lo reentrega a otro consumidor (*at least once*)."

---

### H.2. ¿Por qué la estrategia «reviso y luego inserto» falla ante concurrencia y la restricción `UNIQUE` sí funciona? (LA9 Ejercicio 2 / Pulso A9)
* **Respuesta Técnica**:
  > "«Reviso y luego inserto» (`SELECT existe` seguido de `INSERT`) involucra dos operaciones separadas. Existe una ventana de tiempo (latencia de red / base de datos) entre la verificación y la escritura (vulnerabilidad TOCTOU). Si dos procesos concurrentes o réplicas consultan al mismo tiempo, ambos reciben `false` y ambos insertan, duplicando el registro. Con una restricción `UNIQUE (evento_id)` en la base de datos, la validación y la inserción ocurren en un único paso atómico dentro del motor relacional."

---

### H.3. ¿Por qué cuando ocurre el error SQL `23505` (`unique_violation`) el consumidor hace `ack` y NO `nack` ni lo envía a la DLQ? (LA9 Ejercicio 2 / D9 Slide 16)
* **Respuesta Técnica**:
  > "Porque el código SQLSTATE `23505` prueba que el trabajo ya fue realizado exitosamente en una entrega previa que se quedó sin `ack` por caída de red. La fila ya existe en la tabla con los datos correctos. Hacer `nack` devolvería el mensaje para ciclar infinitamente, y enviarlo a la DLQ saturaría la cola de cartas muertas con mensajes válidos. La DLQ es para lo que no se puede procesar (datos corruptos); un duplicado sí se procesó, una vez, y con eso basta: se confirma con `canal.ack(mensaje)`."

---

### H.4. ¿Cuáles son las tres capas de error al diagnosticar un `compose.yml` con `docker compose config`? (LA9 Ejercicio 3)
* **Respuesta Técnica**:
  > "1. **Lector léxico/sintáctico de YAML** (`while parsing a block mapping`): Indentación desigual entre líneas hermanas. El lector ni siquiera pudo armar el árbol (ojo: líneas base 0 en el mensaje).
  > 2. **Constructor semántico de YAML** (`construct errors: mapping key already defined`): El árbol se armó, pero un servicio hijo quedó indentado dentro de otro (ej. `rabbit1:` con 4 espacios dentro de `postgres:`), duplicando claves.
  > 3. **Validador de esquema de Docker Compose** (`validating ...: volumes.name must be a mapping or null`): YAML sintácticamente válido, pero Compose rechaza la estructura porque no cumple su especificación técnica."

---

### H.5. ¿Cuál es el método de diagnóstico en 4 pasos y cómo se lee un stack trace? (D9 Slides 5–7)
* **Respuesta Técnica**:
  > "1. **Síntoma**: Con sus palabras y códigos exactos (`connect ECONNREFUSED 172.25.0.2:5432`), nunca 'no conecta'.
  > 2. **Hipótesis**: Explicación concreta y falsable.
  > 3. **Comando**: El comando que confirma o descarta la hipótesis (`docker compose ps`). Si descarta, se vuelve a la hipótesis; jamás se cambia código a ciegas.
  > 4. **Cambio**: Modificar una sola cosa y verificar la tendencia.
  > En un stack trace, se leen los logs de arriba hacia abajo (el primer error es la causa) y en la traza se salta todo lo ajeno (`node:net`, `node_modules/`) deteniéndose en la **primera línea de código propio (`src/...`)**."

---

### H.6. ¿Por qué ocurre `ECONNREFUSED` al 5432 al arrancar Compose y cómo se soluciona? (D9 Slides 9–12)
* **Respuesta Técnica**:
  > "Porque `depends_on: [postgres]` a secas solo espera que el contenedor esté en estado `running`, no que el proceso acepte conexiones TCP. Durante el primer arranque, PostgreSQL corre `initdb`, tardando varios segundos en escuchar en el 5432. El consumidor arranca, intenta conectar y es rechazado. Se soluciona configurando un `healthcheck` con `pg_isready` en el servicio `postgres`, declarando `depends_on: { postgres: { condition: service_healthy } }` en el consumidor, e iniciando con `docker compose up -d --wait`."

---

### H.7. ¿Por qué al recrear el contenedor de RabbitMQ las colas desaparecen aunque el volumen nombrado persista? (D9 Slide 13)
* **Respuesta Técnica**:
  > "RabbitMQ guarda su base de datos Mnesia en `/var/lib/rabbitmq/mnesia/rabbit@<hostname>`. Sin un hostname fijo en Compose, Docker genera un ID aleatorio nuevo en cada recreación (ej. `rabbit@a1b2c3d4`). RabbitMQ nace buscando esa carpeta nueva y vacía, dejando intacta y huérfana la carpeta anterior dentro del volumen. Se soluciona declarando obligatoriamente `hostname: rabbit1` en `compose.yml`."

---

### H.8. ¿Cuáles son las cuatro salidas de un consumidor y por qué no se reintenta un error permanente? (D9 Slides 15–17)
* **Respuesta Técnica**:
  > "1. **Éxito**: `canal.ack(mensaje)`.
  > 2. **Duplicado (`23505`)**: `canal.ack(mensaje)` y log informativo.
  > 3. **Error permanente** (JSON mal formado, falta campo obligatorio, error sintáctico SQL 22/23): `canal.nack(mensaje, false, false)` directo a DLQ. No se reintenta porque un dato malo fallará igual en el intento un millón.
  > 4. **Error transitorio** (base de datos caída, timeout): se reintenta con backoff exponencial y jitter hasta un límite fijo; si se agotan los reintentos, se desvía con `canal.nack(mensaje, false, false)` a la DLQ."

---

### H.9. ¿Por qué un clúster de dos nodos no replica automáticamente las colas clásicas y cómo se logra con Quorum Queues? (D9 Slides 20–23)
* **Respuesta Técnica**:
  > "Porque en RabbitMQ una cola clásica (*classic queue*) vive exclusivamente en el nodo en el que fue declarada; los demás nodos solo conocen su metadata y redirigen las conexiones hacia él. Para que una cola se replique en múltiples nodos debe declararse como **Quorum Queue** con `{ durable: true, arguments: { 'x-queue-type': 'quorum' } }`, la cual utiliza el algoritmo de consenso Raft. Las antiguas colas espejadas (`mirrored queues` / `ha-mode`) ya no existen en RabbitMQ 4."

---

### H.10. ¿Cuántas caídas aguanta un clúster de 2 nodos con Quorum Queues y por qué? (D9 Slide 24 / EP2 §5.1)
* **Respuesta Técnica**:
  > "Aguanta **0 caídas**. En el algoritmo Raft, la mayoría requerida es más de la mitad: $\lfloor 2/2 \rfloor + 1 = 2$. Con dos nodos, la mayoría son 2. Si cae un nodo, el nodo sobreviviente queda en estado `minority` (1 de 2) y suspende la confirmación de nuevas escrituras. Para tolerar 1 caída se requieren 3 nodos (donde la mayoría sigue siendo 2). En la defensa de la EP2, demostrar la detención de `rabbit2` evidencia que el clúster entra en minoría y no confirma publicaciones."

---

### H.11. Diagnostique: Cola con `ready: 9` y subiendo, `unacked: 3` y quieto, `consumers: 1`, `deliver: 0`. ¿Qué está pasando? (D9 Slide 29)
* **Respuesta Técnica**:
  > "Es un bug de código en el consumidor: **se alcanzó el tope del `prefetch` (3) y el consumidor olvidó enviar `ack`** (o se quedó colgado en una promesa sin resolver). Como hay 3 mensajes entregados sin confirmar, RabbitMQ se niega a entregar más (`deliver: 0`), mientras que los mensajes nuevos del productor se acumulan en cola (`ready` subiendo). No es que el productor publique muy rápido ni que el broker esté caído."

---

### H.12. ¿Cuál es la diferencia entre desborde `drop-head` y `reject-publish`, y qué política corresponde a `avisos` vs `auditoria`? (D9 Slides 30–33)
* **Respuesta Técnica**:
  > "* **`drop-head`**: Descarta en silencio los mensajes más antiguos del frente de la cola al alcanzar el tope. Corresponde a la **cola de avisos**, porque una notificación vieja de hace días ya no tiene utilidad de negocio.
  > * **`reject-publish`**: Rechaza la publicación devolviendo un nack al productor. Corresponde a la **cola de auditoría**, porque es la prueba legal del sistema; descartar un evento de auditoría en silencio es inaceptable y el productor debe enterarse del rechazo."

---

### H.13. ¿Por qué no se debe republicar al exchange para «reintentar» un mensaje que falló? (D9 Slide 15)
* **Respuesta Técnica**:
  > "Porque en `vidalstore.eventos` la cola de auditoría está enlazada con el comodín `#` y otras colas capturan eventos por patrón. Si el consumidor republica el mensaje fallido al exchange, se disparará una entrega no solo a la cola que falló sino a todas las colas suscritas, generando duplicaciones descontroladas en cascada."

---

### H.14. ¿Qué pasa si una DLQ tiene configurado `drop-head` o un `message-ttl` corto? (D9 Slide 33)
* **Respuesta Técnica**:
  > "Se destruye la evidencia de los errores del sistema. La DLQ existe para preservar los mensajes envenenados para auditoría forense y reprocesamiento. Si la DLQ descarta mensajes por tiempo o desborde, se incumple la exigencia del negocio de Arturo Vidal de no perder nunca la trazabilidad de los fallos."

---

## Bloque I: Las 13 Preguntas Oficiales del Enunciado EP2 (`EP2-Caso-VidalStore.pdf` §5.3)

### I.1. ¿Por qué los eventos van a un exchange `topic` y los comandos a uno `direct`? ¿Qué se rompería al invertirlo?
* **Respuesta Técnica**:
  > "Los **eventos** anuncian hechos consumados en el pasado que le interesan a múltiples consumidores con distintos niveles de granularidad (auditoría quiere `#`, avisos quiere `compra.*` o `licencia.revocada`). Por eso van a un exchange `topic`.  
  > Los **comandos** son órdenes imperativas dirigidas a un único destinatario concreto (`correo.enviar` va solo al consumidor de correos).  
  > Si se invirtiera:
  > - Usar `direct` para eventos impediría enrutamiento por patrones (`*` y `#`), forzando a declarar bindings explícitos uno a uno y rompiendo el desacoplamiento de auditoría global.
  > - Usar `topic` para comandos expondría las órdenes a suscripciones accidentales por comodines, provocando que múltiples workers ejecuten la misma orden de envío."

---

### I.2. ¿Qué pasa exactamente si el consumidor muere después de insertar en Postgres y antes del `ack`? ¿Cuál de las dos garantías entrega este sistema y qué mecanismo la hace tolerable?
* **Respuesta Técnica**:
  > "Si el consumidor muere tras el insert y antes del `ack`, RabbitMQ detecta la pérdida del canal TCP y devuelve el mensaje de `unacknowledged` al frente de la cola (`requeue`). Cuando un nuevo worker se conecta, el mensaje se vuelve a entregar.  
  > Por lo tanto, el sistema entrega la garantía **al menos una vez (*at least once*)**.  
  > El mecanismo que la hace tolerable es el **índice `UNIQUE (evento_id)` en la tabla `eventos_auditoria`**: la segunda inserción es rechazada por Postgres con código `23505`, el consumidor lo atrapa, registra un aviso y envía `ack`, impidiendo filas duplicadas."

---

### I.3. ¿Por qué un mensaje mal formado no se reintenta y un fallo de conexión sí?
* **Respuesta Técnica**:
  > "Porque un mensaje mal formado (JSON roto, falta de campos obligatorios como `usuarioSub`) tiene un **error permanente intrínseco al dato**: fallará exactamente igual en el reintento uno y en el reintento un millón, y reintentarlo bloquearía la cola. Por eso va directo a la DLQ.  
  > En contraste, un fallo de conexión a Postgres o timeout es un **error transitorio del entorno**: el mensaje está sano pero la base de datos se está reiniciando o saturando. Reintentar con backoff permite procesar el mensaje con éxito tan pronto la infraestructura se restablece."

---

### I.4. ¿Qué pasa si la DLQ no existe cuando llega el primer rechazo?
* **Respuesta Técnica**:
  > "Si la DLQ no está declarada o su binding con `vidalstore.dlx` no existe en el momento en que una cola de trabajo rechaza un mensaje con `nack(false, false)`, **RabbitMQ descarta el mensaje silenciosamente y se pierde para siempre sin error**. Por esta razón, la regla de oro de topología exige declarar primero el DLX y las tres DLQs antes de declarar las colas de trabajo."

---

### I.5. ¿Por qué `licencias` lleva un `UNIQUE` parcial y no un `UNIQUE` simple, y por qué esa regla vive en la base de datos y no en el controlador?
* **Respuesta Técnica**:
  > "Porque un `UNIQUE` simple sobre `(usuario_sub, juego_id)` impediría que un usuario vuelva a comprar un juego si su licencia anterior fue revocada. Con un índice parcial `UNIQUE (usuario_sub, juego_id) WHERE estado = 'activa'`, el usuario solo puede tener una licencia **activa** a la vez, pero si se revoca (`estado = 'revocada'`), puede adquirirla nuevamente de forma legítima.  
  > Vive en la base de datos porque es el único punto que previene condiciones de carrera concurrentes (TOCTOU) e inmune a que un controlador olvide comprobar el estado antes de insertar."

---

### I.6. ¿Por qué `juego_id` no es una clave foránea?
* **Respuesta Técnica**:
  > "Porque el catálogo de juegos pertenece a otro microservicio desacoplado (`vidalstore-backend` / Catálogo) que gestiona su propio ciclo de vida y almacenamiento (`catalogo.json`). Crear una clave foránea física en Postgres crearía un **acoplamiento monolítico en base de datos**: si el catálogo cambia o se migra, la base de licencias se rompería. Se almacena como un entero referencial desacoplado y se documenta como relación lógica en el diagrama entidad-relación."

---

### I.7. ¿Por qué `synchronize: true` no se usa en producción, y qué se usa en su lugar?
* **Respuesta Técnica**:
  > "Porque `synchronize: true` compara las entidades de TypeScript con la base de datos al arrancar y modifica el esquema automáticamente en vivo. Si una entidad renombra una columna, TypeORM puede interpretar un `DROP COLUMN` seguido de un `ADD COLUMN`, **borrando irreversiblemente datos reales de producción**. En producción se configura `synchronize: false` y los cambios de esquema se gestionan estrictamente mediante **migraciones versionadas** (`typeorm migration:run`)."

---

### I.8. ¿Qué comparten los dos nodos del clúster y qué no? ¿Qué se pierde al caer uno?
* **Respuesta Técnica**:
  > "* **Qué comparten**: Definiciones globales de usuarios, contraseñas, virtual hosts, exchanges, bindings, políticas y la cookie de Erlang (`RABBITMQ_ERLANG_COOKIE`).
  > * **Qué no comparten por defecto**: Los mensajes y el almacenamiento de las colas clásicas (*classic queues*), que residen en el nodo que las declaró.
  > * **Qué se pierde al caer uno**: Si las colas son clásicas, las colas alojadas en el nodo caído quedan inaccesibles. Si son Quorum Queues, con 2 nodos se pierde el quórum de mayoría (Raft exige 2 de 2), por lo que se suspenden las confirmaciones de nuevas escrituras hasta recuperar el nodo."

---

### I.9. ¿Qué política pusieron en las DLQ y qué evidencia se pierde si esa política está mal calibrada?
* **Respuesta Técnica**:
  > "Las DLQs deben configurarse con límites amplios o retención persistente sin descarte agresivo. Si se aplica por error un `x-overflow: drop-head` o un `x-message-ttl` corto (ej. pocas horas), **se eliminan automáticamente los mensajes envenenados y los fallos de procesamiento**. Eso destruiría la evidencia forense necesaria para responder qué falló y privaría al sistema de los datos para el reproceso controlado."

---

### I.10. ¿Cuál de los once puntos de la demostración fue el más difícil de conseguir y qué lo resolvió?
* **Respuesta Técnica**:
  > "El punto más exigente fue **IE11 (Levantar el clúster y stack completo con Docker Compose y `--wait`)**: lograr la sincronización estricta de arranque entre PostgreSQL y RabbitMQ mediante `healthcheck` y `condition: service_healthy`, asegurando que `rabbit1` y `rabbit2` se reconocieran automáticamente sin scripts manuales y que ningún worker cayera por `ECONNREFUSED`."

---

### I.11. ¿Por qué publica el microservicio y no el BFF? ¿Qué pasa si el microservicio alcanza a escribir la licencia y el proceso se cae antes de publicar el evento, y cómo se darían cuenta?
* **Respuesta Técnica**:
  > "Publica el microservicio porque es el dueño de la entidad y de la transacción. El BFF solo autoriza y reenvía; si publicara él, anunciaría hechos que no escribió y si fallara la red entre BFF y microservicio, se publicarían compras inexistentes.  
  > Si el microservicio escribe en Postgres y cae antes de publicar en RabbitMQ, la licencia queda guardada pero no se emite el evento (ventana de inconsistencia dual).  
  > **Cómo se darían cuenta**: Comparando la tabla `licencias` en Postgres con la tabla `eventos_auditoria`. Habrá una fila en `licencias` cuyo `id` no tiene un evento correlacionado en la auditoría. En arquitecturas avanzadas esto se resuelve con el patrón *Transactional Outbox*."

---

### I.12. ¿Quién es dueño de cada tabla y cómo lo demuestran en el código? ¿Qué pasaría si un consumidor escribiera directamente en `licencias`?
* **Respuesta Técnica**:
  > "* `licencias` pertenece exclusivamente al **microservicio de licencias**, configurada en su módulo de persistencia y esquema propio.
  > * `eventos_auditoria`, `notificaciones` y `mensajes_muertos` pertenecen a **`vidalstore-eventos`**.  
  > Se demuestra en el código porque cada proyecto tiene su propia configuración de conexión TypeORM y sus propias entidades aisladas. Si un consumidor escribiera directamente en `licencias`, violaría los Bounded Contexts y el principio de responsabilidad única, acoplando dos servicios al mismo esquema y arriesgando bloqueos y corrupciones de datos concurrentes."

---

### I.13. ¿De dónde salieron los juegos del catálogo en una máquina recién clonada?
* **Respuesta Técnica**:
  > "Salieron del archivo versionado `data/catalogo.json`, el cual fue generado por el script `data/seed.ts` (o `.js`) que consumió una API externa real (ej. CheapShark / FreeToGame). En una máquina recién clonada, el catálogo está poblado de inmediato desde el repositorio sin necesidad de inicializar bases de datos externas para esa lectura."


