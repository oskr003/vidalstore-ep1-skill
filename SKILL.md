---
name: vidalstore-ep1
description: >-
  Auditoría, verificación estricta y preparación técnica integral para DSY1107 - Desarrollo Cloud Native I (DUOC UC), cubriendo la Evaluación Parcial N°1 (EP1 - Caso VidalStore) y la Unidad 2 / EP2 (Mensajería Asíncrona, RabbitMQ, Docker y Persistencia).
  Usar esta skill siempre que se requiera validar, desarrollar, corregir o auditar código de frontend, gateway, BFF, microservicios, brokers, workers y bases de datos, asegurando el cumplimiento al 100% de la rúbrica oficial (IE1 a IE10), las precisiones de "EP1-aclaraciones.pdf", las clases magistrales D6 ("Git en serio") y D7 ("Docker de verdad y por qué una cola"), los laboratorios L4/L6 y L6A, y las respuestas del profesor Umbingelelo en el foro.
---

# VidalStore EP1 y Unidad 2 — Skill de Aseguramiento de Calidad y Cumplimiento al 100%

Esta skill actúa como el estándar de control de calidad, auditoría técnica y preparación de defensa para la **Evaluación Parcial N°1 (Caso VidalStore)** y la **Unidad 2 / EP2 (Mensajería Asíncrona con RabbitMQ y Docker)** de la asignatura **DSY1107 - Desarrollo Cloud Native I**.

Integra las fuentes normativas obligatorias del encargo:
1. **`EP1-aclaraciones.pdf`**: Documento oficial del profesor Cristian Calderón (`Umbingelelo`), el cual complementa el enunciado y rige sobre él.
2. **`EP1-Caso-VidalStore.pdf`**: Enunciado de negocio, arquitectura objetivo y rúbrica oficial (indicadores IE1 a IE10).
3. **`Pulso.pdf` (L4)**: Guía oficial del Laboratorio L4 ("La cadena completa") y preparación metodológica ("El puente a EP1: tramos 10 al 12") del profesor Cristian Calderón, con las 8 preguntas oficiales de la defensa, pruebas de la cadena y la resolución de la trampa de Cognito.
4. **`D6-Git-en-serio-y-defender-una-arquitectura.html`**: Clase magistral oficial de Semana 7 sobre entrega técnica, higiene de Git, el reloj de 15 minutos, los 5 flujos de defensa de punta a punta y el método de respuesta en 4 pasos.
5. **Resoluciones del foro GitHub (`Umbingelelo/DSY1107-Foro-2026-02`)**: Criterios de evaluación, commits estimados, Hosted UI, idempotencia y defensa en profundidad.
6. **`Plan_VidalStore_EP1.pdf`**: Plan de trabajo específico del grupo (3 integrantes: David, Oscar e Iván).
7. **`D7-Docker-de-verdad-y-por-que-una-cola.html`**: Clase magistral oficial de Semana 8 sobre contenedores Docker de verdad, receta de diagnóstico en 4 pasos, la trampa del estado `Created`, persistencia con volúmenes con nombre, el Erlang nodename (`--hostname rabbit1`), por qué una cola no acelera el trabajo, criterio sincrónico vs encolado (la regla del botón COMPRAR), y arquitectura de exchanges/bindings.
8. **`L6.pdf`**: Guía oficial del Laboratorio L6 ("RabbitMQ y tu primer mensaje") con los 5 tramos (broker en contenedor, Postgres y `timestamptz`, worker `biblioteca-eventos`, productor `prestamos.mjs`, exchanges `topic` y `direct`), las 6 pruebas de aislamiento y las 5 respuestas oficiales de Pulso.
9. **`L6A-L6-RabbitMQ-y-tu-primer-mensaje-con-notas.pdf`**: Clase pre-laboratorio oficial de Semana 8 con notas de orador, las 3 reglas innegociables de mensajería (publica el que escribe, el BFF reenvía pero no publica, ningún nombre suelto en topología), las 6 trampas que cuestan tiempo, la predicción de ruteo y el plan de arranque de la EP2.

