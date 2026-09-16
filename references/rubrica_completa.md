# Rúbrica Oficial y Criterios de Evaluación · EP1 VidalStore

La Evaluación Parcial N°1 pondera un **40% de la nota final del ramo** y se compone de dos instancias:
1. **Encargo Técnico Grupal (40%)**: Evaluación del código en los repositorios entregados en el AVA.
2. **Presentación / Defensa Técnica Individual (60%)**: Ronda de preguntas y pruebas prácticas en vivo en el laboratorio sobre el código propio.

---

## 1. Encargo Grupal (40% de la EP1)

### IE1. Identidad en el Frontend (60% del encargo)
* **Logro Destacado (100%)**:
  - Implementa registro, login y logout utilizando AWS Amplify contra el User Pool de Cognito.
  - Flujo OIDC **Authorization Code con PKCE** obligatorio con Hosted UI (`signInWithRedirect()`).
  - `sessionGuard` en Angular para proteger rutas privadas (`/catalogo`, `/biblioteca`). No hay catálogo público.
  - Interceptor HTTP que adjunta el `access_token` en el encabezado `Authorization: Bearer <token>` **únicamente** a la URL del Gateway (lista blanca de una sola entrada).
  - Almacenamiento del token configurado explícitamente en `sessionStorage` (`cognitoUserPoolsTokenProvider.setKeyValueStorage(sessionStorage)`).
  - Vistas y acciones condicionadas visualmente según el rol del usuario (`cognito:groups`).
  - Botón de compra operativo que crea la licencia e impacta la biblioteca.
* **No Logrado (0%)**:
  - Flujo distinto a Authorization Code con PKCE (ej: ROPC, flujo implícito o formulario propio de usuario/clave).
  - Rutas privadas sin guard o catálogo abierto sin autenticación.
  - Token almacenado por defecto en `localStorage`.
  - Interceptor que envía el token a cualquier dominio o a múltiples URLs.

### IE2. Validación del Token en el Backend (40% del encargo)
* **Logro Destacado (100%)**:
  - El Gateway (NestJS) valida completamente el token contra el JWKS público del User Pool:
    1. **Firma criptográfica** (asymmetric RSA con clave pública del JWKS).
    2. **Emisor (`iss`)**: Debe coincidir con `https://cognito-idp.<region>.amazonaws.com/<userPoolId>`.
    3. **Vigencia temporal (`exp`, `nbf`)**: Token no expirado.
    4. **Tipo de token (`token_use`)**: Debe ser `access` (rechazar `id_token` si se presenta como credencial de API).
    5. **Aplicación de origen (`client_id`)**: Rechazar tokens emitidos para otros App Clients.
  - Defensa en profundidad: El microservicio / BFF detrás del gateway valida nuevamente el token por su cuenta.
  - Códigos HTTP estrictos: `401 Unauthorized` si el token es inválido o no existe; `403 Forbidden` si el rol/scope no alcanza.
* **No Logrado (0%)**:
  - Validar solo la presencia del token sin verificar firma, emisor o app client contra el JWKS.
  - Aceptar tokens emitidos para otra aplicación o tokens de identidad (`id_token`).
  - No propagar ni re-validar el token en el segundo salto.

---

## 2. Presentación y Defensa Individual (60% de la EP1)

Cada integrante del equipo defiende de forma individual sobre el código de los repositorios.

| Indicador | Ponderación | Criterio de Logro Destacado (100%) | Causa de No Logrado (0%) |
|---|:---:|---|---|
| **IE3. Rutas en el Gateway** | **13%** | Las siete rutas del punto 4.3 (y la octava de auditoría para grupos de 3) creadas en el Gateway, enrutadas hacia el backend/BFF y probadas con métodos HTTP correctos. | No hay rutas en el gateway, o el frontend llama directamente al microservicio saltándose el gateway. |
| **IE4. Configuración de CORS** | **7%** | CORS configurado **exclusivamente en el gateway**, restringido al origen de Angular (`http://localhost:4200`) y únicamente a los métodos que las rutas usan. El estudiante explica qué habilitó y por qué. | No hay configuración de CORS, o está abierta con comodín (`*`) a todo origen. CORS configurado en backend/microservicios innecesariamente. |
| **IE5. User Pool y Roles** | **10%** | User pool en AWS con los 3 grupos creados (`jugadores`, `editores`, `administradores`) y usuarios creados en cada uno. Mostrado en consola en vivo. | No existe el user pool o faltan grupos. |
| **IE6. Aplicación Cliente en Cognito** | **10%** | App client público sin secreto de cliente, con URLs de retorno (`http://localhost:4200/callback`) y scopes configurados. El **segundo app client** para la prueba 3 también está creado y listo. | No existe el app client, o tiene `client_secret` habilitado (haciendo fallar el flujo público de SPA). |
| **IE7. Flujo de Registro y Login** | **10%** | Dominio de Cognito operativo, pantalla Hosted UI funcional. Un usuario nuevo se registra en vivo en la demo y puede ingresar de inmediato con su cuenta. | No hay dominio o pantalla de autenticación operativa. |
| **IE8. OIDC Authorization Code con PKCE** | **15%** | El estudiante muestra en el navegador (pestaña Red / Network) los parámetros del flujo (`response_type=code`, `code_challenge`, `code_challenge_method=S256`) y explica técnicamente por qué se usa PKCE y no el flujo implícito. | El flujo implementado no es PKCE, o el estudiante no puede acreditarlo ni explicar sus parámetros. |
| **IE9. Autorización de Rutas con JWT** | **20%** | Todas las rutas protegidas en el backend/gateway. Repartición correcta entre Scopes (para la app) y Grupos (para roles). Respuestas `401` y `403` exactamente donde corresponden. | Las rutas no validan el token, o no diferencian entre falta de autenticación (401) y falta de autorización por rol (403). |
| **IE10. Evidencias y Pruebas del Gateway** | **15%** | El README documenta y el alumno ejecuta en vivo las 4 pruebas del Gateway con sus respuestas: <br>1. Sin token (`401`)<br>2. Token alterado (`401`)<br>3. Token de otra aplicación (`401`)<br>4. Token válido con rol insuficiente (`403`). | Demostración fallida o ausencia de evidencias en el repositorio. |

---

## 3. Condiciones Administrativas de Entrega (Checklist Crítico)

1. **Fecha Límite**: Lunes 21 de septiembre de 2026 a las 23:59 hrs (en AVA).
2. **Formato en AVA**: Documento PDF con los enlaces a **todos** los repositorios privados y el hash del último commit de la rama `main` de cada uno.
3. **Invitación a GitHub**: El docente (`Umbingelelo`) DEBE estar invitado y activo como colaborador en todos los repositorios. *Nota del profesor: "No olviden invitarme o tendrán la nota mínima".*
4. **GitFlow y Rama `main`**:
   - La rama `main` debe estar completamente al día al momento de la entrega, ya que es la que se clona para calificar.
   - Las características deben trabajarse en ramas `feature/...` y mezclarse hacia `dev`, y `dev` hacia `main`.
5. **Cantidad de Commits**: Rango esperado de **100 a 200 commits en total** sumando todos los repositorios.
6. **Limpieza de Secretos**: No commitear `.env` reales, API keys, client secrets o contraseñas. El comando `git grep -iE "password|secret|token|cookie"` debe salir limpio.
