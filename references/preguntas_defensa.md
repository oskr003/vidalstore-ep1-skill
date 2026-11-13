# Banco de Preguntas y Respuestas Modelo · Defensa Individual EP1, EP2 y EP3

La defensa técnica individual representa el **60% de la nota final** (en EP1, EP2 y EP3). El docente Cristian Calderón (`Umbingelelo`) realiza preguntas profundas sobre las decisiones de arquitectura, los tokens, los flujos criptográficos, la mensajería asíncrona, Docker Compose, DLQ/DLT, streaming en Kafka, despliegue multi-cloud y las pruebas en vivo.

Este documento consolida:
1. **Las 8 preguntas oficiales de `Pulso.pdf` (Tramo 12.2)** (Bloque A).
2. **Las preguntas complementarias de rúbrica EP1 (IE1 a IE10)** (Bloques B, C, D y E).
3. **El guion oficial de defensa técnica de la clase D6**: reloj de 15 minutos, 5 flujos y método de 4 pasos.
4. **Las 15 preguntas oficiales de D8, L7A y L7 (Mensajería, Compose, DLQ y Persistencia)** (Bloque F).
5. **Las preguntas de defensa del Microservicio Administrador (Oscar · IE6, IE7, IE8, IE14, IE17, IE18)** (Bloque G: G.1 a G.13).
6. **Diagnóstico, Idempotencia, Clúster y Políticas (D9 y LA9)** (Bloque H: H.1 a H.14).
7. **Las 13 Preguntas Oficiales del Enunciado EP2 (EP2-Caso-VidalStore.pdf §5.3)** (Bloque I: I.1 a I.13).
8. **Las 18 Preguntas Oficiales de L8 y L8A (Clúster RabbitMQ, Quorum Queues, Admin y Políticas)** (Bloque J: J.1 a J.18).
9. **Las 15 Preguntas Oficiales de D13 y Lab A13 (Consumer Lag, Tendencia, Throughput vs Latencia, Percentiles, Escalamiento, Partición Caliente, Replicación, ISR y `min.insync.replicas`)** (Bloque K: K.1 a K.15).
10. **Las 16 Preguntas Oficiales de L10 — Taller de la E2 (Consumer Groups, Idempotencia, CTE de TypeORM, Panel en Vivo, Rebobinado, Catálogo Compactado, Multi-Stage GHCR, AWS y Azure)** (Bloque L: L.1 a L.16).

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

### F.5. ¿El proyecto cuenta con colas de reintento en RabbitMQ? ¿Cómo se gestionan los reintentos y en qué se diferencian de las DLQ y de `q.reprocesar`?
* **Respuesta Técnica**:
  > "1. **No hay colas de reintento dentro de RabbitMQ**: En el broker no se crean colas intermedias con TTL (`q.*.retry`) que retornen mensajes en bucle a la cola operativa.  
  > 2. **Los reintentos se resuelven en memoria en el worker**: La función `procesarConReintentos` (`vidalstore-eventos`) ejecuta un bucle en el proceso Node.js de hasta **3 intentos** con pausas progresivas (2s y 4s), reservado estrictamente para fallas transitorias del entorno (ej. Postgres reiniciándose o corte de red `ECONNREFUSED`). Los mensajes inválidos (JSON corrupto o violación de esquema) se descartan sin reintento alguno.  
  > 3. **Desvío a DLQ**: Al agotar los 3 reintentos o detectar un mensaje corrupto, el worker ejecuta `canal.nack(mensaje, false, false)` sin reencolar. RabbitMQ activa los argumentos de Dead Lettering (`x-dead-letter-exchange: vidalstore.dlx`) y deposita el mensaje en su respectiva DLQ (`dlq.avisos`, `dlq.auditoria`, `dlq.correos`).  
  > 4. **Diferencia con `q.reprocesar`**: La cola `q.reprocesar` **no es de reintento automático**, sino una cola dedicada de contingencia manual (requisito Grupos de 3). Se activa únicamente cuando un administrador autorizado invoca `POST /v1/admin/dlq/:id/reproceso` en `vidalstore-admin`; este microservicio lee la carta muerta de PostgreSQL, la republica en el DLX con routing key `dlq.reprocesar` y el worker la reenvía a la cola operativa original con trazabilidad forense."

---

### F.6. ¿Todos los microservicios se conectan a PostgreSQL mediante un ORM? Explica qué componente utiliza TypeORM y cuáles utilizan conexión directa con `pg.Pool` y por qué.
* **Respuesta Técnica**:
  > "No todos los microservicios usan ORM; existe una segregación arquitectónica según el rol de cada componente:  
  > 1. **`vidalstore-eventos` (Worker) $\rightarrow$ Sí usa ORM (TypeORM)**: Cumple con la pauta de L7 y la EP2 configurando `TypeOrmModule` con entidades decoradas (`EventoAuditoria`, `MensajeMuerto`, `Notificacion`), repositorios inyectados y migraciones versionadas con `synchronize: false`. Modela el esquema relacional asíncrono y garantiza tipos como `jsonb` y `timestamptz`.  
  > 2. **`vidalstore-backend` (Productor de Licencias) $\rightarrow$ No usa ORM, usa conexión directa (`pg.Pool`)**: Utiliza el driver nativo `node-postgres` en `LicenciasDbService`. Se diseñó así para desacoplar el ciclo de vida del productor del worker, optimizar el rendimiento transaccional en compras sincrónicas y gestionar directamente en SQL el índice parcial único `UNIQUE (usuario_sub, juego_id) WHERE estado = 'activa'`.  
  > 3. **`vidalstore-admin` (Microservicio Administrador) $\rightarrow$ No usa ORM, usa conexión directa (`pg.Pool`)**: Utiliza `pg.Pool` nativo en `RabbitAdminService` para ejecutar consultas forenses sobre `mensajes_muertos`, borrado físico atómico (`DELETE ... WHERE id = $1`) y marcado de estado de reproceso (`UPDATE ... SET reprocesada = true`), sin la sobrecarga de un ORM completo.  
  > 4. **`vidalstore-gateway` y `vidalstore-frontend`**: No acceden a base de datos (seguridad perimetral y SPA de cliente)."

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

### G.11. ¿Cómo opera el CRUD dinámico de topología (colas, exchanges, bindings) sobre la RabbitMQ Management HTTP API y cómo maneja las respuestas vacías (204 No Content)? (IE17)
* **Respuesta Técnica**:
  > "1. **Qué hice**: Implementé en `RabbitAdminService` los métodos `crearCola`, `eliminarCola`, `crearExchange`, `eliminarExchange`, `crearBinding` y `eliminarBinding` contra la HTTP API de RabbitMQ (`http://localhost:15672/api/...`) utilizando `fetch` nativo con autenticación Basic (`guest:guest`) y DTOs validados con `class-validator` (`CrearColaDto`, `CrearExchangeDto`, `CrearBindingDto`, `EliminarBindingDto`).
  > 2. **Qué problema resuelve**: Permite crear y desmantelar recursos de mensajería en caliente desde la API administrativa sin reiniciar contenedores ni depender de la UI manual de RabbitMQ.
  > 3. **El desafío del 204 No Content**: Las eliminaciones (`DELETE /api/queues/%2f/<name>`) y declaraciones en RabbitMQ responden con código `204 No Content` o `201 Created` con body vacío. Si se invoca directamente `response.json()`, Node.js lanza `SyntaxError: Unexpected end of JSON input`. En `request()`, validamos si `response.status === 204` o si `response.text()` está vacío antes de parsear, retornando un DTO unificado `{ success: true, message: '...', recurso, tipo }`.
  > 4. **Qué descarté**: Descarté ejecutar comandos CLI por `child_process.exec('rabbitmqctl')` porque acoplaría el proceso de Node.js al sistema operativo del host y no funcionaría en despliegues distribuidos en contenedores.
  > 5. **Cómo lo compruebo**: Con `curl -X POST /v1/admin/queues -d '{"nombre":"q.demo","durable":true}'` recibo `201 Created`, y de inmediato `GET /v1/admin/queues` muestra la cola creada en vivo."

---

### G.12. ¿Por qué `vidalstore-admin` aplica el modelo Zero Trust con `RolesGuard` y qué diferencia semántica existe entre 401 y 403? (IE6, IE7, IE8)
* **Respuesta Técnica**:
  > "1. **Qué hice**: Apliqué a nivel de clase en `AdminController` la combinación `@UseGuards(AuthGuard, RolesGuard)` y el decorador `@Roles('ADMIN', 'administradores')`.
  > 2. **Qué problema resuelve**: Al correr en el puerto `:3020` fuera del perímetro del API Gateway, `vidalstore-admin` no puede asumir que quien conecta es confiable. Protege absolutamente todos los endpoints (tanto operaciones destructivas `POST/DELETE` como lecturas de métricas `GET /queues`, `/cluster`, etc.) impidiendo que usuarios autenticados sin privilegios vean la topología interna.
  > 3. **Diferencia Semántica Rigurosa**:
  >    - **`401 Unauthorized` (Autenticación)**: El token Bearer está ausente, malformado o su firma criptográfica no valida contra el JWKS de Cognito. Significa: *«No sé quién eres»*.
  >    - **`403 Forbidden` (Autorización)**: El token es 100% válido y emitido por Cognito, pero el usuario pertenece a `jugadores` o carece de grupos administrativos. Significa: *«Sé quién eres, pero tu rol no te autoriza a administrar la plataforma»*.
  > 4. **Qué descarté**: Descarté proteger solo los endpoints de escritura (`POST`, `DELETE`) dejando los `GET` desprotegidos; el modelo Zero Trust y la rúbrica exigen que un jugador común no pueda inspeccionar colas ni mensajes muertos."

---

