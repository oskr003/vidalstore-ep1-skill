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

| Indicador | Peso en Encargo | Dónde se Pide | Criterio de Logro Destacado (100%) | Causa de No Logrado (0%) |
|---|:---:|:---:|---|---|
| **IE1. Define de forma centralizada los nombres de colas, exchanges y bindings** | **12%** | 4.1 | Todos los nombres están en el archivo de topología de cada proyecto que toca mensajería. No hay ningún valor suelto en el código, y los nombres coinciden entre los productores y el consumidor. | No hay configuración centralizada: los nombres están dispersos en el código. |
| **IE2. Declara la configuración de RabbitMQ con Queue, Exchange y Binding para cada caso de uso** | **13%** | 4.1 · 4.8 | Los tres exchanges, las seis colas y todos los bindings están declarados, cada ruta de mensajería identificada y documentada en `docs/topologia.md`. | No hay declaración de colas, exchanges ni bindings. |
| **IE3. El código no mezcla la lógica de negocio con la configuración de mensajería. Hay clases de configuración separadas** | **10%** | 4.1 · 4.2 · 4.4 | La configuración está aislada en la carpeta `mensajeria/` de cada proyecto. Los consumidores y los services solo reciben lo ya configurado. No hay un `assertQueue` ni un nombre de cola dentro de un consumidor. | No hay separación: la configuración está incrustada en la lógica de negocio. |
| **IE4. Los consumidores están implementados con el mecanismo que corresponde y se agrupan por dominio funcional** | **15%** | 4.2 | Un consumidor por dominio, cada uno en su archivo y su módulo, con nombres que dicen de qué dominio son. La estructura refleja la separación de responsabilidades. | No se implementan consumidores, o no hay ninguna organización. |
| **IE5. En los consumidores se maneja la confirmación de mensajes: uso de ACK y manejo explícito de errores** | **20%** | 4.3 · 4.4 | `noAck: false` y prefetch explícito. `ack` después del trabajo. Rutas diferenciadas entre reintento, `nack` sin requeue y DLQ, según el tipo de error, documentadas y consistentes. | No hay ACK ni manejo de errores: los consumidores procesan sin control de flujo. |
| **IE6. El microservicio administrador expone endpoints REST bien definidos** | **13%** | 4.5 | Las ocho rutas del punto 4.5, con verbos y recursos coherentes, protegidas por rol (`administradores`) y documentadas. | No existe el microservicio administrador, o no expone rutas REST. |
| **IE7. La lógica para crear colas y exchanges está encapsulada en un `RabbitAdminService`** | **10%** | 4.5 | Toda la administración está en un servicio dedicado. Los controladores llaman métodos de alto nivel y no conocen `amqplib` ni la API del broker. | No existe un servicio dedicado. |
| **IE8. La API valida los parámetros de entrada** | **7%** | 4.5 | DTOs con validación y `ValidationPipe` con `whitelist: true` y `forbidNonWhitelisted: true`. No se puede crear una cola con nombre vacío ni un exchange de tipo inexistente, y un campo que no existe responde `400 Bad Request`. | No se valida: el backend acepta cualquier dato o responde 500 ante datos vacíos. |

---

### 4.2 Presentación y Defensa Técnica Individual (60% de la EP2)

| Indicador | Peso en Defensa | Dónde se Pide | Criterio de Logro Destacado (100%) | Causa de No Logrado (0%) |
|---|:---:|:---:|---|---|
| **IE9. Configura dos nodos de RabbitMQ** | **5%** | 4.7 · 5.1(2) | Dos nodos operativos, con parámetros consistentes, cada uno con su volumen y su puerto, mostrados en vivo. | No hay dos nodos. |
| **IE10. Configura un clúster de RabbitMQ con esos dos nodos** | **8%** | 4.7 · 5.1(3) | El clúster se reconoce como tal, distribuye colas y conexiones, y el grupo explica qué comparten los nodos y qué pasa al caer uno. | No hay clúster. |
| **IE11. Levanta el clúster utilizando Docker Compose** | **17%** | 4.7 · 4.8 · 5.1(1) | Un `compose.yml` del repositorio levanta el clúster completo con un solo comando desde un clon limpio, con volúmenes, healthcheck y el arranque en orden (`--wait`, o `depends_on` con `condition: service_healthy`), y queda documentado. | No se levanta el clúster con Compose. |
| **IE12. Utiliza tres colas para distintas funcionalidades del sistema** | **7%** | 4.1 · 4.2 · 5.1(5) | Tres colas de trabajo claramente diferenciadas, cada una con su caso de uso, su binding y su consumidor, evidenciadas en el código y en la interfaz. | Menos de tres colas, o sin separación funcional. |
| **IE13. Cada cola tiene su DLQ para los mensajes en estado de carta muerta** | **9%** | 4.1 · 4.3 · 5.1(6) | Las tres colas de trabajo con su DLQ, con el dead-letter exchange y la routing key correctas, declaradas antes que las colas de trabajo. | No hay DLQ. |
| **IE14. Utiliza dos tipos de exchange distintos: direct y topic** | **6%** | 4.1 · 5.1(4) | Los dos tipos en uso real, con patrones bien diseñados, y la explicación de cuándo corresponde cada uno. | Solo se usa un tipo de exchange. |
| **IE15. Integra los microservicios con las colas de manera que escriban y lean mensajes** | **10%** | 4.2 · 4.4 · 4.6 · 5.1(7) | El productor publica y los consumidores consumen, con el flujo completo demostrado en vivo desde el frontend hasta Postgres. | No hay integración con las colas. |
| **IE16. Integra los microservicios con las DLQ para registrar en logs los mensajes no entregados** | **8%** | 4.3 · 5.1(8) | El consumidor de mensajes muertos registra cola de origen, routing key, motivo e intentos, y guarda el payload en `mensajes_muertos`. Se demuestra con un mensaje envenenado. | No hay integración con las DLQ. |
| **IE17. Implementa un microservicio administrador que crea colas, exchanges y bindings, y elimina colas y exchanges** | **12%** | 4.5 · 5.1(9) | Las seis operaciones demostradas en vivo, encapsuladas en el servicio, con diseño robusto y errores controlados (400, 404, 503). | No hay microservicio administrador. |
| **IE18. Explica de manera fundamentada las métricas de monitoreo del clúster** | **8%** | 4.8 · 5.1(10) | Explica colas activas, mensajes pendientes (`ready`), `unacked`, consumidores y mensajes en DLQ; cómo interpretar los valores, qué impacto tienen y qué se hace ante cada anomalía. | No explica las métricas, o entrega información incorrecta. |
| **IE19. Implementa políticas de retención y limpieza: límites de cola y expiración** | **10%** | 4.7 · 5.1(11) | Políticas declaradas en el repositorio para las seis colas, con límites, overflow y expiración justificados y documentados, y una demostrada en vivo. | No hay políticas de retención ni limpieza. |