> [!NOTE]
> **Estado de las Evaluaciones:**
> * **EP1 (Cadena Sincrónica de 4 Capas)**: **ENTREGADA Y CERRADA**. Los requisitos de código, commits y proxies quedaron congelados y aprobados.
> * **EP2 (Mensajería Asíncrona, RabbitMQ, Docker y Microservicios)**: **FASE ACTIVA (Semanas 8 a 10)**.
>   * Ponderación: 40% Encargo Grupal (IE1 a IE8) + 60% Presentación Individual (IE9 a IE19).
>   * **Distribución Oficial del Grupo (ep2-plan-v2.pdf)**:
>     * **David**: Dueño de `vidalstore-plataforma` (IE2, IE9, IE10, IE11, IE14, IE19). Clúster RabbitMQ 2 nodos, Postgres 18, `compose.yml`, `shared/topologia.ts`, políticas y documentación de repositorio.
>     * **Iván**: Dueño de `vidalstore-eventos` y frontend (IE3, IE4, IE5, IE12, IE13, IE15, IE16). Consumidores (`AvisosConsumer`, `AuditoriaConsumer`, `CorreosConsumer`, `DlqConsumer`), persistencia en Postgres y demo veneno.
>     * **Oscar**: Dueño de `vidalstore-admin` (IE6, IE7, IE8, IE17, IE18). Productor de eventos, `RabbitAdminService`, 8 endpoints de gestión/métricas, y reproceso de DLQ para grupos de 3.

---

## 1. Reglas Innegociables del Encargo (Checklist Maestro)

Cualquier cambio de código o revisión en los repositorios DEBE cumplir estrictamente con:

1. **Una Sola Dirección y Llamada en el Frontend (EP1 - Cerrado)**:
   - Angular (`vidalstore-frontend`) habla **únicamente** con el API Gateway (`http://localhost:8080`).
   - Jamás invoca al BFF ni a los microservicios de forma directa.
   - El interceptor HTTP tiene una lista blanca explícita con **una sola entrada** (`http://localhost:8080`).
2. **Token en `sessionStorage` (EP1 - Cerrado)**:
   - Configurado en `main.ts` con `cognitoUserPoolsTokenProvider.setKeyValueStorage(sessionStorage)`.
   - Prohibido dejar el token en `localStorage` (hallazgo forense del caso).
3. **Login Externo con Hosted UI (EP1 - Cerrado)**:
   - Obligatorio `signInWithRedirect()` de AWS Amplify (Authorization Code con PKCE).
   - Prohibido formularios propios de usuario/clave o flujos implícitos/ROPC.
   - **Angular SPA sin secreto de cliente**: `userPoolId` y `clientId` son públicos y van en el frontend.
4. **Sin Vistas Públicas (EP1 - Cerrado)**:
   - El catálogo `/catalogo` y la biblioteca `/biblioteca` exigen sesión activa (`canActivate: [sesionGuard]`).
5. **Defensa en Profundidad (Validación en Ambos Saltos)**:
   - **Gateway (NestJS)**: Autentica. Valida token contra el JWKS (firma, emisor, vigencia, tipo de token y app client). Responde `401 Unauthorized` si falla.
   - **BFF / Microservicios**: Autoriza por rol (`cognito:groups`) y busca datos. Responde `403 Forbidden` si el rol no alcanza.
   - **Cierre por detrás**: Si el BFF o un microservicio recibe una petición sin token, responde `401 Unauthorized`.
6. **Resolución de Biblioteca por `sub`**:
   - `GET /v1/biblioteca` resuelve las licencias del usuario **únicamente** a través del claim `sub` del JWT. Prohibido recibir `userId` por parámetro de ruta, query o body (prevención de BOLA / IDOR).
7. **Idempotencia en Compras**:
   - `POST /v1/compras`: Un usuario solo puede tener una licencia por juego. Si ya la posee, responde `409 Conflict`.
8. **Carpeta `data/` con Seed Real**:
   - Cada microservicio debe tener `data/seed.ts` (o `.js`) que consuma al menos una API externa real y guarde los datos en un JSON versionado (`data/catalogo.json`).