### G.13. ¿Por qué `RolesGuard` realiza matching case-insensitive y cómo aborda la «trampa de Cognito» en el backend administrativo? (IE6, IE8)
* **Respuesta Técnica**:
  > "1. **Qué hice**: En `RolesGuard`, extraigo `request.user.groups` (o `request.user['cognito:groups']`), normalizo todos los nombres de grupo con `.toLowerCase()` y comparo con los roles requeridos normalizados.
  > 2. **Qué problema resuelve**: En la especificación oficial conviven diferentes convenciones: la rúbrica pide el grupo en español `administradores`, los ejemplos del laboratorio usan `ADMIN` en mayúsculas, y en la consola de AWS Cognito puede crearse con mayúscula inicial `Administradores`. La comparación insensible a mayúsculas evita rechazos accidentales por discrepancia de capitalización.
  > 3. **Resolución de la trampa de Cognito**: Si un usuario se auto-registró por la Hosted UI, Cognito emite un JWT sin el claim `cognito:groups`. En `RolesGuard`, el arreglo de grupos evalúa como vacío (`[]`), la condición `hasRequiredRole` resulta `false` y arroja de inmediato `ForbiddenException('Acceso denegado: se requiere rol de administrador')` (HTTP 403), asegurando que ninguna cuenta pública pueda acceder a la infraestructura."

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

---

## Bloque J: Preguntas Oficiales de L8 y L8A (Clúster RabbitMQ, Quorum Queues, Microservicio Administrador, Métricas y Políticas)

### J.1. ¿Dos contenedores de RabbitMQ levantados con Docker Compose ya forman un clúster? ¿Qué rol cumple la cookie de Erlang?
* **Respuesta Técnica**:
  > "No. Dos contenedores de RabbitMQ levantados en la misma máquina son simplemente dos brokers completamente aislados que no comparten usuarios, exchanges ni colas.  
  > Para que formen un clúster, deben compartir la misma **cookie de Erlang** (`RABBITMQ_ERLANG_COOKIE`), que actúa como el secreto compartido que permite a las máquinas virtuales de Erlang comunicarse por red. La cookie autentica conversaciones entre nodos, pero **no cifra ni firma los datos del disco**. Además, los nodos deben descubrirse mutuamente a través de `cluster.conf` mediante `cluster_formation.peer_discovery_backend = rabbit_peer_discovery_classic_config`."

---

### J.2. ¿Por qué `rabbit2` no debe llevar `depends_on: { rabbit1: { condition: service_healthy } }` en el `compose.yml`?
* **Respuesta Técnica**:
  > "Porque introduce una trampa de bloqueo mutuo (*deadlock*): si en un reinicio `rabbit1` necesita contactar a `rabbit2` para reconciliar metadatos antes de responder a su propio healthcheck, `rabbit2` jamás arrancaría porque Compose espera que `rabbit1` pase a `healthy`.  
  > Además, si `rabbit1` se recrea por cambio de volumen o imagen, Compose cancelaría el arranque de `rabbit2` con el error `dependency failed to start: container rabbit1 is unhealthy`. Al no llevar `depends_on`, ambos arrancan en paralelo y el mecanismo `cluster.conf` gestiona el emparejamiento de forma autónoma."

---

### J.3. En `rabbitmqctl cluster_status`, ¿cuál es la diferencia entre `Disk Nodes` y `Running Nodes` al detener `rabbit2`?
* **Respuesta Técnica**:
  > "* **`Disk Nodes`**: Muestra los nodos cuya membresía en el clúster está grabada en el almacenamiento persistente (`Mnesia`). Al apagar `rabbit2`, **ambos nodos siguen figurando** en `Disk Nodes` porque el clúster no olvida la unión.  
  > * **`Running Nodes`**: Muestra únicamente los nodos que están encendidos, activos y respondiendo en el instante actual. Al apagar `rabbit2`, solo queda `rabbit@rabbit1`.  
  > Cuando `rabbit2` vuelve a encenderse (`docker compose start rabbit2`), reingresa a `Running Nodes` automáticamente **sin necesidad de repetir ningún comando `join_cluster` manual**."

---

### J.4. Si un nodo arranca desincronizado y no forma clúster, ¿cuál es el procedimiento de rescate a mano y por qué jamás se debe ejecutar `reset` sobre `rabbit1`?
* **Respuesta Técnica**:
  > "Se rescata ejecutando los 4 comandos estrictamente sobre **`rabbit2`**:
  > 1. `docker compose exec rabbit2 rabbitmqctl stop_app` (detiene el broker sin matar Erlang).
  > 2. `docker compose exec rabbit2 rabbitmqctl reset` (borra los datos y metadatos locales de `rabbit2`).
  > 3. `docker compose exec rabbit2 rabbitmqctl join_cluster rabbit@rabbit1` (adopta los metadatos de `rabbit1`).
  > 4. `docker compose exec rabbit2 rabbitmqctl start_app` (arranca como miembro del clúster).  
  > **Jamás ejecutar `reset` sobre `rabbit1`** porque borraría de inmediato la base de datos de metadatos principal, destruyendo todas las colas, exchanges, bindings y usuarios configurados en el sistema."

---

### J.5. ¿Por qué en RabbitMQ 4 ya no se usan colas espejo (`ha-mode: all`) y qué es una Quorum Queue?
* **Respuesta Técnica**:
  > "Las colas espejo (*mirrored queues*) basadas en `ha-mode` presentaban problemas graves de consistencia y sincronización ante particiones de red, y fueron **formalmente eliminadas en RabbitMQ 4.0**.  
  > Su reemplazo moderno y obligatorio son las **Quorum Queues** (`x-queue-type: quorum`), basadas en el algoritmo de consenso distribuido **Raft**. Cada cola quorum tiene un nodo **Leader** (que procesa escrituras) y nodos **Followers** (que replican el log Raft). Si el líder cae, los seguidores eligen un nuevo líder inmediatamente si cuentan con la mayoría de réplicas vivas."

---

### J.6. ¿Por qué al apagar `rabbit2` la API HTTP muestra `state: minority` mientras que `rabbitmqctl list_queues state` sigue diciendo `running`?
* **Respuesta Técnica**:
  > "Porque responden preguntas distintas:
  > * `rabbitmqctl list_queues state`: Evalúa si el proceso local de Erlang de la cola está vivo y corriendo en ese nodo particular (`rabbit1`). Como `rabbit1` está encendido, responde `running`.  
  > * `/api/queues state`: Evalúa el **estado de consenso Raft del clúster**. Con 2 réplicas y 1 nodo apagado, la cola solo tiene 1 réplica viva, por lo que carece de mayoría estricta y se encuentra en estado **`minority`**.  
  > Esto demuestra el principio de D9: la herramienta que eliges determina la respuesta que ves; para diagnosticar salud de clúster se debe consultar la Management API."

---

### J.7. ¿Por qué `canal.sendToQueue(...)` devuelve `true` cuando una cola quorum está en `minority`, y por qué eso no garantiza que el mensaje fue guardado?
* **Respuesta Técnica**:
  > "Porque `sendToQueue` a secas opera de forma asíncrona a nivel de transporte: el retorno `true` solo significa que la librería de Node.js logró empujar los bytes al **buffer del socket TCP local**, no que RabbitMQ los persistió.  
  > Como la cola está en `minority`, el líder Raft no puede confirmar la escritura con la mayoría de réplicas. El mensaje queda flotando y no entra a la cola. Para tener certeza real de guardado se debe utilizar un **canal con confirmaciones (`confirmChannel`)**, donde el broker responde con un *publisher confirm*; en estado `minority`, ese canal lanzará un error de timeout (`confirm_timeout`)."

---

### J.8. ¿Cuál es la fórmula de mayoría de Raft ($\lfloor N/2 \rfloor + 1$) y cuántas caídas tolera un clúster de dos nodos?
* **Respuesta Técnica**:
  > "Raft exige la mayoría estricta de réplicas: $\text{Mayoría} = \lfloor N/2 \rfloor + 1$.  
  > * Con $N = 1$: mayoría = 1, tolera 0 caídas.  
  > * Con $N = 2$: mayoría = $\lfloor 2/2 \rfloor + 1 = 2$. **Tolera 0 caídas**. Perder 1 nodo es perder la mayoría.  
  > * Con $N = 3$: mayoría = $\lfloor 3/2 \rfloor + 1 = 2$. **Tolera 1 caída** (quedan 2 vivos).  
  > Por ende, un clúster de dos nodos **tolera cero caídas** para confirmar escrituras en colas quorum."

---

### J.9. Si un clúster de 2 nodos tolera cero caídas, ¿para qué sirve tener dos nodos y por qué la pauta pide dos nodos? (Pregunta Clave de Defensa)
* **Respuesta Técnica**:
  > "Un clúster de dos nodos me otorga **durabilidad distribuida y recuperación automática**, no alta disponibilidad:  
  > 1. **Cero pérdida de datos**: Cada mensaje confirmado reside físicamente en dos volúmenes de disco independientes. Si un nodo sufre un daño irreparable, los datos sobreviven íntegros en el otro.  
  > 2. **Recuperación automática sin intervención**: Cuando el nodo caído se enciende, el protocolo Raft lo resincroniza solo y el clúster vuelve a `running` sin necesidad de comandos manuales.  
  > 3. **Arquitectura lista para escalar**: La topología y el `cluster.conf` ya están implementados. Escalar a alta disponibilidad real solo requiere agregar `rabbit3` al `compose.yml`, ya que la tolerancia a fallos en consenso distribuido empieza estrictamente con un número impar de 3 nodos."

---

### J.10. ¿Qué verifica el comando `rabbitmq-diagnostics check_if_node_is_quorum_critical`, por qué termina con código de salida 69, y qué rol cumple Khepri (`rabbitmq_metadata`) en RabbitMQ 4.3?
* **Respuesta Técnica**:
  > "Verifica de forma preventiva si la detención del nodo actual provocaría que alguna cola quorum o el almacén de metadatos pierda su quórum de mayoría.  
  > En un clúster de 2 nodos, lista todas las colas de trabajo, las 3 DLQ y **`rabbitmq_metadata`**, indicando que todas quedarán *unavailable* si `rabbit1` se detiene. Finaliza con código de salida **69** a propósito porque es un chequeo que encontró un riesgo crítico.  
  > Esa última línea (`rabbitmq_metadata`) se debe a que en RabbitMQ 4.3 los metadatos del clúster ya no viven en Mnesia sino en **Khepri (un grupo Raft)**, consultable con `rabbitmq-diagnostics metadata_store_status`. Por eso, con un nodo caído tampoco se pueden crear colas ni exchanges nuevos: el intento expira a los ~30 segundos con código `75` (`TEMPFAIL: Khepri cluster could be in minority`)."

---

