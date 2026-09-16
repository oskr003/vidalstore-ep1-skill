# Arquitectura de 4 Capas y Flujo de Comunicación · VidalStore

Según el documento oficial **`EP1-aclaraciones.pdf`**, el sistema VidalStore se organiza en cuatro capas con responsabilidades estrictamente desacopladas:

```text
┌────────────────────────────────────────────────────────┐
│  1. Frontend: Angular (Single Page Application)       │
│  - Habla con UNA sola dirección (el API Gateway)       │
│  - Token vive en sessionStorage                        │
│  - Interceptor con lista blanca de una sola entrada    │
└───────────────────────────┬────────────────────────────┘
                            │ Authorization: Bearer <access_token>
                            ▼
┌────────────────────────────────────────────────────────┐
│  2. API Gateway: NestJS (Puerto 8080)                  │
│  - AUTENTICA: ¿Este token sirve?                       │
│  - Valida firma, emisor, vigencia, tipo y client_id    │
│  - Configura CORS (solo origen de Angular)             │
│  - Si falla el token: 401 Unauthorized                 │
└───────────────────────────┬────────────────────────────┘
                            │ Authorization: Bearer <access_token> (reenviado)
                            ▼
┌────────────────────────────────────────────────────────┐
│  3. BFF (Backend for Frontend): NestJS                 │
│  - AUTORIZA: ¿Este usuario tiene el rol necesario?     │
│  - Lee cognito:groups y aplica reglas de negocio       │
│  - Si el rol no alcanza: 403 Forbidden                 │
│  - Si entra sin token: 401 Unauthorized                │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│  4. Microservicios: Node.js (Catálogo, Compras, etc.)  │
│  - EXPONEN las rutas del punto 4.3 y persisten datos   │
│  - Carpeta data/ con seed que consume API externa real │
│  - Si entra sin token: 401 Unauthorized                │
└────────────────────────────────────────────────────────┘
```

---

## Detalle de Cada Capa

### Capa 1: Angular (Frontend)
* **Stack**: Angular con AWS Amplify.
* **Dirección Base**: Únicamente la del Gateway (`http://localhost:8080`). No conoce la dirección de ninguna otra capa.
* **Almacenamiento del Token**: `sessionStorage` configurado en `main.ts`:
  ```typescript
  import { Amplify } from 'aws-amplify';
  import { cognitoUserPoolsTokenProvider } from 'aws-amplify/auth/cognito';
  import { sessionStorage } from 'aws-amplify/utils';

  Amplify.configure(authConfig);
  cognitoUserPoolsTokenProvider.setKeyValueStorage(sessionStorage);
  ```
* **Lista Blanca del Interceptor**: Debe contener **una sola entrada** (`http://localhost:8080`). Si tuviera más, significaría que el frontend está intentando hablarle a más de una capa.
* **Guards de Rutas**: `sessionGuard` en Angular impide la navegación hacia `/catalogo` o `/biblioteca` si no hay sesión iniciada. Redirige a Cognito Hosted UI mediante `signInWithRedirect()`.

---

### Capa 2: API Gateway (NestJS)
* **Stack**: NestJS (puerto estándar `8080`).
* **Responsabilidad Principal: AUTENTICAR**:
  * Verifica si la petición trae un token válido.
  * Descarga las claves públicas desde el JWKS del User Pool:
    `https://cognito-idp.<region>.amazonaws.com/<userPoolId>/.well-known/jwks.json`
  * Valida los 5 elementos del token:
    1. **Firma criptográfica**: Verifica con la clave pública adecuada (obtenida según el encabezado `kid` del JWT).
    2. **Emisor (`iss`)**: Debe ser exactamente la URL del User Pool.
    3. **Expiración (`exp`)**: Token vigente en el tiempo.
    4. **Tipo de token (`token_use`)**: Debe ser estrictamente `'access'`.
    5. **Cliente (`client_id`)**: Debe coincidir con el App Client de la tienda.
