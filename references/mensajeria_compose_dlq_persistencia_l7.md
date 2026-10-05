# Guía Técnica: Docker Compose, Ack, DLX/DLQ y Persistencia · D8, L7A y L7

Esta guía consolida la base técnica y normativa de la **Semana 9 de DSY1107 - Desarrollo Cloud Native I**, integrando las clases **D8 ("Compose, ack, durabilidad y fallos")**, **L7A ("Clase pre-laboratorio · Exchanges, bindings y DLQ")** y **L7 ("Laboratorio L7 · Exchanges, bindings y DLQ")**, con proyección directa a la **Evaluación Parcial N°2 (EP2 - Caso VidalStore)**.

---

## 1. De L6 a L7: Evolución de la Arquitectura

En L6 cada pieza se levantaba a mano en su propia terminal, un mensaje con error cerraba el canal y lo procesado por los consumidores no quedaba almacenado en base de datos. En L7 todo el sistema pasa a contenedores gestionados por Docker Compose, los fallos se desvían a Dead Letter Queues (DLQ) y todo evento procesado se persiste con TypeORM en PostgreSQL.

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ AL TERMINAR L6 (Semana 8)                                                              │
│  8 terminales a mano + 2 docker run (rabbit1 y postgres)                               │
│  Worker en consola (console.log)                                                       │
│  Sin DLQ: Un mensaje inválido cierra el canal AMQP                                     │
│  Sin persistencia en el worker: al caer el proceso, no queda registro                 │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ EVOLUCIÓN A L7
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ AL TERMINAR L7 (Semana 9)                                                              │
│  compose.yml: 1 comando levanta los 8 contenedores orquestados con healthchecks       │
│  RabbitMQ con 3 DLQ atadas a vidalstore.dlx (una por cola de trabajo)                  │
│  Worker resiliente: ack explícito, prefetch(1), reintentos y nack sin reencolar        │
│  PostgreSQL: 4 tablas en 2 esquemas (3 del worker en public, 1 del productor)          │
│  CartasMuertasConsumidor: procesa las 3 DLQ e inserta en mensajes_muertos              │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Docker Compose: El Sistema Completo en un Archivo (D8 y L7 Tramo 1)

`compose.yml` (en la raíz de `vidalstore-plataforma` o `biblioteca-plataforma`) describe los 8 contenedores, sus dependencias, redes y volúmenes, levantándolos todos en orden con un solo comando.

### 2.1 Los 8 Servicios del Sistema
1. **Frontend Web**: Angular servido por Nginx (`:4200`).
2. **Gateway**: Entrada perimetral NestJS (`:8080`).
3. **BFF**: Backend for Frontend NestJS (`:3000` / `:3001`).
4. **Microservicio 1 (Catálogo/Libros)**: Proceso HTTP (`:3001` / `:3002`).
5. **Microservicio 2 (Licencias/Préstamos)**: Proceso HTTP + Productor de eventos (`:3002` / `:3003`).
6. **Worker (Eventos)**: Consumidores NestJS (`:3010`).
7. **Broker RabbitMQ**: `rabbit1` con consola de administración (`:5672` y `:15672`).
8. **Base de Datos PostgreSQL**: `postgres` con esquemas de negocio (`:5432`).

### 2.2 Reglas Críticas de YAML e Indentación (D8)
* **La sangría es la sintaxis**: En YAML no hay llaves ni corchetes. Dos espacios por nivel, siempre los mismos.
* **Prohibido usar tabs**: YAML rechaza estrictamente tabulaciones. Solo espacios.
* **Alineación de listas**: El guion `-` de una lista se indenta más que la clave que lo contiene (ej. `ports` a 4 espacios, `- "5672:5672"` a 6 espacios). Si queda al mismo nivel, YAML lo interpreta como una clave nueva y el error apunta a otra línea.

### 2.3 Red Interna: `localhost` vs Nombre de Servicio (D8 y L7A)
* **Desde el navegador**: Se usan los puertos publicados en el anfitrión (`localhost:4200`, `localhost:8080`, `localhost:15672`).
* **Entre contenedores**: Se usa el **nombre del servicio** definido en `compose.yml`. Dentro de un contenedor, `localhost` es el propio contenedor, no el vecino.
  * Worker se conecta a: `amqp://biblioteca:biblioteca@rabbit1:5672` y `POSTGRES_HOST=postgres`.
  * Gateway llama a: `http://bff:3000`.
  * Microservicio conecta a: `postgres:5432` y `rabbit1:5672`.