### J.11. ¿Cómo se comunica `RabbitAdminService` con el broker (AMQP `:5672` vs HTTP `:15672`) y por qué abre un canal AMQP efímero por operación?
* **Respuesta Técnica**:
  > "Según `EP2-Caso-VidalStore.pdf` (§3.6 y §4.5), los listados (`GET`) van siempre por la **API HTTP de Management (`:15672`)** porque el protocolo AMQP no tiene una operación para listar todas las colas, mientras que para las escrituras el grupo puede elegir entre AMQP (`:5672`) o la API HTTP (`:15672`).  
  > En nuestro `RabbitAdminService` implementamos ambos mecanismos:
  > * Los endpoints REST (`crearCola`, `eliminarCola`, `crearExchange`, `eliminarExchange`, `crearBinding`, `eliminarBinding`) operan mediante `this.request(...)` contra la API HTTP (`:15672/api/...`), manejando respuestas `204 No Content` y traduciendo `400 precondition_failed` a `409 Conflict`, `404` a `NotFoundException` y timeouts/caídas a `503 ServiceUnavailableException`.
  > * Adicionalmente, para operaciones sobre el protocolo AMQP (`:5672`), mantenemos una sola conexión TCP persistente (porque el handshake AMQP es costoso) y abrimos un **canal efímero por operación (`conCanalEfimero`)**. Esto es vital porque cuando RabbitMQ rechaza una operación AMQP (como `NOT_FOUND` o `PRECONDITION_FAILED`), **cierra el canal entero**; usar un canal por operación con `canal.on('error', ...)` evita que el rechazo de un cliente mate el canal de otros usuarios o tumbe el proceso de Node.js."

---

### J.12. En el microservicio administrador, ¿cómo mapea el método `traducir()` los errores nativos de AMQP y de la Management API a códigos HTTP REST?
* **Respuesta Técnica**:
  > "Mapea las excepciones de `amqplib` y de la API HTTP a excepciones semánticas de NestJS:  
  > * Mensajes con `NOT_FOUND` o HTTP `404` (ej. crear binding sobre una cola que no existe) $\rightarrow$ **`404 Not Found`**.  
  > * Mensajes con `PRECONDITION_FAILED` o `inequivalent arg` (ej. redeclarar una cola quorum existente como classic) $\rightarrow$ **`409 Conflict`**.  
  > * Caída del broker, timeouts o clúster sin mayoría Raft/Khepri $\rightarrow$ **`503 Service Unavailable`**.  
  > Esto evita arrojar errores 500 ciegos, entregando al cliente el código de estado HTTP exacto según la especificación REST."

---

### J.13. ¿Cuáles son las tres opciones críticas de `ValidationPipe` en el microservicio administrador y por qué `forbidNonWhitelisted: true` es indispensable?
* **Respuesta Técnica**:
  > "Las tres opciones en `main.ts` son:
  > 1. `whitelist: true`: Descarta automáticamente cualquier propiedad del JSON que no esté declarada en el DTO.  
  > 2. `forbidNonWhitelisted: true`: En lugar de descartar en silencio, **rechaza de inmediato con `400 Bad Request`** si el cliente envía campos desconocidos. Es indispensable porque previene que un usuario envíe propiedades erróneas (ej. escribir `nombres` en vez de `nombre`) creyendo falsamente que fueron configuradas.  
  > 3. `transform: true`: Instancia formalmente la clase del DTO con los tipos correctos para que `class-validator` ejecute sus decoradores."

---

### J.14. Si mañana observas que `messages_ready` sube sin parar y `consumers` está en 0, ¿qué diagnóstico haces y qué solución aplicas? ¿Por qué reiniciar RabbitMQ o purgar la cola es un error grave?
* **Respuesta Técnica**:
  > "* **Diagnóstico**: Los productores siguen publicando eventos normalmente pero el microservicio consumidor (`vidalstore-eventos`) está caído o desconectado.  
  > * **Solución**: Revisar los logs del worker (`docker compose logs eventos`), subsanar la causa del fallo y encenderlo (`docker compose start eventos`).  
  > * **Por qué no reiniciar RabbitMQ**: Porque el broker está funcionando a la perfección cumpliendo su rol de resguardo duradero. Reiniciarlo interrumpe el tráfico de los demás microservicios sin resolver la falta de consumidores.  
  > * **Por qué no purgar la cola**: Porque purgar eliminaría irreversiblemente compras y eventos legítimos de los usuarios para tapar un síntoma operativo."

---

### J.15. Si observas que `messages_unacknowledged` permanece congelado en el valor de tu `prefetch` (ej. 1) con 1 consumidor activo, ¿qué ocurrió y cómo se resuelve?
* **Respuesta Técnica**:
  > "* **Causa**: El consumidor recibió el mensaje pero **no ha enviado el `ack`**. Esto ocurre si el worker quedó bloqueado esperando una respuesta sincrónica sin timeout (ej. Postgres no responde), o si el código del consumidor sufrió un error lógico y no atrapó la excepción en un bloque `catch` para enviar `nack`. Como el `prefetch` es 1, RabbitMQ no le entrega ningún mensaje más hasta que confirme el actual.  
  > * **Solución**: Depurar el código del worker, configurar timeouts en los clientes de base de datos y asegurar que todo camino de error termine explícitamente en `ack` (idempotencia) o `nack` hacia la DLQ."

---

### J.16. ¿Por qué una cola sin límite puede llevarse por delante al sistema entero, qué diferencia práctica existe entre `overflow: drop-head` y `overflow: reject-publish` en una cola quorum, y cómo está configurado `politicas.json`?
* **Respuesta Técnica**:
  > "Si una cola crece sin límite (ej. la DLQ acumulando mensajes con Postgres caído), satura la memoria o el disco del nodo. Al alcanzar el umbral, RabbitMQ levanta una **alarma de disco o memoria y bloquea todas las publicaciones en todo el broker**, deteniendo compras y catálogos de todo VidalStore.  
  > * **`drop-head`**: Descarta el mensaje más viejo por la cabeza de la cola para hacerle espacio al nuevo; el productor recibe confirmación normal y no se entera. Si la cola tiene `x-dead-letter-exchange`, el mensaje expulsado salta al DLX con `reason = maxlen`.  
  > * **`reject-publish`**: Rechaza el mensaje entrante nuevo con un `nack` al productor (en colas quorum admite +1 mensaje sobre el límite antes de rechazar, y requiere que el productor escuche con `ConfirmChannel` para enterarse).  
  > * **En cátedra (D9 y L8 §5.5)**: Se enseña `drop-head` con TTL para **Avisos** (porque un aviso viejo ya no sirve) y `reject-publish` sin TTL para **Trabajo (`auditoria|correos`)** (para no perder evidencia en silencio).  
  > * **En `vidalstore-plataforma/rabbitmq/politicas.json`**: Definimos `retencion-avisos` (`^q\.avisos$`, TTL 1h, `drop-head`), `retencion-trabajo` (`^q\.(auditoria|correos)$`, sin TTL, `drop-head` hacia DLX para que cualquier desborde caiga a `dlq.auditoria`/`dlq.correos` con motivo `maxlen` y `CartasMuertasConsumidor` lo persista en `mensajes_muertos`, ya que los productores no usan publisher confirms) y `retencion-dlq` (`^dlq\.(avisos|auditoria|correos)$`, TTL 14 días, `reject-publish` como freno final de disco)."

---

### J.17. ¿Por qué el tiempo de caducidad `message-ttl` no elimina los mensajes viejos que ya estaban en la cola antes de aplicar la política?
* **Respuesta Técnica**:
  > "Porque en RabbitMQ el temporizador de caducidad se calcula y asigna individualmente a cada mensaje **en el momento exacto en que ingresa a la cola**. Si una cola ya tiene mensajes previos y se le aplica una política con `message-ttl`, dichos mensajes no poseen la marca de tiempo calculada y **no caducan retroactivamente**. Solo comenzarán a caducar los mensajes que ingresen después de que la política esté activa (para vaciar una cola llena a propósito se usa `rabbitmqctl purge_queue`)."

---

### J.18. En la cola DLQ (`dlq.*`), ¿cuáles son los dos argumentos técnicos para elegir entre `reject-publish` y `drop-head`, y por qué los patrones de `politicas.json` llevan `^` y `$` con `priority: 10`?
* **Respuesta Técnica**:
  > "* **A favor de `reject-publish` en DLQ**: Si una DLQ alcanza su límite, el sistema lleva horas o días roto. El problema no es dónde guardar el mensaje siguiente, sino que el fallo se note fuerte en lugar de seguir tragando en silencio.  
  > * **A favor de `drop-head` en DLQ**: Prefiere conservar siempre los mensajes muertos más recientes descartando los antiguos, garantizando que el equipo tenga los errores frescos para diagnosticar.  
  > * **Anclaje `^...$` y `priority: 10`**: Sin el ancla inicial `^`, el patrón `q\.avisos` calzaría como subcadena dentro de `dlq.avisos`, pisando la política de la DLQ si tienen la misma prioridad. Y usamos `priority: 10` para que cualquier política de prueba creada en vivo con prioridad `0` o `1` no sobreescriba las políticas de las 6 colas operativas."

---

## Bloque K: Preguntas Oficiales de D13 y Lab A13 (Consumer Lag, Tendencia, Throughput, Percentiles, Escalamiento, Partición Caliente, Replicación e ISR)

### K.1. ¿Por qué la key `"18"` cae en la partición `P1` en lugar de `P0` si $18 \bmod 3 = 0$, y qué provoca eso en `biblioteca.lecturas` y `vidalstore.actividad`?
* **Respuesta Técnica (D13 Slide 4)**:
  > "Porque Kafka no aplica el módulo sobre el valor numérico entero, sino sobre el hash **`murmur2` de los bytes del string** (`(murmur2(bytes("18")) & 0x7fffffff) % 3`), cuyo resultado es **`1`** (`P1`).  
  > * En `biblioteca.lecturas` (3 particiones, `2.984` eventos), el libro `18` concentra el `40,2%` de las lecturas y junto con otros libros cuyo hash da `1` deja a **`P1` con `2.279` eventos (`76,4%`)**, `P0` con `492` (`16,5%`) y `P2` con `213` (`7,1%`).  
  > * En `vidalstore.actividad` (3 particiones, `3.039` eventos, key `juegoId`), el juego `292030` cae en **`P0`**, concentrando **`1.751` eventos (`57,6%`)** en `P0`, `520` en `P1` y `768` en `P2`. A ese fenómeno se le denomina **partición caliente (*hot partition*)**."

