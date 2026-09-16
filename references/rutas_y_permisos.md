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

### 8. `GET /v1/auditoria` *(Para Grupos de 3 Integrantes)*
* **Capa / Destino**: Microservicio de Auditoría (vía Gateway/BFF).
* **Mecanismo de Autorización**: **Grupo** (`cognito:groups`).
* **Roles Permitidos**: `administradores`.
* **Propósito**: Devuelve el registro de auditoría de compras, modificaciones de catálogo y revocaciones de licencias.
* **Respuesta Exitosa**: `200 OK` con los registros de auditoría.
* **Respuestas de Error**:
  - `401 Unauthorized`: Sin token válido.
  - `403 Forbidden`: Invocado por usuarios no administradores.
