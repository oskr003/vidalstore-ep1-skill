# Guía Técnica: Mensajería Asíncrona, Docker y RabbitMQ · D7, L6 y L6A

Esta guía consolida la base técnica y normativa de la **Unidad 2 (Mensajería asíncrona y RabbitMQ)** para la asignatura **DSY1107 - Desarrollo Cloud Native I**, integrando las clases **D7 ("Docker de verdad y por qué una cola")**, **L6 ("RabbitMQ y tu primer mensaje")** y **L6A ("Clase pre-laboratorio y notas de orador")**, proyectando su aplicación directa a la **Evaluación Parcial N°2 (EP2 - Caso VidalStore)**.

---

## 1. Las Dos Vías del Sistema: Sincrónica vs Asincrónica (L6A Slide 4)

A partir de la Semana 8, el sistema deja de ser exclusivamente una cadena de llamadas sincrónicas bloqueantes. Coexisten dos vías bien diferenciadas:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ VÍA 1 · SINCRÓNICA (Lo que ya tienes · El usuario espera cada salto)                   │
│                                                                                        │
│  Angular SPA       Gateway (NestJS)          BFF (NestJS)         Microservicio        │
│  :4200        ──►  :8080               ──►   :3000          ──►   :3001 / :3002        │
│                    Verifica Bearer           Verifica, autoriza   Verifica token,      │
│                    CORS                      y reenvía cabecera   persiste dato        │
│                                                                                        │
│                                              ◄── Responde 201 ◄── Termina la petición  │
└───────────────────────────────────────────────────────────┬────────────────────────────┘
                                                            │
                                                            │ RECIÉN DESPUÉS DE GUARDAR
                                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ VÍA 2 · ASINCRÓNICA (Lo nuevo · Nadie lo espera · Desacoplado en el tiempo)            │
│                                                                                        │
│  Microservicio         RabbitMQ (Broker)       Worker (NestJS)       PostgreSQL        │
│  :3002            ──►  rabbit1            ──►  biblioteca-eventos ──► postgres1        │
│  Publica evento        :5672 (AMQP)            vidalstore-eventos    :5432             │
│  a exchange topic      :15672 (Panel Web)      :3010 (ack manual)    Tabla con         │
│                                                                      timestamptz       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> **El Fin de la Petición:**
> La petición del usuario termina cuando el microservicio responde **`201 Created`**. Todo lo que ocurre desde `rabbit1` hacia la derecha sucede **fuera de la petición**, en otro proceso, en otro momento y sin hacer esperar al usuario ni un solo milisegundo.

---

## 2. Las Tres Reglas Innegociables de Mensajería (L6A Slides 6–8)

Cualquier implementación de productores y consumidores en los laboratorios o en la EP2 debe respetar estrictamente estas tres reglas:

### Regla 1: Publica el que escribe, y el token llega hasta él
* **Un evento anuncia un hecho consumado que ya ocurrió en el pasado** (`prestamo.creado`, `compra.realizada`, `licencia.revocada`).
* Por lo tanto, el evento lo publica **el proceso que escribe en la base de datos** (`prestamos.mjs` o el microservicio de licencias), **NUNCA el BFF**.
* **El Orden Inquebrantable**:
  1. BFF reenvía `Authorization: Bearer <token>`.
  2. Microservicio verifica el token con `jose` (`jwtVerify`) y extrae el claim `sub`.
  3. Microservicio **guarda** el registro en la persistencia.
  4. Microservicio **publica** el evento en el broker (`biblioteca.eventos` / `vidalstore.eventos`).
  5. Microservicio responde `201 Created`.
* **Fundamento de Arquitectura:** Si se publicara antes y la escritura fallara (por constraints, desconexión, etc.), se habría anunciado un hecho falso al sistema (notificaciones y correos enviados por un préstamo o compra inexistente), rompiendo la verdad del sistema sin forma de revertirlo.

