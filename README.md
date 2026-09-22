# VidalStore EP1 — Skill de Auditoría, Arquitectura y Cumplimiento al 100%
### DSY1107 · Desarrollo Cloud Native I · DUOC UC (2026-02)

Esta skill es una suite integral de aseguramiento de calidad técnica, control de arquitectura y preparación para la defensa individual de la Evaluación Parcial N°1 (Caso VidalStore).

Integra de forma estricta las seis fuentes normativas del encargo:
1. **`EP1-aclaraciones.pdf`**: Documento oficial del profesor Cristian Calderón (`Umbingelelo`), que rige sobre el enunciado.
2. **`EP1-Caso-VidalStore.pdf`**: Enunciado de negocio, arquitectura objetivo y rúbrica oficial (Indicadores IE1 a IE10).
3. **`Pulso.pdf`**: Guía oficial del Laboratorio L4 ("La cadena completa") y preparación metodológica ("El puente a EP1: tramos 10 al 12"), con las 8 preguntas oficiales de la defensa y la resolución de la trampa de Cognito.
4. **`D6-Git-en-serio-y-defender-una-arquitectura.html`**: Clase magistral oficial de Semana 7 sobre entrega técnica, higiene de Git, el reloj de 15 minutos, los 5 flujos de punta a punta y el método de respuesta en 4 pasos.
5. **Resoluciones del foro oficial de GitHub**: Criterios de evaluación, Hosted UI, idempotencia y defensa en profundidad.
6. **Plan de Trabajo del Proyecto**: Flujo de ramas GitFlow y distribución técnica por integrante.

---

## 1. Arquitectura Global de 4 Capas

El sistema VidalStore desacopla responsabilidades en cuatro capas con comunicacion unidireccional y control estricto de accesos:

```mermaid
flowchart TD
    subgraph Capa1["1. Frontend (Angular - Puerto 4200)"]
        SPA["SPA Angular y Amplify (sessionStorage)"]
        Router["Router Interno (/catalogo, /biblioteca)"]
        Interceptor["HTTP Interceptor (Whitelist: :8080)"]
    end

    subgraph Capa2["2. API Gateway (NestJS - Puerto 8080)"]
        GWAuth["Autenticacion Token (Firma, iss, exp, use, client_id)"]
        GWCors["CORS Estricto (Solo origin :4200)"]
        GWProxy["Enrutador Proxy HTTP"]
    end

    subgraph Cognito["Proveedor de Identidad (AWS Cognito)"]
        UserPool["User Pool (Hosted UI + PKCE)"]
        JWKS["Endpoint JWKS Publico (Claves RSA)"]
        Trigger["Lambda Post-Confirmacion (Grupo jugadores)"]
    end

    subgraph Capa3["3. BFF - Backend for Frontend (NestJS - Puerto 3001)"]
        BFFAuth["Segunda Validacion Token (Defensa en Profundidad)"]
        BFFRoles["Autorizacion por Rol (cognito:groups)"]
        BFFOrq["Orquestacion y Agregacion de Datos"]
    end

    subgraph Capa4["4. Microservicios Internos (Node.js)"]
        MSCat["MS Catalogo (:3002) - data/catalogo.json"]
        MSCom["MS Compras (:3003) - Idempotencia 409"]
        MSBib["MS Biblioteca (:3004) - data/licencias.json"]
        MSAud["MS Auditoria (:3005) - data/auditoria.json"]
    end

    SPA -->|1. Inicio Sesion OIDC PKCE| UserPool
    UserPool -.->|Claves publicas| JWKS
    JWKS -.->|Descarga claves| GWAuth
    UserPool -->|Post-confirmacion| Trigger

    SPA -->|2. UNA llamada API con Bearer JWT| Interceptor
    Interceptor -->|Ruta /v1/...| GWAuth
    GWAuth --> GWProxy
    GWProxy -->|Reenvia JWT intacto| BFFAuth

    BFFOrq -->|Consulta juegos| MSCat
    BFFOrq -->|Registra compra| MSCom
    BFFOrq -->|Consulta y revoca licencias| MSBib
    BFFOrq -->|Registra eventos forenses| MSAud
```

