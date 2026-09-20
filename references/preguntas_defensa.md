# Banco de Preguntas y Respuestas Modelo · Defensa Individual EP1

La defensa técnica individual representa el **60% de la nota final de la EP1**. El docente Cristian Calderón (`Umbingelelo`) realiza preguntas profundas sobre las decisiones de arquitectura, los tokens, los flujos criptográficos y las pruebas en vivo.

Este documento consolida:
1. **Las 8 preguntas oficiales y obligatorias de la guía oficial `Pulso.pdf` (Tramo 12.2)**.
2. **Las preguntas complementarias de rúbrica (IE1 a IE10), caso forense de VidalStore y discusiones de GitHub**.

---

## Bloque A: Las 8 Preguntas Oficiales de `Pulso.pdf` (§12.2)

Estas ocho preguntas son las que el profesor Cristian Calderón extrajo de los tramos de laboratorio para la defensa de la EP1.

### 1. ¿Por qué el BFF vuelve a validar el token si el gateway ya lo validó?
* **Referencia en Pulso**: *Tramo 5.2 (Página 37)*.
* **Respuesta Técnica**:
  > "Por tres razones de arquitectura y seguridad, ninguna de las cuales es desconfianza hacia el gateway:
  > 1. **Defensa en profundidad y Zero Trust**: Nadie garantiza que la petición provino exclusivamente del gateway. Si un servicio dentro de la red interna o un contenedor mal configurado habla directo al puerto del BFF, el BFF no puede asumir ciegamente que la petición 'viene de adentro'.
  > 2. **El BFF necesita los claims, no solo el veredicto**: El gateway responde un veredicto binario (pasa / no pasa), pero el BFF necesita saber quién es el usuario (`sub`) para filtrar sus datos en el service. Ya que tiene que abrir el token para leerlo, verificar la firma criptográfica con `jwtVerify` tiene un costo computacional casi nulo.
  > 3. **Múltiples canales de entrada futuros**: En la evolución del sistema (ej. consumo de mensajes desde una cola RabbitMQ o SQS), las peticiones no pasan por ningún gateway. Si la validación viviera solo en el borde, cualquier entrada alternativa quedaría desprotegida."
  * **Frase clave**: *«El gateway protege el perímetro; el BFF protege al servicio, incluso de dentro del perímetro.»*

---

### 2. ¿Qué decide un scope y qué decide un grupo, y por qué son cosas distintas?
* **Referencia en Pulso**: *L3 §7.1, Tramo 6 (Página 42)*.
* **Respuesta Técnica**:
  > "Son dos niveles de autorización completamente distintos:
  > * **El Scope (`vidalstore/catalogo.leer`) decide qué operaciones puede pedir la aplicación cliente** (el frontend web o móvil) ante la API. Limita el alcance técnico del cliente. Cualquier persona que entre por ese cliente recibirá un token con esos mismos scopes.
  > * **El Grupo (`cognito:groups`) decide qué rol tiene la persona humana** que está detrás del teclado (`jugadores`, `editores`, `administradores`).
  > El Gateway autoriza por **scope** en el perímetro; el BFF autoriza por **grupo** en las rutas protegidas (ej. revocar licencias con `@Roles('administradores')`)."

---

### 3. ¿Cuándo respondes 401 y cuándo 403?
* **Referencia en Pulso**: *Página 3, Tramo 9 (Pruebas 1 y 3)*.
* **Respuesta Técnica**:
  > "* **401 Unauthorized**: Significa **«No sé quién eres»**. Ocurre cuando no hay token, la firma criptográfica no cuadra, expiró (`exp`), no está vigente (`nbf`), o el token no es de tipo acceso (`token_use !== 'access'`).
  > * **403 Forbidden**: Significa **«Sé perfectamente quién eres, pero tu rol o permiso no te alcanza»**. Ocurre cuando el token es 100% válido, pero al usuario le falta el scope requerido o no pertenece al grupo necesario (`cognito:groups`).
  > *Confundir 401 con 403 crea un bucle infinito de login*, porque un 401 le dice al navegador 'vuelve a autenticarte', y el usuario volverá a ingresar las mismas credenciales fallando indefinidamente."

---

### 4. ¿Qué pregunta de autorización no puede responder un guard, y dónde va esa comprobación?
* **Referencia en Pulso**: *Tramo 7 (Páginas 45–46)*.
* **Respuesta Técnica**:
  > "La pregunta que ningún guard puede responder es: **«¿Este recurso le pertenece a este usuario?»**.
  > Un guard de NestJS solo inspecciona la cabecera HTTP, la URL y las anotaciones de la clase/método antes de ejecutar la lógica; **no ve los datos persistidos**.
  > Para saber si una licencia o préstamo le pertenece al usuario que llama, hay que mirar el registro en la base de datos. Por eso esa comprobación vive exclusivamente en la capa de **Service**, filtrando los registros por `usuarioSub === sub`.
  > Además, si el usuario no posee registros propios, el servicio responde **`200 OK` con un arreglo vacío `[]`**, jamás 403 ni 404 (evitando ataques de enumeración)."