### Regla 2: El BFF autoriza y reenvía, pero JAMÁS publica
* El BFF no es el dueño de la entidad ni de la transacción.
* Si guardar y anunciar quedaran en dos procesos distintos (microservicio guarda y BFF publica), bastaría una caída de red entre ambos para tener un préstamo/licencia creado del que nadie se enteró.
* **El usuarioSub sale del token**: El BFF reenvía el encabezado `Authorization`. El microservicio extrae la identidad del claim `sub` verificado. Un `usuarioSub` falso enviado en el cuerpo de la petición jamás llega al evento ni al registro.

### Regla 3: Ningún nombre suelto: toda la topología en `topologia.ts` / `topologia.mjs`
* La topología es el conjunto de exchanges, colas y bindings del sistema.
* En el worker vive en `src/mensajeria/topologia.ts`.
* En el productor vive en `servicios/mensajeria/topologia.mjs`.
* **Prohibido hardcodear strings en los consumidores o productores:**
  * Un nombre de exchange mal escrito genera: `Channel closed by server: 404 (NOT_FOUND) with message "NOT_FOUND - no exchange 'biblioteca.eventoss'"`.
  * Una letra errónea en un consumidor cierra el canal AMQP completo.
  * Al centralizar los objetos `EXCHANGES`, `COLAS`, `ROUTING_KEYS` y `BINDINGS`, este error queda eliminado por diseño.

---

## 3. Criterio de Decisión: Sincrónico vs Encolado (D7 Slides 13–15)

Encolar indiscriminadamente crea problemas peores que los que resuelve. Existe un criterio de oro para decidir:

> [!NOTE]
> **Pregunta de Oro:** *¿El usuario necesita el resultado de esta operación para seguir?*
> * **Si SÍ**: Va **sincrónico**. El usuario necesita confirmación inmediata (ej: crear la licencia, comprar el juego). Responde `201 Created` informando que el recurso ya existe. Encolarlo significaría decirle "listo" sin que el juego aparezca en su biblioteca al querer jugar.
> * **Si NO**: Va **encolado**. La operación puede ocurrir después en segundo plano (ej: enviar correo con la boleta, recalcular estadísticas de popularidad, notificar actividad a la lista de amigos).

### Tres Cosas que una Cola NO Resuelve (D7 Slide 13)
1. **NO acelera el trabajo**: Mueve la espera fuera de la petición del cliente. Acelerar el procesamiento es responsabilidad de tener **consumidores paralelos** (múltiples workers leyendo de la misma cola).
2. **NO sirve si necesitas la respuesta ahora**: Si la vista requiere el ID del nuevo recurso o el estado inmediato, encolar no ayuda.
3. **NO arregla una operación que falla sin aviso**: Al contrario, el fallo ahora ocurre lejos del usuario; si el worker o el servidor de correos falla, la falla ocurre en silencio en segundo plano y se requiere monitoreo y DLQ para detectarla.

---

## 4. Topología AMQP: Exchanges, Routing Keys y Bindings

En RabbitMQ, **el productor NUNCA publica directamente a una cola**. Publica a un **Exchange** acompañado de una **Routing Key**, y el Exchange distribuye copias del mensaje hacia las colas que tengan un **Binding** coincidente.

```text
                             ┌───────────────────────┐
                             │  EXCHANGE (Topic)     │
                             │  vidalstore.eventos   │
                             └──────────┬────────────┘
                                        │
             ┌──────────────────────────┴──────────────────────────┐
             │ Binding: compra.*                                   │ Binding: #
             ▼                                                     ▼
┌──────────────────────────┐                              ┌──────────────────────────┐
│ Cola: avisos             │                              │ Cola: auditoria          │
│ (Recibe compra.realizada)│                              │ (Recibe TODO)            │
└──────────────────────────┘                              └──────────────────────────┘
```

