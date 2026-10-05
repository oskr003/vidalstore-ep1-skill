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

## 3. Condiciones Administrativas de Entrega (Checklist Crítico de la Clase D6)

1. **Fecha Límite**: Lunes 21 de septiembre de 2026 a las 23:59 hrs (en AVA).
2. **Formato de Entrega en AVA**:
   - Documento PDF que contiene los enlaces a **todos** los repositorios privados y el **hash del último commit de la rama `main`** de cada uno.
   - *Regla de oro*: Lo que no se declara en la plantilla de entrega, no se califica.
3. **Invitación a GitHub**: El docente (`Umbingelelo` / `cr.calderons`) DEBE estar invitado y activo como colaborador en **todos** los repositorios privados. Un repositorio al que el docente no pueda acceder cuenta como no entregado (nota mínima 1.0).
4. **Commits Propios Obligatorios por Integrante (Evidencia de Autoría)**:
   - Se exige que **todos los integrantes tengan commits propios y significativos**.
   - El historial de Git es la evidencia legal de quién trabajó. Un grupo donde todos los commits son de una sola persona tiene un problema de admisibilidad previo a defender.
   - Mensajes de commit con sentido: deben explicar qué cambió y por qué (ej: `Valida client_id en guard del BFF`; prohibido `cambios`, `asdf`, `arreglos`).
5. **Estrategia de Ramas para Grupo Chico (2 a 3 personas)**:
   - `main`: Siempre funciona. Es la rama que se clona para calificar y de donde sale el hash declarado.
   - `dev`: Rama de integración previa.
   - Ramas cortas de funcionalidad (`feat/guard-jwt`, duración 2 a 3 días).
   - **Pull Request obligatorio**: El compañero revisa y comenta antes de mezclar a `dev`. Permite que todos conozcan el código ajeno para la defensa individual.
   - Prohibido GitFlow sobrecargado con ramas de release innecesarias.
6. **Distinción Crítica: Archivos Generados vs Secretos Comprometidos**:
   - **Molesto (Generado)**: `node_modules/`, `dist/`, `.angular/`, `coverage/`, `*.log`, `.DS_Store`. Se resuelve agregando al `.gitignore`, ejecutando `git rm -r --cached` y haciendo commit.
   - **Grave (Secretos)**: `.env`, `*.pem`, `*.jks`, `credentials.json`, `clientSecret` o contraseñas. Si se commitea un secreto, **queda comprometido para siempre** en el historial, clones y caché de GitHub. Borrar el archivo del repositorio NO alcanza: **la única solución real es rotar la credencial en AWS** donde se emitió.
   - **SPA sin secreto de cliente**: El App Client de Angular jamás debe tener `client_secret`. `userPoolId` y `clientId` no son secretos y van en el frontend.
7. **Limpieza y Verificación**:
   - `git status` limpio en todos los repositorios.
   - `git grep -iE "password|secret|token|cookie"` debe salir limpio de credenciales reales.
   - Cantidad de commits esperada: entre **100 y 200 commits en total** sumando todos los repositorios.

---

## 4. Rúbrica Oficial de la Evaluación Parcial N°2 (EP2 · Unidad 2)

La EP2 evalúa la arquitectura de mensajería asíncrona, Docker Compose, clúster de RabbitMQ, persistencia relacional con PostgreSQL y resiliencia con DLQ (Semanas 8 a 10).
* **Ponderación Global**: 40% Encargo Técnico Grupal (IE1 a IE8) + 60% Presentación Técnica Individual (IE9 a IE19).

### 4.1 Encargo Técnico Grupal (40% de la EP2)

| Indicador | Peso en Encargo | Dónde Quedó Resuelto | Criterio de Logro Destacado (100%) | Causa de No Logrado (0%) |
|---|:---:|:---:|---|---|
| **IE1. Centralización de Topología** | **12%** | L6 / L7 Tramo 3 (`topologia.ts` y `topologia.mjs`) | Nombres de colas, exchanges, bindings y routing keys declarados de forma centralizada en objetos inmutables. Ningún string mágico suelto en consumidores o controladores. | Strings de exchanges o colas escritos a mano en los servicios. |
| **IE2. Declaración de Configuración RabbitMQ** | **13%** | L6 / L7 Tramo 3 (`declararTopologia` y `docs/topologia.md`) | Función `declararTopologia` declara todos los exchanges (topic, direct, dlx), colas de trabajo, DLQs y bindings antes de consumir. Documentado en Markdown. | Topología declarada parcialmente o sin DLQs; colas sin argumentos `x-dead-letter-*`. |
| **IE3. Desacoplamiento de Negocio y Mensajería** | **10%** | L7 Tramo 5.3 (`publicador.mjs`) | `topologia.ts` no conoce la lógica de negocio; el microservicio productor publica exclusivamente a través de un módulo `publicador.mjs` desacoplado del servidor HTTP. | Servidor HTTP o lógica de negocio invocando directamente métodos de bajo nivel de `amqplib`. |
| **IE4. Consumidores por Dominio Funcional** | **15%** | L6 / L7 (`src/mensajeria/consumidores/`) | Cuatro consumidores implementados en archivos y módulos NestJS independientes: Avisos, Auditoría, Correos y Cartas Muertas. | Consumidores mezclados en un solo archivo monolítico o sin modularización en NestJS. |
| **IE5. Confirmación ACK y Manejo de Errores** | **20%** | L7 Tramos 2, 3 y 4 | `canal.ack(mensaje)` tras persistir con éxito; rechazo explícito `canal.nack(mensaje, false, false)` hacia DLQ para errores del mensaje; `canal.ack(mensaje)` para colisiones por duplicado (`23505`); reintentos (`conReintentos`) ante fallos de conexión. Rutas documentadas en README. | Usar `noAck: true`, hacer ack antes de persistir, o mandar duplicados legítimos a la DLQ. |
| **IE6. Microservicio Administrador** | **13%** | L8 / Semana 10 (`vidalstore-admin`) | Microservicio NestJS independiente en puerto `:3020` con `RabbitAdminService` para gestión del clúster. | Microservicio ausente o embebido dentro del worker. |
| **IE7. Endpoints de Gestión Administrativa** | **10%** | L8 / Semana 10 (`vidalstore-admin`) | 8 endpoints REST operativos para consultar colas, métricas, purgar mensajes y reprocesar cartas muertas. | Endpoints incompletos o sin validación de roles de administrador. |
| **IE8. Gestión y Monitoreo del Clúster** | **7%** | L8 / Semana 10 (`vidalstore-admin`) | Integración con la API de administración de RabbitMQ para monitorear estados y emitir alarmas. | Sin monitoreo ni integración con la API de RabbitMQ. |