---

### K.2. ¿Cuál es la diferencia entre una métrica `counter` y un `gauge`? Clasifica: eventos publicados en un topic, `consumer lag`, compras históricas y memoria libre del broker.
* **Respuesta Técnica (D13 Slides 5–6)**:
  > "* **`Counter` (Contador acumulativo)**: Solo sube monotónicamente (solo vuelve a 0 al reiniciar el proceso). No importa su valor aislado sino su **tasa de cambio** ($\Delta \text{valor} / \Delta t$). Son `counter`: **eventos publicados en un topic** (`LOG-END-OFFSET`) y **total de compras históricas**. *(Nota: `kafka_exporter` exporta el offset etiquetado como `gauge`, pero matemáticamente es un `counter` y en Grafana se grafica su `rate`)*.  
  > * **`Gauge` (Medidor instantáneo)**: Sube y baja libremente según el estado actual. Importa su valor actual y su **tendencia (pendiente)**. Son `gauge`: **`consumer lag`** y **memoria libre del broker**."

---

### K.3. ¿Cómo se calcula el `consumer lag` en `kafka-consumer-groups.sh --describe`, qué significan `LOG-END-OFFSET` y `CURRENT-OFFSET`, y qué columna no tiene sentido sumar?
* **Respuesta Técnica (D13 Slides 7–10)**:
  > "Por cada partición $p$, $\text{LAG}_p = \text{LOG-END-OFFSET}_p - \text{CURRENT-OFFSET}_p$:  
  > * **`LOG-END-OFFSET` (*high watermark*)**: Es el próximo offset que el broker escribirá en esa partición (equivale al total de mensajes escritos en esa partición).  
  > * **`CURRENT-OFFSET`**: Es el próximo offset que leerá el grupo, es decir, el valor confirmado en el último commit manual (`offset_procesado + 1`).  
  > * **Qué se suma y qué no**: Tiene sentido sumar `LOG-END-OFFSET` (total de eventos del topic) y sumar `LAG` (total de eventos pendientes del grupo). **No tiene ningún sentido sumar `CURRENT-OFFSET`** cuando aún hay lag, porque es una posición de cursor local a cada partición."

---

### K.4. En el segundo 40, dos grupos muestran exactamente `LAG = 5000`. La Serie A venía de `3000 -> 5000` y la Serie B venía de `7000 -> 5000`. ¿En cuál hay que intervenir y por qué?
* **Respuesta Técnica (D13 Slides 11–12 y Lab A13 Pregunta 4)**:
  > "**La tendencia importa más que el valor aislado**: $\text{pendiente} = (\text{lag}_{\text{final}} - \text{lag}_{\text{inicial}}) / \Delta t = \text{entrada} - \text{procesamiento}$.  
  > * **Serie A (`3000 -> 5000` en 40 s)**: Tiene pendiente **`+50.0 ev/s` (`SUBE`)**. Entran 50 eventos/s más de los que el grupo logra procesar; la fila crece sin techo y **hay que intervenir de inmediato**.  
  > * **Serie B (`7000 -> 5000` en 40 s)**: Tiene pendiente **`-50.0 ev/s` (`BAJA`)**. El grupo ya procesa 50 ev/s más rápido de lo que entra tras un pico pasado y se vaciará solo a `0` en $5000 / 50 = 100\text{ segundos}$. **No hay que tocar nada**."

---

### K.5. Si un grupo muestra `LAG = 0` durante 10 minutos seguidos, ¿es siempre buena noticia? ¿Cómo lo compruebas?
* **Respuesta Técnica (D13 Slide 13)**:
  > "**No siempre es buena noticia.** `LAG = 0` significa que $\text{CURRENT-OFFSET} = \text{LOG-END-OFFSET}$, lo cual ocurre en dos escenarios opuestos:  
  > 1. El consumidor está sano y procesa al ritmo que entra.  
  > 2. **El productor se cayó o dejó de publicar hace 10 minutos** (un incidente grave disfrazado de calma).  
  > Se comprueba mirando en dos mediciones separadas si **`LOG-END-OFFSET` sigue subiendo**."

---

### K.6. ¿Cuál es la diferencia entre `throughput`, `latencia` y `espera en la partición`? Si un consumidor tarda `10 ms` por evento y pasas de 1 a 3 consumidores, ¿baja la latencia a `3,3 ms`?
* **Respuesta Técnica (D13 Slides 14–16)**:
  > "* **Latencia**: Tiempo que tarda **un solo evento** en procesarse (ej. `10 ms` en insertar en Postgres).  
  > * **Throughput**: Cantidad de eventos despachados por segundo ($\text{throughput} = 1000 / \text{ms\_por\_evento}$).  
  > * **Espera en la partición**: Tiempo que el evento pasa haciendo fila antes de que lo tome un consumidor.  
  > Al pasar de 1 a 3 consumidores, **la latencia individual NO baja a `3,3 ms`**: cada consumidor sigue tardando exactamente `10 ms` en hablar con Postgres. Lo que se triplica es el **throughput del grupo** (de `100 ev/s` a `300 ev/s`), y lo que baja para el negocio es el **tiempo de espera en la partición**."

---

### K.7. ¿Por qué se mide la latencia con percentiles (`p50` y `p99`) en lugar del promedio, y por qué en Node.js se usa `performance.now()` con `for...of` y jamás `Promise.all`?
* **Respuesta Técnica (D13 Slides 17–21 y Lab A13 Ejercicio 2)**:
  > "* **Percentiles vs Promedio**: En una muestra de 10 eventos `[2, 2, 2, 2, 2, 3, 3, 3, 4, 380]` ms, el promedio da `40,3 ms`, un número que no representa ni a los 9 eventos rápidos (`p50 = 2 ms`) ni al evento estancado (`p99 = 380 ms`).  
  > * **`performance.now()` vs `Date.now()`**: `Date.now()` mide milisegundos enteros y puede saltar o retroceder si NTP ajusta el reloj del sistema; `performance.now()` entrega resolución de microsegundos sobre un reloj monotónico.  
  > * **`for...of` con `await` vs `Promise.all`**: Un consumidor real de Kafka procesa su partición secuencialmente con `for await (const m of flujo)` para respetar el orden y confirmar el offset después de escribir. Si midiéramos con `Promise.all`, dispararíamos las 200 esperas en paralelo midiendo el temporizador de Node y no el throughput real de un consumidor."

---

### K.8. Si en tu grupo cada escritura en Postgres tarda `40 ms` y al topic llegan `50 eventos/s`, ¿cuántos consumidores necesitas como mínimo para que el lag no suba?
* **Respuesta Técnica (Lab A13 Pregunta 5)**:
  > "Si cada escritura tarda `40 ms`, el throughput máximo de 1 consumidor es $1000 / 40 = \mathbf{25\text{ eventos/s}}$.  
  > Para sostener una tasa de entrada de `50 eventos/s` sin acumular lag se necesitan como mínimo $\lceil 50 / 25 \rceil = \mathbf{2\text{ consumidores}}$ activos (siempre que el topic tenga al menos 2 particiones y la carga esté bien distribuida)."

---

### K.9. ¿Por qué la partición es la unidad mínima de paralelismo en Kafka y qué ocurre al levantar 4 instancias de `eventos` sobre `vidalstore-alertas` vs `vidalstore-panel`?
* **Respuesta Técnica (D13 Slides 23–25 y L10 Tramo 3)**:
  > "Una partición nunca puede ser leída simultáneamente por dos consumidores del mismo grupo, porque rompería la garantía de orden por key y pisaría los commits de offset. Por lo tanto, trabajan como máximo $\min(\text{consumidores}, \text{particiones})$ y el resto queda **ocioso (`#PARTITIONS = 0`)**.  
  > Al levantar **4 instancias de `eventos`**:  
  > * En **`vidalstore-alertas`** (y **`vidalstore-historial`**), que se suscriben a **1 solo topic de 3 particiones**, `--describe --members` muestra `#PARTITIONS`: **`1, 1, 1 y 0`** (la 4.ª instancia queda ociosa).  
  > * En **`vidalstore-panel`**, que se suscribe a **2 topics (`actividad` + `compras` = 6 particiones)**, `--describe --members` muestra `#PARTITIONS`: **`2, 2, 1 y 1`** (ninguna queda ociosa; recién habría una ociosa con 7 instancias)."

---

### K.10. En el Escenario 2 de `reparto.mjs` (`P1` caliente con `70 ev/s` y capacidad de `40 ev/s` por consumidor), ¿por qué subir de 3 a 6 o 9 consumidores no quita la marca `[SE ATRASA]` de `c2`? ¿Qué sí lo resuelve?
* **Respuesta Técnica (D13 Slides 26–28 y Lab A13 Pregunta 6)**:
  > "Con 3 consumidores, `c2` atiende `P1 + P4` (`70 + 10 = 80 ev/s`). Al subir a 6 o 9 consumidores, `c2` queda dedicado exclusivamente a `P1`, pero **`P1` por sí sola trae `70 ev/s`**, lo que sigue superando su capacidad de `40 ev/s`. Como Kafka jamás divide una partición entre dos consumidores del mismo grupo, agregar más consumidores solo deja instancias ociosas.  
  > Solo hay dos soluciones reales: **(1) optimizar el consumidor** para que supere los `70 ev/s` (ej. caché en memoria o escrituras en lote), o **(2) cambiar la key de particionamiento** si el negocio no exige orden estricto por esa clave."

---

### K.11. ¿Cuáles son las 5 causas de lag creciente y cómo distingues cada una mirando `kafka-consumer-groups.sh --describe`?
* **Respuesta Técnica (D13 Slides 29–33)**:
  > "1. **Consumidor lento**: El `LAG` sube de forma **pareja en todas las particiones** y todas tienen `CONSUMER-ID` activo.  
  > 2. **Partición caliente**: Casi todo el `LAG` se acumula en **una sola partición** cuyo `LOG-END-OFFSET` es mucho más alto que el resto.  
  > 3. **Pocos consumidores**: El `LAG` sube en las particiones que **comparten el mismo `CONSUMER-ID`** (un consumidor leyendo varias particiones).  
  > 4. **Consumidor caído sin cierre limpio**: El `LAG` sube en su partición mientras el broker sigue mostrando el `CONSUMER-ID` muerto durante los `60 s` del `sessionTimeout` antes de rebalancear (el guion `-` solo aparece si no queda ningún miembro vivo en el grupo).  
  > 5. **Rebalanceo continuo**: Todas las particiones detienen su lectura a la vez y la consola advierte `Warning: Consumer group is rebalancing`."