### Tipos de Exchange
| Tipo de Exchange | Comportamiento | Uso en el Sistema |
|---|---|---|
| **`topic`** | Enrutamiento por patrones jerárquicos usando puntos (`.`) y comodines. | **Eventos (1 a muchos)**: `biblioteca.eventos` / `vidalstore.eventos`. |
| **`direct`** | Coincidencia exacta de la routing key, sin comodines. | **Comandos (1 a 1)**: `biblioteca.comandos` / `vidalstore.comandos` y Dead Letter Exchanges (`dlx`). |

### Comodines del Exchange `topic`
* **`*` (asterisco)**: Sustituye a **exactamente una palabra**.
  * El binding `prestamo.*` calza con `prestamo.creado` y `prestamo.devuelto`.
  * **NO calza** con `prestamo.creado.maipu` (dos palabras después de prestamo).
  * **NO calza** con `libro.agotado` (la primera palabra no es prestamo).
* **`#` (numeral / hash)**: Sustituye a **cero o más palabras**.
  * El binding `#` calza con absolutamente cualquier routing key que se publique en ese exchange (ideal para auditoría global).

### Anatomía de una Routing Key
Convención estándar: `<recurso>.<qué_pasó>.<detalle_opcional>`
* Todo en minúsculas y separado por puntos.
* Ejemplos: `prestamo.creado`, `prestamo.devuelto`, `compra.realizada`, `licencia.revocada`, `juego.publicado`, `correo.enviar`.

---

## 5. Docker de Verdad: Diagnóstico y Persistencia (D7 y L6)

### Anatomía de Publicación de Puertos (`-p host:container`)
* `-p 15672:15672`:
  * **Izquierda (`15672:`)**: Puerto en tu máquina anfitriona (el que abres en el navegador).
  * **Derecha (`:15672`)**: Puerto interno del contenedor (lo fija la imagen).
* **Puertos del Sistema**:
  * `5672`: Protocolo AMQP de RabbitMQ (usado por productores y consumidores en código).
  * `15672`: Consola Web de Administración de RabbitMQ (navegador: `guest`/`guest`).
  * `5432`: Protocolo de PostgreSQL (usado por `psql` y librerías cliente).

### Receta de Diagnóstico en 4 Pasos (D7 Slide 8)
Ante cualquier fallo, seguir esta receta en orden estricto sin borrar contenedores:
1. **`docker ps`**: ¿Está corriendo y con qué puertos publicados? Si aparece con puertos correctos, el problema no es Docker.
2. **`docker ps -a`**: Si no apareció en `ps`, ¿existe y está detenido? Muestra estados `Exited` y `Created`.
3. **`docker logs <nombre>`**: Si está en `Exited`, el proceso escribió el motivo antes de morir. (El 80% de los diagnósticos termina aquí).
4. **`docker exec -it <nombre> sh`**: Si corre pero no responde, entras y miras desde adentro (solo tiene sentido si está vivo).

> [!WARNING]
> **La Trampa del Estado `Created` (D7 Slide 9):**
> Si intentas levantar un contenedor en un puerto que ya está ocupado por otro (ej: puerto `5672` ya tomado por otro contenedor `a`), el `docker run` fallará con `Bind for 0.0.0.0:5672 failed: port is already allocated` (código 125).
> El contenedor fallido queda en estado **`Created`** (NO `Exited`), y ejecutar `docker logs` devolverá **CERO líneas**, porque el proceso principal nunca llegó a ejecutarse. La causa del error está en la salida del comando `docker run`, no en el log.

