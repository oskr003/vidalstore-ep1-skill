# Banco de Preguntas y Respuestas Modelo · Defensa Individual EP1 y EP2

La defensa técnica individual representa el **60% de la nota final** (tanto en EP1 como en EP2). El docente Cristian Calderón (`Umbingelelo`) realiza preguntas profundas sobre las decisiones de arquitectura, los tokens, los flujos criptográficos, la mensajería asíncrona, Docker Compose, DLQ y las pruebas en vivo.

Este documento consolida:
1. **Las 8 preguntas oficiales de `Pulso.pdf` (Tramo 12.2)** (Bloque A).
2. **Las preguntas complementarias de rúbrica EP1 (IE1 a IE10)** (Bloques B, C, D y E).
3. **El guion oficial de defensa técnica de la clase D6**: reloj de 15 minutos, 5 flujos y método de 4 pasos.
4. **Las 15 preguntas oficiales de D8, L7A y L7 (Mensajería, Compose, DLQ y Persistencia)** (Bloque F).
5. **Las preguntas de defensa del Microservicio Administrador (Oscar · IE6, IE7, IE8, IE14, IE17, IE18)** (Bloque G).

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

---

## Bloque C: Guion Oficial de la Defensa Técnica · Clase D6 ("Git en Serio y Defender una Arquitectura")

La clase magistral D6 del profesor Cristian Calderón (`Umbingelelo`) define el estándar con el que se evalúa la presentación individual (60% de la nota final).

> [!IMPORTANT]
> **Criterio de Evaluación de D6:**
> No se mide si el estudiante memorizó conceptos teóricos generales. Se mide si **construyó el sistema**, y la diferencia se nota en que quien construyó habla de **su caso particular** (sus puertos, sus logs, las líneas de su código, los errores que rompió y arregló); quien no construyó solo puede dar respuestas genéricas de manual.

---

### 1. El Reloj de 15 Minutos de la Defensa

El turno dura exactamente **15 minutos cronometrados por grupo**, sean 2 o 3 integrantes:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Minuto 0 a 1   │ Todos los integrantes: declaran procesos corriendo y en qué puerto.   │
├────────────────┼───────────────────────────────────────────────────────────────────────┤
│ Minuto 1 a 7   │ Flujo A (un integrante) y Flujo B (otro integrante).                   │
│                │ *Nadie conduce dos flujos seguidos*.                                  │
├────────────────┼───────────────────────────────────────────────────────────────────────┤
│ Minuto 7 a 12  │ Flujos C y D, y 30 segundos del Flujo E (abrir el script de seed).    │
├────────────────┼───────────────────────────────────────────────────────────────────────┤
│ Minuto 12 a 14 │ Modificación señalada: una por integrante sobre código que NO escribió│
├────────────────┼───────────────────────────────────────────────────────────────────────┤
│ Minuto 14 a 15 │ Pregunta del botón COMPRAR: evaluación de fundamentación técnica.     │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

* **Repartición de preguntas**: En un grupo de 3 integrantes caen entre 5 y 6 preguntas por persona. **La mitad de las preguntas son sobre un flujo que condujo tu compañero**, por lo que «eso lo hizo el otro» equivale a un 0% en la pregunta.
* **Regla de oro de inicio**: Se debe entrar a la sala con el **sistema ya levantado y la sesión recién iniciada** (el token de Cognito expira en 1 hora; si vence en pleno flujo B se pierden 3 valiosos minutos). Si el sistema no levanta, solo hay 3 minutos de gracia para intentar levantarlo; luego la defensa sigue en frío sobre el código.

---

### 2. Las 5 Ventanas Obligatorias Abiertas al Entrar

Para no perder tiempo buscando archivos o levantando servicios, el grupo debe ingresar con estas 5 ventanas abiertas:

| Ventana | Qué debe estar mostrando en pantalla |
|---|---|
| **1. Terminal** | Procesos activos con sus puertos: Angular (`4200`), Gateway (`8080`), BFF (`3000`/`3001`), Microservicios (`3002`, `3003`, `3004`, `3005`). |
| **2. Navegador** | Aplicación con sesión iniciada, pestaña **Red (Network)** limpia lista para registrar peticiones, y pestaña **Application** mostrando el token en `sessionStorage`. |
| **3. Cliente REST / curl** | Dos tokens vigentes listos (jugador y administrador) para probar la misma ruta con `403` y `200`, más llamada directa al BFF sin token (`401`). |
| **4. Editor (VS Code)** | Pestañas del interceptor de Angular y de los guards del BFF (`JwtGuard`, `RolesGuard`) ya abiertas. |
| **5. Consola AWS Cognito** | User Pool con sus grupos (`jugadores`, `editores`, `administradores`), usuarios creados y los **dos app clients** configurados. *(Es lo único en la nube; todo lo demás corre en la máquina local)*. |

---

### 3. El Framework de Respuesta en 4 Pasos (1 Minuto por Parada)

Cada parada de un flujo dura aproximadamente 1 minuto. Para responder con rigor técnico y convencer al docente de que hubo autoría real, estructurar la respuesta en estos 4 pasos:

```text
1. QUÉ HICE               --> "Puse un BFF en NestJS entre Angular y los microservicios."
2. QUÉ PROBLEMA RESUELVE  --> "La vista necesitaba 4 llamadas y la autorización por grupo debía centralizarse."
3. QUÉ DESCARTÉ           --> "Podía hacer las 4 llamadas desde el frontend, pero lo descarté porque 
                              fugaría datos confidenciales y saturaría la red móvil."
4. CÓMO LO COMPRUEBO      --> "Acá está el Promise.all en el código y en la pestaña Red se ve 1 sola llamada."
```

* **Por qué importa el paso 3 («Qué descarté»)**: Es el que más pesa y el que casi nadie hace. Nombrar la alternativa técnica que rechazaste demuestra que hubo análisis de ingeniería y no una copia ciega de código.
* **Por qué importa el paso 4 («Cómo lo compruebo»)**: Saca al estudiante del relato teórico abstracto y lo devuelve a la pantalla, que es donde se califica la defensa.

---

### 4. Preguntas Parada por Parada y Señales de Alarma (El Guion Oficial de D6)

| Parada / Flujo | Pregunta Oficial del Docente | Señal de Alarma (Lo que NUNCA debes responder) | Respuesta Técnica Correcta |
|---|---|---|---|
| **A · Identidad** | *¿En qué grupo queda esta cuenta recién creada, y quién se lo asignó?* | «Yo se lo asigno después a mano en la consola de AWS». | Queda asignada automáticamente en `jugadores`. Se explica la trampa de Cognito (auto-registro deja `cognito:groups` vacío) y cómo se resolvió: por fallback en el guard (`roles = groups.length ? groups : ['jugadores']`) o mediante trigger Lambda Post-Confirmation. |
| **A · Identidad** | *¿Qué claim del token dice quién eres y cuál dice qué puedes hacer?* | Confundir el `scope` con el rol, o creer que el rol está en el claim `sub`. | `sub` (Subject) es el UUID inmutable que dice **quién eres**. `cognito:groups` indica **qué rol humano tienes** (`administradores`, `editores`, `jugadores`) y `scope` indica **qué operaciones tiene permitidas la aplicación cliente** ante el Resource Server. |
| **B · Lo Propio** | *¿A qué direcciones le habló el navegador en esta pantalla?* | Aparecen 2 o 3 direcciones distintas en la pestaña Red (ej: habla directo al BFF o microservicio). | El navegador habla a **UNA SOLA dirección**: `http://localhost:8080` (API Gateway). La lista blanca del interceptor tiene una sola entrada. Es el BFF quien orquesta por detrás con los microservicios. |
| **B · Lo Propio** | *¿De dónde sale el usuario cuyas licencias devuelves?* | Lo recibe por parámetro de ruta, query o body («pero igual está protegido con token»). | Sale exclusivamente del claim `sub` del JWT verificado en `req.user.sub`. Recibirlo por parámetro expondría la vulnerabilidad BOLA/IDOR (cualquiera cambiaría el ID y vería juegos ajenos). |
| **C · Rol Insuficiente** | *Con el token del jugador, demuéstrame que el control está en el servidor.* | Responde `401` en vez de `403`, o responde `200` y el alumno dice «es que en la interfaz el botón está oculto». | Se ejecuta la llamada `DELETE /v1/licencias/:id` con token de jugador vía `curl` o cliente REST. El servidor backend responde **`403 Forbidden`** porque el `RolesGuard` cortó la ejecución. La seguridad no depende del botón en Angular. |
| **D · Por Detrás** | *Llama al BFF y al microservicio directo en su puerto, sin token. ¿Qué responden y por qué?* | Responde `200 OK` (demuestra que la capa interna está desprotegida). | Responde **`401 Unauthorized`**. Por defensa en profundidad y Zero Trust, el BFF y microservicios no asumen que la petición viene del gateway; si no hay token firmado, se cierran. |
| **D · Por Detrás** | *Cambia un carácter del token. ¿Qué pasa y quién emite ese 401?* | El estudiante no sabe qué capa lo rechazó ni contra qué se verificó la firma. | Responde **`401 Unauthorized`**. Lo emite el Gateway porque la firma criptográfica RSA falló al verificarse contra la clave pública del JWKS de Cognito (`/.well-known/jwks.json`). |
| **D · Por Detrás** | *¿Qué origen acepta tu CORS, y qué pasa si te llaman desde otro?* | `origin: *` («para que funcionara»), o creer que el CORS es un mecanismo de control de acceso a la API. | Acepta exclusivamente `http://localhost:4200`. Si se llama desde otro origen en navegador, el navegador bloquea la respuesta. Si se llama con `curl`, la llamada pasa (CORS es política del navegador, la autenticación por token es el control real). |
| **E · Origen** | *¿De dónde salieron estos juegos, y qué pasa si corro el seed en una máquina limpia?* | «Los escribí a mano», o el archivo `catalogo.json` existe pero no hay script de seed. | Provienen de una API externa real (FreeToGame / RAWG). Si se borra `catalogo.json` y se corre `npm run seed`, el script consume la API externa, mapea el DTO y regenera el archivo de persistencia idéntico. |
| **Transversal** | *¿Qué de todo esto está en la nube y qué no?* | Cree que el API Gateway es de AWS, o no sabe qué levantó él mismo en su máquina. | **Lo ÚNICO en la nube es el User Pool de AWS Cognito**. El Frontend Angular, el Gateway NestJS, el BFF NestJS y los Microservicios corren 100% en la máquina local. |
| **Transversal** | *Si mañana entra un quinto microservicio, ¿qué tienes que tocar?* | «Habría que agregar la URL nueva en el Angular». | Se toca el BFF (para agregar la llamada interna y mapear el DTO agregado) y opcionalmente el Gateway si expone una nueva ruta `/v1/`. **En Angular NO se toca ninguna URL**, porque Angular solo conoce al Gateway. |