---

## 2. Distincion Clave: Rutas del Frontend vs Llamadas a la API

Segun la aclaracion del docente:
* **Rutas del Frontend (Navegacion SPA)**: Se gestionan localmente en el cliente Angular (`app.routes.ts`) para determinar que componente renderizar (`/catalogo`, `/biblioteca`, `/admin/licencias`, `/callback`). No generan peticiones de red por si solas.
* **Llamadas a la API**: Salen del frontend hacia la red. El frontend tiene **UNA sola direccion base** (`http://localhost:8080`) y emite **UNA sola llamada HTTP** al Gateway por accion o vista.
* **Orquestacion en el BFF**: El Gateway reenvia esa llamada unica al BFF (`:3001`), y es el BFF quien realiza multiples llamadas internas concurrentes hacia los microservicios para componer la respuesta.

```text
+-----------------------------------------------------------------------------------+
| FRONTEND (Angular :4200)                                                          |
| El usuario entra a la vista /biblioteca (Ruta de router Angular)                  |
| El servicio VidalStore emite UNA SOLA llamada HTTP a la API:                      |
| --> GET http://localhost:8080/v1/biblioteca                                       |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          | (1 sola llamada con Authorization Bearer)
                                          v
+-----------------------------------------------------------------------------------+
| API GATEWAY (NestJS :8080)                                                        |
| 1. Valida token contra JWKS de Cognito (firma, exp, iss, client_id, token_use).   |
| 2. Aplica politica CORS (Access-Control-Allow-Origin: http://localhost:4200).     |
| 3. Reenvia UNA SOLA llamada al BFF:                                               |
| --> GET http://localhost:3001/v1/biblioteca                                       |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          | (Reenvio proxy con JWT propagado)
                                          v
+-----------------------------------------------------------------------------------+
| BFF - BACKEND FOR FRONTEND (NestJS :3001)                                         |
| 1. Vuelve a validar token por defensa en profundidad (401 si viene sin token).    |
| 2. Extrae el claim 'sub' para saber quien es el usuario (sin aceptar userId URL). |
| 3. ORQUESTACION: Realiza MULTIPLES llamadas internas a los microservicios:        |
|    |                                                                              |
|    +---> Llamada 1: GET http://localhost:3004/v1/biblioteca (Trae licencias)     |
|    |                                                                              |
|    +---> Llamada 2: GET http://localhost:3002/v1/catalogo   (Trae juegos)        |
|                                                                                   |
| 4. Combina en memoria las licencias con los datos del catalogo (titulo, precio).  |
| 5. Devuelve UNA SOLA respuesta consolidada al Gateway -> Frontend.                |
+-----------------------------------------------------------------------------------+
```

---

## 3. Diagramas de Secuencia de los Flujos Principales

### A. Flujo de Autenticacion OIDC con Authorization Code y PKCE

Cumplimiento de Indicadores IE1, IE7 e IE8:

```mermaid
sequenceDiagram
    autonumber
    actor Usuario
    participant SPA as Frontend Angular (:4200)
    participant Cognito as AWS Cognito Hosted UI
    participant Lambda as Trigger Post-Confirmacion
    participant Storage as sessionStorage

    Usuario->>SPA: Clic en 'Iniciar Sesion'
    Note over SPA: Genera code_verifier y code_challenge (SHA-256)
    SPA->>Cognito: Redireccion a Hosted UI con code_challenge (S256)
    Usuario->>Cognito: Ingresa credenciales o se registra
    opt Registro de Usuario Nuevo
        Cognito->>Lambda: Ejecuta trigger Post-Confirmacion
        Lambda->>Cognito: Asigna usuario al grupo 'jugadores' sin intervencion manual
    end
    Cognito-->>SPA: Redirige a /callback?code=AUTH_CODE
    SPA->>Cognito: POST /oauth2/token (Canje de code + code_verifier)
    Cognito-->>SPA: Retorna tokens (access_token, id_token, refresh_token)
    SPA->>Storage: Guarda access_token en sessionStorage
    SPA->>Usuario: Redirige a /catalogo con sesion activa
```