* *Causa #1 de `ECONNREFUSED`*: Dejar `localhost` en el `.env` de un servicio dentro de Docker.

### 2.4 Diferencia entre «Arrancó» y «Está Listo»: `healthcheck` y `depends_on` (D8 y L7 Tramo 1.6)
* `depends_on` por sí solo **solo ordena el arranque**: Docker arranca RabbitMQ y de inmediato pasa al siguiente contenedor. Pero RabbitMQ tarda 5 a 10 segundos en levantar su motor AMQP. Si el worker intenta conectarse apenas arranca, recibe `ECONNREFUSED` y muere.
* **Solución Obligatoria**: Configurar un `healthcheck` que pruebe activamente el servicio y usar `condition: service_healthy`:

```yaml
services:
  rabbit1:
    image: rabbitmq:4.3-management
    hostname: rabbit1
    volumes:
      - datos-rabbit:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "-q", "check_port_connectivity"]
      interval: 5s
      timeout: 5s
      retries: 10

  postgres:
    image: postgres:18
    volumes:
      - datos-postgres:/var/lib/postgresql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U biblioteca -d biblioteca"]
      interval: 5s
      timeout: 5s
      retries: 10

  eventos:
    build: ../biblioteca-eventos
    depends_on:
      rabbit1:
        condition: service_healthy
      postgres:
        condition: service_healthy
```

* **Comando oficial de arranque**:
  ```bash
  docker compose up -d --build --wait
  ```
  Con `--wait`, Compose bloquea la terminal hasta que todos los servicios estén en estado `healthy`.

---

## 3. El Misterio del Mensaje Desaparecido: Ack, Durabilidad y Prefetch (D8 y L7 Tramo 2)

### 3.1 El Ciclo de Vida del Mensaje y el Ack
RabbitMQ maneja tres estados para cada mensaje encolado:
1. **`ready` (en la cola)**: Esperando ser entregado a un consumidor.
2. **`unacked` (entregado / sin confirmar)**: Apartado en el limbo por RabbitMQ; el consumidor lo tiene en memoria procesándolo.
3. **`borrado` (confirmado)**: El consumidor mandó `canal.ack(mensaje)` y RabbitMQ lo elimina definitivamente del broker.

> [!CAUTION]
> **El `await` antes del `ack`:**
> ```typescript
> await this.eventos.insert({ ... }); // 1. Primero terminar y persistir de verdad
> canal.ack(mensaje);                  // 2. Recién ahora confirmar al broker
> ```
> Si se invierte el orden o se hace ack antes de terminar la escritura en base de datos, se confirma algo que aún no ha ocurrido. Si el proceso muere en el insert, RabbitMQ ya borró el mensaje creyendo que terminó, y el dato se evapora para siempre.

### 3.2 ¿Qué pasa si el consumidor muere antes del ack?
Si el proceso del worker muere o se corta su conexión TCP mientras el mensaje está en estado `unacked`, RabbitMQ detecta la caída y **reencola automáticamente el mensaje** (lo devuelve al frente de la cola en estado `ready`) para entregárselo a otro consumidor disponible.

### 3.3 ¿Qué pasa si el consumidor olvida hacer ack?
Si el consumidor procesa el mensaje pero olvida llamar a `canal.ack(mensaje)`:
1. El mensaje permanece eternamente en estado `Unacked`.
2. Al acumularse mensajes sin confirmar hasta el límite de `prefetch`, RabbitMQ **congela la entrega** y la cola se detiene.
3. En la Management UI se aprecia un número creciente en la columna "Unacked".
4. Si el worker se reinicia, **TODOS esos mensajes se reentregan de golpe** y se vuelven a procesar.