9. **Resolución de la "Trampa de Cognito" en Auto-registro**:
   - Al registrarse por Managed Login / Hosted UI, Cognito no asigna ningún grupo por omisión (`cognito:groups` viene vacío).
   - El guard / backend asume por omisión el rol de menor privilegio (`jugadores`) si el arreglo de grupos está vacío.
10. **Reglas de Escritura, Identidad y Borrado Lógico**:
    - Endpoints con `@Body()` y `@Param('id', ParseIntPipe)`.
    - El ID del nuevo registro lo asigna el microservicio / persistencia (`Math.max(...) + 1`), jamás el cliente ni el BFF.
    - **Regla de Oro de Identidad**: La identidad del que actúa nunca se lee del `@Body()`; se extrae siempre de `req.user.sub` (token firmado).
11. **Agregación Concurrente Eficiente en el BFF**:
    - Llamadas internas con `Promise.all` para ejecución concurrente en servidor.
    - Cruces de datos en memoria mediante `new Map()` indexado por ID (complejidad $O(N)$ vs $O(N \times M)$ de `.find()` anidado).
12. **Semántica de Códigos HTTP y Prevención de Enumeración**:
    - Si el usuario consulta su propia biblioteca/préstamos y está vacía, debe retornar **`200 OK` con `[]`**, jamás 403 ni 404.
13. **CORS Estricto**:
    - Únicamente en el Gateway (`app.enableCors({ origin: 'http://localhost:4200' })`). Prohibido `origin: *`.
14. **Higiene de Repositorios y Git en EP2**:
    - **Mensajes de Commit Obligatorios con Prefijo Semántico y Español Imperativo**: Todos los commits deben llevar obligatoriamente un prefijo semántico en minúsculas (`feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`), y el mensaje debe redactarse estrictamente en **español** y en **modo imperativo** (ej: `feat: Configurar arranque...`, `fix: Sincronizar topología...`, `test: Adaptar pruebas...`, `docs: Actualizar documentación...`). Prohibido el inglés y prohibidos los mensajes vagos o en pasado/presente indicativo (`arreglos`, `se agregó`, `cambios`, `fixed`).
    - **Commits Estrictamente Atómicos**: Cada commit debe ser indivisible y representar una sola responsabilidad clara. Queda prohibido agrupar múltiples fases (scaffolding, dependencias, lógica y pruebas) en un commit monolítico.
    - **Ramas de Trabajo EP2**:
      - `main`: Estable. Solo recibe merges desde `dev`.
      - `dev`: Rama de integración grupal.
      - Ramas feature específicas por responsable:
        - David: `feature/infra-setup`, `feature/rabbit-cluster`, `feature/dlq-order`, `feature/retention-policies`.
        - Iván: `feature/eventos-setup`, `feature/consumer-avisos`, `feature/consumer-auditoria`, `feature/consumer-dlq`.
        - Oscar: `feature/admin-setup`, `feature/validation-pipe`, `feature/rabbit-admin-svc`, `feature/ep-dlq-reproceso`.
15. **Publica el que Escribe, y el Token Llega hasta Él (L6A Slide 6, Pulso L6 Tramo 4.1)**:
    - Un evento anuncia un hecho consumado que ya ocurrió en el pasado (`prestamo.creado`, `compra.realizada`, `licencia.revocada`).
    - El evento lo publica **estrictamente el microservicio que escribe en la persistencia**, y **únicamente después de haber guardado con éxito**. Si la persistencia falla (error de base de datos o validación), no se publica nada.
    - Publicar antes de guardar rompe la verdad del sistema: se anuncian compras/préstamos inexistentes que desencadenan correos o auditorías imposibles de desavisar.
    - **La identidad sale siempre del token**: El `usuarioSub` se extrae de `req.user.sub` verificado con `jose`, jamás de un campo del body o query.
16. **El BFF Autoriza y Reenvía, pero JAMÁS Publica en el Broker (L6A Slide 6)**:
    - El BFF solo reenvía la cabecera `Authorization` hacia los microservicios.
    - El BFF no es dueño de la entidad ni de la transacción. Si el microservicio guardara y el BFF publicara, cualquier caída de red entre ambos generaría un recurso creado del que nadie se enteró.