---

### B. Flujo de Consulta de Biblioteca (Orquestacion y Agregacion)

Cumplimiento de Indicadores IE2, IE3, IE9 e IE10:

```mermaid
sequenceDiagram
    autonumber
    actor Jugador
    participant SPA as Frontend Angular (:4200)
    participant GW as API Gateway (:8080)
    participant BFF as BFF (:3001)
    participant MSBib as MS Biblioteca (:3004)
    participant MSCat as MS Catalogo (:3002)

    Jugador->>SPA: Navega a /biblioteca
    Note over SPA: Interceptor adjunta access_token desde sessionStorage
    SPA->>GW: GET /v1/biblioteca (Authorization: Bearer JWT)
    GW->>GW: Valida token con JWKS (RSA, iss, exp, client_id, token_use=access)
    GW->>BFF: Proxy GET /v1/biblioteca (Propaga Bearer JWT)
    Note over BFF: Valida token y extrae claim sub
    par Llamadas concurrentes del BFF
        BFF->>MSBib: GET /v1/biblioteca (Filtra por sub)
        MSBib-->>BFF: Retorna licencias del usuario
    and
        BFF->>MSCat: GET /v1/catalogo
        MSCat-->>BFF: Retorna catalogo de juegos
    end
    Note over BFF: Cruza datos y enriquece cada licencia con su juego
    BFF-->>GW: HTTP 200 OK con Licencias Enriquecidas
    GW-->>SPA: HTTP 200 OK (con Access-Control-Allow-Origin: :4200)
    SPA-->>Jugador: Renderiza las tarjetas de juegos adquiridos
```

---

### C. Flujo Forense de Revocacion y Auditoria (Grupos de 3)

Cumplimiento del Requerimiento 4.8 y Caso de Defensa:

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Administrador
    participant SPA as Frontend Angular (:4200)
    participant GW as API Gateway (:8080)
    participant BFF as BFF (:3001)
    participant MSBib as MS Biblioteca (:3004)
    participant MSAud as MS Auditoria (:3005)

    Admin->>SPA: Clic en 'Revocar Licencia' (id: lic-99)
    SPA->>GW: DELETE /v1/licencias/lic-99 (Bearer JWT Admin)
    GW->>GW: Valida token y grupo 'administradores'
    GW->>BFF: Proxy DELETE /v1/licencias/lic-99
    Note over BFF: Verifica pertenencia al grupo 'administradores'
    
    BFF->>MSBib: DELETE /v1/licencias/lic-99
    MSBib-->>BFF: Retorna confirmacion y licencia eliminada
    
    BFF->>MSAud: POST /v1/auditoria (adminSub, usuarioSub, juegoId, motivo)
    MSAud-->>BFF: Retorna evento registrado con timestamp
    
    BFF-->>GW: HTTP 200 OK (licencia revocada y auditoria registrada)
    GW-->>SPA: HTTP 200 OK
    SPA-->>Admin: Actualiza lista y la licencia desaparece