---

### 5. Análisis Modelo de la Parada B3 (La Más Discriminante de la Defensa)

**Pregunta del Docente:** *«¿De dónde sale el usuario cuyas licencias devuelves?»*

**Respuesta Técnica Modelo (Aplicando los 4 Pasos):**
> *«Sale del claim `sub`. Te muestro en el código: acá en el BFF el `JwtGuard` ya verificó el token y dejó el payload en `request.user`; en esta línea tomo `req.user.sub` y se lo paso al microservicio de biblioteca.*
> 
> *Fíjate que la ruta `/v1/biblioteca` no tiene ningún parámetro de usuario, a propósito: si recibiera el ID por query o por body, cualquiera con un token válido podría pedir la biblioteca de otro usuario cambiando un número (vulnerabilidad BOLA / IDOR).*
> 
> *De hecho, al principio me pasó al revés: la primera versión la hice con `/v1/biblioteca/:usuarioId` porque era cómodo para probar con Postman. Lo dejé así hasta que entré con dos cuentas distintas en Cognito, le pasé el ID del otro usuario y me devolvió sus juegos. Ahí entendí el problema y lo cambié.*
> 
> *Y te lo demuestro en vivo con estas dos pestañas de curl: mismo endpoint, token de la cuenta A $\rightarrow$ devuelve estos 3 juegos; token de la cuenta B $\rightarrow$ devuelve estos 2 juegos. No cambié nada en la URL ni en los parámetros, solo el token.»*

* **Extracto de Código Clave** (`vidalstore-backend/src/bff/biblioteca/bff-biblioteca.controller.ts:L20-L31`):
  ```typescript
  @Get()
  @UseGuards(BffAuthGuard)
  async obtenerBiblioteca(
    @CurrentUser('sub') usuarioSub: string,
    @Req() req?: any,
  ) {
    if (!usuarioSub) {
      throw new UnauthorizedException('No se pudo resolver la identidad a partir del claim sub.');
    }
    // Llama al microservicio con el sub resuelto criptográficamente:
    const [licencias, catalogo] = await Promise.all([...]);
  ```
* **Comando de Prueba en Vivo (Terminal)**:
  ```bash
  # Probar con dos tokens distintos: cada uno devuelve SOLO sus juegos
  curl -s -H "Authorization: Bearer $TOKEN_USUARIO_A" http://localhost:8080/v1/biblioteca | jq '.[].juego.titulo'
  curl -s -H "Authorization: Bearer $TOKEN_USUARIO_B" http://localhost:8080/v1/biblioteca | jq '.[].juego.titulo'
  ```

---

### 6. La Modificación Señalada (Minuto 12 a 14)

En este bloque de 2 minutos, el docente pide a cada integrante una modificación puntual sobre un frente del proyecto que **no construyó él**.

* **Cómo se rinde**: **No se programa en vivo**. Se abre el archivo en el editor, se sitúa el cursor en la línea exacta y se explica qué se escribiría y qué efecto tendría en el sistema.
* **Casos Clásicos con Código y Comprobación**:
  1. *«¿Dónde y cómo agregarías una ruta que solo puedan consultar los administradores?»*
     * **Código**: En `bff-licencias.controller.ts` agregar `@UseGuards(BffAuthGuard, GroupsGuard)` y `@RequireGroups('administradores')`. En `gateway.controller.ts` mapear la ruta proxy con el mismo decorador.
     * **Comando**: `curl -i -H "Authorization: Bearer $TOKEN_JUGADOR" http://localhost:8080/v1/admin/licencias` $\rightarrow$ `403 Forbidden`.
  2. *«¿Qué pasa y qué se rompe si comento esta línea en el interceptor de Angular?»*
     * **Código**: En `src/app/auth/token.interceptor.ts` comentar `setHeaders['Authorization'] = ...`.
     * **Comando**: Angular compila bien, pero las peticiones salen limpias: `curl -i http://localhost:8080/v1/catalogo` $\rightarrow$ `HTTP/1.1 401 Unauthorized` inmediato en Gateway.
  3. *«¿Qué sucedería si configuro en el Gateway el client_id del App Client 2?»*
     * **Código**: En `vidalstore-gateway/.env` cambiar `COGNITO_CLIENT_ID`. En `auth.service.ts` fallará `if (expectedClientId && cognitoPayload.client_id !== expectedClientId)`.
     * **Comando**: Al llamar con token de SPA: `HTTP/1.1 401 Unauthorized` ("Client ID no autorizado").
  4. *«¿Qué pasa si quitas un microservicio del Promise.all en el BFF?»*
     * **Código**: En `bff-biblioteca.controller.ts` quitar `this.bffHttpService.request(catalogoUrl)`.
     * **Comando**: La biblioteca responde licencias pero `juego: null`; la interfaz queda sin portadas ni títulos.

---

### 7. La Pregunta del Botón COMPRAR (Minuto 14 a 15)

**Pregunta del Docente:** *«Si el usuario ya tiene la licencia de un juego, ¿qué debe hacer el botón COMPRAR en la interfaz? ¿Ocultarse, deshabilitarse, o permitir el clic y que el servidor responda con error?»*

* **Respuesta Técnica**: *«En la UI lo deshabilito por experiencia de usuario, pero la regla de negocio y la seguridad NUNCA se delegan al cliente: el backend siempre valida idempotencia y corta con 409 Conflict si llega la petición.»*
* **Extracto de Código Clave** (`vidalstore-backend/src/microservicios/biblioteca/biblioteca.service.ts:L49-L54`):
  ```typescript
  const licenciaExistente = this.buscarLicenciaPorUsuarioYJuego(usuarioSub, licenciaDatos.juegoId);
  if (licenciaExistente) {
    throw new ConflictException(
      `El usuario ya posee una licencia activa para el juego con ID '${licenciaDatos.juegoId}'.`
    );
  }
  ```
* **Comando de Prueba en Vivo (Terminal)**:
  ```bash
  # Primera compra: 201 Created
  curl -i -X POST http://localhost:8080/v1/compras -H "Authorization: Bearer $TOKEN_JUGADOR" -H "Content-Type: application/json" -d '{"juegoId":"1"}'
  # Segunda compra del mismo juego: 409 Conflict
  curl -i -X POST http://localhost:8080/v1/compras -H "Authorization: Bearer $TOKEN_JUGADOR" -H "Content-Type: application/json" -d '{"juegoId":"1"}'
  ```

---

### 8. Preparación: La Bitácora de Errores Propios