17. **Topología Centralizada: Ningún Nombre Suelto en el Código (L6A Slide 8, L6 Tramo 3.5)**:
    - Toda la topología vive centralizada en `src/mensajeria/topologia.ts` (worker) y `servicios/mensajeria/topologia.mjs` (productor).
    - Prohibido escribir strings mágicos o nombres de exchanges/colas a mano en consumidores o controladores.
    - Un nombre de exchange con una letra errónea genera: `Channel closed by server: 404 (NOT_FOUND)` y mata el canal AMQP. Centralizar los objetos `EXCHANGES`, `COLAS`, `ROUTING_KEYS` y `BINDINGS` elimina este error por diseño.
18. **Criterio Sincrónico vs Encolado y la Regla del Botón COMPRAR (D7 Slides 13–15)**:
    - **Criterio de necesidad de resultado**: *¿El usuario necesita el resultado de esta operación para seguir?*
      - **Si SÍ**: Va **sincrónico** (`POST /v1/compras`). Responde `201 Created` informando que el recurso ya existe. Encolarlo significaría decirle "listo" sin que la licencia exista y sin que el juego aparezca en su biblioteca.
      - **Si NO**: Va **encolado** (AMQP / RabbitMQ). El usuario no necesita esperar que se envíe el correo con la boleta, se recalculen estadísticas de popularidad o se notifique a los amigos.
    - **Tres cosas que la cola NO hace**: No acelera el trabajo (mueve la espera; acelerar requiere consumidores paralelos), no sirve si requieres respuesta inmediata, y no arregla operaciones que fallan sin aviso (falla en silencio en segundo plano).
19. **Docker de Verdad y Persistencia sin Trampas (D7 Slides 8–11, L6 Tramos 1 y 2)**:
    - **RabbitMQ**: Obligatorio `--hostname rabbit1` y volumen nombrado `-v datos-rabbit:/var/lib/rabbitmq` sobre `rabbitmq:4.3-management`. Sin `--hostname`, Docker asigna el Container ID aleatorio como nodename de Erlang (`rabbit@<id>`), provocando que al recrear el contenedor se cree una base Mnesia nueva y se pierdan colas y usuarios aunque el volumen esté montado.
    - **PostgreSQL**: Obligatorio `-v datos-postgres:/var/lib/postgresql`, `postgres:18`, y columnas de tiempo con **`timestamptz`** (`timestamp with time zone` normalizado en UTC; jamás `timestamp` plano que pierde el huso horario).
    - **Receta de diagnóstico en orden**: 1. `docker ps` -> 2. `docker ps -a` -> 3. `docker logs` -> 4. `docker exec -it <nombre> sh`. Si `docker logs` devuelve 0 líneas, el contenedor quedó en `Created` por conflicto de puertos (código 125); la causa está en la salida del comando `docker run`.
20. **Confirmación con `ack` Explícito (`noAck: false`) (L6 Tramos 3.7 y 4.7)**:
    - En los consumidores es obligatorio configurar `{ noAck: false }` y ejecutar `canal.ack(mensaje)` explícito solo tras procesar con éxito.
    - `noAck: true` (auto-ack) le dice a RabbitMQ que borre el mensaje en el microsegundo en que sale por el socket de red. Si el worker muere antes de procesarlo, el mensaje se destruye para siempre sin reintento.
21. **Transición a la EP2 y Repositorios Fijos (L6A Slides 11–13)**:
    - Nombres fijos de repositorios: `vidalstore-plataforma`, `vidalstore-eventos`, `vidalstore-admin`. Los de la EP1 no se renombran ni se fusionan.
    - `vidalstore-plataforma/docs/repositorios.md` congelado con una fila por componente del grupo.
    - Nombres fijos en topología: Exchanges `vidalstore.eventos` (`topic`), `vidalstore.comandos` (`direct`), `vidalstore.dlx` (`direct`). Routing keys: `compra.realizada`, `licencia.revocada`, `juego.publicado`, `correo.enviar`.
    - Del grupo: nombres de las seis colas (3 de trabajo + 3 DLQ), el patrón de la cola de avisos (`compra.*`), el prefetch (L7) y las políticas (L8).

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