```

---

## 4. Matriz de Responsabilidades y Codigos HTTP

| Situacion / Condicion | Capa Responsable | Codigo HTTP |
|---|---|:---:|
| Peticion sin cabecera Authorization | API Gateway (o Backend en llamada directa) | 401 Unauthorized |
| Token alterado, expirado o con firma invalida | API Gateway | 401 Unauthorized |
| Token emitido para otra aplicacion (App Client 2) | API Gateway | 401 Unauthorized |
| Token id_token en lugar de access_token | API Gateway | 401 Unauthorized |
| Token valido pero usuario no pertenece al grupo requerido | BFF | 403 Forbidden |
| Token valido pero sin el scope de aplicacion | API Gateway / BFF | 403 Forbidden |
| Compra de un juego que el usuario ya posee | Microservicio Compras | 409 Conflict |
| Recurso solicitado no existe (juego o licencia) | Microservicio Catálogo / Biblioteca | 404 Not Found |
| Operacion exitosa de lectura o eliminacion | Microservicio / BFF | 200 OK |
| Operacion exitosa de creacion (compra, nuevo juego) | Microservicio / BFF | 201 Created |

---

## 5. Pruebas Practicas en Terminal (Rubrica IE10)

Estas cuatro pruebas deben ejecutarse en vivo en la terminal sin usar la interfaz grafica:

### Prueba 1: Peticion sin token (401 Unauthorized)
```bash
curl -i http://localhost:8080/v1/catalogo
```

### Prueba 2: Peticion con token alterado (401 Unauthorized)
```bash
curl -i -H "Authorization: Bearer token_falso_invalido" http://localhost:8080/v1/catalogo
```

### Prueba 3: Peticion con token de otra aplicacion (401 Unauthorized)
```bash
curl -i -H "Authorization: Bearer <TOKEN_APP_CLIENT_2>" http://localhost:8080/v1/catalogo
```

### Prueba 4: Peticion con rol insuficiente (403 Forbidden)
```bash
curl -i -X DELETE -H "Authorization: Bearer <TOKEN_JUGADOR>" http://localhost:8080/v1/licencias/lic-1
```

### Prueba Extra: Defensa en Profundidad (Llamada interna sin Gateway)
```bash
curl -i http://localhost:3001/v1/catalogo
# Retorna 401 Unauthorized demostrando que el backend se protege a si mismo
```

---

## 6. Estructura de Repositorios

```text
Evaluacion 1/
├── vidalstore-frontend/       # Capa 1: Angular + Amplify (Puerto 4200)
├── vidalstore-gateway/        # Capa 2: API Gateway NestJS (Puerto 8080)
├── vidalstore-backend/        # Capa 3 y 4: BFF (:3001) y Microservicios (:3002 - :3005)
└── .agents/skills/vidalstore-ep1/ # Suite de auditoria tecnica y rubricas
```

---

## 7. Fundamentos Técnicos y Arquitectura de `Pulso.pdf` (L4 y Puente a EP1)

La guía oficial `Pulso.pdf` profundiza en los criterios de ingeniería de software que el profesor evalúa en el encargo y en la defensa:

### A. La "Trampa de Cognito" en el Auto-registro (Tramo 10)
Al habilitar *Self-service sign-up* en Cognito, los usuarios pueden crear su cuenta desde la Hosted UI. Sin embargo:
* **El Problema**: Cognito **no asigna ningún grupo por defecto**. El token emitido no contiene el claim `cognito:groups`.
* **La Consecuencia**: Si las rutas protegidas exigen roles (`@Roles('jugadores')`), el usuario recién registrado recibe **`403 Forbidden`** en todas partes, incluso para ver su propia pantalla.
* **Las Dos Soluciones Legítimas**:
  * **Salida A (Nivel de Código / Guard)**: Si `cognito:groups` viene vacío o ausente en el payload, el guard asigna en memoria el rol de menor privilegio (`jugadores`). Esto protege la aplicación inmediatamente sin depender de servicios externos.
  * **Salida B (Nivel de Infraestructura AWS)**: Función Lambda configurada como trigger *Post-Confirmation* que ejecuta `AdminAddUserToGroup` al verificarse el correo del usuario.
* **Defensa Técnica**: En la defensa se destaca reconocer el límite de la solución: *"Salida A es nuestro respaldo a nivel de dominio; en producción se migra a Salida B (Lambda trigger) para que el token venga firmado con el grupo directamente desde AWS"*.

---

### B. Reglas de Escritura, Borrado Lógico y Prevención de BOLA (Tramo 11)
Para las rutas de mutación (`POST /v1/compras`, `POST /v1/catalogo`, `DELETE /v1/licencias/:id`):
1. **Asignación de IDs**: El ID del nuevo registro lo asigna el microservicio / capa de persistencia (`Math.max(...) + 1`), **nunca el cliente ni el BFF**. Un cliente que elige su propio ID terminaría pisando registros de otros.
2. **Borrado Lógico vs. Físico**:
   * En transacciones con historial (compras, licencias, préstamos), un `DELETE` **no elimina la fila física de la base de datos**.
   * Se aplica **borrado lógico** actualizando su estado (`devuelto: true` o `estado: 'revocada'`), preservando la trazabilidad para auditoría forense. La ruta se llama `DELETE` porque describe la intención del cliente (*"elimina esto de mi lista activa"*), no la implementación interna.
3. **La Regla de Oro de la Identidad**:
   * El `usuarioSub` **siempre** proviene de `req.user.sub` (token validado).
   * **NUNCA** se acepta `usuarioSub` o `userId` desde el `@Body()`. Si el cliente envía ese campo en el JSON, se descarta para evitar suplantaciones de identidad (vulnerabilidad BOLA / OWASP API #1).
4. **Semántica de Códigos de Error**:
   * `400 Bad Request`: Parámetro con formato incorrecto (ej. ID de texto en lugar de entero con `ParseIntPipe`).
   * `404 Not Found`: El recurso a revocar o consultar no existe en el sistema.
   * `405 Method Not Allowed`: Se invoca un método HTTP no soportado sobre la ruta (distinto de 404 que indica que la ruta no existe).
   * `409 Conflict`: Regla de negocio infringida o violación de idempotencia (el usuario ya compró la licencia o no quedan ejemplares disponibles).

---

### C. Agregación Eficiente en el BFF y Rendimiento ($O(N)$ vs $O(N \times M)$) (Tramos 1 y 4)
* **Principio de Diseño**: *"El cliente recibe lo que necesita mostrar, no la base de datos"*.
  * El BFF evita que el cliente deba descargar el catálogo completo y exponer campos internos (precios de costo, stock reservado) en las herramientas de desarrollo (F12).
* **Concurrencia en Servidor**: Las peticiones internas hacia los microservicios se ejecutan en paralelo con `Promise.all([fetchCatalogo(), fetchBiblioteca()])`. Con 300 ms de latencia simulada por microservicio:
  * Ejecución en Serie: $300\text{ ms} + 300\text{ ms} = 600\text{ ms}$.
  * Ejecución en Paralelo (BFF): $\max(300\text{ ms}, 300\text{ ms}) = 300\text{ ms}$.
* **Cruce de Datos con `Map`**:
  * Para combinar las licencias con los datos del catálogo se indexa el catálogo en un `new Map<string, Juego>(catalogo.map(j => [j.id, j]))`.
  * La búsqueda por ID en el `Map` toma tiempo constante $O(1)$, logrando una complejidad global de **$O(N)$**.
  * Si se usara `.find()` dentro de un `.map()`, la complejidad sería **$O(N \times M)$**, lo cual degradaría drásticamente el rendimiento con catálogos masivos.
* **Fail-Fast con `ConfigService.getOrThrow()`**:
  * Leer variables de entorno con `getOrThrow` provoca que el BFF falle al momento de iniciar en la terminal si falta una variable crítica (`COGNITO_ISSUER`), en lugar de fallar en tiempo de ejecución con errores crípticos de `Invalid URL` ante los usuarios.

---

### D. Semántica de Códigos HTTP y Prevención de Enumeración (Tramo 7)
* Si un usuario nuevo o sin compras consulta su biblioteca (`GET /v1/biblioteca`), el sistema responde **`200 OK` con `[]`** (lista vacía).
* Responder `403` o `404` sería erróneo y peligroso:
  * El usuario tiene derecho a preguntar por su biblioteca (no es 403).
  * Distinguir *"no tienes registros"* de *"no tienes permiso para ver"* evita ataques de **enumeración** de recursos.

---

### E. Manejo Defensivo de Red con `fetch` en Node.js (Tramo 2)
* En Node.js, `fetch` **no lanza excepción** cuando el servidor responde con códigos de error HTTP como 400, 401, 404, 429 o 500. La promesa se resuelve exitosamente con `response.ok = false`.
* Si no se verifica `if (!response.ok)`, el código intentará ejecutar `response.json()` sobre el cuerpo del error y fallará con un `TypeError: Cannot read properties of undefined`, ocultando la causa raíz del fallo.

---

## 8. Las 6 Pruebas de Integración de la Cadena Completa (Tramo 9)

Estas pruebas validan el flujo de extremo a extremo y el comportamiento de la arquitectura de 4 capas:

| # | Tipo de Petición | Comando Terminal | Código Esperado | Quién lo Corta / Responde | Justificación de Arquitectura |
|---|---|---|:---:|---|---|
| **1** | Sin cabecera `Authorization` | `curl -i http://localhost:8080/v1/catalogo` | **401** | API Gateway (:8080) | El perímetro exterior corta peticiones anónimas; el BFF ni se entera. |
| **2** | Token válido de jugador | `curl -i -H "Authorization: Bearer $T" http://localhost:8080/v1/biblioteca` | **200** | BFF (:3001) | Gateway valida token; BFF orquesta y responde con datos agregados en 1 llamada. |
| **3** | Token de jugador en ruta de administración | `curl -i -H "Authorization: Bearer $T_JUG" http://localhost:8080/v1/licencias` | **403** | BFF (`RolGuard`) | Gateway valida que el token es legal; el `RolGuard` del BFF comprueba que no pertenece a `administradores`. |
| **4** | Token de administrador en ruta de administración | `curl -i -H "Authorization: Bearer $T_ADM" http://localhost:8080/v1/licencias` | **200** | BFF (:3001) | Acceso concedido al rol con máximos privilegios. |
| **5** | Llamada directa al BFF sin pasar por Gateway | `curl -i http://localhost:3001/v1/catalogo` | **401** | BFF (`JwtGuard`) | **Defensa en profundidad**: El BFF no asume que las llamadas internas son de confianza; se protege a sí mismo. |
| **6** | Microservicio interno caído (apagado) | `curl -i -H "Authorization: Bearer $T" http://localhost:8080/v1/biblioteca` | **503** | BFF (:3001) | El BFF detecta la indisponibilidad del servicio interno y devuelve `503 Service Unavailable` indicando el servicio afectado. |