1. **Error de App Client con Secreto**: SPA pública en Angular no puede almacenar secretos $\rightarrow$ recrear App Client sin secret.
2. **Error de Token Expirado en Pruebas**: Token expiró a los 60 minutos (`exp`) $\rightarrow$ 401 Unauthorized en curl.
3. **Error de Trampa de Cognito**: Auto-registro deja `cognito:groups` vacío $\rightarrow$ fallback a `jugadores` en `groups.guard.ts`.
4. **Error de CORS en Backend**: Configurar CORS en BFF $\rightarrow$ comprender que CORS solo aplica a navegadores en el Gateway.
5. **Error de Whitelist en Interceptor**: Token Bearer filtrado a Google Fonts $\rightarrow$ whitelist estricta `req.url.startsWith('http://localhost:8080')`.

---

## Bloque D: Reglas de Negocio, Modelo de Datos e Identificadores (UUID vs Sub vs Integer)

---

### D.1. ¿Cómo se gestionaron y modelaron las licencias en el sistema? (Ciclo de Vida y Dueño del Agregado)

* **Pregunta del Docente**: *«Muestra el modelo de licencias. ¿Cómo se gestionan, quién es el dueño de esos datos, cómo nacen y cómo se relacionan con los juegos y usuarios?»*
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: Modelé la entidad `Licencia` con `id` (UUID v4), `juegoId`, `usuarioSub` (claim `sub`), `fechaAdquisicion`, `codigoCanje`, `estadoPago: 'aprobado'` y `precioPagado`. Biblioteca es el único dueño (*Single Source of Truth*), respaldado en `MemoryStorageService` y persistido en `data/licencias.json`.
  2. **Qué problema resuelve**: Desacopla la transacción de compra de la titularidad digital permanente. Compras valida el pago y delega por HTTP interno a Biblioteca la emisión de la licencia.
  3. **Qué descarté**: Descarté embeber licencias dentro del usuario en Cognito y descarté que Catálogo gestione compras.
  4. **Cómo lo compruebo**: Mostrando `crearLicencia()` en `biblioteca.service.ts` y verificando `data/licencias.json`.
* **Extracto de Código Clave** (`vidalstore-backend/src/models/licencia.model.ts`):
  ```typescript
  export interface Licencia {
    id: string; // UUID v4 único
    juegoId: string; // ID foráneo del catálogo
    usuarioSub: string; // Claim 'sub' inmutable de Cognito
    fechaAdquisicion: string; // ISO 8601
    codigoCanje?: string; // Formato VS-XXXXXXXXXXXXXXXX
    estadoPago?: 'aprobado' | 'rechazado';
    precioPagado?: number;
  }
  ```

---

### D.2. ¿Por qué se usa ese tipo de ID para el usuario (`sub` UUID) y por qué NO usar su email o su username?

* **Pregunta del Docente**: *«¿Por qué en las licencias guardas `usuarioSub` en lugar del correo electrónico (`email`) o el nombre de usuario (`username`)? ¿Qué ganaron con esa decisión?»*
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: Utilicé como clave foránea el claim `sub` (Subject) emitido por AWS Cognito (UUID v4 inmutable de 36 caracteres), extraído de `req.user.sub`.
  2. **Qué problema resuelve**:
     * **Inmutabilidad Absoluta**: El email o username pueden cambiar; el `sub` es inmutable de por vida (no se pierden compras).
     * **Privacidad por Diseño (Zero PII Leakage / GDPR)**: El `sub` es un UUID opaco sin datos personales. Microservicios y logs no filtran correos ni RUTs.
     * **Desacoplamiento del Identity Provider**: Si cambiamos Cognito por Auth0 o Keycloak, el modelo no cambia.
  3. **Qué descarté**: Descarté email o username como claves primarias, y descarté IDs locales autoincrementales de usuario.
  4. **Cómo lo compruebo**: Comparando el JWT decodificado con `data/licencias.json`.
* **Extracto de Código Clave** (`vidalstore-backend/src/microservicios/biblioteca/biblioteca.service.ts:L64-L66`):
  ```typescript
  buscarLicenciasPorUsuario(usuarioSub: string): Licencia[] {
    return this.storageService.buscarLicenciasPorUsuarioSub(usuarioSub);
  }
  ```

---

### D.3. ¿Por qué la licencia usa un UUID v4 (`randomUUID`) en lugar de un entero auto-incremental (1, 2, 3...)?

* **Pregunta del Docente**: *«¿Por qué el ID de la licencia es un UUID (`randomUUID()`) y no un número secuencial simple como 1, 2, 3...?»*
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: Cada nueva licencia recibe `id: randomUUID()`, generado con `node:crypto`.
  2. **Qué problema resuelve**:
     * **Sistemas Distribuidos sin Cuello de Botella Central**: En microservicios, los autoincrementales exigen base de datos centralizada con bloqueos. El UUID v4 se genera descentralizado en cualquier nodo con colisión despreciable ($2^{122}$).
     * **Confidencialidad y Anti-Scraping**: Evita que competidores deduzcan ventas diarias y que atacantes enumeren URLs secuenciales (`/licencias/103`).
  3. **Qué descarté**: Descarté secuencias numéricas (`id: ++contador`).
  4. **Cómo lo compruebo**: Generando compras consecutivas y revisando los IDs únicos resultantes.
* **Extracto de Código Clave** (`vidalstore-backend/src/storage/memory-storage.service.ts:L202-L206`):
  ```typescript
  const nuevaLicencia: Licencia = {
    id: randomUUID(), // UUID v4 RFC 4122 (128 bits, sin colisión distribuida)
    juegoId: datos.juegoId,
    usuarioSub: datos.usuarioSub,
    fechaAdquisicion: new Date().toISOString(),
  ```

---

### D.4. ¿Por qué los juegos del catálogo tienen un ID distinto (números como `"452"`, `"540"`) que las licencias (UUIDs)? ¿Cómo conviven ambos?

* **Pregunta del Docente**: *«Veo que en el catálogo los IDs son números como "452", pero las licencias son UUIDs. ¿Por qué esa diferencia y cómo conviven ambos?»*
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: Catálogo tipa `id: string` con valores numéricos seriales de la API FreeToGame (`seed.ts`). Licencia guarda `juegoId: string` como clave foránea.
  2. **Qué problema resuelve**: Respeta la separación entre catálogo de publisher externo y transacciones internas de la plataforma. Mantener el ID original de FreeToGame preserva la trazabilidad externa.
  3. **Qué descarté**: Descarté sobreescribir los IDs de FreeToGame con nuevos UUIDs en el seed.
  4. **Cómo lo compruebo**: Comparando `data/catalogo.json` con `data/licencias.json`.
* **Extracto de Código Clave** (`vidalstore-backend/data/seed.ts` vs `licencia.model.ts`):
  ```typescript
  // seed.ts: FreeToGame entrega id numérico, se estandariza a string:
  id: String(juegoExterno.id),
  // licencia.model.ts: almacena juegoId tipado como string:
  juegoId: string,
  ```

---

### D.5. ¿Cómo se garantiza la unicidad e idempotencia de una licencia? ¿Qué regla de negocio impide duplicar compras?

* **Pregunta del Docente**: *«¿Qué regla de negocio impide que un usuario compre dos veces el mismo juego y cómo está implementada en el código?»*
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: En `biblioteca.service.ts`, `crearLicencia()` ejecuta `buscarLicenciaPorUsuarioYJuego(usuarioSub, juegoId)`. Si existe, arroja `ConflictException` (HTTP 409 Conflict).
  2. **Qué problema resuelve**: Comercialización de software digital: la posesión de una licencia digital es unívoca. Previene cobros dobles por clics repetidos o reintentos de red.
  3. **Qué descarté**: Descarté delegar la regla a la interfaz gráfica y descarté responder `200 OK` cobrando dos veces.
  4. **Cómo lo compruebo**: Disparando dos `POST /v1/compras` con el mismo `juegoId`.
* **Extracto de Código Clave** (`vidalstore-backend/src/microservicios/biblioteca/biblioteca.service.ts:L49-L54`):
  ```typescript
  const licenciaExistente = this.buscarLicenciaPorUsuarioYJuego(usuarioSub, licenciaDatos.juegoId);
  if (licenciaExistente) {
    throw new ConflictException(
      `El usuario ya posee una licencia activa para el juego con ID '${licenciaDatos.juegoId}'.`
    );
  }
  ```
* **Comando de Prueba en Vivo (Terminal)**:
  ```bash
  # Primera llamada -> 201 Created
  curl -i -X POST http://localhost:8080/v1/compras -H "Authorization: Bearer $TOKEN_JUGADOR" -H "Content-Type: application/json" -d '{"juegoId":"1"}'
  # Segunda llamada idéntica -> 409 Conflict
  curl -i -X POST http://localhost:8080/v1/compras -H "Authorization: Bearer $TOKEN_JUGADOR" -H "Content-Type: application/json" -d '{"juegoId":"1"}'
  ```

---