### Persistencia y Volúmenes: Las Dos Trampas Ocultas (D7 Slide 11)
1. **El volumen anónimo por omisión**: Si omites la bandera `-v` y la imagen declara un volumen en su Dockerfile (como Postgres y RabbitMQ), Docker crea un volumen anónimo con un hash hexadecimal de 64 caracteres. Al recrear el contenedor, Docker crea otro volumen anónimo distinto y los datos anteriores quedan huérfanos en el disco.
2. **El Erlang Node Name de RabbitMQ (`--hostname`)**:
   * RabbitMQ almacena su base de datos Mnesia en `/var/lib/rabbitmq/mnesia/rabbit@<hostname>`.
   * Por defecto, el hostname de un contenedor Docker es el Container ID aleatorio (ej: `6b098aef6d3d`).
   * Si recreas el contenedor aunque uses un volumen con nombre (`-v datos-rabbit:...`), el nuevo contenedor tendrá un ID distinto, RabbitMQ buscará en `rabbit@6fc48e32f172` y las colas, usuarios y configuraciones **desaparecerán por completo**.
   * **Solución Obligatoria**: Fijar siempre `--hostname rabbit1`.

### Comandos Oficiales de Arranque (L6 Tramo 1 y 2)

**RabbitMQ con Management y Volumen:**
```bash
docker run -d \
  --name rabbit1 \
  --hostname rabbit1 \
  -p 5672:5672 \
  -p 15672:15672 \
  -v datos-rabbit:/var/lib/rabbitmq \
  rabbitmq:4.3-management
```

**PostgreSQL con Base Inicializada y Volumen:**
```bash
docker run -d \
  --name postgres1 \
  -e POSTGRES_USER=biblioteca \
  -e POSTGRES_PASSWORD=biblioteca \
  -e POSTGRES_DB=biblioteca \
  -p 5432:5432 \
  -v datos-postgres:/var/lib/postgresql \
  postgres:18
```

> [!TIP]
> **Por qué `timestamptz` y no `timestamp` (L6 Tramo 2.6):**
> `timestamptz` (`timestamp with time zone`) convierte y almacena el instante temporal en UTC normalizado y lo presenta en la zona horaria del cliente. `timestamp` plano descarta el huso horario, lo cual provoca inconsistencias graves en arquitecturas cloud donde clientes, microservicios y bases de datos residen en diferentes regiones geográficas.

---

## 6. Manejo de Confirmación: `ack` Explícito vs `noAck: true` (L6 Tramo 3.7 y 4.7)

* **`noAck: true` (Auto-Ack)**:
  * El broker considera que el mensaje fue procesado en el milisegundo exacto en que lo envía por el socket de red hacia el consumidor, borrándolo de la cola de inmediato.
  * Si el proceso del worker se cae o muere justo después de recibirlo (o durante su procesamiento), **el mensaje se pierde para siempre** sin haber sido procesado ni reentregado.
* **`noAck: false` (Confirmación Manual con `canal.ack(mensaje)`)**:
  * El mensaje permanece en estado `Unacked` en RabbitMQ mientras el worker lo procesa.
  * Solo cuando el worker ejecuta exitosamente `canal.ack(mensaje)`, RabbitMQ lo elimina de la cola.
  * Si el worker muere o se desconecta sin enviar el ack, RabbitMQ detecta la pérdida de la conexión TCP y **reencola automáticamente el mensaje** para que otro worker disponible lo reciba.

---

## 7. Mapeo del Proyecto Guía (L6) a VidalStore (EP2)