---

## 9. Matriz de las 8 Preguntas Oficiales de la Defensa Individual (`Pulso.pdf` §12.2)

La evaluación asigna el **60% de la nota final a la defensa técnica individual**. La guía oficial establece estas 8 preguntas literales:

| # | Pregunta Oficial del Tramo 12.2 | Tramo Origen | Concepto Clave a Responder |
|---|---|:---:|---|
| **1** | *¿Por qué el BFF vuelve a validar el token si el gateway ya lo validó?* | Tramo 5.2 | **Defensa en profundidad y Zero Trust**: Red interna no confiable, necesidad de los claims (`sub`) con costo criptográfico marginal, y protección ante futuros canales sin gateway (colas RabbitMQ/SQS). |
| **2** | *¿Qué decide un scope y qué decide un grupo, y por qué son cosas distintas?* | L3 §7.1, Tramo 6 | **Scope**: Qué operaciones puede pedir la *aplicación cliente*. **Grupo**: Qué rol tiene la *persona humana*. Gateway autoriza scope; BFF autoriza grupo. |
| **3** | *¿Cuándo respondes 401 y cuándo 403?* | Tramo 9 (P1 y P3) | **401**: Identidad no comprobada (*"no sé quién eres"*). **403**: Identidad comprobada pero permiso insuficiente (*"no te alcanza el rol"*). Evita bucle infinito de login. |
| **4** | *¿Qué pregunta de autorización no puede responder un guard, y dónde va esa comprobación?* | Tramo 7 | *"¿Este recurso le pertenece a este usuario?"*. Un guard no ve la persistencia. Se comprueba en el **Service** filtrando por `usuarioSub === sub`. Si está vacío devuelve `200 []`. |
| **5** | *¿Por qué el `client_id` del access token no sirve para autorizar?* | L3 §7.1 | Identifica la aplicación cliente emisora, no al usuario humano. Solo sirve para rechazar tokens de otras aplicaciones del mismo User Pool. |
| **6** | *¿Qué gana el frontend con que exista el BFF? Da el número medido* | Tramo 4.3 | Una sola llamada de red, concurrencia en servidor con `Promise.all` (~300 ms vs ~600 ms en serie), cruce en memoria $O(N)$ con `Map` y cero fuga de datos internos (F12). |
| **7** | *Un usuario se registra solo y no puede entrar a nada. ¿Qué pasó y cómo lo resolviste?* | Tramo 10 | Trampa de Cognito (auto-registro sin grupos). Salida A: rol de menor privilegio por omisión en el guard. Salida B: trigger Lambda Post-Confirmation. |
| **8** | *Al crear o revocar un recurso, ¿de dónde sacas el usuario, y por qué no del cuerpo?* | Tramo 11.3 | Se extrae estrictamente de `req.user.sub` (token firmado). Si viniera del `@Body()`, cualquiera podría falsificar el ID y operar sobre cuentas ajenas (vulnerabilidad BOLA). |