---

### K.12. ¿Cuáles son las 4 palancas para resolver problemas de capacidad, ordenadas de la más barata a la más cara, y qué peligro tiene agregar particiones a un topic con key?
* **Respuesta Técnica (D13 Slide 34)**:
  > "De la más barata a la más cara:  
  > 1. **Hacer más rápido al consumidor** (gratis y reversible: caché en memoria, índices SQL).  
  > 2. **Agregar consumidores al grupo** (barato y reversible: útil solo si algún consumidor atiende $> 1$ partición).  
  > 3. **Agregar particiones al topic** (caro e **irreversible**: no se pueden reducir particiones, los mensajes ya escritos no se mueven, y al cambiar $N$ en `murmur2(key) % N` **las keys nuevas caen en otra partición distinta de su historia previa**, rompiendo el orden por key).  
  > 4. **Agregar brokers al clúster** (el más caro: y un broker nuevo no recibe particiones existentes hasta ejecutar una reasignación manual)."

---

### K.13. ¿Cuál es el orden estricto de los 6 pasos para diagnosticar un problema de consumer lag?
* **Respuesta Técnica (D13 Slide 35)**:
  > "1. **Mirar la tendencia del lag** (2 mediciones: ¿sube, baja o está estable?).  
  > 2. **Mirar el lag por partición** (`--describe`: ¿parejo o partición caliente?).  
  > 3. **Mirar el `CONSUMER-ID` de cada partición** (¿un mismo miembro lee varias particiones o hay un caído?).  
  > 4. **Medir el throughput individual del consumidor** (ms por evento en BD; si es lento, optimizar primero).  
  > 5. **Agregar consumidores al grupo** (si el consumidor ya es rápido y lee más de 1 partición).  
  > 6. **Agregar particiones al topic** (último recurso cuando ya hay 1 consumidor rápido por partición)."

---

### K.14. ¿Por qué `acks=all` sin `min.insync.replicas=2` es una trampa, y qué pasa exactamente con 0, 1, 2 y 3 brokers caídos en nuestro clúster de 3 brokers (`replication.factor=3`, `min.insync.replicas=2`, `acks=all`)?
* **Respuesta Técnica (D13 Slides 38–45 y Lab A13 Pregunta 7)**:
  > "`acks=all` exige confirmación de todas las réplicas que estén **actualmente en el `ISR`**. Si `min.insync.replicas` fuera `1` (el valor por defecto) y cayeran 2 brokers, el `ISR` quedaría con 1 sola réplica y `acks=all` seguiría aceptando escrituras en un único disco (degradándose en silencio a `acks=1`). Con `min.insync.replicas=2`:  
  > * **0 brokers caídos (`ISR = 3/3`)**: Acepta escritura confirmada en 3 copias.  
  > * **1 broker caído (`broker-3`, `ISR = 2/3`)**: Como $2 \ge 2$, **sigue aceptando escrituras sin error** confirmadas en los 2 brokers vivos.  
  > * **2 brokers caídos (`broker-2` y `broker-3`, `ISR = 1/3`)**: Como $1 < 2$, el líder **rechaza la escritura con `NOT_ENOUGH_REPLICAS`** y Kafka 4.3 tampoco entrega eventos nuevos a los consumidores hasta recuperar el mínimo. Además, en AWS (donde cada VM `mq-1..3` aloja 1 controller + 1 broker), caer 2 máquinas rompe el quórum Raft de controllers (1 de 3).  
  > * **3 brokers caídos (`ISR = 0/3`)**: Falla la conexión (`Connection failed`). Al reencender, con *unclean leader election* desactivado, **no hay líder hasta que vuelva uno de los últimos brokers que estuvieron en el `ISR`** (`broker-1` o `broker-2`)."

---

### K.15. ¿Qué representan los números `4, 5, 6` en `Replicas` e `Isr` de `kafka-topics.sh --describe`, y cómo se mantienen sincronizadas las réplicas seguidoras?
* **Respuesta Técnica (D13 Slides 36–37)**:
  > "Son los `KAFKA_NODE_ID` de los tres brokers en nuestro `compose.yml` (`broker-1 = 4`, `broker-2 = 5`, `broker-3 = 6`; los IDs `1, 2, 3` son los controllers). El primer número de `Replicas` es el *preferred leader*.  
  > Todo productor escribe únicamente en el **líder** de la partición, y las réplicas **seguidoras (*followers*) hacen *fetch* continuo desde el líder**. Si una seguidora se apaga o se atrasa más de `replica.lag.time.max.ms` (`30 s`), el líder la expulsa del `Isr`."

---

## Bloque L: Preguntas Oficiales de L10 y Enunciado EP3 Entrega 2 (Página 10)

> [!IMPORTANT]
> ### Las 6 Preguntas Obligatorias del Enunciado EP3 Entrega 2 (Página 10)
> *«Lo que cada uno tiene que poder explicar después de la E2, porque la defensa lo pregunta:»*
> 1. **¿Por qué `panel` y `alertas` leen el mismo topic sin estorbarse, y qué hace una cuarta instancia?**
>    - *Respuesta*: Porque pertenecen a dos **consumer groups distintos** (`vidalstore-panel` y `vidalstore-alertas`). Kafka almacena punteros de commit separados en `__consumer_offsets` para cada grupo; si uno se pausa, reinicia o atrasa, el otro continúa a su propio ritmo. En cuanto a la cuarta instancia: al suscribirse a un topic de 3 particiones (`vidalstore.actividad`), cada una de las 3 primeras instancias asume 1 partición; la cuarta instancia queda **completamente ociosa (`#PARTITIONS = 0`)** porque la partición es la unidad mínima indivisible de concurrencia y no puede subdividirse entre dos consumidores del mismo grupo.
> 2. **¿Qué pasa si el consumidor muere entre el `INSERT` y el commit del offset?**
>    - *Respuesta*: El evento ya fue guardado en Postgres pero su offset **no quedó confirmado en Kafka**. Al reanimarse el contenedor o rebalancearse el grupo, Kafka reentrega el mismo mensaje. Al intentar ejecutar el `INSERT`, la restricción **`UNIQUE (evento_id)`** (o clave primaria) en PostgreSQL rechaza la inserción duplicada. El consumidor captura el conflicto como «ya procesado», confirma el offset inmediatamente con `await m.commit()` y avanza sin duplicar agregaciones ni contadores (semántica de entrega *at-least-once* con resultado final *exactly-once*).
> 3. **¿Por qué el panel no suma dos veces los 17 duplicados?**
>    - *Respuesta*: Porque el diseño de la persistencia es estrictamente **idempotente**. La tabla receptora posee restricción `PRIMARY KEY (evento_id)` con cláusula `ON CONFLICT (evento_id) DO NOTHING` (o inserción en tabla `eventos_procesados (grupo, evento_id)` en la misma transacción). Cuando el simulador inyecta los 17 eventos duplicados del dataset, Postgres descarta la inserción y la consulta de agregación del panel no incrementa las métricas dos veces.
> 4. **¿Por qué la key `usuarioSub` deja restar bien una revocación?**
>    - *Respuesta*: Porque Kafka garantiza el orden total de los mensajes **dentro de una misma partición** mediante el hashing determinista de la clave (`murmur2(usuarioSub) % 3`). Como tanto la compra original (`compra.realizada`) como su revocación posterior (`licencia.revocada`) utilizan la misma key (`usuarioSub`), ambos eventos viajan obligatoriamente a la misma partición y en secuencia temporal monotónica. La revocación siempre llega después de la compra, permitiendo al consumidor encontrar el precio pagado original asociado al `licenciaId` y restarlo limpiamente.
> 5. **¿Cómo descarga su imagen `mq-1` sin IP pública, y por qué sin `nat` no hay Session Manager?**
>    - *Respuesta*: `mq-1` se encuentra en una subred privada sin asignación de IP pública. Descarga su imagen de GHCR a través de la instancia `nat`, cuya tabla de rutas privada enruta `0.0.0.0/0` hacia su interfaz de red y ejecuta enmascaramiento con `iptables MASQUERADE`. Por su parte, AWS Systems Manager (SSM) opera mediante el agente `amazon-ssm-agent`, el cual requiere establecer conexiones HTTPS salientes hacia los endpoints públicos de SSM (`ssm.us-east-1.amazonaws.com`). Sin la máquina `nat` operativa, la instancia privada no tiene conectividad saliente a internet y el agente no puede comunicarse con AWS, imposibilitando abrir sesiones de Session Manager.
> 6. **¿Por qué `bff` sale a internet por `gw-azure`, y qué falta para eso si solo se crea la tabla de rutas?**
>    - *Respuesta*: Porque la subred privada de Azure tiene configurada la propiedad `--default-outbound false` y su tabla de rutas redirige todo el tráfico saliente (`0.0.0.0/0`) hacia el Virtual Appliance en `10.1.1.4` (`gw-azure`), saliendo con la IP pública estática de esta última. Sin embargo, para que el tráfico fluya con éxito **no basta solo con la tabla de rutas**: faltan 3 configuraciones críticas en `gw-azure`: (1) activar `--ip-forwarding true` en su tarjeta de red de Azure, (2) habilitar el reenvío IP en el kernel Linux (`net.ipv4.ip_forward = 1`), y (3) configurar reglas de NAT en `iptables`, agregando explícitamente reglas en la cadena `DOCKER-USER` para evitar que las reglas de Docker descarten el tráfico reenviado.

---

