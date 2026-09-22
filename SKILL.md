---
name: vidalstore-ep1
description: >-
  Auditoría, verificación estricta y preparación técnica integral para la Evaluación Parcial N°1 (EP1) Caso VidalStore de DSY1107 - Desarrollo Cloud Native I (DUOC UC).
  Usar esta skill siempre que se requiera validar, desarrollar, corregir o auditar código de frontend, gateway, BFF o microservicios, asegurando el cumplimiento al 100% de la rúbrica oficial (IE1 a IE10), las precisiones de "EP1-aclaraciones.pdf", la clase magistral D6 ("Git en serio y defender una arquitectura") y las respuestas del profesor Umbingelelo en el foro.
---

# VidalStore EP1 — Skill de Aseguramiento de Calidad y Cumplimiento al 100%

Esta skill actúa como el estándar de control de calidad, auditoría técnica y preparación de defensa para la **Evaluación Parcial N°1 (Caso VidalStore)** de la asignatura **DSY1107 - Desarrollo Cloud Native I**.

Integra las fuentes normativas obligatorias del encargo:
1. **`EP1-aclaraciones.pdf`**: Documento oficial del profesor Cristian Calderón (`Umbingelelo`), el cual complementa el enunciado y rige sobre él.
2. **`EP1-Caso-VidalStore.pdf`**: Enunciado de negocio, arquitectura objetivo y rúbrica oficial (indicadores IE1 a IE10).
3. **`Pulso.pdf`**: Guía oficial del Laboratorio L4 ("La cadena completa") y preparación metodológica ("El puente a EP1: tramos 10 al 12") del profesor Cristian Calderón, con las 8 preguntas oficiales de la defensa, pruebas de la cadena y la resolución de la trampa de Cognito.
4. **`D6-Git-en-serio-y-defender-una-arquitectura.html`**: Clase magistral oficial de Semana 7 sobre entrega técnica, higiene de Git, el reloj de 15 minutos, los 5 flujos de defensa de punta a punta y el método de respuesta en 4 pasos.
5. **Resoluciones del foro GitHub (`Umbingelelo/DSY1107-Foro-2026-02`)**: Criterios de evaluación, commits estimados, Hosted UI, idempotencia y defensa en profundidad.
6. **`Plan_VidalStore_EP1.pdf`**: Plan de trabajo específico del grupo (3 integrantes: David, Oscar e Iván).

> [!IMPORTANT]
> **Ponderación Real de la EP1 (Clase D6 Slide 3):**
> * **El Código (40% de la EP1)**: Lo entrega el grupo. Se congela a las 23:59 hrs en el commit de la rama `main` declarado en la plantilla de entrega en AVA, y se revisa después.
> * **La Presentación / Defensa Técnica (60% de la EP1)**: Es **estrictamente individual**. La rinde cada integrante por separado y vale más que todo el código junto. Un estudiante con el sistema perfecto reprobará si no puede justificar las decisiones de arquitectura ni rastrear un dato por las 4 capas.

---

## 1. Reglas Innegociables del Encargo (Checklist Maestro)

Cualquier cambio de código o revisión en los repositorios DEBE cumplir estrictamente con:

1. **Una Sola Dirección y Llamada en el Frontend**:
   - Angular (`vidalstore-frontend`) habla **únicamente** con el API Gateway (`http://localhost:8080`).
   - Jamás invoca al BFF ni a los microservicios de forma directa.
   - El interceptor HTTP tiene una lista blanca explícita con **una sola entrada** (`http://localhost:8080`).
   - **Distinción clave del profesor Umbingelelo**: Las rutas del frontend (`/catalogo`, `/biblioteca`, `/callback`, etc.) son rutas del enrutador SPA de Angular para saber qué componente renderizar y no tienen restricción. Las rutas que deben ir por una sola dirección son las llamadas de red hacia la API. Desde el frontend solo se hace **UNA llamada** a la API del Gateway por acción/vista; posteriormente el **BFF** realiza múltiples llamadas internas concurrentes hacia los microservicios para orquestar y agregar los datos (ej: `GET /v1/biblioteca` llama internamente a biblioteca y catálogo; `DELETE /v1/licencias/:id` llama a biblioteca y auditoría).