### 3.4 Las Tres Durabilidades Indispensables (D8 Slide 22)
Para sobrevivir al reinicio de RabbitMQ se requieren **tres piezas distintas**. Si falta una sola, los datos se pierden:
1. **Volumen de Docker** (`datos-rabbit:/var/lib/rabbitmq`): Conserva el disco físico entre destrucciones de contenedores.
2. **Cola Durable** (`{ durable: true }`): Hace que la definición de la cola se anote en ese disco.
3. **Mensaje Persistent** (`{ persistent: true }` al publicar): Hace que el cuerpo y headers del mensaje se sincronicen en el disco.
* *Una cola durable con mensajes no persistentes sobrevive al reinicio pero vuelve vacía*.

### 3.5 Prefetch: Control de Concurrencia por Consumidor (L7A y L7 Tramo 2.4)
* `prefetch` define cuántos mensajes sin confirmar puede retener simultáneamente cada consumidor.
* **Sin prefetch (o `prefetch(0)`)**: RabbitMQ entrega la cola completa de golpe a la memoria del worker. Si la cola tiene 10.000 mensajes y el worker se cae, los 10.000 vuelven al broker, saturando la red.
* **`prefetch(1)`**: El consumidor recibe un mensaje, lo procesa, persiste en base de datos, envía `ack`, y recién entonces RabbitMQ le envía el siguiente.
* **Obligatorio en `mensajeria.service.ts`**:
  ```typescript
  await this.canal.prefetch(1);
  ```
  Se declara una sola vez sobre el canal y aplica a todos los consumidores que lo compartan.

---

## 4. Idempotencia: La Garantía «Al Menos Una Vez» (D8 y L7 Tramo 4.9)

RabbitMQ garantiza entrega **al menos una vez** (*at least once*): nunca menos, pero a veces más.
Si un consumidor guarda en la base de datos y justo antes de que llegue el `ack` al broker se corta la red o muere el contenedor, RabbitMQ reentrega el mensaje a otro consumidor. El mismo evento llega por segunda vez.

### 4.1 Por qué un `if` en el código NO sirve
```typescript
// ❌ CÓDIGO VULNERABLE A CONDICIÓN DE CARRERA (Race Condition):
const existe = await this.eventos.findOne({ where: { eventoId } });
if (!existe) {
  await this.eventos.insert({ eventoId, ... });
}
```
Si dos réplicas del worker o dos eventos concurrentes se evalúan en paralelo, ambos pasan el `if (!existe)` simultáneamente y ambos ejecutan el `insert`, duplicando el registro.

### 4.2 La Solución Definitiva: Restricción `UNIQUE` en la Base de Datos
La idempotencia se delega en el motor relacional de PostgreSQL mediante una restricción única:
```sql
CONSTRAINT uq_eventos_evento_id UNIQUE (evento_id)
```
En TypeORM:
```typescript
@Column({ name: 'evento_id', type: 'uuid', unique: true })
eventoId!: string;
```

### 4.3 Qué hacer ante el choque de duplicado (`SQLSTATE 23505`)
Cuando un mensaje repetido intenta insertarse, Postgres rechaza la transacción con el código de error `23505` (*unique_violation*).
* **Decisión del Consumidor**: **Confirmar con `canal.ack(mensaje)` y NO enviar a la DLQ**.
* **Fundamento**: El mensaje ya cumplió su trabajo en la primera entrega. Un duplicado es un éxito del transporte, no un fallo del mensaje. Si se mandara a la DLQ, esta se saturaría de mensajes válidos.

---

## 5. Arquitectura de DLX y las Tres DLQ (L7 Tramos 3 y 5)

Un mensaje roto (ej. JSON mal formado, campos requeridos faltantes) fallará hoy, mañana y siempre. Si el consumidor hace `nack` con reencolado (`requeue: true`), se genera un **bucle infinito** de reintentos inmediatos que satura el procesador y bloquea la cola.

### 5.1 Salida de Emergencia hacia DLQ
```text
┌─────────────────┐       nack(false, false)        ┌─────────────────┐      Routing Key       ┌─────────────────┐
│ Cola de Trabajo │ ──────────────────────────────► │  DLX (Direct)   │ ─────────────────────► │ Cola .dlq       │
│ (ej. auditoria) │   RabbitMQ detecta descarte     │ vidalstore.dlx  │   "auditoria"          │ auditoria.dlq   │
└─────────────────┘                                 └─────────────────┘                        └─────────────────┘
```