---

## 10. Guía Maestra de Diagnóstico y Resolución de Errores (Troubleshooting)

Tabla de síntomas extraída de `Pulso.pdf` (Páginas 72–74) para depuración rápida durante el desarrollo y la evaluación:

| Síntoma Observado | Causa Raíz Probable | Solución Inmediata |
|---|---|---|
| `npm error Cannot read properties of null (reading 'edgesOut')` | Versión de npm desactualizada (npm 10 en Node 22). | Actualizar a Node 24 y npm 11 (`nvm use 24`) o usar `--legacy-peer-deps`. |
| `Cannot find module './panel.service'` en BFF | El BFF corre en ESM (`"type": "module"`) y falta la extensión. | Agregar la extensión `.js` al import: `from './panel.service.js'`. |
| `TypeError: Invalid URL` al iniciar BFF | Se leyó `process.env.COGNITO_ISSUER` arriba del archivo antes de cargar el entorno. | Inyectar `ConfigService` en el constructor del guard/servicio o usar `ConfigModule.forRoot({ isGlobal: true })`. |
| `Configuration key "COGNITO_ISSUER" does not exist` | Falta la variable en el archivo `.env` del servicio. | Agregar la variable requerida al archivo `.env` local. |
| `Nest can't resolve dependencies of the XService` | Falta registrar el servicio o guard en el arreglo `providers` o `imports` del módulo. | Agregar la clase dependiente a `providers: [...]` en el módulo correspondiente. |
| `EADDRINUSE :::8080` o `:::3001` | Un proceso anterior de Node/Nest quedó ejecutándose en segundo plano. | Identificar el PID con `lsof -i :<PUERTO>` y terminarlo con `kill -9 <PID>`. Nunca cambiar los puertos de la arquitectura. |
| `401 Unauthorized «sin token»` tras enviar token desde Angular | El Gateway recibió el token pero olvidó reenviar la cabecera en el fetch hacia el BFF. | Asegurar `headers: { authorization }` en la llamada proxy del Gateway al Backend. |
| `403 Forbidden` para todos los usuarios (incluso admin) | El orden de los guards está invertido: `RolGuard` corrió antes que `JwtGuard`. | Configurar estrictamente `@UseGuards(JwtGuard, RolGuard)` en ese orden. |
| `401` donde se esperaba `403` | Se está tratando la falta de permisos de rol como una falla de autenticación. | Lanzar `ForbiddenException` (403) en lugar de `UnauthorizedException` (401). |
| Petición directa al BFF responde `200` sin token | Falta el decorador `@UseGuards(JwtGuard)` a nivel del controlador del BFF. | Colocar `@UseGuards(JwtGuard)` sobre la clase controladora para cerrar el perímetro interno. |
| Catálogo o biblioteca devuelve `200` con `[]` en usuario nuevo | Comportamiento esperado y correcto: el usuario no tiene registros previos. | No es un error; evita ataques de enumeración. |
| Error de CORS en la consola del navegador | Angular está llamando al puerto `3001` directo o al puerto incorrecto del Gateway. | Verificar que Angular llame exclusivamente a `http://localhost:8080`. |
| Token falla con `401` repentinamente tras una hora | Los tokens de AWS Cognito expiran a los 60 minutos. | Volver a iniciar sesión en la Hosted UI para obtener un nuevo token vigente. |
| Usuario recién registrado recibe `403` en todo | Cognito no le asignó ningún grupo (trampa del auto-registro). | Verificar que el guard asigne `jugadores` por defecto (Salida A) o que el trigger Lambda esté activo (Salida B). |
| `400` en `POST` desde Gateway, pero `201` directo al BFF | El Gateway no reenvió el cuerpo de la petición en el fetch. | Agregar `body: JSON.stringify(body)` y `Content-Type: application/json` en el proxy del Gateway. |

