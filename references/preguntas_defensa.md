# Banco de Preguntas y Respuestas Modelo · Defensa Individual EP1 y EP2

La defensa técnica individual representa el **60% de la nota final** (tanto en EP1 como en EP2). El docente Cristian Calderón (`Umbingelelo`) realiza preguntas profundas sobre las decisiones de arquitectura, los tokens, los flujos criptográficos, la mensajería asíncrona, Docker Compose, DLQ y las pruebas en vivo.

Este documento consolida:
1. **Las 8 preguntas oficiales de `Pulso.pdf` (Tramo 12.2)** (Bloque A).
2. **Las preguntas complementarias de rúbrica EP1 (IE1 a IE10)** (Bloques B, C, D y E).
3. **El guion oficial de defensa técnica de la clase D6**: reloj de 15 minutos, 5 flujos y método de 4 pasos.
4. **Las 15 preguntas oficiales de D8, L7A y L7 (Mensajería, Compose, DLQ y Persistencia)** (Bloque F).
5. **Las preguntas de defensa del Microservicio Administrador (Oscar · IE6, IE7, IE8, IE14, IE17, IE18)** (Bloque G: G.1 a G.9).

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