### 5.2 Declaración en `topologia.ts`: Argumentos de Cola
Cada cola de trabajo se declara vinculada al exchange de cartas muertas:
```typescript
export const EXCHANGES = {
  eventos: 'vidalstore.eventos',
  comandos: 'vidalstore.comandos',
  dlx: 'vidalstore.dlx',
} as const;

export const COLAS = {
  avisos: 'cola-avisos',
  auditoria: 'cola-auditoria',
  correos: 'cola-correos',
} as const;

export const DLQ = {
  avisos: 'cola-avisos.dlq',
  auditoria: 'cola-auditoria.dlq',
  correos: 'cola-correos.dlq',
} as const;
```

En la función `declararTopologia(canal)`:
```typescript
// 1. Declarar Exchanges (eventos topic, comandos direct, dlx direct)
await canal.assertExchange(EXCHANGES.eventos, 'topic', { durable: true });
await canal.assertExchange(EXCHANGES.comandos, 'direct', { durable: true });
await canal.assertExchange(EXCHANGES.dlx, 'direct', { durable: true });

// 2. Declarar las tres DLQ y enlazarlas al DLX usando el nombre de su cola como routing key
for (const [clave, nombreDlq] of Object.entries(DLQ)) {
  await canal.assertQueue(nombreDlq, { durable: true });
  await canal.bindQueue(nombreDlq, EXCHANGES.dlx, COLAS[clave as keyof typeof COLAS]);
}

// 3. Declarar las colas de trabajo con sus argumentos de Dead Lettering
for (const [clave, nombreCola] of Object.entries(COLAS)) {
  await canal.assertQueue(nombreCola, {
    durable: true,
    deadLetterExchange: EXCHANGES.dlx,
    deadLetterRoutingKey: nombreCola, // enruta a su DLQ correspondiente
  });
}

// 4. Enlazar colas de trabajo a los exchanges principales
await canal.bindQueue(COLAS.avisos, EXCHANGES.eventos, 'compra.*');
await canal.bindQueue(COLAS.auditoria, EXCHANGES.eventos, '#');
await canal.bindQueue(COLAS.correos, EXCHANGES.comandos, 'correo.enviar');
```

> [!IMPORTANT]
> **Orden Estricto de Declaración:**
> Las DLQ y sus bindings deben crearse **ANTES** que las colas de trabajo. Si una cola de trabajo rechaza un mensaje y su DLQ de destino aún no existe en el broker, RabbitMQ descarta el mensaje silenciosamente y se pierde sin dejar rastro.

### 5.3 Error `406 PRECONDITION_FAILED` y su Solución
* **Síntoma**: Al relanzar el worker tras configurar DLQ, el contenedor muere con `Channel closed by server: 406 (PRECONDITION-FAILED) with message "PRECONDITION_FAILED - inequivalent arg 'x-dead-letter-exchange' for queue 'auditoria' in vhost '/'`.
* **Causa**: Las colas creadas en L6 ya existían en RabbitMQ sin los argumentos de DLX. RabbitMQ no permite modificar los argumentos de una cola existente.
* **Solución**: Eliminar las colas de trabajo antiguas antes de volver a levantar el worker:
  ```bash
  docker compose exec rabbit1 rabbitmqctl delete_queue auditoria
  docker compose exec rabbit1 rabbitmqctl delete_queue notificaciones
  docker compose exec rabbit1 rabbitmqctl delete_queue correos
  docker compose up -d eventos
  ```

---

## 6. Diagnóstico Forense: El Header `x-death` (L7 Tramos 3.7 y 3.8)

Cuando un mensaje es rechazado sin reencolar (`nack(mensaje, false, false)`), RabbitMQ le inyecta automáticamente el encabezado de metadatos `x-death`.

### 6.1 Anatomía del `x-death`
```json
{
  "x-death": [
    {
      "count": 1,
      "reason": "rejected",
      "queue": "cola-auditoria",
      "time": { "!": "timestamp", "value": 1789162816 },
      "exchange": "vidalstore.eventos",
      "routing-keys": ["compra.realizada"]
    }
  ],
  "x-evento-id": "0dc8acd1-5722-4af9-bcbd-aaed49f89086",
  "x-emitido-en": "2026-10-05T10:15:00.000Z",
  "x-first-death-queue": "cola-auditoria",
  "x-first-death-reason": "rejected"
}
```

