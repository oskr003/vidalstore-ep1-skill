# Banco de Preguntas y Respuestas Modelo · Defensa Individual EP1

La defensa técnica individual representa el **60% de la nota final de la EP1**. El docente Cristian Calderón (`Umbingelelo`) realiza preguntas profundas sobre las decisiones de arquitectura, los tokens, los flujos criptográficos y las pruebas en vivo.

A continuación se detallan las 10 preguntas más probables con sus respuestas técnicas fundamentadas al 100%.

---

### Pregunta 1: ¿Por qué guardan el token en `sessionStorage` y no en `localStorage`? ¿Qué se gana y qué problema sigue sin resolver?
* **Fuente**: *EP1-aclaraciones.pdf (Página 5)*.
* **Respuesta Modelo**:
  > "Configuramos `sessionStorage` en `main.ts` mediante `cognitoUserPoolsTokenProvider.setKeyValueStorage(sessionStorage)` porque `localStorage` persiste indefinidamente en disco duro, lo que representaba el segundo hallazgo crítico del informe forense de VidalStore (amplia ventana de exposición ante robo o acceso a la máquina).
  > Con `sessionStorage` ganamos que el token se destruye automáticamente al cerrar la pestaña o ventana del navegador y queda aislado por contexto de navegación.
  > Sin embargo, **lo que sigue sin resolver** es la vulnerabilidad ante ataques **XSS (Cross-Site Scripting)**: cualquier script malicioso ejecutado en el contexto de la página puede acceder a `sessionStorage` y exfiltrar el token en memoria mientras la pestaña esté abierta. La solución definitiva frente a XSS sería delegar el almacenamiento a cookies seguras con atributos `HttpOnly`, `SameSite` y `Secure` manejadas por un BFF."

---

### Pregunta 2: ¿Cuál es la diferencia de responsabilidades entre el API Gateway y el BFF? ¿Por qué validar el token en ambos saltos?
* **Fuente**: *EP1-aclaraciones.pdf (Páginas 2 y 4), Discusión #8*.
* **Respuesta Modelo**:
  > "El **API Gateway autentica**: su única responsabilidad es verificar la validez técnica y criptográfica del token contra el JWKS de Cognito (firma, emisor, vigencia, tipo de token y client_id). Si el token no sirve, responde `401 Unauthorized`.
  > El **BFF autoriza**: asume que la identidad fue probada, inspecciona los grupos del usuario (`cognito:groups`) y decide si su rol le permite ejecutar la acción solicitada. Si el rol no alcanza, responde `403 Forbidden`.
  > Validamos en los **dos saltos (defensa en profundidad)** porque en arquitecturas Cloud Native rige el principio de *Zero Trust*: ninguna capa interna debe asumir ciegamente que la capa anterior hizo su trabajo. Si un atacante lograra saltarse el gateway y enviar una petición directa al puerto interno del backend/BFF sin token, este se cierra de inmediato con un `401 Unauthorized`."

---

### Pregunta 3: ¿Por qué la ruta `GET /v1/biblioteca` no recibe el ID del usuario por parámetro ni por cuerpo?
* **Fuente**: *EP1-Caso-VidalStore.pdf (Página 9)*.
* **Respuesta Modelo**:
  > "Porque si la ruta aceptara un `userId` por parámetro (como `/v1/biblioteca?usuarioId=123` o `/v1/biblioteca/123`), cualquier usuario autenticado con un token válido podría consultar la biblioteca de otros usuarios simplemente cambiando el parámetro (vulnerabilidad BOLA / IDOR).
  > En nuestro diseño, la identidad se extrae estrictamente del claim **`sub` (Subject)** contenido en el payload del JWT firmado por Cognito. El usuario solo puede consultar sus propios datos porque el backend resuelve la consulta exclusivamente a partir de la identidad criptográficamente verificada en el token."

---

### Pregunta 4: ¿Cuál es la diferencia entre un Scope y un Grupo en Cognito? ¿Por qué revocar una licencia no se autoriza por Scope?
* **Fuente**: *EP1-Caso-VidalStore.pdf (Página 8), Discusión #17*.
* **Respuesta Modelo**:
  > "Un **Scope** se define en el Resource Server y se otorga al App Client: determina qué operaciones puede solicitar la **aplicación cliente** ante la API (limita la superficie expuesta a ese cliente, por ejemplo web vs móvil). Cualquier usuario que inicie sesión a través de esa aplicación obtendrá un token con esos mismos scopes.
  > Un **Grupo (`cognito:groups`)** representa el rol de la **persona** humana que está usando el sistema (`jugadores`, `editores`, `administradores`).
  > La operación de revocar una licencia (`DELETE /v1/licencias/:id`) es la más crítica del sistema. No puede autorizarse por scope porque cualquier jugador que entre por la tienda tendría ese scope; debe autorizarse estrictamente por pertenencia al grupo `administradores`."

---