### D.6. ¿Qué es y cómo se genera el `codigoCanje` (`VS-XXXXXXXXXXXXXXXX`)?

* **Pregunta del Docente**: *«¿Para qué sirve el campo `codigoCanje` en la licencia y con qué criterio se genera?»*
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: Al emitir la licencia en `biblioteca.service.ts`:
     ```typescript
     codigoCanje: `VS-${randomUUID().replaceAll('-', '').slice(0, 16).toUpperCase()}`
     ```
  2. **Qué problema resuelve**: Separa la titularidad legal en VidalStore de la clave de activación (CD-Key) requerida por el jugador para canjear en Steam o Epic Games.
  3. **Qué descarté**: Descarté `Math.random()` (predecible). Usamos `randomUUID()` con entropía criptográfica CSPRNG.
  4. **Cómo lo compruebo**: Inspeccionando las licencias devueltas por `/v1/biblioteca`.
* **Extracto de Código Clave** (`vidalstore-backend/src/microservicios/biblioteca/biblioteca.service.ts:L59`):
  ```typescript
  return this.storageService.agregarLicencia({
    ...licenciaDatos,
    usuarioSub,
    codigoCanje: `VS-${randomUUID().replaceAll('-', '').slice(0, 16).toUpperCase()}`,
    estadoPago: 'aprobado',
  });
  ```

---

### D.7. ¿Cómo se previene el fraude IDOR / BOLA al consultar la biblioteca?

* **Pregunta del Docente**: *«Si quiero consultar las licencias de otro usuario con mi token legítimo, ¿dónde me frena el sistema?»*
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: La ruta es `/v1/biblioteca` (sin parámetros de usuario). El backend extrae el usuario de `req.user.sub` firmado por Cognito.
  2. **Qué problema resuelve**: Mitiga la vulnerabilidad #1 OWASP API: BOLA/IDOR. Nadie puede alterar un parámetro en URL para espiar bibliotecas ajenas.
  3. **Qué descarté**: Descarté confiar en `@Param('usuarioId')` o `@Body('usuarioSub')`.
  4. **Cómo lo compruebo**: Probando con dos tokens distintos (Parada B.3).
* **Extracto de Código Clave** (`vidalstore-backend/src/bff/biblioteca/bff-biblioteca.controller.ts:L22-L24`):
  ```typescript
  @Get()
  @UseGuards(BffAuthGuard)
  async obtenerBiblioteca(@CurrentUser('sub') usuarioSub: string) {
    // El sub viene del token JWT verificado por el guard, NUNCA del cliente
    return this.bffHttpService.request(this.bffHttpService.bibliotecaUrl, 'GET', '/v1/biblioteca');
  ```

---

### D.8. ¿Cómo interactúan los roles de negocio (`administradores` vs `jugadores`) con las licencias?

* **Pregunta del Docente**: *«¿Cómo manejan la administración y revocación de licencias según el rol del usuario?»*
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: Rutas `/v1/licencias` y `DELETE /v1/licencias/:id` protegidas con `@RequireGroups('administradores')` y `GroupsGuard`.
  2. **Qué problema resuelve**: Permite al personal administrativo auditar y revocar licencias sin permitir a jugadores invocar estas funciones.
  3. **Qué descarté**: Descarté confiar en banderas del cliente como `isAdmin: true`.
  4. **Cómo lo compruebo**: Jugador recibe 403 Forbidden; Administrador recibe 200 OK.
* **Extracto de Código Clave** (`vidalstore-gateway/src/gateway.controller.ts:L83-L86`):
  ```typescript
  @Delete('licencias/:licenciaId')
  @UseGuards(AuthGuard, GroupsGuard)
  @RequireGroups('administradores')
  async revocarLicencia(@Param('licenciaId') licenciaId: string, @Request() req: ExpressRequest) {
    return this.gatewayService.forward('DELETE', `/v1/licencias/${licenciaId}`, req);
  }
  ```
* **Comando de Prueba en Vivo (Terminal)**:
  ```bash
  # Jugador intentando revocar: 403 Forbidden
  curl -i -X DELETE -H "Authorization: Bearer $TOKEN_JUGADOR" http://localhost:8080/v1/licencias/xyz-123
  # Administrador revoca con éxito: 200 OK
  curl -i -X DELETE -H "Authorization: Bearer $TOKEN_ADMIN" http://localhost:8080/v1/licencias/xyz-123
  ```

---

## Bloque E: Preguntas Oficiales de Mensajería, Docker y RabbitMQ (D7, L6 y L6A)

Este bloque cubre las preguntas técnicas de los **Puntos de Control de Pulso L6**, las clases magistrales **D7 ("Docker de verdad y por qué una cola")** y **L6A ("Clase pre-laboratorio y notas de orador")**, evaluadas en la defensa individual.

---

### E.1. ¿Por qué el `-v` solo no alcanzó, y qué agregó el `--hostname` al contenedor de RabbitMQ?
* **Fuente**: *Pulso L6 Punto de control 1 (Página 18) y D7 Slide 11*.
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: Ejecutamos el contenedor con `--hostname rabbit1 -v datos-rabbit:/var/lib/rabbitmq`.
  2. **Qué problema resuelve**: Garantiza la persistencia real de colas y usuarios al recrear el contenedor. RabbitMQ almacena su base de datos interna Mnesia en un directorio nombrado según el nodo Erlang: `/var/lib/rabbitmq/mnesia/rabbit@<hostname>`.
  3. **Qué descarté**: Descarté correr `docker run` sin `--hostname`. Si se omite, Docker asigna el Container ID aleatorio como hostname. Al destruir y recrear el contenedor, nace un nodo Erlang nuevo (`rabbit@nuevo_id`) con la base vacía, ignorando el directorio anterior aunque el volumen esté montado.
  4. **Cómo lo compruebo**: Ejecutando `docker exec rabbit1 rabbitmqctl eval "node()."`, el cual responde invariablemente `rabbit@rabbit1`, y comprobando con `list_queues` que la cola sobrevive tras `docker rm -f rabbit1` y recrear.

---

### E.2. ¿Por qué la columna de fecha en PostgreSQL es `timestamptz` y no `timestamp`?
* **Fuente**: *Pulso L6 Punto de control 2 (Página 30) y L6 Tramo 2.6*.
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: Definimos la columna de auditoría como `recibido_en timestamptz NOT NULL DEFAULT now()`.
  2. **Qué problema resuelve**: Elimina la ambigüedad temporal en arquitecturas distribuidas. `timestamptz` (`timestamp with time zone`) convierte y almacena el instante temporal en UTC normalizado en el motor de base de datos, y lo proyecta a la zona horaria del cliente al consultar.
  3. **Qué descarté**: Descarté `timestamp` sin zona horaria. Si los microservicios corren en servidores en Virginia (UTC-4) o contenedores en UTC y el cliente consulta desde Santiago (UTC-3 o UTC-4 según horario de verano), un `timestamp` plano almacena números descontextualizados, haciendo imposible ordenar cronológicamente eventos concurrentes.
  4. **Cómo lo compruebo**: Ejecutando `\d mensajes_taller` en `psql` para constatar el tipo `timestamp with time zone`.

---

### E.3. ¿Qué pasaría si cambiaras `noAck: false` por `noAck: true` y tu worker se cayera justo después de recibir un mensaje?
* **Fuente**: *Pulso L6 Punto de control 3 (Página 43) y L6A Slide 4*.
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: Configuramos el consumidor con `{ noAck: false }` y ejecutamos `canal.ack(mensaje)` explícito únicamente tras procesar el mensaje con éxito.
  2. **Qué problema resuelve**: Previene la pérdida definitiva de mensajes ante fallas del worker. Con `noAck: false`, el mensaje queda en estado `Unacked` en RabbitMQ; si el proceso se cae o pierde la conexión TCP sin enviar el ack, RabbitMQ lo reencola automáticamente para que otro consumidor lo procese.
  3. **Qué descarté**: Descarté `noAck: true` (auto-ack). Con auto-ack, RabbitMQ considera entregado el mensaje y lo elimina de la cola en el microsegundo exacto en que sale por el socket de red hacia el worker. Si el proceso muere antes de escribir en disco o base de datos, el mensaje se destruye para siempre sin aviso ni reintento.
  4. **Cómo lo compruebo**: Mostrando en el código del consumidor la llamada `this.canal.ack(mensaje)` dentro del bloque `try/catch`.

---