| Elemento | Proyecto Guía (L6 - Biblioteca) | Proyecto VidalStore (EP2 - Tienda de Juegos) |
|---|---|---|
| **Exchange de Eventos** | `biblioteca.eventos` (`topic`) | `vidalstore.eventos` (`topic`) |
| **Exchange de Comandos** | `biblioteca.comandos` (`direct`) | `vidalstore.comandos` (`direct`) |
| **Exchange de Fallos** | `biblioteca.dlx` (`direct`) | `vidalstore.dlx` (`direct`) |
| **Routing Keys Fijas** | `prestamo.creado`<br>`prestamo.devuelto`<br>`libro.agotado`<br>`correo.enviar` | `compra.realizada`<br>`licencia.revocada`<br>`juego.publicado`<br>`correo.enviar` |
| **Colas de Trabajo** | `notificaciones` (escucha `prestamo.*`)<br>`auditoria` (escucha `#`)<br>`correos` (escucha `correo.enviar`) | 3 colas definidas por el grupo (ej: `avisos`, `auditoria`, `correos`) con los mismos bindings funcionales |
| **Dead Letter Queues (DLQ)** | Llegada en L7 (una por cola de trabajo) | Llegada en Semana 9 / L7 (3 DLQ vinculadas a `vidalstore.dlx`) |
| **Microservicio Productor 1** | `prestamos.mjs` (:3002) publica tras guardar | Microservicio de **Licencias** publica `compra.realizada` y `licencia.revocada` tras persistir |
| **Microservicio Productor 2** | N/A (`libros.mjs` no publica en L6) | Microservicio de **Catálogo** publica `juego.publicado` cuando un editor publica un juego |
| **Worker Consumidor** | `biblioteca-eventos` (:3010) | `vidalstore-eventos` (:3010) |
| **Repositorio Plataforma** | `biblioteca-plataforma` (sin código) | `vidalstore-plataforma` (sin código, con `docs/repositorios.md` y `compose.yml`) |
| **Repositorio Admin** | `biblioteca-admin` (:3020, L8) | `vidalstore-admin` (:3020, creado en Semana 8, código en Semana 10) |

---

## 8. Qué es Fijo y Qué Decide el Grupo en la EP2 (L6A Slide 12)

* **Estrictamente Fijo por Normativa (No se negocia):**
  1. Los nombres de los tres repositorios nuevos: `vidalstore-plataforma`, `vidalstore-eventos` y `vidalstore-admin`.
  2. Los nombres y tipos de los tres exchanges: `vidalstore.eventos` (`topic`), `vidalstore.comandos` (`direct`) y `vidalstore.dlx` (`direct`).
  3. Los nombres de las cuatro routing keys obligatorias: `compra.realizada`, `licencia.revocada`, `juego.publicado`, `correo.enviar`.
  4. El binding de auditoría con `#` (cero o más palabras).
  5. El binding de correos con `correo.enviar`.
  6. Una DLQ por cada cola de trabajo (total 6 colas).
* **Decisiones del Grupo (Se eligen y se justifican en la defensa):**
  1. Los nombres de las seis colas (ej: `cola-avisos`, `cola-auditoria`, `cola-correos`, etc.).
  2. El patrón de binding exacto de la cola de avisos (ej: `compra.*`).
  3. El valor del prefetch en los consumidores (L7).
  4. Los valores de las políticas de TTL y longitud en RabbitMQ (L8).

---

## 9. Las Seis Trampas Conocidas que Cuestan Tiempo (L6A Slide 10)

| Síntoma que ves | Causa real | Salida inmediata |
|---|---|---|
| `Cannot connect to the Docker daemon` | Docker Desktop está instalado pero apagado. | Abrir Docker Desktop y esperar a que el icono deje de animarse antes de correr comandos. |
| `reading 'edgesOut'` al correr `nest new` | Incompatibilidad de npm 10 que acompaña a Node 22. | Ejecutar `nvm use 24` (usar Node 24.15.0 o superior y npm 11). |
| `Bind for 0.0.0.0:5672 failed: port is already allocated` | El contenedor `a` de la prueba previa sigue ocupando el puerto 5672. | Ejecutar `docker rm -f a b c p1` y volver a crear `rabbit1`. |
| `list_queues` vacío después de recrear el contenedor | Faltó `--hostname rabbit1`: el nodo Erlang cambió de nombre y creó otra carpeta. | Recrear el contenedor con el comando completo fijando `--hostname rabbit1`. |
| El `POST` da `401 Unauthorized` con todo el código correcto | El token JWT expiró (duración máxima de 1 hora en Cognito). | Iniciar sesión nuevamente en Hosted UI o renovar tokens mediante el script de autenticación. |
| `curl` rechaza `-i` o `-X` en Windows PowerShell | En PowerShell 5.1, `curl` es un alias de `Invoke-WebRequest`. | Escribir explícitamente `curl.exe` con la extensión. |