2. **Token en `sessionStorage`**:
   - Configurado en `main.ts` con `cognitoUserPoolsTokenProvider.setKeyValueStorage(sessionStorage)`.
   - Prohibido dejar el token en `localStorage` (hallazgo forense del caso).
3. **Login Externo con Hosted UI**:
   - Obligatorio `signInWithRedirect()` de AWS Amplify (Authorization Code con PKCE).
   - Prohibido formularios propios de usuario/clave o flujos implícitos/ROPC.
   - **Angular SPA sin secreto de cliente**: El App Client público de Angular jamás debe tener `client_secret` (crearlo con secret es el error clásico de SPA). `userPoolId` y `clientId` son públicos y van en el frontend.
4. **Sin Vistas Públicas**:
   - El catálogo `/catalogo` y la biblioteca `/biblioteca` exigen sesión activa (`canActivate: [sesionGuard]`). En la plataforma solo son públicos el login/callback.
5. **Defensa en Profundidad (Validación en Ambos Saltos)**:
   - **Gateway (NestJS)**: Autentica. Valida token contra el JWKS (firma, emisor, vigencia, tipo de token y app client). Responde `401 Unauthorized` si falla.
   - **BFF / Microservicios**: Autoriza por rol (`cognito:groups`) y busca datos. Responde `403 Forbidden` si el rol no alcanza.
   - **Cierre por detrás**: Si el BFF o un microservicio recibe una petición sin token, responde `401 Unauthorized`.
6. **Resolución de Biblioteca por `sub`**:
   - `GET /v1/biblioteca` resuelve las licencias del usuario **únicamente** a través del claim `sub` del JWT. Prohibido recibir `userId` por parámetro de ruta, query o body (prevención de BOLA / IDOR).
7. **Idempotencia en Compras**:
   - `POST /v1/compras`: Un usuario solo puede tener una licencia por juego. Si ya la posee, responde `409 Conflict`.
8. **Carpeta `data/` con Seed Real**:
   - Cada microservicio debe tener `data/seed.ts` (o `.js`) que consuma al menos una API externa real (FreeToGame, RAWG, etc.) y guarde los datos en un JSON versionado (`data/catalogo.json`). Prohibidos datos inventados a mano.
9. **Resolución de la "Trampa de Cognito" en Auto-registro**:
   - Al registrarse por Managed Login / Hosted UI, Cognito no asigna ningún grupo por omisión (`cognito:groups` viene vacío).
   - **Salida A**: El guard / backend asume por omisión el rol de menor privilegio (`jugadores`) si el arreglo de grupos está vacío.
   - **Salida B**: Trigger Lambda Post-Confirmación en AWS que ejecuta `AdminAddUserToGroup`.
10. **Reglas de Escritura, Identidad y Borrado Lógico**:
    - Endpoints con `@Body()` y `@Param('id', ParseIntPipe)`.
    - El ID del nuevo registro lo asigna el microservicio / persistencia (`Math.max(...) + 1`), jamás el cliente ni el BFF.
    - **Borrado Lógico**: `DELETE` marca el estado como revocado (`devuelto: true` o `estado: 'revocada'`), preservando el registro para trazabilidad y auditoría.
    - **Regla de Oro de Identidad**: La identidad del que actúa nunca se lee del `@Body()`; se extrae siempre de `req.user.sub` (token firmado).
11. **Agregación Concurrente Eficiente en el BFF**:
    - Llamadas internas con `Promise.all` para ejecución concurrente en servidor.
    - Cruces de datos en memoria mediante `new Map()` indexado por ID (complejidad $O(N)$ vs $O(N \times M)$ de `.find()` anidado).
    - Patrón Fail-Fast al arranque con `configService.getOrThrow()`.
12. **Semántica de Códigos HTTP y Prevención de Enumeración**:
    - Si el usuario consulta su propia biblioteca/préstamos y está vacía, debe retornar **`200 OK` con `[]`**, jamás 403 ni 404 (evita vulnerabilidad de enumeración).
    - Verbos HTTP no soportados responden **`405 Method Not Allowed`**.
13. **CORS Estricto**:
    - Únicamente en el Gateway (`app.enableCors({ origin: 'http://localhost:4200' })`). Prohibido `origin: *`.
    - Prohibido configurar CORS en el BFF o microservicios.