### E.4. ¿Por qué el evento se publica después de que el microservicio guarda el registro, y no antes? ¿Por qué no publica el BFF?
* **Fuente**: *Pulso L6 Punto de control 4 (Página 56) y L6A Slides 6–7*.
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: En el microservicio, el orden estricto dentro del endpoint es: 1. Verificar token y extraer `sub` -> 2. Persistir en base de datos -> 3. Publicar evento en el exchange -> 4. Responder `201 Created`. El BFF solo reenvía la cabecera `Authorization` y jamás publica.
  2. **Qué problema resuelve**: Garantiza la veracidad del sistema. Un evento afirma un hecho consumado que ya ocurrió en el pasado (`compra.realizada`, `prestamo.creado`). Si publicáramos antes de guardar y la base de datos fallara (por constraints, desconexión o disco lleno), se habría anunciado un evento falso al broker: otros microservicios habrían mandado correos o descontado saldo por una operación inexistente, sin posibilidad de "desavisar".
  3. **Qué descarté**: Descarté publicar desde el BFF. El BFF no es dueño de la transacción ni de la persistencia. Si el microservicio guardara y el BFF publicara, cualquier caída de red entre ambos dejaría una compra realizada sin que ningún evento sea emitido jamás.
  4. **Cómo lo compruebo**: Mostrando que si el worker está apagado, el microservicio responde `201` de inmediato y el mensaje queda esperando en la cola de RabbitMQ (`list_queues`).

---

### E.5. ¿Por qué `libro.agotado` llegó a una sola cola, si se publicó en el mismo exchange que `prestamo.creado`?
* **Fuente**: *Pulso L6 Punto de control 5 (Página 63) y L6A Slide 9*.
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: Declaramos el exchange `biblioteca.eventos` (o `vidalstore.eventos`) de tipo `topic`, con bindings diferenciados: `prestamo.*` para notificaciones y `#` para auditoría.
  2. **Qué problema resuelve**: Permite el desacoplamiento y la discriminación precisa de eventos según los intereses de cada consumidor.
  3. **Qué descarté**: Descarté exchanges de tipo `fanout` (que copian todo a todas las colas sin filtrar) o `direct` (que no admiten comodines).
  4. **Cómo lo compruebo**: En el exchange topic, el asterisco `*` exige **exactamente una palabra**: `prestamo.creado` calza con `prestamo.*` (llega a notificaciones) y calza con `#` (llega a auditoría), despertando a dos colas. En cambio, `libro.agotado` no empieza con `prestamo`, por lo que el exchange lo descarta para notificaciones y solo lo entrega a la cola de auditoría gracias a `#` (que acepta cero o más palabras).

---

### E.6. ¿Qué NO resuelve una cola de mensajería? Cita las tres limitaciones de D7 y explica por qué encolar no acelera
* **Fuente**: *Clase magistral D7 Slide 13*.
* **Respuesta Técnica Modelo**:
  > "Una cola de mensajería es un buffer desacoplador, pero tiene tres limitaciones fundamentales:
  > 1. **NO acelera el trabajo**: Mueve la espera fuera de la petición del usuario, pero el trabajo de fondo sigue tomando exactamente el mismo tiempo. Acelerar es responsabilidad de los **consumidores paralelos** (múltiples workers leyendo de la misma cola).
  > 2. **NO sirve si necesitas la respuesta ahora**: Si la vista del frontend necesita saber inmediatamente el ID o el estado del nuevo recurso, encolar no ayuda porque el resultado aún no existe.
  > 3. **NO arregla operaciones que fallan sin aviso**: Al contrario, el fallo ahora ocurre lejos de la vista del usuario. Si un envío de correo falla encolado, falla en silencio y nadie se entera a menos que se implementen Dead Letter Queues (DLQ) y monitoreo activo."

---

### E.7. La regla del botón COMPRAR: ¿Cómo decides si una operación va sincrónica o encolada?
* **Fuente**: *Clase magistral D7 Slide 14*.
* **Respuesta Técnica Modelo**:
  > "Aplicamos el **criterio de necesidad de resultado**: *¿El usuario necesita el resultado de esta operación para poder seguir?*
  > * **Va sincrónico (HTTP REST)**: Cuando el usuario requiere confirmación inmediata para continuar su flujo. Crear la licencia al pulsar 'COMPRAR' va sincrónico porque el jugador necesita saber que ya posee el juego y verlo en su biblioteca; la respuesta es un **`201 Created`** que certifica que el recurso ya existe.
  > * **Va encolado (AMQP / RabbitMQ)**: Todo lo que no detiene el flujo del usuario. Mandar el correo con la boleta, actualizar estadísticas de popularidad del juego o notificar a los amigos son tareas en segundo plano que pueden tardar segundos o minutos sin degradar la experiencia de compra."

---

### E.8. ¿Por qué un contenedor queda en estado `Created` con 0 líneas en `docker logs` cuando hay conflicto de puerto?
* **Fuente**: *Clase magistral D7 Slides 8–9*.
* **Respuesta Técnica Modelo**:
  > "Ocurre cuando Docker no puede enlazar el puerto solicitado del anfitrión (ej. `Bind for 0.0.0.0:5672 failed: port is already allocated`) porque otro contenedor o proceso del sistema ya lo está ocupando.
  > Docker crea la capa del contenedor (por eso aparece en `docker ps -a` como `Created`), pero aborta antes de invocar el proceso principal.
  > Como el proceso interno jamás llegó a ejecutarse, nunca escribió nada en `stdout` ni `stderr`. Por lo tanto, `docker logs` devuelve **cero líneas**. La causa del error no está en el log del contenedor, sino en la salida del comando `docker run` en la terminal (código de salida 125)."

---

### E.9. ¿Por qué en RabbitMQ el productor nunca publica directamente a una cola?
* **Fuente**: *Clase magistral D7 Slide 16*.
* **Respuesta Técnica Modelo**:
  > "Porque en la arquitectura AMQP existe un desacoplamiento estricto entre productores y consumidores:
  > El productor publica únicamente a un **Exchange** acompañando el payload de una **Routing Key** (etiqueta que describe qué hecho ocurrió).
  > El productor no sabe, no le interesa y no debe saber cuántas colas existen ni quiénes las leen. El enrutamiento hacia una, varias o ninguna cola lo decide exclusivamente el Exchange en base a las reglas de **Binding** declaradas por los consumidores. Si mañana agregamos un nuevo consumidor de analítica o multas, se crea una cola y un binding sin tocar ni redesplegar una sola línea del productor."

---

### E.10. En la topología de la EP2, ¿qué elementos son estrictamente fijos y qué decide el grupo?
* **Fuente**: *L6A Slides 11–13*.
* **Respuesta Técnica Modelo**:
  > "* **Estrictamente Fijo por Normativa**:
  >   1. Los 3 exchanges y sus tipos: `vidalstore.eventos` (`topic`), `vidalstore.comandos` (`direct`) y `vidalstore.dlx` (`direct`).
  >   2. Las 4 routing keys: `compra.realizada`, `licencia.revocada`, `juego.publicado` y `correo.enviar`.
  >   3. El binding de auditoría con `#` (cero o más palabras).
  >   4. El binding de correos con `correo.enviar`.
  >   5. La existencia de una DLQ por cada cola de trabajo (total 6 colas).
  > * **Decisiones Autónomas del Grupo (a justificar en la defensa)**:
  >   1. Los nombres de las seis colas (ej: `cola-avisos`, `cola-auditoria`, `cola-correos`, etc.).
  >   2. El patrón de binding exacto de la cola de avisos (ej: `compra.*`).
  >   3. El prefetch de los consumidores (Semana 9).
  >   4. Los valores de las políticas de TTL y longitud en RabbitMQ (Semana 10)."

---

## Bloque F: Preguntas Oficiales de Compose, Ack, DLQ, Idempotencia y Persistencia (D8, L7A y L7)

Este bloque consolida las preguntas de defensa individual de la **Semana 9**, extraídas directamente de los cinco Puntos de Control de L7, la clase D8 ("Compose, ack, durabilidad y fallos") y el pre-laboratorio L7A.

---

### F.1. ¿Por qué `depends_on` solo no alcanza y hace falta un `healthcheck` con `condition: service_healthy`?
* **Fuente**: *D8 Slides 15–18, L7A Slide 12 y L7 Tramo 1.6*.
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: En `compose.yml`, configuramos healthchecks con `pg_isready -U biblioteca -d biblioteca` en Postgres y `rabbitmq-diagnostics -q check_port_connectivity` en RabbitMQ, y atamos los servicios dependientes con `depends_on: { <servicio>: { condition: service_healthy } }`.
  2. **Qué problema resuelve**: Previene caídas por carrera al arrancar. `depends_on` básico solo ordena el inicio de los contenedores; apenas el contenedor de RabbitMQ pasa a `running`, Compose asume cumplida la dependencia. Sin embargo, el motor Erlang tarda de 5 a 10 segundos en abrir sus sockets. Sin la condición de salud, el worker o la API arrancan, intentan conectarse de inmediato, reciben `ECONNREFUSED` y mueren.
  3. **Qué descarté**: Descarté poner retrasos artificiales con `sleep` o suponer que el contenedor está listo solo porque encendió.
  4. **Cómo lo compruebo**: Mostrando en `compose.yml` el bloque `healthcheck` y verificando con `docker compose ps` que los servicios pasan por el estado `(health: starting)` hasta alcanzar `(healthy)` antes de que el worker inicie.