### L.1. ¿Cómo están organizados los consumer groups dentro de `vidalstore-eventos` y por qué cada grupo se divide en `<grupo>.consumidor.ts` y `<grupo>.negocio.ts`? (`IE5`)
* **Respuesta Técnica (L10 §1.1–1.4)**:
  > "Cada consumer group vive en su propio módulo NestJS dentro de `src/streaming/<grupo>/` y separa responsabilidades en dos clases:  
  > 1. **`<grupo>.consumidor.ts` (extiende `ConsumidorKafka<T>`)**: Habla con `@platformatic/kafka`, se suscribe con `autocommit: false`, valida el sobre con `Contrato<T>`, ejecuta el bucle `for await`, reintenta cada 2 s si Postgres falla y ejecuta **`await m.commit()` recién después de escribir en la base**.  
  > 2. **`<grupo>.negocio.ts` (implementa `Procesador<T>`)**: Contiene únicamente las consultas SQL/TypeORM contra Postgres y **no importa absolutamente nada de Kafka**. Esto cumple el principio de responsabilidad única de `IE5` y permite probar la lógica de negocio sin levantar un broker."

---

### L.2. ¿Qué diferencia hay en `ConsumidorKafka<T>` cuando falla `contrato.validar()` (`EventoInvalido`) frente a cuando falla `negocio.procesar()` (caída de Postgres)?
* **Respuesta Técnica (L10 §1.2–1.3)**:
  > "* **Cuando falla `contrato.validar()` (`EventoInvalido`)**: El mensaje tiene un error permanente en el dato (JSON roto, falta `eventoId`, versión distinta de `1`). Reintentarlo un millón de veces dará el mismo fallo y bloquearía la partición. Por eso en la E2 se registra un `WARN ... INVALIDO`, **se hace `await m.commit()`** para avanzar (y en la E3 se publica antes en el `.dlt`).  
  > * **Cuando falla `negocio.procesar()` (error de Postgres)**: El mensaje es válido pero la base de datos está caída o reiniciándose. `procesarHastaEscribir()` **no hace commit**, registra una advertencia y reintenta cada **2 segundos** hasta que Postgres responda."

---

### L.3. ¿Cuáles son las tres formas de idempotencia en Postgres implementadas en `eventos` y por qué la clave primaria de `eventos_procesados` es `(grupo, evento_id)` y no solo `evento_id`?
* **Respuesta Técnica (L10 §1.5–1.9)**:
  > "1. **Una fila por evento (`kpi_minuto` en `panel`)**: La PK es `evento_id`; inserta con `ON CONFLICT (evento_id) DO NOTHING RETURNING evento_id`.  
  > 2. **Contadores + tabla `eventos_procesados` en la misma transacción (`alertas` e `historial`)**: Dentro de `this.base.transaction(...)`, inserta primero en `eventos_procesados (grupo, evento_id)` con `ON CONFLICT DO NOTHING RETURNING evento_id`; solo si devuelve fila actualiza los contadores.  
  > 3. **Reemplazo con guarda temporal (`catalogo` en grupos de 3)**: `ON CONFLICT (juego_id) DO UPDATE ... WHERE catalogo.emitido_en < EXCLUDED.emitido_en`.  
  > La clave primaria de `eventos_procesados` debe ser compuesta **`(grupo, evento_id)`** porque en Kafka un mismo evento (ej. una compra) es leído legítimamente por varios consumer groups independientes (`panel` e `historial`). Si la PK fuera solo `evento_id`, el primer grupo en procesarlo bloquearía al segundo."

---

### L.4. ¿Por qué un `UPDATE ... RETURNING` directo en `tx.query(...)` de TypeORM falla silenciosamente al desestructurar `const [p] = ...` y cómo lo resolviste?
* **Respuesta Técnica (L10 §1.7, pág. 26)**:
  > "Porque en TypeORM, `tx.query('UPDATE ... RETURNING ...')` no devuelve el arreglo `filas`, sino una tupla de dos elementos: **`[filas, cantidadActualizada]`**. Al hacer `const [p] = ...`, `p` recibe el arreglo `filas` completo en lugar del primer objeto, dejando `p.semana` y `p.precio` como `undefined` sin lanzar ningún error.  
  > Lo resolvimos envolviendo el `UPDATE ... RETURNING` en un CTE **`WITH devuelto AS (UPDATE ... RETURNING ...) SELECT ... FROM devuelto`**, ya que al tratarse de una sentencia `SELECT`, TypeORM devuelve directamente el arreglo de filas."

---

### L.5. En `vidalstore-alertas`, ¿por qué las ventanas de 5 minutos se calculan sobre `emitidoEn` del evento y no con `now()`, y por qué se exige un mínimo de partidas terminadas?
* **Respuesta Técnica (L10 §1.4 y §1.6)**:
  > "Se trunca `emitidoEn` (`Math.floor(Date.parse(emitidoEn) / 300_000) * 300_000`) porque el simulador y los reprocesos reproducen una jornada histórica a cámara rápida; si usáramos `now()` del reloj del contenedor, los 3.039 eventos caerían todos en el minuto actual.  
  > Además, exigimos `terminadas >= MINIMO` (ej. `3` o `5`) además de `porcentaje_error > 20%` porque sin un mínimo, una ventana tranquila con 1 sola partida que casualmente falló tendría `1/1 = 100%` de error y dispararía una falsa alarma. Con el mínimo se filtra el ruido y queda únicamente el incidente real del **juego `1328670` entre las `21:30` y `21:35` UTC (`68` errores de `69` terminadas)**."

---

### L.6. En `vidalstore-historial`, si el evento `licencia.revocada` no trae el precio en su payload, ¿cómo sabe el consumidor cuánto dinero descontar y qué garantiza que la compra original ya esté en la tabla?
* **Respuesta Técnica (L10 §1.7 y §1.11)**:
  > "Cuando llega `compra.realizada`, el consumidor guarda el detalle de esa licencia (`licencia_id`, `juego_id`, `semana`, `precio_pagado`) en la tabla auxiliar `compras_vistas` (o `licencias_vistas`) y suma en `ventas_semana`. Cuando más tarde llega `licencia.revocada`, busca la fila original por `licencia_id`, la marca como revocada y descuenta ese mismo monto en la semana original (`380` compras por `6.291.370 CLP` menos `15` revocaciones = **`6.032.190 CLP` netos**).  
  > Lo que garantiza que `compra.realizada` llegue siempre antes que `licencia.revocada` es que el topic `vidalstore.compras` usa **`usuarioSub` como `record key`**, enviando ambos eventos del mismo jugador a la misma partición en orden estricto."

---

### L.7. ¿Cómo viaja la petición del panel en vivo desde Angular hasta Postgres y por qué el BFF no consulta las tablas directamente?
* **Respuesta Técnica (L10 Tramo 2)**:
  > "La vista `/panel` de Angular consulta cada 5 s `GET /v1/panel/en-vivo` al **Gateway (`:8080`)**, que valida el JWT y el scope y reenvía al **BFF (`:3000/panel/en-vivo`)**. El BFF valida nuevamente el JWT y exige `@Roles('administradores')` con `RolGuard`, y hace `fetch` interno a **`eventos` (`:3010/panel/en-vivo`)**, donde `PanelNegocio` ejecuta 3 consultas en paralelo con `Promise.all` contra Postgres.  
  > El BFF **jamás se conecta a Postgres** porque no es dueño de ninguna tabla: toda la lectura y escritura de las proyecciones de streaming pertenece exclusivamente al microservicio `eventos`."

---

### L.8. ¿Por qué `kafka-consumer-groups.sh --reset-offsets` falla si `eventos` está corriendo y cuáles son los pasos exactos para rebobinar un grupo y demostrar idempotencia/reconstrucción? (`IE7`)
* **Respuesta Técnica (L10 §3.1)**:
  > "Kafka prohíbe cambiar los offsets de un grupo con miembros conectados (`Error: Assignments can only be reset if the group '...' is inactive, but the current state is Stable`) porque los consumidores activos sobrescribirían el offset en su siguiente commit.  
  > Los pasos son: **(1)** `docker compose stop eventos` (el grupo pasa a `Empty`); **(2)** `--reset-offsets --to-earliest --execute` sobre el grupo (`NEW-OFFSET = 0`); **(3)** `TRUNCATE` de la tabla del grupo y `DELETE FROM eventos_procesados WHERE grupo = '...'`; y **(4)** `docker compose start eventos`. En ~2 segundos el grupo relee el log desde el inicio y reconstruye exactamente las mismas cifras sin mover el offset de los otros dos grupos."

---

### L.9. ¿Cómo funciona la compactación en `vidalstore.catalogo` (Grupos de 3), por qué no lleva `retention.ms` y por qué el productor lee el topic desde `offset 0` antes de sembrar?
* **Respuesta Técnica (L10 §1.9 y §3.5)**:
  > "* **`cleanup.policy=compact` sin `retention.ms`**: La compactación conserva siempre el último mensaje de cada `key` (`juegoId`). Si tuviera `retention.ms` (por defecto 7 días), Kafka borraría por antigüedad los juegos cuyo precio no ha cambiado en una semana, dejando el catálogo incompleto.  
  > * **Lectura previa en el productor**: Al arrancar, el microservicio de catálogo lee su propio topic desde `offset 0` para conocer el último estado publicado de cada juego y publicar únicamente los juegos nuevos o modificados, evitando llenar el topic con duplicados en cada reinicio.  
  > * **Reconstrucción en el consumidor**: El grupo `vidalstore-catalogo` consume con `mode: EARLIEST` y aplica `WHERE catalogo.emitido_en < EXCLUDED.emitido_en` por si el segmento activo aún conserva versiones previas sin compactar."

---

### L.10. ¿Qué contiene cada etapa del `Dockerfile` multi-stage de un servicio NestJS y cómo compruebas que la imagen final cumple las reglas de seguridad de la E2?
* **Respuesta Técnica (L10 Tramo 4)**:
  > "* **Etapa 1 (`FROM node:24-slim AS build`)**: Instala todas las dependencias (`npm ci`, incluyendo TypeScript y `@nestjs/cli`) y compila `src/` a JavaScript en `/app/dist`.  
  > * **Etapa 2 (`FROM node:24-slim`)**: Define `ENV NODE_ENV=production`, instala solo dependencias de producción (`npm ci --omit=dev && npm cache clean --force`), copia `/app/dist` desde la etapa `build` (y `COPY esquema.sql ./` en `catalogo`, `licencias` y `eventos`), y cambia al usuario sin privilegios **`USER node` (`uid=1000`)**.  
  > * **Comprobación**: Ejecutando `id` dentro del contenedor responde `uid=1000(node)` (no `root`), y buscando el binario `nest` en `/app/node_modules` devuelve `0`."