| Campo | Significado | Importancia Forense |
|---|---|---|
| `queue` | Cola desde la cual murió el mensaje | Permite saber qué componente descartó el mensaje en colas compartidas. |
| `reason` | Motivo de la muerte (`rejected`, `expired`, `maxlen`) | Distingue entre rechazo explícito por código (`rejected`), expiración por TTL (`expired`) o cola llena (`maxlen`). |
| `count` | Cantidad de veces que murió por esa causa | Un contador mayor a 1 delata reintentos cíclicos sin corrección. |
| `routing-keys` | Routing key original con la que nació el evento | En la DLQ la routing key es el nombre de la cola; este campo conserva el hecho original (`compra.realizada`). |
| `exchange` | Exchange original por donde ingresó | Informa si provenía de eventos o de comandos. |
| `x-first-death-queue` | Primera cola donde murió | Se preserva intacto aunque el mensaje sufra múltiples saltos o reprocesamientos. |

---

## 7. Matriz de Decisión de Errores y Reintentos (L7 Tramo 4.8)

Todo consumidor debe implementar un bloque `try/catch` con discriminación explícita del tipo de error:

```typescript
// L7 · reintentos.ts
export const REINTENTOS = { maximo: 3, esperaMs: 2000 } as const;

export class MensajeInvalido extends Error {}

export function esDelMensaje(error: unknown): boolean {
  if (error instanceof SyntaxError || error instanceof MensajeInvalido) return true;
  const codigo = (error as { code?: unknown }).code;
  // SQLSTATE 22 = dato mal formado, 23 = restriccion violada (salvo 23505)
  return typeof codigo === 'string' && (codigo.startsWith('22') || (codigo.startsWith('23') && codigo !== '23505'));
}

export async function conReintentos<T>(
  trabajo: () => Promise<T>,
  alFallar: (intento: number, error: Error) => void,
): Promise<T> {
  for (let intento = 1; ; intento++) {
    try {
      return await trabajo();
    } catch (error) {
      if (esDelMensaje(error) || intento >= REINTENTOS.maximo) throw error;
      alFallar(intento, error as Error);
      await esperar(REINTENTOS.esperaMs * intento); // 2s, 4s backoff progresivo
    }
  }
}
```

### 7.1 Tabla de Decisiones del Consumidor
| Qué falló | Qué hace el Consumidor | Por qué técnica y normativamente |
|---|---|---|
| **JSON mal formado, sintaxis inválida, faltan datos obligatorios o error SQLSTATE `22...` / `23...`** | `canal.nack(mensaje, false, false)` de inmediato hacia la DLQ | Es un error intrínseco del mensaje. Reintentarlo un millón de veces fallará siempre; no debe congestionar la cola de trabajo. |
| **Colisión por duplicado (código SQL `23505`)** | `canal.ack(mensaje)` y registro en log de advertencia | El mensaje ya se persistió con éxito en una entrega anterior. Es la reentrega prometida por *at least once*. |
| **Base de datos detenida, corte de red, error de conexión (`ECONNREFUSED`, `getaddrinfo`)** | Hasta 3 intentos esperando 2s y 4s con `conReintentos`. Si se agotan, `canal.nack(mensaje, false, false)` hacia DLQ | El mensaje está sano; el que está caído es el entorno. Se reintenta temporalmente y, si la falla persiste, se resguarda en la DLQ. |

---

## 8. Persistencia Relacional con TypeORM: 4 Tablas y 2 Dueños (L7 Tramos 4 y 5)

En la base de datos PostgreSQL conviven 4 tablas con estricta segregación de dominios y **cero Foreign Keys entre servicios**.