---

### 4.3 El Orden Oficial de la Demostración en Vivo (11 Pasos de §5.1)

El docente evalúa la presentación siguiendo estrictamente este recorrido de 11 pasos cronológicos con el sistema previamente apagado (sin `-v`):
1. **`compose.yml` y clúster levantándose (IE11 · 17%)**: `docker compose up -d --wait` desde el clon limpio de `vidalstore-plataforma`.
2. **Los dos nodos (IE9 · 5%)**: Management UI en `:15672` y `:15673`, o `rabbitmq-diagnostics status` en cada nodo.
3. **El clúster formado (IE10 · 8%)**: `rabbitmqctl cluster_status` o pestaña Overview mostrando `rabbit@rabbit1` y `rabbit@rabbit2` compartiendo cookie y metadatos.
4. **Exchanges direct y topic (IE14 · 6%)**: Los 3 exchanges en la interfaz y explicación de ruteo por qué eventos a `topic` y comandos a `direct`.
5. **Las tres colas y sus tres funciones (IE12 · 7%)**: 6 colas en interfaz (3 trabajo + 3 DLQ), justificando caso de uso, binding y consumidor.
6. **Cada cola con su DLQ (IE13 · 9%)**: Argumentos `x-dead-letter-exchange` y `x-dead-letter-routing-key` mostrados en la interfaz.
7. **Flujo completo con revocación de licencia (IE15 · 10%)**: Revocación desde Angular $\rightarrow$ Gateway $\rightarrow$ BFF $\rightarrow$ Licencias (escribe en Postgres y publica) $\rightarrow$ logs de consumidores $\rightarrow$ comando `correo.enviar` $\rightarrow$ tablas en Postgres proyectadas sobre el ERD.
8. **Mensaje envenenado (IE16 · 8%)**: Publicar mensaje corrupto $\rightarrow$ `nack` en log $\rightarrow$ desvío a DLQ $\rightarrow$ persistencia en `mensajes_muertos` con `payload text` y `x-death`.
9. **Microservicio administrador (IE17 · 12%, IE8 · 7%)**: Operaciones CRUD de topología en vivo y rechazo con `400 Bad Request` ante entradas inválidas.
10. **Métricas del clúster con tráfico real (IE18 · 8%)**: Interpretación de `ready`, `unacked`, `consumers` y DLQ en vivo.
11. **Políticas de retención y desborde (IE19 · 10%)**: Demostración de política en cola de prueba con `max-length` y comportamiento de `overflow` (`drop-head` vs `reject-publish`).
* **Cierre: Caída de un nodo**: Detener `rabbit2` y explicar por qué con 2 nodos la mayoría es 2 y las publicaciones se suspenden (estado `minority`).

---

### 4.4 Orden Estricto de Prioridades si no Alcanza el Tiempo (§7 de EP2)
1. **Clúster levantándose con Compose (IE11, IE9, IE10)**: 30 pts presentación.
2. **Tres colas con DLQ y dos tipos de exchange (IE12, IE13, IE14, IE1, IE2)**: 22 pts presentación + 25 pts encargo.
3. **Ack, manejo de errores y flujo completo (IE5, IE15, IE16, IE4)**: 35 pts encargo + 18 pts presentación.
4. **Microservicio administrador con servicio y validación (IE6, IE7, IE8, IE17)**: 30 pts encargo + 12 pts presentación.
5. **Base de datos con 4 tablas y restricciones (IE5, IE15)**: `eventos_auditoria` con `UNIQUE (evento_id)` es la prioridad máxima.
6. **Políticas de retención (IE19)**: 10 pts presentación.
7. **Métricas explicadas (IE18)**: 8 pts presentación.
8. **Documentación restante**: `README.md` y `docs/modelo-de-datos.md`.