---

### L.11. En `.github/workflows/imagen.yml`, ¿por qué se usa `${GITHUB_REPOSITORY,,}` y `${GITHUB_SHA}` en lugar de `:latest`, y cómo verificas que el docente podrá descargar la imagen?
* **Respuesta Técnica (L10 §4.4–4.6)**:
  > "* **`${GITHUB_REPOSITORY,,}`**: Convierte el propietario y nombre del repositorio a minúsculas en bash, porque Docker y GHCR rechazan etiquetas de imagen con letras mayúsculas.  
  > * **`${GITHUB_SHA}` en vez de `:latest`**: Ata de forma inmutable cada imagen al hash exacto del commit en `main` que la construyó, haciendo auditable qué versión está corriendo en la nube.  
  > * **Verificación sin credenciales**: Tras cambiar la visibilidad de los 7 paquetes a **Public** en GHCR, ejecutamos `docker logout ghcr.io && docker pull --platform linux/amd64 ghcr.io/<usuario>/<repo>:<sha>`."

---

### L.12. En AWS (`deploy/aws/`), ¿por qué no se puede crear un Security Group con `--group-name sg-gw`, por qué `nat-user-data.sh` ejecuta `iptables -F`, y dónde se guardan las contraseñas?
* **Respuesta Técnica (L10 Tramo 5)**:
  > "1. **Prefijo `sg-` reservado**: AWS rechaza cualquier `--group-name` que comience con `sg-` (`GroupName cannot start with reserved prefix "sg-"`). Por eso creamos el grupo con `--group-name vidalstore-gw` y le asignamos el nombre pedido mediante el tag **`Name=sg-gw`**.  
  > 2. **`iptables -F` en `nat`**: Amazon Linux 2023 trae por defecto una regla en la cadena `FORWARD` que rechaza todo el tráfico (`REJECT all -- icmp-host-prohibited`). Si no se limpia la tabla `filter` con `iptables -F` además del `MASQUERADE` y `--no-source-dest-check`, las instancias privadas no salen a internet.  
  > 3. **Secretos en SSM Parameter Store**: `03-subir.sh` excluye `aws/secretos/*` al sincronizar el bucket S3 y sube `mq-1.env`, `mq-2.env` y `datos.env` a **SSM Parameter Store como `SecureString`**, desde donde cada EC2 los descarga al arrancar."

---

### L.13. En AWS, ¿por qué el `compose.yml` de Kafka en `mq-1..3` usa `network_mode: host` y cómo se configura la cookie de Erlang en RabbitMQ 4.3?
* **Respuesta Técnica (L10 §5.5)**:
  > "* **`network_mode: host` en Kafka**: En cada instancia `mq-N` corren juntos un `controller` (`:9093`) y un `broker` (`:19092`), mientras los otros miembros del quórum están en las otras dos EC2 (`10.0.21.11`, `10.0.22.12`, `10.0.21.13`). Con `network_mode: host`, ambos contenedores usan directamente la interfaz de red de la EC2 y se ven por sus IPs privadas sin conflictos de NAT de Docker.  
  > * **Cookie de Erlang en RabbitMQ 4.3**: Como la variable `RABBITMQ_ERLANG_COOKIE` quedó deprecada, `secretos.sh` escribe el valor sin salto de línea (`printf '%s'`) en `erlang.cookie` con permisos **`chmod 400`** y propietario **`chown 999:999`** (el UID del usuario `rabbitmq` dentro del contenedor) y lo monta en `/var/lib/rabbitmq/.erlang.cookie:ro`."

---

### L.14. En Azure (`deploy/azure/`), ¿qué pasa si pones una tilde o una `ñ` en `cloud-init-gw-azure.yaml` y por qué hay que agregar reglas en `DOCKER-USER`?
* **Respuesta Técnica (L10 §6.3)**:
  > "* **Trampa de caracteres no ASCII en `cloud-init`**: Si el archivo YAML lleva una tilde o `ñ`, Azure CLI en Windows lo recodifica en `cp1252`. Al arrancar Ubuntu, `cloud-init` falla al decodificar `UTF-8` (`UnicodeDecodeError`), **descarta el archivo entero sin instalar Docker ni activar el NAT**, pero igual reporta `status: done`. Por eso los `cloud-init-*.yaml` deben ser 100% ASCII puro.  
  > * **Trampa de Docker sobre `FORWARD`**: Al instalarse `docker.io` en `gw-azure`, Docker cambia la política de la cadena `FORWARD` de `iptables` a `DROP`, cortando el tráfico NAT de la subred privada `10.1.2.0/24`. Para permitir el paso se insertan en `DOCKER-USER` las reglas `-s 10.1.2.0/24 -j ACCEPT` y `-d 10.1.2.0/24 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT`."

---

### L.15. En Azure, ¿por qué la subred `privada` requiere `--default-outbound false` y cuál es la diferencia entre `VM stopped` y `VM deallocated`?
* **Respuesta Técnica (L10 §6.2 y §6.5)**:
  > "* **`--default-outbound false`**: A diferencia de AWS, Azure otorga salida implícita a internet a las subredes nuevas. Desactivarla con `--default-outbound false` obliga a que todo el tráfico saliente de `bff` (`10.1.2.4`) pase exclusivamente por la tabla de rutas `rt-privada` hacia el Virtual Appliance `gw-azure` (`10.1.1.4`), saliendo con su IP pública estática.  
  > * **`VM stopped` vs `VM deallocated`**: Apagar la máquina desde dentro del sistema operativo la deja en `VM stopped`, donde Azure **sigue reservando y cobrando las vCPUs y la RAM cada hora**. Ejecutar `az vm deallocate` (`apagar.sh`) libera el hardware físico y la deja en **`VM deallocated`**, deteniendo el cobro de cómputo y preservando los discos y la IP pública estática."

---

### L.16. ¿Por qué en Windows el archivo `envs-grupoNN-seccion.zip` debe crearse con `/c/Windows/System32/tar.exe` y no con `tar` a secas en Git Bash?
* **Respuesta Técnica (L10 §7.2)**:
  > "Porque en Git Bash el comando `tar` por defecto es **GNU tar**, el cual ignora el flag `-a` para formato `.zip` y genera un archivo en formato `.tar` aunque el nombre termine en `.zip` (provocando error de archivo dañado al descomprimirlo). En cambio, `/c/Windows/System32/tar.exe` es **bsdtar** de Windows, que al recibir `-a -c -f archivo.zip` detecta la extensión `.zip` y empaqueta un archivo ZIP estándar genuino."

---

## Bloque M: Preguntas Oficiales y Quizzes de D14 (La E2 de Punta a Punta)

> ### Las Preguntas de Arquitectura, Confirmación, Diagnóstico y Nube de la Clase D14

### M.1. ¿De dónde obtiene el BFF los datos para alimentar el panel en vivo `/panel` y por qué no consulta directamente a Postgres? (Quiz D14.1 · Slide 8)
* **Pregunta de Quiz**:
  > *"El administrador abre `/panel` y el BFF necesita las partidas en curso de las 21:46. ¿De dónde las obtiene?"*
* **Respuesta Técnica Correcta**:
  > "Se las pide por **HTTP interno a `vidalstore-eventos` (`GET http://eventos:3010/panel/en-vivo`)**, el microservicio dueño de la tabla `kpi_minuto`."
* **Por qué los distractores son trampas de arquitectura**:
  > 1. **Abrir conexión a Postgres y consultar `kpi_minuto` directo**: Error grave de encapsulamiento. Cada tabla tiene un único microservicio dueño; si el BFF consulta directo, cualquier migración de base de datos o cambio en el esquema de streaming rompe dos servicios a la vez.  
  > 2. **Suscribirse a `vidalstore.actividad` y contar él mismo**: Error. Solo contaría eventos que lleguen desde el momento en que se abre la página en el navegador, perdiendo todo el histórico desde las 21:00 y duplicando inútilmente el trabajo de agregación de `vidalstore-panel`.  
  > 3. **Angular las calcula leyendo Kafka**: Error de seguridad y diseño. El navegador web jamás se conecta a brokers de Kafka; todo pasa a través del API Gateway y el BFF.

---

### M.2. ¿En qué lugar exacto del código del consumidor va el commit del offset y por qué el auto-commit es causal de pérdida grave de puntos? (Quiz D14.2 · Slide 10)
* **Pregunta de Quiz**:
  > *"Tu consumidor de `vidalstore-panel` valida el evento, hace el INSERT en `kpi_minuto` y confirma el offset. ¿En qué lugar del código va el commit?"*
* **Respuesta Técnica Correcta**:
  > "**Después de escribir en Postgres; y si el evento no cumple el contrato (DTO), después de registrarlo.**  
  > La regla de oro es: primero se asegura la persistencia relacional, y recién con la confirmación de la base de datos se avisa a Kafka (`commit = offset + 1` con `autocommit: false`). Si el evento viola el contrato, se registra en el log y también se confirma para no congelar la partición. Si falla Postgres, se relanza la excepción y **no se confirma**."
* **Por qué los distractores son trampas**:
  > 1. **Apenas llega el mensaje, antes del INSERT**: Si el contenedor muere o es desalojado entre el commit y el INSERT, Kafka cree que ya fue procesado y no lo vuelve a entregar: pérdida irreparable de datos (*at-most-once*).  
  > 2. **Auto-commit (`autocommit: true`)**: Confirma por tiempo transcurrido (reloj), no por trabajo efectivamente terminado en base de datos; puede confirmar eventos que todavía están encolados o no persistidos. Es de los errores más sancionados en IE5.  
  > 3. **Solo cuando el INSERT funcionó dejando el inválido sin confirmar**: Un evento que viola el contrato fallará siempre; sin commit, el consumidor reintentará el veneno infinitamente y la partición quedará congelada con el lag subiendo sin control.

---