14. **Higiene de Repositorios, Git y Checklist de Entrega (D6 Slides 4–11)**:
    - **Historial de Git como Evidencia de Autoría**: Es requisito de admisibilidad obligatorio que **todos los integrantes tengan commits propios**. Un repositorio donde todos los commits pertenecen a una sola persona genera un problema de evaluación antes de comenzar a defender.
    - **Mensajes de Commit con Sentido**: Los commits deben explicar qué cambió y por qué (ej: `Valida el client_id del token en el guard del BFF`; prohibido `cambios`, `asdf`, `arreglos`).
    - **Flujo de Ramas para Grupo Chico (2–3 integrantes)**:
      - `main`: Siempre funciona. Es la rama que clona el docente y de donde se extrae el hash para la entrega.
      - Ramas cortas de feature (`feat/guard-jwt`, duración 2–3 días) que van a `dev`.
      - Pull Request obligatorio para que el compañero revise el código antes de mezclar (garantiza que todos conozcan el código del proyecto).
      - `dev` se mezcla a `main` antes de la entrega final. Prohibido GitFlow sobrecargado con ramas de release innecesarias.
    - **Distinción Estricta entre lo Molesto y lo Grave**:
      - *Molesto (archivos generados)*: `node_modules/`, `dist/`, `.angular/`, `coverage/`, `*.log`, `.DS_Store`. Se resuelve agregando al `.gitignore`, ejecutando `git rm -r --cached` y haciendo commit.
      - *Grave (secretos)*: `.env`, `*.pem`, `*.jks`, `credentials.json`, archivos con `clientSecret` o contraseñas. Si se commitea un secreto, **queda comprometido para siempre** en el historial, clones y caché de GitHub. Borrar el archivo NO alcanza: **la única solución real es rotar la credencial en AWS** donde se emitió.
    - **Checklist de Última Hora antes de las 23:59**:
      1. `git status` limpio en todos los repositorios.
      2. `.gitignore` de Node y Angular verificado.
      3. `dev` mezclado a `main` antes de congelar.
      4. Docente (`cr.calderons` / `Umbingelelo`) agregado como colaborador en **todos** los repositorios privados.
      5. **Hash del último commit de `main`** de cada repositorio declarado en el documento de entrega en AVA. Lo que no se declara no se califica.

---

## 2. Metodología Oficial de la Defensa Técnica (D6 Slides 13–24)

La defensa individual dura exactamente **15 minutos cronometrados por grupo** y recorre flujos completos de punta a punta, no definiciones teóricas sueltas.

### El Reloj de 15 Minutos
| Tramo | Minutos | Qué Ocurre en la Sala |
|---|:---:|---|
| **Paso 1: Procesos y Puertos** | **0 a 1** | Todos los integrantes declaran qué procesos corren y en qué puerto (Angular `4200`, Gateway `8080`, BFF `3000`/`3001`, Microservicios). |
| **Paso 2: Flujos A y B** | **1 a 7** | Un integrante conduce el **Flujo A**, otro integrante conduce el **Flujo B**. Nadie conduce dos flujos seguidos. |
| **Paso 3: Flujos C, D y E** | **7 a 12** | Conducción de los **Flujos C y D**, más 30 segundos del **Flujo E** (abrir el script de seed). |
| **Paso 4: Modificación Señalada** | **12 a 14** | Una modificación por integrante sobre un frente que **no construyó él** (ubicar el archivo, poner el cursor en la línea y explicar qué escribiría y qué pasaría). |
| **Paso 5: La Pregunta del Botón** | **14 a 15** | Pregunta del botón COMPRAR (se evalúa la fundamentación técnica y de negocio, no la postura). |

> [!WARNING]
> Se debe ingresar a la sala con el **sistema ya levantado y la sesión recién iniciada** (el token de Cognito expira en 1 hora). Si el sistema no levanta, solo hay 3 minutos de gracia; luego la defensa continúa en frío sobre el código.

