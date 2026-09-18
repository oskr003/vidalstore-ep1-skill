# VidalStore EP1 — Skill de Auditoría, Arquitectura y Cumplimiento al 100%
### DSY1107 · Desarrollo Cloud Native I · DUOC UC (2026-02)

Esta skill es una suite integral de aseguramiento de calidad técnica, control de arquitectura y preparación para la defensa individual de la Evaluación Parcial N°1 (Caso VidalStore).

Integra de forma estricta las cuatro fuentes normativas del encargo:
1. **EP1-aclaraciones.pdf**: Documento oficial del profesor Cristian Calderon (Umbingelelo), que rige sobre el enunciado.
2. **EP1-Caso-VidalStore.pdf**: Enunciado de negocio, arquitectura objetivo y rubrica oficial (Indicadores IE1 a IE10).
3. **Resoluciones del foro oficial de GitHub**: Criterios de evaluacion, Hosted UI, idempotencia y defensa en profundidad.
4. **Plan de Trabajo del Proyecto**: Flujo de ramas GitFlow y distribucion tecnica por integrante.

---

## 1. Arquitectura Global de 4 Capas

El sistema VidalStore desacopla responsabilidades en cuatro capas con comunicacion unidireccional y control estricto de accesos:

```mermaid
flowchart TD
    subgraph Capa1["1. Frontend (Angular - Puerto 4200)"]
        SPA["SPA Angular / Amplify<br/>(sessionStorage)"]
        Router["Router Interno<br/>(/catalogo, /biblioteca, etc.)"]
        Interceptor["HTTP Interceptor<br/>(Whitelist: :8080)"]
    end

    subgraph Capa2["2. API Gateway (NestJS - Puerto 8080)"]
        GWAuth["Autenticacion Token<br/>(Firma, iss, exp, use, client_id)"]
        GWCors["CORS Estricto<br/>(Solo origin :4200)"]
        GWProxy["Enrutador Proxy HTTP"]
    end

    subgraph Cognito["Proveedor de Identidad (AWS Cognito)"]
        UserPool["User Pool<br/>(Hosted UI + PKCE)"]
        JWKS["Endpoint JWKS Publico<br/>(Claves RSA para verificar)"]
        Trigger["Lambda Post-Confirmacion<br/>(Asigna grupo 'jugadores')"]
    end

    subgraph Capa3["3. BFF - Backend for Frontend (NestJS - Puerto 3001)"]
        BFFAuth["Segunda Validacion Token<br/>(Defensa en Profundidad)"]
        BFFRoles["Autorizacion por Rol<br/>(cognito:groups)"]
        BFFOrq["Orquestacion y Agregacion<br/>de Datos"]
    end

    subgraph Capa4["4. Microservicios Internos (Node.js)"]
        MSCat["MS Catalogo (:3002)<br/>(data/catalogo.json)"]
        MSCom["MS Compras (:3003)<br/>(Idempotencia 409)"]
        MSBib["MS Biblioteca (:3004)<br/>(data/licencias.json)"]
        MSAud["MS Auditoria (:3005)<br/>(data/auditoria.json)"]
    end

    SPA -->|1. Inicio Sesion OIDC PKCE| UserPool
    UserPool -.->|Claves publicas| JWKS
    JWKS -.->|Descarga claves| GWAuth
    UserPool -->|Post-confirmacion| Trigger

    SPA -->|2. UNA llamada API con Bearer JWT| Interceptor
    Interceptor -->|http://localhost:8080/v1/...| GWAuth
    GWAuth --> GWProxy
    GWProxy -->|Reenvia JWT intacto| Capa3

    BFFOrq -->|Consulta juegos| MSCat
    BFFOrq -->|Registra compra| MSCom
    BFFOrq -->|Consulta/Revoca licencias| MSBib
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
    participant SPA as Angular SPA (:4200)
    participant Cognito as AWS Cognito Hosted UI
    participant Lambda as Trigger Post-Confirmacion
    participant Storage as sessionStorage

    Usuario->>SPA: Clic en 'Iniciar Sesion'
    Note over SPA: Genera code_verifier y code_challenge (SHA-256)
    SPA->>Cognito: Redireccion a Hosted UI (/oauth2/authorize)<br/>response_type=code & code_challenge & code_challenge_method=S256
    Usuario->>Cognito: Ingresa credenciales o se registra
    opt Registro de Usuario Nuevo
        Cognito->>Lambda: Ejecuta trigger Post-Confirmacion
        Lambda->>Cognito: Asigna usuario al grupo 'jugadores' sin intervencion manual
    end
    Cognito-->>SPA: Redirige a /callback?code=AUTH_CODE
    SPA->>Cognito: POST /oauth2/token (Canje de code + code_verifier)
    Cognito-->>SPA: Retorna tokens (access_token, id_token, refresh_token)
    SPA->>Storage: Guarda access_token en sessionStorage (prohibido localStorage)
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
    SPA->>GW: GET http://localhost:8080/v1/biblioteca (Authorization: Bearer JWT)
    GW->>GW: Valida token con JWKS (RSA, iss, exp, client_id, token_use=access)
    GW->>BFF: Proxy GET http://localhost:3001/v1/biblioteca (Propaga Bearer JWT)
    Note over BFF: Valida token y extrae claim sub (prohibido recibir userId en URL)
    par Llamadas concurrentes del BFF
        BFF->>MSBib: GET http://localhost:3004/v1/biblioteca (Filtra por sub)
        MSBib-->>BFF: Retorna [Licencia{id, juegoId, usuarioSub}]
    and
        BFF->>MSCat: GET http://localhost:3002/v1/catalogo
        MSCat-->>BFF--: Retorna [Juego{id, titulo, precio, imagen}]
    end
    Note over BFF: Cruza datos: licencia.juego = catalogo.find(id)
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
    SPA->>GW: DELETE http://localhost:8080/v1/licencias/lic-99 (Bearer JWT Admin)
    GW->>GW: Valida token y grupo 'administradores'
    GW->>BFF: Proxy DELETE http://localhost:3001/v1/licencias/lic-99
    Note over BFF: Verifica pertenencia al grupo 'administradores' (403 si falla)
    
    BFF->>MSBib: DELETE http://localhost:3004/v1/licencias/lic-99
    MSBib-->>BFF: Retorna {mensaje, licenciaEliminada}
    
    BFF->>MSAud: POST http://localhost:3005/v1/auditoria<br/>{adminSub, usuarioSub, juegoId, licenciaId, motivo}
    MSAud-->>BFF: Retorna {id, ...datos, timestamp}
    
    BFF-->>GW: HTTP 200 OK {mensaje: 'Licencia revocada exitosamente', auditoria}
    GW-->>SPA: HTTP 200 OK
    SPA-->>Admin: Actualiza lista; la licencia desaparece
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