### Pregunta 5: ¿Por qué se utiliza Authorization Code con PKCE en lugar del Flujo Implícito o ROPC?
* **Fuente**: *Rúbrica Oficial (IE8)*.
* **Respuesta Modelo**:
  > "En aplicaciones SPA (Single Page Applications) como Angular, el código corre en el navegador del usuario y no puede mantener un secreto de cliente (`client_secret`) seguro.
  > El **flujo implícito** está deprecado por OAuth 2.1 porque devuelve el token directamente en el fragmento de la URL (`#access_token=...`), exponiéndolo en el historial del navegador, logs de proxies y fugas por Referer.
  > El flujo **ROPC (Resource Owner Password Credentials)** exige que el frontend capture usuario y contraseña directamente, rompiendo la delegación de identidad y permitiendo que la aplicación conozca las credenciales.
  > **Authorization Code con PKCE (Proof Key for Code Exchange)** mitiga la interceptación del código de autorización: el cliente genera un `code_verifier` aleatorio y envía su hash `code_challenge` con algoritmo `S256`. Al canjear el código, envía el `code_verifier` original, demostrando criptográficamente que quien canjea el código es el mismo que inició la petición, sin necesidad de un `client_secret` estático."

---

### Pregunta 6: ¿Por qué la compra de licencias (`POST /v1/compras`) es idempotente y qué sucede si un usuario hace doble clic?
* **Fuente**: *Discusión #10*.
* **Respuesta Modelo**:
  > "Un usuario solo debe poseer una única licencia activa por cada juego. Si la petición de compra se repite (por doble clic accidental, reintento de red o reenvío del formulario), el microservicio de compras verifica si ya existe una licencia para la tupla `(usuarioSub, juegoId)`. Si ya existe, responde con un código **`409 Conflict`** (o retorna la licencia existente) impidiendo la creación redundante de licencias o cobros duplicados."

---

### Pregunta 7: ¿De dónde salieron los datos del catálogo inicial?
* **Fuente**: *EP1-aclaraciones.pdf (Página 7)*.
* **Respuesta Modelo**:
  > "No utilizamos arreglos hardcodeados ni datos inventados. En la carpeta `data/` del microservicio disponemos del script `seed.ts` (o `seed.js`) que consume una API externa real de videojuegos (ej. RAWG / FreeToGame / PokeAPI), transforma los campos requeridos (título, descripción, precio, estado) y genera el archivo versionado `data/catalogo.json`. Cualquiera que clone el repositorio puede ejecutar el script de seed y volver a generar los datos de manera reproducible."

---

### Pregunta 8: ¿Por qué CORS está configurado solo en el Gateway y no en el BFF ni en los microservicios?
* **Fuente**: *EP1-aclaraciones.pdf (Página 3), Rúbrica (IE4)*.
* **Respuesta Modelo**:
  > "CORS (Cross-Origin Resource Sharing) es un mecanismo de seguridad impuesto exclusivamente por los **navegadores web**. Como el navegador Angular únicamente se comunica con el API Gateway (`http://localhost:8080`), solo el Gateway requiere cabeceras CORS (`Access-Control-Allow-Origin: http://localhost:4200`).
  > El BFF y los microservicios son invocados exclusivamente servidor a servidor (backend-to-backend) mediante peticiones HTTP/Fetch directas desde Node.js, donde el navegador no interviene; por lo tanto, configurar CORS en capas internas es innecesario y representaría una mala práctica de configuración."

---

### Pregunta 9: ¿Qué elementos específicos valida el Gateway en el JWT contra el JWKS de Cognito?
* **Fuente**: *Rúbrica Oficial (IE2, IE9)*.
* **Respuesta Modelo**:
  > "El Gateway utiliza las claves públicas expuestas en el JWKS (`/.well-known/jwks.json`) de Cognito para verificar:
  > 1. **Firma criptográfica**: Verifica con el algoritmo RSA adecuado haciendo match con el `kid` (Key ID) del header del JWT.
  > 2. **Emisor (`iss`)**: Que coincida exactamente con la URL del User Pool de AWS.
  > 3. **Vigencia temporal**: Que el tiempo actual se encuentre entre `nbf` (not before) y `exp` (expiration time).
  > 4. **Tipo de token (`token_use`)**: Que sea `'access'` y no `'id'`, ya que los id_tokens no deben utilizarse para autorizar APIs.
  > 5. **Aplicación cliente (`client_id`)**: Que haya sido emitido para el App Client de la tienda y no para otra aplicación."

---

### Pregunta 10: ¿Cómo se demuestran en vivo las 4 pruebas del Gateway? (IE10)
* **Fuente**: *Rúbrica Oficial (IE10), EP1-Caso-VidalStore.pdf (Página 10)*.
* **Respuesta y Comandos en Vivo**:
  1. **Sin token**:
     ```bash
     curl -i http://localhost:8080/v1/catalogo
     # Resultado esperado: HTTP/1.1 401 Unauthorized
     ```
  2. **Token alterado**:
     ```bash
     curl -i -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.tokenModificado" http://localhost:8080/v1/catalogo
     # Resultado esperado: HTTP/1.1 401 Unauthorized
     ```
  3. **Token de otra aplicación (App Client 2)**:
     ```bash
     curl -i -H "Authorization: Bearer <token_segundo_app_client>" http://localhost:8080/v1/catalogo
     # Resultado esperado: HTTP/1.1 401 Unauthorized
     ```
  4. **Token con rol insuficiente**:
     ```bash
     curl -i -X DELETE -H "Authorization: Bearer <token_usuario_jugador>" http://localhost:8080/v1/licencias/lic-001
     # Resultado esperado: HTTP/1.1 403 Forbidden
     ```