* **CORS**:
  * Es el **único** componente del sistema que habilita CORS.
  * Restringido a:
    * `origin`: `'http://localhost:4200'`
    * `methods`: `'GET, POST, PUT, DELETE, OPTIONS'`
    * `allowedHeaders`: `'Authorization, Content-Type'`
* **Proxy de Rutas**:
  * El Gateway intercepta las peticiones dirigidas a `/v1/*` y las reenvía al Backend/BFF.
  * **Muy importante**: Siempre reenvía el encabezado `Authorization: req.headers['authorization']` para mantener la defensa en profundidad.

---

### Capa 3: BFF (Backend for Frontend - NestJS)
* **Stack**: NestJS (puede estar en el mismo servicio de backend o desacoplado).
* **Responsabilidad Principal: AUTORIZAR**:
  * Determina si el usuario autenticado tiene los permisos/roles necesarios para la operación solicitada.
  * Inspecciona el claim `cognito:groups` del payload del JWT:
    * `jugadores`: Acceso a catálogo, compras y biblioteca propia.
    * `editores`: Lo anterior + crear/editar juegos en catálogo.
    * `administradores`: Lo anterior + ver todas las licencias, revocar licencias (`DELETE /v1/licencias/:id`) y ver auditoría.
  * Si el rol es insuficiente, responde inmediatamente con **`403 Forbidden`**.
  * Si una petición llega sin token (llamada directa por detrás), responde **`401 Unauthorized`**.

---

### Capa 4: Microservicios (Catálogo, Compras, Licencias)
* **Stack**: Node.js (NestJS o Express).
* **Responsabilidad**:
  * Exponen los 7 endpoints del punto 4.3 (y el 8vo de auditoría).
  * Manejan el estado y la persistencia de datos (en memoria o JSON).
  * **Carpeta `data/`**:
    * Debe existir una carpeta `data/` con un script de semilla (`seed.ts` o `seed.js`).
    * El script debe consumir una **API externa real** (por ejemplo RAWG, PokeAPI, FreeToGame, Open Critic) para alimentar el catálogo inicial.
    * Los datos generados deben quedar almacenados en un archivo versionado (ej: `data/catalogo.json`).
  * Si se invoca sin token, responde **`401 Unauthorized`**.

---

## Matriz de Códigos de Respuesta HTTP

| Situación | Quién Responde | Código HTTP |
|---|---|:---:|
| No hay token en la petición | API Gateway (o BFF/Microservicio si lo llaman directo) | `401 Unauthorized` |
| Token alterado, expirado o firma corrupta | API Gateway | `401 Unauthorized` |
| Token emitido para otro App Client | API Gateway | `401 Unauthorized` |
| Token es un `id_token` en vez de `access_token` | API Gateway | `401 Unauthorized` |
| Token válido, pero el usuario no tiene el grupo/rol requerido | BFF | `403 Forbidden` |
| Token válido, pero falta el scope de la aplicación | Gateway / BFF | `403 Forbidden` |
| Juego no encontrado en catálogo al comprar o editar | Microservicio Catálogo / Compras | `404 Not Found` |
| Usuario ya posee una licencia para el juego comprado | Microservicio Compras | `409 Conflict` |
| Operación exitosa de consulta o actualización | Microservicio | `200 OK` |
| Operación exitosa de creación (nuevo juego, compra) | Microservicio | `201 Created` |

---

## Concepto Clave para Defensa: Defensa en Profundidad
**Pregunta**: *¿Por qué el BFF o los microservicios vuelven a validar el token si el API Gateway ya lo hizo?*
**Respuesta**: *Ninguna capa interior debe confiar ciegamente en que la capa anterior hizo su trabajo o en que la red interna es inviolable. Si un atacante o un contenedor comprometido envía una petición directamente a la IP/puerto interno del backend saltándose el gateway, el microservicio cortará la comunicación con un 401 si no hay token, evitando la fuga o manipulación de datos.*