### 8.1 Dueño 1: Worker (`vidalstore-eventos` / `biblioteca-eventos`) · Esquema `public`
1. **`eventos_auditoria`**:
   - `id`: `uuid` PK.
   - `routing_key`: `text` NOT NULL.
   - `evento_id`: `uuid` NOT NULL UNIQUE (provee la idempotencia).
   - `usuario_sub`: `text` NULL (permite eventos del sistema sin usuario humano).
   - `payload`: **`jsonb`** NOT NULL (es JSON válido garantizado tras pasar `JSON.parse`). Permite consultas indexadas (`payload ->> 'juegoId'`).
   - `emitido_en`: `timestamptz` NOT NULL (header `x-emitido-en`).
   - `recibido_en`: `timestamptz` NOT NULL DEFAULT now().

2. **`notificaciones`**:
   - `id`: `uuid` PK.
   - `para`: `text` NOT NULL (`usuarioSub` del destinatario).
   - `asunto`: `text` NOT NULL.
   - `estado`: `text` NOT NULL con restricción `CHECK (estado IN ('enviada', 'fallida'))`.
   - `evento_id`: `uuid` NOT NULL (relación lógica con auditoría, sin FK).
   - `enviada_en`: `timestamptz` NOT NULL DEFAULT now().

3. **`mensajes_muertos`**:
   - `id`: `uuid` PK.
   - `cola_origen`: `text` NOT NULL (`x-first-death-queue`).
   - `routing_key`: `text` NOT NULL (`x-death[0].routing-keys[0]`).
   - `motivo`: `text` NOT NULL (`x-death[0].reason`).
   - `intentos`: `int` NOT NULL con restricción `CHECK (intentos >= 1)`.
   - `payload`: **`text`** NOT NULL (**JAMÁS `jsonb`**, porque justamente almacena los payloads corruptos que no pudieron ser parseados como JSON).
   - `recibido_en`: `timestamptz` NOT NULL DEFAULT now().

> [!TIP]
> **Por qué `CHECK` en la base y no solo un `type` o `enum` en TypeScript:**
> Un tipo de TypeScript solo lo valida el transpilador antes de compilar. La base de datos no sabe nada de TypeScript; cualquier inserción directa vía `psql`, script de migración u otro microservicio podría insertar valores inconsistentes si no existiera la restricción `CHECK` ejecutada por el propio PostgreSQL.

### 8.2 Dueño 2: Microservicio Productor (`licencias` / `prestamos`) · Esquema Dedicado
* Tabla `licencias` (o `prestamos.prestamos`):
  - `id`: `serial` / `identity` PK.
  - `juego_id`: `int` NOT NULL (relación lógica con catálogo, sin FK).
  - `usuario_sub`: `text` NOT NULL (extraído de `req.user.sub`).
  - `estado`: `text` NOT NULL CHECK (estado IN ('activa', 'revocada')).
  - `adquirida_en`: `timestamptz` NOT NULL DEFAULT now().
  - `revocada_en`: `timestamptz` NULL.
  - `revocada_por`: `text` NULL (`sub` del administrador que ejecutó la revocación).

> [!IMPORTANT]
> **La Regla del Índice Parcial (Arturo):**
> Un jugador no puede tener dos licencias activas del mismo juego, pero sí puede volver a comprarlo legalmente si la anterior fue revocada.
> Un `UNIQUE (usuario_sub, juego_id)` plano impediría una segunda compra de por vida.
> **Solución**: Crear un **índice único parcial**:
> ```sql
> CREATE UNIQUE INDEX uq_licencias_activas 
> ON licencias.licencias (usuario_sub, juego_id) 
> WHERE estado = 'activa';
> ```
> En TypeORM: `@Index(['usuarioSub', 'juegoId'], { unique: true, where: "estado = 'activa'" })`.

---

## 9. Consumidor de Cartas Muertas (`CartasMuertasConsumidor`) (L7 Tramo 5.1)

El consumidor de cartas muertas evita que las DLQ crezcan indefinidamente sin supervisión:
1. **Un solo consumidor para las 3 DLQ**: Itera sobre `Object.values(DLQ)` consumiendo en un bucle `for`. Evita triplicar código idéntico.
2. **Inspección forense**: Extrae `x-first-death-queue` y `x-death[0]`.
3. **Persistencia en `mensajes_muertos`**: Inserta la fila en PostgreSQL y recién después ejecuta `canal.ack(mensaje)`.
4. **Resiliencia si la base de datos se cae**: Si el insert falla, captura el error, espera 5 segundos y ejecuta `canal.nack(mensaje, false, true)` para devolverlo a la DLQ sin perder la última copia del mensaje.