### M.3. Si el proceso consumidor muere abruptamente entre el INSERT en Postgres y el commit del offset a Kafka, ¿qué sucede al reiniciar el proceso y cómo se garantiza el resultado exactamente una vez? (Predicción D14 · Slide 13)
* **Respuesta Técnica**:
  > "1. Kafka no sabe que el evento se escribió en Postgres; solo sabe hasta el último offset confirmado.  
  > 2. Al arrancar de nuevo el contenedor, Kafka reentrega el offset no confirmado.  
  > 3. El consumidor intenta ejecutar el `INSERT INTO kpi_minuto ... ON CONFLICT (evento_id) DO NOTHING`.  
  > 4. Como la clave `evento_id` ya existe en Postgres, la base de datos detecta el conflicto, no inserta una fila duplicada y no incrementa los contadores (`RETURNING evento_id` devuelve 0 filas).  
  > 5. El consumidor avanza y envía el commit del offset a Kafka.  
  > 6. **Conclusión**: A pesar de que el transporte es de entrega *al menos una vez* (*at-least-once*), la idempotencia de la tabla garantiza que el estado final en base de datos sea **resultado exactamente una vez** (*effectively exactly-once*), absorbiendo tanto los 17 duplicados del dataset como cualquier caída de proceso."

---

### M.4. En `vidalstore-alertas`, ¿por qué la regla de alerta del 20% de errores exige un umbral mínimo de partidas terminadas por ventana de 5 minutos, y cuántas alertas quedan en el dataset si el mínimo es 3? (Quiz D14.3 · Slides 15 y 16)
* **Respuesta Técnica**:
  > "* **Necesidad del Mínimo**: Si una ventana fija de 5 minutos de `emitidoEn` registra una única partida terminada y esta finalizó en error, la tasa de fallos es $1/1 = 100\%$, superando el 20%. Sin un mínimo de partidas, una sola falla aislada dispararía una alerta crítica falsa, generando fatiga de alarmas.  
  > * **Dataset de VidalStore con mínimo de 3 partidas**: En el dataset existen 5 ventanas que superan el 20%: juego `2379780` (1/1), juego `1328670` (68/69), juego `1203220` (dos ventanas de 1/2) y juego `1145360` (1/1). Al exigir un mínimo de 3 partidas terminadas, **queda exactamente UNA sola alerta en la tabla `alertas`**: el incidente del juego **`1328670` entre 21:30 y 21:35 con 68 de 69 partidas en error (98.6%)**."

---

### M.5. ¿Por qué el topic `vidalstore.compras` debe tener obligatoriamente `usuarioSub` como key y qué desastre de cálculo ocurriría en `vidalstore-historial` si la key fuera aleatoria? (D14 Slide 17)
* **Respuesta Técnica**:
  > "El evento `licencia.revocada` no incluye el precio de la licencia en su payload; `vidalstore-historial` debe buscar la compra original con el mismo `licenciaId` en su tabla local para descontar el importe del neto de ventas.  
  > Como el productor utiliza **`key = usuarioSub`**, la función de hash garantiza que **`compra.realizada` y `licencia.revocada` viajen obligatoriamente a la misma partición física**. Dentro de una partición individual, Kafka garantiza orden monotónico estricto; por ende, la compra siempre se procesa antes que la revocación.  
  > Si la key fuera aleatoria o por juego, caerían en particiones distintas que se consumen en paralelo: la revocación podría leerse antes que la compra, no encontraría el precio para descontar y el total neto (**6.032.190 CLP**) quedaría descuadrado."

---

### M.6. Si levantas cuatro instancias de `vidalstore-eventos`, ¿qué muestra `#PARTITIONS` en `kafka-consumer-groups.sh --describe --members` para `vidalstore-alertas` frente a `vidalstore-panel` y por qué? (Quiz D14.4 · Slides 20 a 22)
* **Respuesta Técnica**:
  > "* **En `vidalstore-alertas`**: Lee únicamente `vidalstore.actividad` (3 particiones). Como una partición solo puede ser atendida por un único consumidor del grupo, Kafka asigna una partición a cada una de las 3 primeras instancias y **la cuarta instancia queda completamente ociosa**, mostrando `#PARTITIONS` **1, 1, 1 y 0**. Más instancias que particiones no aceleran el procesamiento, solo esperan.  
  > * **En `vidalstore-panel`**: Lee dos topics (`vidalstore.actividad` y `vidalstore.compras`), totalizando 6 particiones. Al repartir 6 particiones entre 4 instancias, el asignador entrega `#PARTITIONS` **2, 2, 1 y 1**."

---

### M.7. ¿Cuáles son los pasos estrictos para rebobinar un consumer group a `earliest` y por qué la herramienta falla si el servicio está corriendo? ¿Cómo se repite una demostración ante el profesor en la defensa? (D14 Slides 23 y 24)
* **Respuesta Técnica**:
  > "* **Fallo con grupo activo**: Kafka exige que el consumer group esté inactivo para reasignar offsets; si el servicio está corriendo (`Stable`), `kafka-consumer-groups.sh` se niega con el error `Assignments can only be reset if the group ... is inactive, but the current state is Stable`.  
  > * **Pasos Estrictos de Rebobinado**:  
  >   1. Detener `vidalstore-eventos` (`docker compose stop eventos`).  
  >   2. Esperar entre 10 y 30 segundos a que venza la sesión del consumidor.  
  >   3. Ejecutar `--reset-offsets --to-earliest --execute` y verificar `NEW-OFFSET: 0`.  
  >   4. Levantar nuevamente `eventos` (`docker compose start eventos`).  
  >   5. Comprobar que `ventas_semana` se recalcula idempotentemente con los mismos **6.032.190 CLP netos**.  
  > * **Repetición en la Defensa**: Para repetir una demostración en vivo ante el docente **NO se rebobina**: se vacían las tablas en Postgres con `TRUNCATE` y se reproduce el dataset completo nuevamente con el simulador."

---

### M.8. En nuestro clúster KRaft de 3 brokers con factor 3, `min.insync.replicas=2` y `acks=all`, ¿qué ocurre si se caen 2 brokers y por qué rechazar con `NOT_ENOUGH_REPLICAS` es la decisión correcta? (D14 Slides 26 y 27)
* **Respuesta Técnica**:
  > "Al caerse 2 brokers, el conjunto ISR se reduce a 1 réplica. Como $1 < \text{min.insync.replicas}=2$, el broker rechaza la escritura arrojando `NOT_ENOUGH_REPLICAS`.  
  > Esto es **rigurosamente correcto por diseño**: en un sistema transaccional de compras, **jamás se debe confirmar una transacción que resida en una única copia en disco**, ya que si ese único broker restante sufriera una falla de hardware antes de replicar, los datos de la compra se perderían irrevocablemente junto con el dinero del cliente."

---

### M.9. Al desplegar en la nube, una máquina de AWS intenta descargar una imagen desde GHCR y recibe HTTP `401 Unauthorized`. ¿Cuál es la causa y cómo se corrige? (Quiz D14.5 · Slide 31)
* **Respuesta Técnica**:
  > "La causa es que **el paquete en GitHub Container Registry quedó configurado como `Private`**, que es el estado por defecto con el que GitHub crea todo nuevo paquete.  
  > Se soluciona ingresando a GitHub en el repositorio respectivo $\to$ *Packages* $\to$ *Package settings* $\to$ zona de peligro *Change package visibility* $\to$ seleccionar **`Public`**. Las máquinas en la nube no deben almacenar tokens ni credenciales personales de GitHub."

---

### M.10. En AWS, si el Learner Lab se reinicia y la máquina `nat` queda apagada mientras `mq-1` se enciende, ¿por qué `mq-1` no aparece en Session Manager a pesar de tener el rol IAM asignado? (Quiz D14.6 · Slide 35)
* **Respuesta Técnica**:
  > "Porque el rol IAM (`LabInstanceProfile`) solo otorga las autorizaciones a nivel de plano de control de AWS, pero el demonio `amazon-ssm-agent` de la instancia EC2 necesita establecer físicamente una conexión HTTPS de salida hacia los endpoints de AWS Systems Manager en internet.  
  > Dado que `mq-1` reside en una subred privada sin IP pública, **su único camino a internet es la instancia `nat` (10.0.1.10)**. Si `nat` está detenida, `mq-1` está totalmente incomunicada del exterior y jamás podrá registrarse como `Online` ni descargar paquetes o contenedores."

---

### M.11. En Azure, tras asociar la tabla de rutas `0.0.0.0/0 -> 10.1.1.4` a la subred privada, un `curl https://api.ipify.org` ejecutado dentro de `bff` no responde. ¿Qué dos configuraciones faltan en `gw-azure`? (Quiz D14.7 · Slide 38)
* **Respuesta Técnica**:
  > "La tabla de rutas solo transporta los paquetes hasta la tarjeta de red de `gw-azure`. Para que el tráfico salga a internet faltan dos elementos indispensables:  
  > 1. **IP Forwarding habilitado en la interfaz de red de Azure (`NIC`)** de `gw-azure`, permitiendo que acepte paquetes cuyo destino no es su propia IP.  
  > 2. **Reglas de NAT / iptables** en el sistema operativo de `gw-azure` (`MASQUERADE` y reglas en la cadena `DOCKER-USER` para no ser bloqueado por el cortafuegos de Docker).  
  > *(Cuidado crítico: si el script `cloud-init` contenía tildes o caracteres fuera de ASCII, Azure CLI en Windows lo corrompe y cloud-init lo descarta entero en silencio sin configurar iptables)*."

---

### M.12. ¿Cuál es la regla de oro del 30% en la pauta de corrección de la E2 y qué orden exacto sigue el profesor Umbingelelo al corregir el archivo ZIP? (D14 Slides 3 y 39)
* **Respuesta Técnica**:
  > "* **La Regla del 30%**: En la E2, 60 puntos corresponden a Kafka (IE5, IE7, IE8) y 40 puntos a ingeniería. Si el script `bash levantar.sh` no logra dejar el sistema levantado y saludable desde un clon limpio, los 60 puntos de Kafka quedan inmediatamente con un **tope máximo del 30% (máximo 18 puntos)**, provocando la reprobación del encargo.  
  > * **Protocolo de Corrección del Docente**:  
  >   1. Clona los repositorios listados en `repositorios.md` en el commit SHA exacto de `main` a las 23:59.  
  >   2. Descomprime la carpeta `envs/` al lado de los clones, dejando cada `.env` en su repositorio.  
  >   3. Entra a `vidalstore-plataforma` y ejecuta `bash levantar.sh`.  
  >   4. Revisa `informe.pdf`, `docs/despliegue.md`, el panel en `/panel` y las cifras del dataset."