### Paso 5: Los 5 Puntos de Control y Entregables de Pulso L6 (Mensajería)
Comprobar los 5 hitos del laboratorio de mensajería:
1. **Control 1 (Broker vivo y nodename)**: `docker ps` muestra `rabbit1` en Up; `docker exec rabbit1 rabbitmqctl eval "node()."` responde `rabbit@rabbit1`; `list_queues` comprueba que la cola sobrevive a `docker rm -f` y recreación.
2. **Control 2 (PostgreSQL y persistencia)**: `\d mensajes_taller` muestra `recibido_en timestamptz`; consulta `payload ->> 'libroId'` funciona; `SELECT count(*)` da 2 tras recrear el contenedor.
3. **Control 3 (Topología y Worker)**: Worker arranca con `topologia declarada`; `list_bindings` lista los 3 bindings (`prestamo.*`, `#`, `correo.enviar`); `AuditoriaConsumidor` consume con `noAck: false`.
4. **Control 4 (Productor desacoplado)**: `POST` responde `201`; el mismo UUID de evento aparece en el log de `prestamos.mjs` y del worker; con el worker apagado, `list_queues` muestra los mensajes esperando en cola sin perderse.
5. **Control 5 (Discriminación topic vs direct)**: `libro.agotado` produce 1 sola línea (solo entra a auditoría por `#`); `prestamo.creado` produce 3 líneas (auditoría, notificaciones y correos); `correo.enviar` solo despierta a `CorreosConsumidor` en el exchange direct.

### Paso 6: Verificación de las 6 Trampas Conocidas de L6A
Descartar causas comunes de error antes de modificar código:
1. **Docker Desktop apagado**: `Cannot connect to the Docker daemon` -> Abrir Docker Desktop y esperar arranque.
2. **Conflicto de npm**: `reading 'edgesOut'` al correr `nest new` -> Usar `nvm use 24` (Node 24.15.0+ y npm 11).
3. **Puerto 5672 ocupado**: `Bind for 0.0.0.0:5672 failed: port is already allocated` -> Ejecutar `docker rm -f a b c p1` y recrear `rabbit1`.
4. **Colas perdidas tras recrear**: `list_queues` vacío -> Faltó `--hostname rabbit1`. Recrear fijando hostname.
5. **Token expirado**: `POST` da `401 Unauthorized` con código correcto -> El token duró 1 hora; renovar sesión en Cognito Hosted UI.
6. **Alias en PowerShell**: `curl` rechaza `-i` o `-X` en Windows -> Invocar como `curl.exe`.

---

## 5. Guías de Referencia Detalladas

Para profundizar en áreas específicas del encargo, consultar los siguientes documentos de referencia adjuntos:
- [Guía Técnica de Mensajería, Docker y RabbitMQ](./references/mensajeria_docker_rabbitmq_l6.md): Dos vías del sistema, topología AMQP, Docker de verdad, `ack` explícito, `timestamptz` y transición a EP2.
- [Rúbrica Oficial Detallada (IE1 a IE10)](./references/rubrica_completa.md): Ponderaciones, criterios destacados, peso del 60% de la defensa y causas de nota mínima.
- [Arquitectura de 4 Capas y Códigos HTTP](./references/arquitectura_4_capas.md): Responsabilidad de cada componente, CORS, flujo de petición de arriba a abajo y distinción Cloud vs Local.
- [Configuración de Cognito y Seguridad](./references/cognito_y_seguridad.md): User Pool, Resource Server, grupos, scopes, App Clients, auto-registro y Lambda trigger.
- [Banco de Preguntas Oficiales para la Defensa Técnica](./references/preguntas_defensa.md): Las 8 preguntas de `Pulso.pdf` §12.2 + 10 preguntas de D7/L6/L6A + Guion oficial de D6 con preguntas parada por parada, señales de alarma y framework de 4 pasos.

---

## 6. Regla Git para el Asistente

> [!CAUTION]
> **RECORDATORIO DE REGLA DEL USUARIO:**
> **NO USAR NINGÚN COMANDO DE GIT SIN AUTORIZACIÓN EXPRESA DEL USUARIO.**
> Siempre explicar qué hace el comando y por qué se necesita antes de solicitar su ejecución.