---

## 11. Metodología Oficial de Defensa Técnica · Clase D6 (El Reloj de 15 Minutos y los 5 Flujos)

La clase magistral D6 del profesor Cristian Calderón (`Umbingelelo`) define el estándar con el que se evalúa la presentación individual (60% de la nota final):

### Cronograma del Reloj de 15 Minutos
* **Minutos 0 a 1**: Los integrantes declaran procesos activos y sus puertos.
* **Minutos 1 a 7**: Conducción del **Flujo A** (un integrante) y **Flujo B** (otro integrante). Nadie conduce dos flujos seguidos.
* **Minutos 7 a 12**: Conducción de los **Flujos C y D**, y 30 segundos del **Flujo E** (abrir el script `seed.ts`).
* **Minutos 12 a 14**: **Modificación señalada**: una por integrante sobre un archivo que no construyó él (ubicar el archivo, poner el cursor en la línea y explicar qué escribiría y qué pasaría).
* **Minutos 14 a 15**: Pregunta del botón COMPRAR (evaluación de fundamentación técnica de experiencia de usuario vs seguridad e idempotencia en backend).

### Los 5 Flujos de Punta a Punta
1. **Flujo A (Identidad)**: Registro/login con Hosted UI + PKCE. Resolución de la trampa de Cognito (cuenta nueva en grupo `jugadores`). `sub` (quién eres) vs `cognito:groups`/`scope` (qué puedes hacer).
2. **Flujo B (Lo propio)**: `GET /v1/biblioteca` resuelto exclusivamente por el claim `sub` del JWT verificado, jamás por parámetro de URL/body. Una sola llamada de red del frontend al Gateway.
3. **Flujo C (Rol insuficiente)**: Jugador intenta revocar licencia (`DELETE /v1/licencias/:id`) $\rightarrow$ el servidor backend responde `403 Forbidden`. La seguridad reside en el backend, no en ocultar el botón en la UI.
4. **Flujo D (Por detrás / Perímetro)**: Llamada directa a BFF o microservicio sin token $\rightarrow$ `401 Unauthorized`. Token alterado $\rightarrow$ `401 Unauthorized`. CORS restringido a `localhost:4200` solo en Gateway.
5. **Flujo E (Origen / Trazabilidad)**: Seed en `data/` consume API externa real hacia JSON versionado.

### Las 5 Ventanas Obligatorias al Iniciar el Turno
1. **Terminal**: Procesos y puertos corriendo (Angular 4200, Gateway 8080, BFF 3000/3001, Microservicios 3002..3005).
2. **Navegador**: App con sesión recién iniciada, pestaña Red limpia y Application mostrando `sessionStorage`.
3. **Cliente REST o curl**: Dos tokens vigentes listos (jugador y administrador) para probar 403 vs 200, y llamada directa sin token para 401.
4. **Editor de Código**: Interceptor de Angular y Guards de NestJS ya abiertos.
5. **Consola AWS Cognito**: User Pool con grupos, usuarios y los dos App Clients.

### Framework de Respuesta en 4 Pasos (1 Minuto por Parada)
1. **Qué hice**: Nombrar el componente o mecanismo exacto y mostrar la línea de código en el editor.
2. **Qué problema resuelve**: Explicar la necesidad concreta de seguridad, rendimiento o arquitectura.
3. **Qué descarté**: Nombrar explícitamente la alternativa técnica rechazada (el paso que más pesa, demuestra decisión propia).
4. **Cómo lo compruebo**: Demostrarlo en vivo en la pantalla (pestaña Red, dos tokens en curl, etc.).