---

### 5. ¿Por qué el `client_id` del access token no sirve para autorizar al usuario?
* **Referencia en Pulso**: *L3 §7.1, Tramo 5.3 (Página 39)*.
* **Respuesta Técnica**:
  > "Porque el `client_id` identifica a la **aplicación cliente** (el software SPA registrado en Cognito) y no al sujeto o usuario humano.
  > Solo sirve para validar que el token fue emitido específicamente para nuestro frontend de VidalStore y no para otra aplicación distinta dentro del mismo User Pool (Prueba 3 del Gateway). Autorizar privilegios de usuario usando el `client_id` asumiría erróneamente que todos los usuarios de la web tienen los mismos derechos."

---

### 6. ¿Qué gana el frontend con que exista el BFF? Da el número que mediste
* **Referencia en Pulso**: *Tramo 1.1, Tramo 4.3 (Páginas 10 y 35)*.
* **Respuesta Técnica**:
  > "El frontend gana tres beneficios fundamentales:
  > 1. **Una sola llamada HTTP en lugar de múltiples peticiones**: Reduce drásticamente la latencia en redes móviles.
  > 2. **Concurrencia en servidor**: Gracias a `Promise.all`, las llamadas internas a los microservicios se ejecutan en paralelo. En la medición de laboratorio con 300 ms de latencia por servicio, la llamada en serie tardaba ~600 ms ($300 + 300$), mientras que en paralelo tardó **~300 ms** ($\max(300, 300)$). Con 5 microservicios, en serie serían 1500 ms y en paralelo seguirían siendo ~300 ms.
  > 3. **Agregación $O(N)$ y Zero Fuga de Datos**: El cruce de datos se hace en servidor mediante un `Map` por ID, enviando al navegador un DTO que contiene exclusivamente lo que la vista necesita mostrar (evitando la descarga de catálogos completos con precios internos o stock confidencial accesibles en F12)."

---

### 7. Un usuario se registra solo y no puede entrar a nada. ¿Qué pasó y cómo lo resolviste?
* **Referencia en Pulso**: *Tramo 10 (Páginas 54–57)*.
* **Respuesta Técnica**:
  > "Ocurrió la **«trampa de Cognito»**: cuando un usuario se registra por autoservicio en Cognito Managed Login / Hosted UI, Cognito **no le asigna ningún grupo por omisión**. Por lo tanto, el claim `cognito:groups` viene vacío y el usuario recibe 403 Forbidden en todas las rutas protegidas.
  > Se resuelve de dos formas:
  > * **Salida A (Nivel de código en el Guard)**: Si el token no trae grupos, el backend asume en memoria el rol de menor privilegio (`jugadores`).
  > * **Salida B (Nivel de Infraestructura AWS)**: Un trigger Lambda de tipo *Post Confirmation* que captura el evento `PostConfirmation_ConfirmSignUp` y ejecuta `AdminAddUserToGroup` para asignarlo automáticamente a `jugadores`.
  > *En la defensa explicamos:* Implementamos el fallback seguro en el guard, pero en producción la solución correcta es el trigger Lambda para que el token ya viaje con el claim firmado desde AWS."

---

### 8. Al crear o revocar un recurso, ¿de dónde sacas el usuario, y por qué no del cuerpo de la petición?
* **Referencia en Pulso**: *Tramo 11.3 (Páginas 62–64)*.
* **Respuesta Técnica**:
  > "El identificador del usuario (`usuarioSub`) se obtiene **estrictamente de `req.user.sub`**, el cual fue extraído del token JWT verificado criptográficamente por el `JwtGuard`.
  > **Nunca se lee del cuerpo (`@Body()`)** porque lo que envía el cliente es manipulable. Si aceptáramos el `usuarioSub` o `userId` en el JSON de la petición, un usuario malicioso podría enviar el ID de otra persona y comprar o revocar licencias a nombre de un tercero (vulnerabilidad BOLA / OWASP API #1).
  > **Regla de oro de ingeniería:** *La identidad del que actúa nunca viene en el cuerpo de la petición; viene siempre del token firmado.*"

---

## Bloque B: Preguntas Complementarias del Caso VidalStore y Rúbrica EP1

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