### 4.2 Presentación y Defensa Técnica Individual (60% de la EP2)

| Indicador | Peso en Defensa | Dónde Quedó Resuelto | Criterio de Logro Destacado (100%) | Causa de No Logrado (0%) |
|---|:---:|:---:|---|---|
| **IE9. Clúster de Dos Nodos** | **5%** | L8 | Clúster RabbitMQ operativo con `rabbit1` y `rabbit2` compartiendo el Erlang cookie y formando un clúster activo. | Solo un nodo corriendo o nodos aislados sin clustering. |
| **IE10. Sincronización y Alta Disponibilidad** | **8%** | L8 | Demostración en vivo de sincronización de mensajes entre nodos ante detención intempestiva de un nodo. | Caída del nodo primario provoca pérdida de colas o interrupción del servicio. |
| **IE11. Orquestación con Docker Compose** | **17%** | L7 Tramo 1 / L8 | `compose.yml` levanta el sistema completo (8 servicios), con volúmenes nombrados, redes dedicadas, variables `.env`, `healthcheck` y `depends_on: { condition: service_healthy }`. | Usar scripts con `docker run` dispersos, sin healthcheck o con errores de indentación. |
| **IE12. Tres Colas de Trabajo Diferenciadas** | **7%** | L6 / L7 | Tres colas de trabajo para responsabilidades distintas: avisos, auditoría global y correos. | Menos de tres colas o colas sin justificación de negocio. |
| **IE13. DLQ por Cada Cola de Trabajo** | **9%** | L7 Tramo 3 | Tres DLQs vinculadas al exchange direct `vidalstore.dlx`, cada una recibiendo los descartes de su cola de trabajo respectiva. | No hay DLQ, o se usa una sola DLQ genérica sin trazabilidad de origen. |
| **IE14. Dos Tipos de Exchange (Direct y Topic)** | **6%** | L6 / L7 Tramo 3 | Uso correcto de `topic` para eventos (`vidalstore.eventos`) con ruteo por patrones (`#`, `compra.*`) y `direct` para comandos (`vidalstore.comandos`) y descartes (`vidalstore.dlx`). | Usar solo un tipo de exchange o usar el exchange por omisión (default exchange). |
| **IE15. Microservicios del Frontend a Postgres** | **10%** | L7 Tramos 4 y 5 | Flujo de punta a punta: el frontend gatilla la compra, el productor guarda en PostgreSQL y publica el evento, y el worker lo consume y persiste con TypeORM. | La cadena se corta en algún punto o los eventos no impactan la base de datos relacional. |
| **IE16. Registro Forense de Cartas Muertas** | **8%** | L7 Tramo 5 | `CartasMuertasConsumidor` consume las 3 DLQ, lee los encabezados `x-death` y persiste el registro en la tabla `mensajes_muertos` (columna `payload text`). | Cartas muertas acumuladas en cola sin consumidor o caída por intentar parsear como `jsonb`. |
| **IE17. Demostración del Microservicio Admin** | **12%** | L8 / Semana 10 | Ejecución en vivo de los endpoints administrativos desde Swagger, Postman o curl ante el docente. | Fallo en la invocación de endpoints o falta de evidencias de reprocesamiento. |
| **IE18. Métricas del Clúster en Vivo** | **8%** | L8 / Semana 10 | Exposición de métricas de tasas de mensajes (publicados, entregados, acked) en tiempo real. | Ausencia de métricas o métricas estáticas sin correlación con el broker. |
| **IE19. Políticas de Retención y Limpieza** | **10%** | L8 / Semana 10 | Definición y aplicación de políticas en RabbitMQ (`set_policy`) para TTL de mensajes y límite de longitud máxima de colas. | Colas sin políticas de retención permitiendo crecimiento infinito no supervisado. |
