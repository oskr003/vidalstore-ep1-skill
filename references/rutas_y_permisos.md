# Matriz Detallada de Rutas y Permisos · VidalStore EP1

En el enunciado **`EP1-Caso-VidalStore.pdf`** (punto 4.3) y el documento de aclaraciones **`EP1-aclaraciones.pdf`**, se estipula que el sistema cuenta con las siguientes rutas. No hacen falta más para cumplir la pauta, y agregar otras no suma puntaje. Para grupos de 3 integrantes (caso de David, Oscar e Iván según el plan de trabajo), se incluye además la ruta de auditoría.

---

## 1. Matriz de Endpoints

### 1. `GET /v1/catalogo`
* **Capa / Destino**: Microservicio de Catálogo (vía Gateway).
* **Mecanismo de Autorización**: **Scope** (`vidalstore/catalogo.leer`).
* **Condición de Acceso**: Cualquier sesión válida con token emitido por el User Pool. En VidalStore **no hay vitrina pública**; exige sesión iniciada (Discusión #7).
* **Respuesta Exitosa**: `200 OK` con el listado de videojuegos disponibles.
* **Respuestas de Error**:
  - `401 Unauthorized`: Token ausente, corrupto o vencido.
  - `403 Forbidden`: Token válido pero no posee el scope `vidalstore/catalogo.leer`.

---

### 2. `POST /v1/catalogo`
* **Capa / Destino**: Microservicio de Catálogo (vía Gateway/BFF).
* **Mecanismo de Autorización**: **Grupo** (`cognito:groups`).
* **Roles Permitidos**: `editores`, `administradores`.
* **Cuerpo de la Petición (`body`)**:
  ```json
  {
    "titulo": "The Legend of Zelda: Echoes of Wisdom",
    "descripcion": "Aventura de acción...",
    "precio": 59990,
    "estado": "disponible"
  }
  ```
* **Respuesta Exitosa**: `201 Created` con el juego creado y su `id` asignado.
* **Respuestas de Error**:
  - `400 Bad Request`: Datos incompletos o tipos incorrectos.
  - `401 Unauthorized`: Token no válido o ausente.
  - `403 Forbidden`: Usuario con rol `jugadores` intenta publicar.

---

### 3. `PUT /v1/catalogo/:juegoId`
* **Capa / Destino**: Microservicio de Catálogo (vía Gateway/BFF).
* **Mecanismo de Autorización**: **Grupo** (`cognito:groups`).
* **Roles Permitidos**: `editores`, `administradores`.
* **Parámetro de Ruta**: `juegoId` del juego a actualizar.
* **Respuesta Exitosa**: `200 OK` con el juego actualizado.
* **Respuestas de Error**:
  - `400 Bad Request`: Payload inválido.
  - `401 Unauthorized`: Sin token.
  - `403 Forbidden`: Usuario sin rol editor ni administrador.
  - `404 Not Found`: El `juegoId` no existe en el catálogo.

---

### 4. `POST /v1/compras`
* **Capa / Destino**: Microservicio de Compras (vía Gateway/BFF).
* **Mecanismo de Autorización**: **Scope** (`vidalstore/catalogo.leer` o sesión válida).
* **Identidad**: El comprador se resuelve **únicamente a partir del claim `sub` del token JWT**.
* **Idempotencia (Discusión #10)**: Un usuario solo puede comprar una licencia por juego.
  - Si el usuario ya posee una licencia para ese `juegoId`, responde **`409 Conflict`**.
* **Cuerpo de la Petición (`body`)**:
  ```json
  {
    "juegoId": "game-001"
  }
  ```
* **Respuesta Exitosa**: `201 Created` con la licencia creada vinculada al `sub` del usuario.
* **Respuestas de Error**:
  - `400 Bad Request`: `juegoId` faltante o no válido.
  - `401 Unauthorized`: Token inválido o sin `sub`.
  - `404 Not Found`: El `juegoId` no existe en el catálogo.
  - `409 Conflict`: El usuario ya posee una licencia activa para dicho juego.

---

### 5. `GET /v1/biblioteca`
* **Capa / Destino**: Microservicio de Biblioteca (vía Gateway/BFF).
* **Mecanismo de Autorización**: **Scope** / Sesión válida con **`sub`**.
* **Regla Innegociable**:
  > *`GET /v1/biblioteca` no recibe ningún identificador de usuario por parámetro ni por cuerpo. El usuario sale del claim `sub` del token y de ninguna otra parte. Un endpoint que acepte un usuario por parámetro o cuerpo y devuelva sus licencias se evalúa como no logrado, aunque exija un token válido.*
* **Respuesta Exitosa**: `200 OK` con el arreglo de licencias pertenecientes única y exclusivamente al `sub` del token autenticado.
* **Respuestas de Error**:
  - `401 Unauthorized`: Token no válido o sin `sub`.

---

### 6. `GET /v1/licencias`
* **Capa / Destino**: Microservicio de Licencias (vía Gateway/BFF).
* **Mecanismo de Autorización**: **Grupo** (`cognito:groups`).
* **Roles Permitidos**: `administradores`.
* **Propósito**: Permite listar las licencias de **todos** los usuarios de la plataforma para fines de auditoría y revocación administrativa.
* **Respuesta Exitosa**: `200 OK` con todas las licencias del sistema.
* **Respuestas de Error**:
  - `401 Unauthorized`: Petición anónima.
  - `403 Forbidden`: Invocado por `jugadores` o `editores`.

---

### 7. `DELETE /v1/licencias/:licenciaId`
* **Capa / Destino**: Microservicio de Licencias (vía Gateway/BFF).
* **Mecanismo de Autorización**: **Grupo** (`cognito:groups`).
* **Roles Permitidos**: `administradores`.
* **Descripción de Negocio**: Es la operación más sensible del sistema (revocación forzosa de la licencia de un usuario).
* **Respuesta Exitosa**: `200 OK` con confirmación de licencia revocada/eliminada.
* **Respuestas de Error**:
  - `401 Unauthorized`: Sin token válido.
  - `403 Forbidden`: Cualquier usuario que no sea `administrador`.
  - `404 Not Found`: Si la licencia no existe.

---

### 8. `GET /v1/auditoria` *(Para Grupos de 3 Integrantes en EP1)*
* **Capa / Destino**: Microservicio de Auditoría (vía Gateway/BFF).
* **Mecanismo de Autorización**: **Grupo** (`cognito:groups`).
* **Roles Permitidos**: `administradores`.
* **Propósito**: Devuelve el registro de auditoría de compras, modificaciones de catálogo y revocaciones de licencias.
* **Respuesta Exitosa**: `200 OK` con los registros de auditoría.
* **Respuestas de Error**:
  - `401 Unauthorized`: Sin token válido.
  - `403 Forbidden`: Invocado por usuarios no administradores.

---

## 2. Matriz de Endpoints de la Unidad 2 / EP2 (`vidalstore-admin` `:3020` y `vidalstore-eventos` `:3010`)

Según [`EP2-Caso-VidalStore.pdf`](file:///Users/oscar/Downloads/DUOC/CloudNative/Evaluacion%202/EP2-Caso-VidalStore.pdf) (§4.2, §4.5 y §4.9) y [`L8.pdf`](file:///Users/oscar/Downloads/DUOC/CloudNative/Evaluacion%202/material/L8.pdf) (Tramo 3):
- Todas las rutas de `vidalstore-admin` (`:3020`) están protegidas directamente en la clase `AdminController` con `@UseGuards(AuthGuard, RolesGuard)` y `@Roles('ADMIN', 'administradores')` (sin depender del Gateway, aunque `vidalstore-gateway` en `:8080` también expone un proxy hacia `/v1/admin/*` para el dashboard de Angular).
- `RolGuard` / `RolesGuard` lee los metadatos tanto del método como de la clase (`ctx.getHandler() ?? ctx.getClass() ?? []`).

### 2.1 Las 8 Rutas Obligatorias de Administración de Topología (`EP2-Caso-VidalStore.pdf` §4.5 · IE6, IE7, IE8, IE17)

| # | Método y Ruta | Qué hace | Cuerpo (`@Body()`) Validado con `class-validator` | Códigos HTTP |
|:---:|---|---|---|---|
| **1** | `GET /v1/admin/colas`<br/>*(y alias `/v1/admin/queues`)* | Lista las colas con `name`, `type`, `state`, `messages_ready`, `messages_unacknowledged`, `consumers`. | — | `200`, `401`, `403`, `503` |
| **2** | `POST /v1/admin/colas` | Crea o declara una cola (por omisión `quorum`). | `{ nombre, tipo?, durable?, autoDelete?, arguments? }` (`nombre` con regex `/^[a-zA-Z0-9._-]+$/`). | `201`, `400`, `401`, `403`, `409` (`PRECONDITION_FAILED`), `503` |
| **3** | `DELETE /v1/admin/colas/:nombre` | Elimina una cola de forma idempotente. | — | `200`, `401`, `403`, `503` |
| **4** | `GET /v1/admin/exchanges` | Lista los exchanges con `name`, `type`, `durable`. | — | `200`, `401`, `403`, `503` |
| **5** | `POST /v1/admin/exchanges` | Crea o declara un exchange. | `{ nombre, tipo, durable?, autoDelete?, arguments? }` (`tipo` en `['direct', 'topic', 'fanout', 'headers']`). | `201`, `400`, `401`, `403`, `409`, `503` |
| **6** | `DELETE /v1/admin/exchanges/:nombre` | Elimina un exchange de forma idempotente. | — | `200`, `401`, `403`, `503` |
| **7** | `POST /v1/admin/bindings` | Crea un binding entre un exchange y una cola. | En enunciado (`EP2` pág. 20 / `L8` pág. 25): `{ exchange, cola, routingKey }`.<br/>En `CrearBindingDto` actual: `{ origen, destino, tipoDestino?, routingKey? }`. | `201`, `400`, `401`, `403`, `404` (`NOT_FOUND`), `503` |
| **8** | `DELETE /v1/admin/bindings` | Elimina un binding (DELETE con cuerpo porque se identifica por la terna exchange + cola + routingKey). | Mismo DTO que `POST /v1/admin/bindings`. | `200`, `400`, `401`, `403`, `404`, `503` |

### 2.2 Ruta Adicional Obligatoria para Grupos de 3 Integrantes (`EP2-Caso-VidalStore.pdf` §4.9)

| Método y Ruta | Qué hace | Especificación Oficial (§4.9 pág. 24–25) vs Implementación Actual | Códigos HTTP |
|---|---|---|---|
| `POST /v1/admin/dlq/:id/reproceso` | Solicita el reproceso controlado de un mensaje muerto registrado en `mensajes_muertos`. | • **Según `EP2-Caso-VidalStore.pdf` §4.9**: `vidalstore-admin` no toca `mensajes_muertos`; publica en `vidalstore.comandos` con `dlq.reprocesar` `{ mensajeMuertoId, payloadCorregido?, solicitadoPor }`. `vidalstore-eventos` consume de su cola `q.reprocesar`, republica al exchange original con su `routing_key` y `x-evento-id` original, y marca `reprocesada = true`.<br/>• **Implementación actual**: `vidalstore-admin` consulta `mensajes_muertos`, publica en `vidalstore.dlx` con `dlq.reprocesar` y marca `reprocesada = true` (400 si ya estaba reprocesada). | `200`/`201`, `400`, `401`, `403`, `404`, `503` |

### 2.3 Endpoints Complementarios de Observabilidad y Salud

| Microservicio | Método y Ruta | Propósito |
|---|---|---|
| `vidalstore-admin` (`:3020`) | `GET /v1/admin/queues/:name` | Detalle individual de una cola (`404` si no existe). |
| `vidalstore-admin` (`:3020`) | `GET /v1/admin/cluster` | Resumen global del clúster (`/api/overview`: versión, nodos, totales de colas y tasas). |
| `vidalstore-admin` (`:3020`) | `GET /v1/admin/mensajes-muertos`<br/>`DELETE /v1/admin/mensajes-muertos/:id` | Listado y depuración de cartas muertas registradas en PostgreSQL. |
| `vidalstore-admin` (`:3020`) | `POST /v1/admin/eventos`<br/>`POST /v1/admin/comandos` | Publicación administrativa de eventos (`vidalstore.eventos`) o comandos (`vidalstore.comandos`). |
| `vidalstore-eventos` (`:3010`) | `GET /salud` | Único endpoint HTTP del worker (`EP2-Caso-VidalStore.pdf` §4.2 pág. 16). Verifica que el canal con RabbitMQ esté abierto y que PostgreSQL responda `SELECT 1` (`200 OK` o `503 Service Unavailable`). Usado por el `healthcheck` de Docker Compose. |