---

## 10. Mapeo Completo: Proyecto Guía (L7) vs VidalStore (EP2)

| Componente | Proyecto Guía (Biblioteca L7) | Proyecto VidalStore (EP2) |
|---|---|---|
| **Exchange de Eventos** | `biblioteca.eventos` (`topic`) | `vidalstore.eventos` (`topic`) |
| **Exchange de Comandos** | `biblioteca.comandos` (`direct`) | `vidalstore.comandos` (`direct`) |
| **Exchange de Fallos** | `biblioteca.dlx` (`direct`) | `vidalstore.dlx` (`direct`) |
| **Routing Keys** | `prestamo.creado`<br>`prestamo.devuelto`<br>`libro.agotado`<br>`correo.enviar` | `compra.realizada`<br>`licencia.revocada`<br>`juego.publicado`<br>`correo.enviar` |
| **Colas de Trabajo** | `notificaciones` (binding `prestamo.*`)<br>`auditoria` (binding `#`)<br>`correos` (binding `correo.enviar`) | 3 colas de trabajo del grupo:<br>`avisos` (binding debe recibir `licencia.revocada`)<br>`auditoria` (binding `#`)<br>`correos` (binding `correo.enviar`) |
| **Dead Letter Queues** | `notificaciones.dlq`<br>`auditoria.dlq`<br>`correos.dlq` | 3 DLQs vinculadas a `vidalstore.dlx`<br>`avisos.dlq`<br>`auditoria.dlq`<br>`correos.dlq` |
| **Consumidor DLQ** | `CartasMuertasConsumidor` | `CartasMuertasConsumidor` / `DlqConsumer` |
| **Persistencia Worker** | `eventos_auditoria`, `notificaciones`, `mensajes_muertos` | Mismas 3 tablas del worker en esquema `public` |
| **Persistencia Productor** | `prestamos.mjs` (tabla `prestamos.prestamos`) | Microservicio `licencias` (tabla `licencias.licencias`) |
| **Restricción Parcial** | `UNIQUE (usuario_sub, libro_id) WHERE estado = 'vigente'` | `UNIQUE (usuario_sub, juego_id) WHERE estado = 'activa'` |
| **Mensaje Envenenado** | `emitir.mjs 1 --roto` con `prestamo.creado` | `emitir.mjs 1 --roto` con `compra.realizada` |

---

## 11. Errores Frecuentes y Diagnóstico Inmediato (L7 Tramo 5.6)

| Mensaje de Error | Causa Real | Solución Inmediata |
|---|---|---|
| `no configuration file provided` | El comando de Compose se corrió fuera del directorio raíz de la plataforma. | Situarse en `vidalstore-plataforma` (donde reside `compose.yml`). |
| `ECONNREFUSED 127.0.0.1` dentro de un contenedor | El servicio intenta conectarse usando `localhost`. | Reemplazar `localhost` por el nombre de servicio de Docker (`postgres`, `rabbit1`). |
| `getaddrinfo ENOTFOUND postgres` | El servicio busca a `postgres` pero el contenedor de la base está detenido. | Caso que activa los reintentos (`conReintentos`); levantar Postgres con `docker compose up -d postgres`. |
| `Cambié el código y no pasa nada` | Docker reutilizó la imagen construida anteriormente. | Reconstruir la imagen del servicio con `docker compose up -d --build <servicio>`. |
| `406 PRECONDITION_FAILED` en worker | Las colas existían sin los argumentos de DLX. | Ejecutar `rabbitmqctl delete_queue <nombre>` para las colas de trabajo y reiniciar el worker. |
| `password authentication failed for user` | La contraseña en el `.env` no coincide con la guardada en el volumen inicializado. | Usar la contraseña original o limpiar el volumen con `docker compose down -v`. |
| `ERROR [MensajeriaService] canal: JSON.parse` | Un consumidor sin `try/catch` intentó parsear un mensaje inválido y botó el canal. | Envolver el parse en `try/catch` y rechazar con `nack(mensaje, false, false)`. |