### Los 5 Flujos de Punta a Punta
1. **Flujo A · Identidad**: Un anónimo se convierte en sujeto identificado. Registro y login con Hosted UI + PKCE. La cuenta nueva queda asignada al grupo `jugadores` (resolución de la trampa de Cognito). Distinción: `sub` dice quién eres; `cognito:groups` y `scope` dicen qué puedes hacer.
2. **Flujo B · Lo Propio**: Un sujeto identificado lee lo suyo y solo lo suyo. `GET /v1/biblioteca` resuelto exclusivamente por el claim `sub`, nunca por parámetro. Una sola llamada de red del frontend al Gateway.
3. **Flujo C · Rol Insuficiente**: Un sujeto intenta una acción por sobre su rol. Jugador llama a revocar licencia (`DELETE /v1/licencias/:id`) $\rightarrow$ el backend responde `403 Forbidden` (demostración de que la seguridad reside en el servidor y no en ocultar el botón en la UI).
4. **Flujo D · Por Detrás (Defensa en Profundidad)**: Acceso directo sin pasar por el perímetro. Llamada directa a BFF o microservicio sin token $\rightarrow$ `401 Unauthorized`. Token alterado $\rightarrow$ `401 Unauthorized`. CORS restringido a `localhost:4200` solo en Gateway.
5. **Flujo E · Origen y Trazabilidad**: El dato que se muestra tiene origen rastreable. El catálogo proviene de `data/seed.ts` consumiendo una API externa real hacia `data/catalogo.json`.

### Las 5 Ventanas Obligatorias Abiertas al Iniciar el Turno
1. **Terminal**: Procesos corriendo en sus respectivos puertos.
2. **Navegador**: Aplicación con sesión recién iniciada, pestaña **Red** lista e inspeccionada, pestaña **Application** mostrando el token en `sessionStorage`.
3. **Cliente REST o curl**: Dos tokens listos (jugador y administrador) para la misma ruta (demostrar `403` vs `200`), y llamada directa al BFF sin token (`401`).
4. **Editor de Código**: Pestañas del interceptor HTTP de Angular y del guard de NestJS ya abiertas.
5. **Consola de Cognito**: User pool con grupos, usuarios y los **dos app clients**. (Único componente en la nube; todo lo demás es local).

### Framework de Respuesta en 4 Pasos (1 Minuto por Parada)
Para responder cualquier decisión de arquitectura:
1. **Qué hice**: Nombrar el componente o mecanismo exacto y mostrar la línea de código en el editor.
2. **Qué problema resuelve**: Explicar la necesidad concreta de seguridad, rendimiento o arquitectura.
3. **Qué descarté**: Nombrar explícitamente la alternativa técnica rechazada (el paso que más pesa, demuestra decisión y no copia).
4. **Cómo lo compruebo**: Demostrarlo en vivo en la pantalla (pestaña Red, dos tokens en curl, etc.).

---

## 3. Mapa de Rutas del Sistema (Matriz de Permisos)

| Método | Ruta | Autoriza por | Grupos / Condición | Código de Éxito | Códigos de Error |
|---|---|---|---|:---:|:---:|
| `GET` | `/v1/catalogo` | Scope | `vidalstore/catalogo.leer` (cualquier sesión válida) | `200 OK` | `401`, `403` |
| `POST` | `/v1/catalogo` | Grupo | `editores`, `administradores` | `201 Created` | `400`, `401`, `403` |
| `PUT` | `/v1/catalogo/:juegoId` | Grupo | `editores`, `administradores` | `200 OK` | `400`, `401`, `403`, `404` |
| `POST` | `/v1/compras` | Scope | Sesión válida (`sub` del token). Idempotente | `201 Created` | `400`, `401`, `404`, `409` |
| `GET` | `/v1/biblioteca` | Scope / `sub` | Sesión válida (resuelve por `sub` del token) | `200 OK` | `401`, `403` |
| `GET` | `/v1/licencias` | Grupo | `administradores` (lista licencias de todos) | `200 OK` | `401`, `403` |
| `DELETE` | `/v1/licencias/:licenciaId` | Grupo | `administradores` (revoca licencia) | `200 OK` | `401`, `403`, `404` |
| `GET` | `/v1/auditoria` | Grupo | `administradores` (obligatoria para grupos de 3) | `200 OK` | `401`, `403` |

---

## 4. Procedimiento de Auditoría Técnica

Cuando se active esta skill para revisar el estado del proyecto, seguir este orden de verificación:

### Paso 1: Ejecutar el Script de Auditoría
Ejecutar el script de diagnóstico incluido en la skill:
```bash
python3 .agents/skills/vidalstore-ep1/scripts/audit_ep1.py
```
El script evaluará:
- Existencia y puertos de los servicios (`frontend`: 4200, `gateway`: 8080, `backend/bff`: 3001).
- Presencia de `sessionStorage` en el frontend.
- Rutas expuestas en el Gateway vs Backend.
- Conteo y autores de commits por repositorio.
- Verificación de `.gitignore` (ignorancia de `.env`, `node_modules/`, `dist/`).
- Existencia de la carpeta `data/` y script `seed`.

### Paso 2: Verificar la Cadena de Peticiones en el Gateway
Confirmar que el Gateway (`vidalstore-gateway`):
1. Expone los endpoints bajo el prefijo `/v1/` para coincidir exactamente con el servicio de Angular.
2. Contiene controladores proxy para:
   - `/v1/catalogo` (GET, POST, PUT)
   - `/v1/biblioteca` (GET)
   - `/v1/compras` (POST)
   - `/v1/licencias` (GET, DELETE)
   - `/v1/auditoria` (GET)
3. Reenvía el encabezado `Authorization` en cada llamada proxy hacia el Backend/BFF.

### Paso 3: Verificar las 4 Pruebas Obligatorias de Gateway (IE10)
Deben estar documentadas en el README y ser reproducibles con `curl`:
1. **Petición sin token**:
   `curl -i http://localhost:8080/v1/catalogo` -> Retorna `401 Unauthorized`.
2. **Petición con token alterado (firma inválida)**:
   `curl -i -H "Authorization: Bearer <token_modificado>" http://localhost:8080/v1/catalogo` -> Retorna `401 Unauthorized`.
3. **Petición con token de otra aplicación (App Client 2)**:
   `curl -i -H "Authorization: Bearer <token_client2>" http://localhost:8080/v1/catalogo` -> Retorna `401 Unauthorized`.
4. **Petición con token válido pero rol insuficiente**:
   `curl -i -H "Authorization: Bearer <token_jugador>" -X DELETE http://localhost:8080/v1/licencias/lic-123` -> Retorna `403 Forbidden`.

### Paso 4: Las 6 Pruebas de la Cadena Completa (Pulso.pdf Tramo 9)
Comprobar el aislamiento y la resiliencia en la terminal:
1. **Sin token contra Gateway**: Retorna `401` (Gateway corta en el borde).
2. **Token válido de jugador**: Retorna `200` con datos agregados en una sola llamada.
3. **Token de jugador a ruta administrativa (`/licencias`)**: Retorna `403` (cortado por el `RolGuard` del BFF).
4. **Token de administrador a ruta administrativa**: Retorna `200` con todos los registros.
5. **Petición directa al BFF (`:3001`) sin pasar por Gateway**: Retorna `401` (defensa en profundidad; el BFF se protege solo).
6. **Microservicio interno caído**: Retorna `503 Service Unavailable` indicando qué microservicio falló. Al restablecerlo, vuelve a responder `200` de inmediato sin reiniciar el Gateway ni el BFF.

---

## 5. Guías de Referencia Detalladas

Para profundizar en áreas específicas del encargo, consultar los siguientes documentos de referencia adjuntos:
- [Rúbrica Oficial Detallada (IE1 a IE10)](./references/rubrica_completa.md): Ponderaciones, criterios destacados, peso del 60% de la defensa y causas de nota mínima.
- [Arquitectura de 4 Capas y Códigos HTTP](./references/arquitectura_4_capas.md): Responsabilidad de cada componente, CORS, flujo de petición de arriba a abajo y distinción Cloud vs Local.
- [Configuración de Cognito y Seguridad](./references/cognito_y_seguridad.md): User Pool, Resource Server, grupos, scopes, App Clients, auto-registro y Lambda trigger.
- [Banco de Preguntas Oficiales para la Defensa Técnica](./references/preguntas_defensa.md): Las 8 preguntas literales de `Pulso.pdf` §12.2 + 10 preguntas complementarias + Guion oficial de D6 con preguntas parada por parada, señales de alarma y framework de 4 pasos.

---

## 6. Regla Git para el Asistente

> [!CAUTION]
> **RECORDATORIO DE REGLA DEL USUARIO:**
> **NO USAR NINGÚN COMANDO DE GIT SIN AUTORIZACIÓN EXPRESA DEL USUARIO.**
> Siempre explicar qué hace el comando y por qué se necesita antes de solicitar su ejecución.