---

### F.2. ¿Qué le pasa a un mensaje si el consumidor muere antes de enviar el `ack`?
* **Fuente**: *D8 Slide 20 y L7A Slide 17*.
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: Configuramos todos los consumidores con confirmación manual explícita (`noAck: false`) y ubicamos `canal.ack(mensaje)` estrictamente después de haber persistido el registro en PostgreSQL.
  2. **Qué problema resuelve**: Garantiza la tolerancia a fallos bajo el modelo *at least once*. Mientras el consumidor procesa el mensaje, este reside en RabbitMQ en estado `unacked`. Si el proceso muere, el contenedor se apaga o la conexión TCP se interrumpe antes del `ack`, RabbitMQ detecta el cierre del canal y devuelve automáticamente el mensaje a la cola (estado `ready`), reentregándolo al siguiente consumidor disponible.
  3. **Qué descarté**: Descarté auto-ack (`noAck: true`) o ejecutar `ack` antes de guardar en la base de datos (`await insert`). Si confirmáramos antes y el proceso muriera durante la persistencia, el broker ya habría borrado el mensaje y los datos se evaporarían.
  4. **Cómo lo compruebo**: Deteniendo el consumidor con `Ctrl+C` durante el experimento de `consumidor-lento.mjs` y verificando con `rabbitmqctl list_queues` que la cola vuelve inmediatamente de `5 4 1` a `5 5 0`.

---

### F.3. ¿Cuáles son las tres durabilidades y qué se pierde si falta cada una?
* **Fuente**: *D8 Slides 22–24 y L7 Tramo 2.1*.
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: Configuramos las tres capas de durabilidad: 1. Volumen con nombre de Docker (`datos-rabbit:/var/lib/rabbitmq`) en `compose.yml`; 2. Colas durables (`{ durable: true }`) en `topologia.ts`; 3. Mensajes persistentes (`{ persistent: true }`) en `publicador.mjs`.
  2. **Qué problema resuelve**: Garantiza la supervivencia de colas y mensajes ante caídas intempestivas o reinicios del broker RabbitMQ.
  3. **Qué descarté / Qué se pierde si falta cada una**:
     * **Si falta el Volumen**: Se pierde todo al recrear el contenedor, porque el disco de RabbitMQ vivía en la capa efímera de escritura de Docker.
     * **Si falta la Cola Durable**: Aunque exista el volumen, la metadata de la cola residía solo en memoria RAM; al reiniciar RabbitMQ la cola desaparece.
     * **Si falta el Mensaje Persistent**: La cola durable sobrevive y reaparece tras el reinicio, pero vuelve **completamente vacía**, porque los mensajes no se volcaron al disco.
  4. **Cómo lo compruebo**: Publicando con el worker apagado, ejecutando `docker compose restart rabbit1` y comprobando con `rabbitmqctl list_queues` que los mensajes persisten en disco.

---

### F.4. «RabbitMQ garantiza al menos una vez. ¿Cómo evitas duplicar registros?»
* **Fuente**: *D8 Slides 26–28, L7A Slide 24 y L7 Tramo 4.9*.
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: Delegamos la idempotencia en el motor relacional de PostgreSQL mediante una restricción `UNIQUE` en la columna `evento_id` de la tabla `eventos_auditoria`, y el productor genera un UUID único (`x-evento-id`) por cada hecho.
  2. **Qué problema resuelve**: Previene la duplicación de datos provocada por reentregas legítimas del broker (cuando el consumidor guardó pero la red falló antes del `ack`).
  3. **Qué descarté**: Descarté hacer una comprobación previa en el código con `if (!await repo.findOne(...))`. Esa consulta previa tiene una **condición de carrera** (*race condition*): si dos instancias del worker procesan duplicados concurrentemente, ambas leen que no existe y ambas ejecutan el insert. Una regla de negocio en un `if` se puede saltar bajo concurrencia; un índice `UNIQUE` en la base de datos es infranqueable.
  4. **Cómo lo compruebo**: Ejecutando dos veces consecutivas `emitir.mjs 1 --repetido` con el mismo UUID: el worker registra `guardado` en la primera y `reentrega: ya estaba guardado` en la segunda, y `SELECT count(*)` en PostgreSQL devuelve exactamente `1`.

---

### F.5. ¿Qué hace tu consumidor ante un error `23505` de PostgreSQL y por qué NO lo manda a la DLQ?
* **Fuente**: *L7A Slide 25 y L7 Tramo 4.8*.
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: En el bloque `catch` del consumidor, capturamos `error.code === '23505'` (*unique_violation*), emitimos un log de advertencia (`this.log.warn(...)`) y ejecutamos inmediatamente `canal.ack(mensaje)`.
  2. **Qué problema resuelve**: Permite que el transporte asíncrono continúe limpio. El código `23505` demuestra que el evento ya fue insertado y procesado exitosamente en una entrega anterior.
  3. **Qué descarté**: Descarté enviar el error `23505` a la Dead Letter Queue (DLQ). Si enviáramos un duplicado a la DLQ, estaríamos tratando un éxito previo del negocio como un fallo del mensaje, contaminando la DLQ con mensajes perfectamente válidos y alertando falsos positivos a los operadores.
  4. **Cómo lo compruebo**: Mostrando en `auditoria.consumidor.ts` el bloque `if ((error as { code?: string }).code === '23505') { canal.ack(mensaje); return; }`.

---

### F.6. ¿Por qué el payload de `eventos_auditoria` es `jsonb` y el de `mensajes_muertos` es `text`?
* **Fuente**: *L7 Tramos 4.4 y 4.5*.
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: En TypeORM definimos `payload: jsonb` para `EventoAuditoria` y `payload: text` para `MensajeMuerto`.
  2. **Qué problema resuelve**: Modela la realidad ontológica de los datos. Un tipo de columna es una promesa sobre lo que puede ingresar:
     * Un mensaje que llega a `eventos_auditoria` superó exitosamente el `JSON.parse`: es **JSON válido por definición**. El tipo `jsonb` de PostgreSQL almacena el JSON descompuesto en binario, permitiendo indexar atributos y realizar consultas profundas (ej: `payload ->> 'juegoId'`).
     * Un mensaje que llega a `mensajes_muertos` es precisamente **el que no pudo procesarse**: puede ser un string truncado, XML, texto plano corrupto o bytes no parseables.
  3. **Qué descarté**: Descarté tipar `payload` de `mensajes_muertos` como `jsonb`. Si fuera `jsonb`, al intentar registrar un mensaje envenenado (`{ esto no es JSON valido`), Postgres abortaría el `INSERT` por error de sintaxis y el consumidor de cartas muertas moriría intentando registrar por qué murió otro proceso.
  4. **Cómo lo compruebo**: Emitiendo el mensaje corrupto `emitir.mjs 1 --roto`: el consumidor de cartas muertas lo inserta sin problemas en `mensajes_muertos` y la columna almacena el texto literal rechazado.

---

### F.7. ¿Por qué el estado en la base es un `CHECK` y no un simple `type` o `enum` de TypeScript?
* **Fuente**: *L7 Tramos 4.5 y 4.11*.
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: Agregamos restricciones relacionales `CHECK (estado IN ('enviada', 'fallida'))` en `notificaciones` y `CHECK (estado IN ('activa', 'revocada'))` en `licencias`.
  2. **Qué problema resuelve**: Garantiza la integridad de datos a nivel de motor. Un `type Estado = 'enviada' | 'fallida'` solo existe en tiempo de desarrollo y compilación de TypeScript; desaparece por completo al generar el código JavaScript ejecutable. La base de datos no sabe nada de TypeScript.
  3. **Qué descarté**: Descarté confiar únicamente en la validación del código cliente o de los decoradores de NestJS. Cualquier inserción o modificación que provenga de fuera de la aplicación (un script de migración, una consulta directa de un DBA en `psql`, o un microservicio en otro lenguaje) podría insertar estados arbitrarios como `'pendiente'` o `'borrado'` rompiendo la coherencia del sistema.
  4. **Cómo lo compruebo**: Ejecutando en `psql` un `INSERT INTO notificaciones (estado, ...) VALUES ('invalido', ...)` y observando el error relacional inmediato: `new row for relation "notificaciones" violates check constraint`.

---

