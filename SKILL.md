---
name: vidalstore-ep1
description: >-
  Auditoría, verificación estricta y preparación técnica integral para la Evaluación Parcial N°1 (EP1) Caso VidalStore de DSY1107 - Desarrollo Cloud Native I (DUOC UC).
  Usar esta skill siempre que se requiera validar, desarrollar, corregir o auditar código de frontend, gateway, BFF o microservicios, asegurando el cumplimiento al 100% de la rúbrica oficial (IE1 a IE10), las precisiones de "EP1-aclaraciones.pdf" y las respuestas del profesor Umbingelelo en el foro.
---

# VidalStore EP1 — Skill de Aseguramiento de Calidad y Cumplimiento al 100%

Esta skill actúa como el estándar de control de calidad, auditoría técnica y preparación de defensa para la **Evaluación Parcial N°1 (Caso VidalStore)** de la asignatura **DSY1107 - Desarrollo Cloud Native I**.

Integra las fuentes normativas obligatorias del encargo:
1. **`EP1-aclaraciones.pdf`**: Documento oficial del profesor Cristian Calderón (`Umbingelelo`), el cual complementa el enunciado y rige sobre él.
2. **`EP1-Caso-VidalStore.pdf`**: Enunciado de negocio, arquitectura objetivo y rúbrica oficial (indicadores IE1 a IE10).
3. **Resoluciones del foro GitHub (`Umbingelelo/DSY1107-Foro-2026-02`)**: Criterios de evaluación, commits estimados, Hosted UI, idempotencia y defensa en profundidad.
4. **`Plan_VidalStore_EP1.pdf`**: Plan de trabajo específico del grupo (3 integrantes: David, Oscar e Iván).

---

## 1. Reglas Innegociables del Encargo (Checklist Maestro)

Cualquier cambio de código o revisión en los repositorios DEBE cumplir estrictamente con:

1. **Una Sola Dirección en el Frontend**:
   - Angular (`vidalstore-frontend`) habla **únicamente** con el API Gateway (`http://localhost:8080`).
   - Jamás invoca al BFF ni a los microservicios de forma directa.
   - El interceptor HTTP tiene una lista blanca explícita con **una sola entrada** (`http://localhost:8080`).
2. **Token en `sessionStorage`**:
   - Configurado en `main.ts` con `cognitoUserPoolsTokenProvider.setKeyValueStorage(sessionStorage)`.
   - Prohibido dejar el token en `localStorage` (hallazgo forense del caso).
3. **Login Externo con Hosted UI**:
   - Obligatorio `signInWithRedirect()` de AWS Amplify (Authorization Code con PKCE).
   - Prohibido formularios propios de usuario/clave o flujos implícitos/ROPC.
4. **Sin Vistas Públicas**:
   - El catálogo `/catalogo` y la biblioteca `/biblioteca` exigen sesión activa (`canActivate: [sesionGuard]`). En la plataforma solo son públicos el login/callback.
5. **Defensa en Profundidad (Validación en Ambos Saltos)**:
   - **Gateway (NestJS)**: Autentica. Valida token contra el JWKS (firma, emisor, vigencia, tipo de token y app client). Responde `401 Unauthorized` si falla.
   - **BFF / Microservicios**: Autoriza por rol (`cognito:groups`) y busca datos. Responde `403 Forbidden` si el rol no alcanza.
   - **Cierre por detrás**: Si el BFF o un microservicio recibe una petición sin token, responde `401 Unauthorized`.
6. **Resolución de Biblioteca por `sub`**:
   - `GET /v1/biblioteca` resuelve las licencias del usuario **únicamente** a través del claim `sub` del JWT. Prohibido recibir `userId` por parámetro de ruta, query o body.
7. **Idempotencia en Compras**:
   - `POST /v1/compras`: Un usuario solo puede tener una licencia por juego. Si ya la posee, responde `409 Conflict`.
8. **Carpeta `data/` con Seed Real**:
   - Cada microservicio debe tener `data/seed.ts` (o `.js`) que consuma al menos una API externa real (RAWG, FreeToGame, PokeAPI, etc.) y guarde los datos en un JSON versionado (`data/catalogo.json`). Prohibidos datos inventados a mano.
9. **Asignación Automática de Grupo en Cognito**:
   - El registro de usuario nuevo asigna automáticamente el grupo `jugadores` mediante trigger Lambda Post-Confirmación, sin intervención manual en AWS.
10. **CORS Estricto**:
    - Únicamente en el Gateway. Origen restringido a `http://localhost:4200` y métodos HTTP utilizados.
11. **Higiene de Repositorios y Git**:
    - Repositorios separados y privados.
    - Flujo GitFlow: `main` recibe merges de `dev`, y `dev` de `feature/...`.
    - Docente (`Umbingelelo`) agregado como colaborador en **todos** los repositorios.
    - Meta estimada de commits: **entre 100 y 200 commits en total** entre todos los repositorios.
    - Cero secretos commiteados: verificación obligatoria con `git grep -iE "password|secret|token|cookie"`.

---

## 2. Mapa de Rutas del Sistema (Matriz de Permisos)

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

## 3. Procedimiento de Auditoría Técnica

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
- Conteo de commits por repositorio.
- Búsqueda de posibles credenciales o secretos en el código fuente.
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
   `curl -i http://localhost:8080/v1/catalogo` -> Debe retornar `401 Unauthorized`.
2. **Petición con token alterado (firma inválida)**:
   `curl -i -H "Authorization: Bearer <token_modificado>" http://localhost:8080/v1/catalogo` -> Debe retornar `401 Unauthorized`.
3. **Petición con token de otra aplicación (App Client 2)**:
   `curl -i -H "Authorization: Bearer <token_client2>" http://localhost:8080/v1/catalogo` -> Debe retornar `401 Unauthorized`.
4. **Petición con token válido pero rol insuficiente**:
   `curl -i -H "Authorization: Bearer <token_jugador>" -X DELETE http://localhost:8080/v1/licencias/lic-123` -> Debe retornar `403 Forbidden`.

---

## 4. Guías de Referencia Detalladas

Para profundizar en áreas específicas del encargo, consultar los siguientes documentos de referencia adjuntos:
- [Rúbrica Oficial Detallada (IE1 a IE10)](./references/rubrica_completa.md): Ponderaciones, criterios destacados y causas de nota mínima.
- [Arquitectura de 4 Capas y Códigos HTTP](./references/arquitectura_4_capas.md): Responsabilidad de cada componente, CORS y matriz de códigos de error.
- [Configuración de Cognito y Seguridad](./references/cognito_y_seguridad.md): User Pool, Resource Server, grupos, scopes, App Clients y trigger Lambda.
- [Preguntas Típicas de la Defensa Técnica](./references/preguntas_defensa.md): Argumentación y respuestas modelo para la defensa individual de Oscar, David e Iván.

---

## 5. Regla Git para el Asistente

> [!CAUTION]
> **RECORDATORIO DE REGLA DEL USUARIO:**
> **NO USAR NINGÚN COMANDO DE GIT SIN AUTORIZACIÓN EXPRESA DEL USUARIO.**
> Siempre explicar qué hace el comando y por qué se necesita antes de solicitar su ejecución.