### F.8. ¿Por qué en `CartasMuertasConsumidor` se usa un solo consumidor para las tres DLQ y de dónde saca la cola de origen?
* **Fuente**: *L7 Tramos 5.1 y 5.4*.
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: En `cartas-muertas.consumidor.ts` implementamos un único consumidor que itera con un bucle `for (const cola of Object.values(DLQ))` sobre las tres colas de cartas muertas, y extrae la cola de origen desde el encabezado `x-first-death-queue`.
  2. **Qué problema resuelve**: Aplica el principio DRY (Don't Repeat Yourself). El trabajo de registrar una carta muerta es exactamente el mismo sin importar de qué cola provenga. Crear tres clases idénticas triplicaría código innecesariamente.
  3. **Qué descarté**: Descarté extraer la cola de origen desde `x-death[0].queue`. El arreglo `x-death` viene ordenado cronológicamente con la muerte más reciente primero; si un mensaje sufriera múltiples rechazos sucesivos, `x-death[0]` indicaría la última cola, no la original. RabbitMQ preserva la cola donde el mensaje falló por primera vez en el header inmutable `x-first-death-queue`.
  4. **Cómo lo compruebo**: Mostrando en el log del worker la línea `[CartasMuertasConsumidor] registrada carta muerta de cola-auditoria`.

---

### F.9. ¿Por qué las DLQ deben declararse ANTES que las colas de trabajo en `declararTopologia`?
* **Fuente**: *L7A Slide 20 y L7 Tramo 3.3*.
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: En la función `declararTopologia`, el orden inquebrantable es: 1. Declarar Exchanges -> 2. Declarar las tres DLQ y sus bindings al DLX -> 3. Declarar las tres colas de trabajo con `x-dead-letter-exchange` -> 4. Bindings de trabajo.
  2. **Qué problema resuelve**: Previene la pérdida silenciosa de mensajes descartados. En RabbitMQ, primero debe existir el destino antes que el origen pueda enrutar hacia él.
  3. **Qué descarté**: Descarté declarar las colas de trabajo primero. Si una cola de trabajo se crea con `deadLetterExchange: 'vidalstore.dlx'` y empieza a recibir mensajes inmediatamente, cualquier descarte (`nack(false, false)`) antes de que las DLQ hayan sido creadas en el broker causaría que RabbitMQ descarte el mensaje al vacío sin generar ningún error, perdiéndose la evidencia para siempre.
  4. **Cómo lo compruebo**: Mostrando en `topologia.ts` la secuencia de promesas `await canal.assertQueue(DLQ...)` antes de `await canal.assertQueue(COLAS...)`.

---

### F.10. ¿Qué significa el error `406 PRECONDITION_FAILED` al relanzar el worker y cómo se soluciona?
* **Fuente**: *L7A Slide 21 y L7 Tramo 3.5*.
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: Ante el error `406 PRECONDITION_FAILED`, ejecutamos `docker compose exec rabbit1 rabbitmqctl delete_queue <nombre>` para borrar las colas previas y relanzamos el worker.
  2. **Qué problema resuelve**: Permite la actualización de argumentos de colas en RabbitMQ. Una cola creada en AMQP es inmutable en su definición básica: no se pueden alterar argumentos como `x-dead-letter-exchange` sobre una cola ya existente.
  3. **Qué descarté**: Descarté pensar que era un bug de código en TypeScript o reiniciar RabbitMQ borrando volúmenes (`down -v`), lo que destruiría la base de datos de usuarios y configuraciones.
  4. **Cómo lo compruebo**: Mostrando que tras eliminar la cola huérfana con `delete_queue`, el worker arranca en limpio creando la cola con sus argumentos de cartas muertas sin lanzar excepciones.

---

### F.11. ¿Para qué sirve `prefetch(1)` y qué pasaría con `prefetch(0)` si la base de datos se cae?
* **Fuente**: *L7A Slide 18 y L7 Tramo 2.4*.
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: Ejecutamos `await this.canal.prefetch(1)` en `mensajeria.service.ts` inmediatamente tras instanciar el canal de comunicación.
  2. **Qué problema resuelve**: Limita la retención en memoria a exactamente un mensaje sin confirmar por consumidor. Si la base de datos entra en fallo o latencia alta, el consumidor retiene solo ese mensaje mientras ejecuta los reintentos con backoff progresivo (2s, 4s). La cola de RabbitMQ se detiene ordenadamente protegiendo al worker.
  3. **Qué descarté**: Descarté dejar el valor por omisión o `prefetch(0)` (que en RabbitMQ significa ilimitado). Con `prefetch(0)`, RabbitMQ le entrega de golpe todos los mensajes acumulados en la cola al proceso. Si la base de datos está caída, el consumidor recibiría miles de mensajes en RAM; si el proceso se cae por falta de memoria o reinicio, los miles de mensajes vuelven al broker saturando la red.
  4. **Cómo lo compruebo**: Ejecutando el experimento de `consumidor-lento.mjs 5` (que simula prefetch 5 y toma 5 mensajes de una sola vez) en comparación con el worker productivo que procesa estrictamente de a uno.

---

### F.12. ¿Por qué el índice de licencias es parcial (`WHERE estado = 'activa'`) y qué fallaría con un UNIQUE simple?
* **Fuente**: *L7 Tramo 5.3 y 5.4*.
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: En PostgreSQL y TypeORM definimos un índice único parcial: `CREATE UNIQUE INDEX uq_licencias_activas ON licencias (usuario_sub, juego_id) WHERE estado = 'activa'`.
  2. **Qué problema resuelve**: Implementa en el motor de base de datos la regla de negocio de Arturo: *"Un jugador no puede poseer dos licencias activas del mismo juego, pero sí puede volver a comprarlo legalmente si su licencia previa fue revocada"*.
  3. **Qué descarté**: Descarté un `UNIQUE (usuario_sub, juego_id)` sin cláusula `WHERE`. Un índice único tradicional bloquearía indefinidamente cualquier compra legítima posterior después de que una licencia fue revocada o devuelta, devolviendo siempre un error de clave duplicada.
  4. **Cómo lo compruebo**: Ejecutando la secuencia de prueba: 1. `INSERT` licencia activa (éxito); 2. Segundo `INSERT` activa (falla con `duplicate key`); 3. `UPDATE` estado a `'revocada'`; 4. Tercer `INSERT` activa (éxito rotundo).

---

### F.13. ¿Por qué al publicar `licencia.revocada` el `usuarioSub` del evento sale de la fila persistida y no del token del administrador?
* **Fuente**: *L7 Tramo 5.4 (Página 82)*.
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: En el microservicio de licencias, al procesar `DELETE /v1/licencias/:id`, actualizamos la fila guardando quién revocó (`revocada_por = token.sub`), pero al armar el evento `licencia.revocada` extraemos `usuarioSub` de la columna `licencia.usuario_sub` de la fila persistida.
  2. **Qué problema resuelve**: Mantiene la semántica del dominio de eventos. El claim `sub` del token Bearer corresponde al **administrador que ejecuta la revocación**. Si pusiéramos ese `sub` en `usuarioSub` del evento, los consumidores aguas abajo (como la cola de avisos y el servicio de correos) enviarían la notificación de revocación a la casilla del administrador en lugar de alertar al jugador afectado.
  3. **Qué descarté**: Descarté asumir que el `sub` del token es siempre el sujeto afectado por la operación.
  4. **Cómo lo compruebo**: Mostrando en el código que `usuarioSub: licencia.usuarioSub` y `revocadaPor: subAdmin`, permitiendo que el jugador reciba el aviso de pérdida de acceso y la auditoría conserve la autoría del administrador en `payload ->> 'revocadaPor'`.

---

### F.14. En caso de caída de base de datos en `CartasMuertasConsumidor`, ¿por qué hace `nack(false, true)` con un timeout de 5 segundos?
* **Fuente**: *L7 Tramo 5.1 (Página 69)*.
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: En el `catch` de `CartasMuertasConsumidor`, si la persistencia en `mensajes_muertos` falla, no hacemos `ack`: programamos un `setTimeout` de 5000 ms y ejecutamos `this.mensajeria.canal.nack(mensaje, false, true)`.
  2. **Qué problema resuelve**: Evita la pérdida irrecuperable de la última copia del mensaje muerto. Como la DLQ es el destino final de descarte, si la base de datos no puede registrarlo en ese instante, el mensaje no tiene otra DLQ a donde ir. Reencolarlo (`requeue: true`) tras una pausa prudente permite que sobreviva en la DLQ hasta que la base de datos se recupere.
  3. **Qué descarté**: Descarté hacer `nack` inmediato sin espera (lo que generaría un ciclo continuo al 100% de CPU) o hacer `ack` descartando la carta muerta sin haberla grabado en PostgreSQL.
  4. **Cómo lo compruebo**: Mostrando en `cartas-muertas.consumidor.ts` la función `setTimeout(() => canal.nack(mensaje, false, true), 5000)`.

---

### F.15. ¿Qué información forense aporta el encabezado `x-death` en las DLQ?
* **Fuente**: *L7 Tramos 3.7 y 3.8*.
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: Implementamos la herramienta `herramientas/ver-dlq.mjs` para inspeccionar mensajes en DLQ sin consumirlos y procesamos el array `x-death` en el worker.
  2. **Qué problema resuelve**: Funciona como la caja negra del fallo en sistemas distribuidos. RabbitMQ inyecta automáticamente metadatos forenses inmutables:
     * `queue`: De qué cola provino el rechazo.
     * `reason`: Por qué murió (`rejected` por código, `expired` por TTL o `maxlen` por sobrecupo).
     * `count`: Cuántas veces fue rechazado (revela bucles de reintento).
     * `routing-keys`: La routing key original con la que nació el evento (ya que en la DLQ viaja con el nombre de la cola).
     * `time`: Timestamp AMQP preciso de la defunción.
  3. **Qué descarté**: Descarté depender únicamente de logs efímeros de consola que se pierden al reiniciar contenedores.
  4. **Cómo lo compruebo**: Ejecutando `docker compose run --rm --no-deps eventos node herramientas/ver-dlq.mjs cola-auditoria.dlq` y observando el JSON estructurado de cabeceras.

---

## Bloque G: Microservicio Administrador y Métricas de Broker (Oscar · IE6, IE7, IE8, IE14, IE17, IE18)

Este bloque consolida las preguntas y respuestas técnicas evaluadas durante la presentación individual de 15 minutos para el dueño de `vidalstore-admin`.

---

### G.1. ¿Por qué los controladores de `vidalstore-admin` nunca importan `amqplib` directamente ni realizan peticiones `fetch` de red?
* **Indicador de Rúbrica**: **IE7 (10% encargo grupal)**.
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: Encapsulé el 100% del acceso a RabbitMQ (tanto el canal AMQP `:5672` como el cliente HTTP de la Management API `:15672`) dentro de la clase `RabbitAdminService`, e inyecté este servicio en `AdminController`.
  2. **Qué problema resuelve**: Cumple con el principio de desacoplamiento de capas y responsabilidad única. Si cambia la URL del broker, el protocolo, las credenciales o los endpoints de la API de RabbitMQ, los controladores de NestJS no sufren alteraciones ni conocen detalles de bajo nivel.
  3. **Qué descarté**: Descarté importar `amqplib` en los controllers o dispersar llamadas `fetch` con cabeceras `Basic Auth` en cada método, lo que habría roto la arquitectura modular y duplicado lógica de red.
  4. **Cómo lo compruebo**: Mostrando [src/admin/admin.controller.ts](file:///Users/oscar/Downloads/DUOC/CloudNative/Evaluacion%202/vidalstore-admin/src/admin/admin.controller.ts), donde se evidencia que el controlador solo interactúa con métodos de alto nivel (`listarColas()`, `obtenerDetalleCola()`, `listarExchanges()`, `publicarEvento()`), y corriendo la suite de tests con mocks de servicio.

---

### G.2. Si RabbitMQ o el puerto 15672 se cae, ¿qué responde tu microservicio y por qué no devolvemos un error 500 genérico?
* **Indicador de Rúbrica**: **IE17 (12% defensa individual)**.
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: En `RabbitAdminService`, envolví las peticiones `fetch` con un `AbortSignal.timeout(5000)` y un bloque `catch` que captura `ECONNREFUSED`, `TimeoutError` o errores de socket, transformándolos inmediatamente en una excepción `ServiceUnavailableException` (HTTP 503).
  2. **Qué problema resuelve**: Garantiza la resiliencia y el manejo robusto de errores exigido por la rúbrica (IE17). Le comunica semánticamente al cliente (Postman, Frontend o Gateway) que el problema no es un bug del microservicio ni un error de código interno, sino que la infraestructura subyacente está temporalmente fuera de servicio.
  3. **Qué descarté**: Descarté permitir que el error de conexión se propague como un error 500 ciego sin mensaje útil o que el hilo quede congelado indefinidamente sin timeout.
  4. **Cómo lo compruebo**: Mostrando la prueba unitaria `debe lanzar ServiceUnavailableException (HTTP 503) cuando RabbitMQ está caído` en [src/admin/rabbit-admin.service.spec.ts](file:///Users/oscar/Downloads/DUOC/CloudNative/Evaluacion%202/vidalstore-admin/src/admin/rabbit-admin.service.spec.ts).

---

### G.3. En tu endpoint `GET /v1/admin/queues`, ¿qué significa exactamente `messages_unacknowledged` y cómo actuar si este número comienza a crecer sin detenerse?
* **Indicador de Rúbrica**: **IE18 (8% defensa individual)**.
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: En `QueueResponseDto` y en `listarColas()`, extraje la métrica `messages_unacknowledged` de cada cola directamente desde `/api/queues`.
  2. **Qué problema resuelve**: Permite diagnosticar la salud de los consumidores. Un mensaje `unacknowledged` es un mensaje que RabbitMQ ya entregó por TCP a un worker (`AvisosConsumer`, `AuditoriaConsumer`), pero que el worker aún no ha confirmado con `ack()` ni rechazado con `nack()`. El mensaje está "en vuelo".
  3. **Qué descarté y Diagnóstico de Anomalía**:
     * Si `messages_unacknowledged` sube y no baja, **no es un fallo de RabbitMQ**: es un síntoma de que un consumidor tiene una fuga de promesas o un bloqueo (llamada colgada a Postgres o API externa sin timeout) que le impide invocar `canal.ack(mensaje)`.
     * Gracias a `{ noAck: false }` y `prefetch(1)`, ese consumidor queda saturado y no absorbe más mensajes.
  4. **Cómo actuar (Remediación operativa)**:
     * Si el worker está trabado, se reinicia su contenedor (`docker restart eventos`).
     * Al cerrarse la conexión TCP, RabbitMQ devuelve automáticamente todos los mensajes `unacknowledged` al estado `messages_ready`, reencolándolos para que otro worker sano los procese sin pérdida de información (*at least once delivery*).

---

### G.4. En `GET /v1/admin/queues/:name`, ¿por qué responder HTTP 404 ante una cola inexistente y cómo se diferencia de una lista vacía?
* **Indicador de Rúbrica**: **IE17 (12% defensa individual)**.
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: En `obtenerDetalleCola(nombre)`, consultamos `/api/queues/%2f/:name`. Si la API de RabbitMQ responde 404, lanzamos `NotFoundException("La cola '...' no existe en RabbitMQ")`.
  2. **Qué problema resuelve**: Respeta estrictamente la semántica HTTP REST. Mientras que un endpoint de colección (`GET /queues`) debe retornar `200 OK` con un array vacío `[]` si no hay elementos, un endpoint de recurso singular (`GET /queues/:name`) debe responder `404 Not Found` si el identificador puntual no existe.
  3. **Qué descarté**: Descarté devolver `null` o `200 OK` con un objeto vacío, lo que confundiría a los clientes haciéndoles creer que la cola existe con 0 mensajes.
  4. **Cómo lo compruebo**: Mostrando la prueba unitaria que verifica que `/v1/admin/queues/fantasma` rechaza con `NotFoundException` (HTTP 404).

---

### G.5. En `GET /v1/admin/exchanges`, ¿por qué `vidalstore.eventos` es `topic` mientras que `vidalstore.comandos` y `vidalstore.dlx` son `direct`?
* **Indicador de Rúbrica**: **IE14 (6% defensa) e IE6**.
* **Respuesta Técnica Modelo (4 Pasos)**:
  1. **Qué hice**: Implementé `GET /v1/admin/exchanges` que refleja la topología: `vidalstore.eventos` es `topic`, y `vidalstore.comandos` junto con `vidalstore.dlx` son `direct`.
  2. **Por qué `topic` para eventos**: Los eventos de negocio (`compra.realizada`, `licencia.revocada`) representan hechos consumados que interesan a múltiples consumidores simultáneamente (fan-out selectivo). El tipo `topic` permite ruteo por patrones jerárquicos con wildcards (`#.realizada`, `compra.*`), permitiendo que `q.avisos` y `q.auditoria` escuchen sin que el productor sepa de su existencia.
  3. **Por qué `direct` para comandos y DLX**: Los comandos (`correo.enviar`) tienen un destinatario único y determinista (`q.correos`). De la misma manera, en `vidalstore.dlx`, cada cola de trabajo desvía sus mensajes muertos a su propia DLQ usando su nombre exacto como clave de ruteo (`dlq.avisos`, `dlq.auditoria`, `dlq.correos`).
  4. **Cómo lo compruebo**: Mostrando la salida del endpoint `GET /v1/admin/exchanges` y el archivo [src/mensajeria/topologia.ts](file:///Users/oscar/Downloads/DUOC/CloudNative/Evaluacion%202/vidalstore-admin/src/mensajeria/topologia.ts).
