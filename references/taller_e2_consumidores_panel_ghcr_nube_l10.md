# Taller de la Entrega 2 (E2): Consumer Groups, Panel en Vivo, GHCR y Despliegue en AWS/Azure (L10)

Guía técnica y normativa completa del **Laboratorio L10 (`L10.pdf` · 111 páginas — «Taller de la E2»)**, con el mapeo exacto entre el proyecto de cátedra (`Biblioteca`) y el encargo evaluado **`VidalStore`** para la Entrega 2 (E2) de la Evaluación Parcial N°3 (EP3).

---

## 1. Mapa de la Entrega 2 (E2), Pauta de Puntaje y Mapeo Biblioteca $\leftrightarrow$ VidalStore

### 1.1 Distribución de los 100 Puntos de la E2
| Tramo | Contenido Técnico | Indicador Evaluado | Puntaje |
| :---: | :--- | :--- | :---: |
| **1 y 2** | Tablas en Postgres, 3 consumer groups con commit manual e idempotencia, y panel en vivo (`/panel` $\to$ `/v1/panel/en-vivo` $\to$ `/panel/en-vivo`). | **`IE5`** | **22 pts** |
| **3** | Rebobinar un grupo a `offset 0`, escalar a 3 y 4 instancias de `eventos`, `docs/topics.md`, `docs/consumer-groups.md`, y catálogo compactado (grupos de 3). | **`IE7` (19) + `IE8` (19)** | **38 pts** |
| **4** | `Dockerfile` multi-stage sobre `node:24-slim` (`USER node`) y workflow `.github/workflows/imagen.yml` publicando a GHCR con tag `${{ github.sha }}`. | **`Imágenes en GHCR`** | **10 pts** |
| **5 y 6** | Red AWS + capa de datos encendida (`mq-1..3`, `datos`, `gestion`, `nat`) y red Azure + 2 VMs creadas y desasignadas (`VM deallocated`). | **`Red y datos en la nube`** | **20 pts** |
| **7** | `bash levantar.sh` deja todo arriba + evidencia en `docs/despliegue.md`, `.zip` de `.env` y trabajo en equipo en Git (PRs cruzados sin automerge). | **`Compila` (5) + `Git` (5)** | **10 pts** |

> [!CAUTION]
> **Reglas de Tope de la Pauta E2**:
> 1. Si `bash levantar.sh` **no deja el sistema arriba y respondiendo**, los indicadores **`IE5`, `IE7` e `IE8` quedan con tope del 30%**.
> 2. Lo que haya quedado pendiente de la **E1** (productor de compras, simulador, `kafka/topics.sh`, primer consumidor) **recupera hasta el 60%** si llega resuelto en esta entrega.

### 1.2 Tabla de Equivalencia Exacta: `Biblioteca` (L10) $\leftrightarrow$ `VidalStore` (EP3)
| Elemento | Caso `Biblioteca` (L10) | Caso `VidalStore` (EP3) |
| :--- | :--- | :--- |
| **Topic de actividad / telemetría** | `biblioteca.lecturas` (key `libroId`, 1 día, `2.984` ev) | `vidalstore.actividad` (key `juegoId`, 1 día, `3.039` ev) |
| **Topic de transacciones** | `biblioteca.prestamos` (key `usuarioSub`, 7 días, `404` ev) | `vidalstore.compras` (key `usuarioSub`, 7 días, `401` ev) |
| **Topic compactado (Grupos de 3)** | `biblioteca.catalogo` (key `libroId`, `compact`, `15` ev) | `vidalstore.catalogo` (key `juegoId`, `compact`) |
| **Grupo 1 (2 topics $\to$ KPIs por minuto)** | `biblioteca-panel` $\to$ tabla `kpi_minuto` | `vidalstore-panel` $\to$ tabla `kpi_minuto` |
| **Grupo 2 (actividad $\to$ alertas 5 min)** | `biblioteca-alertas` $\to$ `ventanas_lectura` + `alertas` | `vidalstore-alertas` $\to$ `ventanas_actividad` (o `ventanas_lectura`) + `alertas` |
| **Grupo 3 (compras $\to$ neto semanal)** | `biblioteca-historial` $\to$ `prestamos_semana` + `prestamos_vistos` | `vidalstore-historial` $\to$ `ventas_semana` + `compras_vistas` (o `licencias_vistas`) |
| **Grupo 4 (Grupos de 3 $\to$ catálogo)** | `biblioteca-catalogo` $\to$ `catalogo_libros` | `vidalstore-catalogo` $\to$ `catalogo` (o `catalogo_juegos`) |
| **Rol exigido en `GET /panel/en-vivo`** | `@Roles('bibliotecarios')` | `@Roles('administradores')` |

---

## 2. Tramo 1 · Arquitectura de `eventos` (`src/streaming/`), Separación e Idempotencia (`IE5`)

### 2.1 Estructura Obligatoria de `src/streaming/` (Un Módulo por Grupo, Dos Clases por Grupo)
En `vidalstore-eventos`, cada consumer group vive en su propia subcarpeta con su módulo NestJS y **se divide estrictamente en dos clases**:

```text
eventos/src/streaming/
├── contrato.ts                  # Validación del sobre + EventoInvalido
├── consumidor-kafka.ts          # Clase base abstracta ConsumidorKafka<T>
├── ventanas.ts                  # Truncado de 5 min (UTC) y semana (America/Santiago)
├── streaming.module.ts          # Importa PanelModule, AlertasModule, HistorialModule (, CatalogoModule)
├── panel/
│   ├── panel.consumidor.ts      # Extiende ConsumidorKafka (SOLO Kafka)
│   ├── panel.negocio.ts         # Implementa Procesador (SOLO SQL/Postgres, CERO imports de Kafka)
│   ├── panel.controller.ts      # GET /panel/en-vivo
│   └── panel.module.ts
├── alertas/
│   ├── alertas.consumidor.ts
│   ├── alertas.negocio.ts
│   └── alertas.module.ts
├── historial/
│   ├── historial.consumidor.ts
│   ├── historial.negocio.ts
│   └── historial.module.ts
└── catalogo/                    # Obligatorio en grupos de 3
    ├── catalogo.consumidor.ts
    ├── catalogo.negocio.ts
    └── catalogo.module.ts
```

> [!IMPORTANT]
> **Regla de Oro de `IE5` (Separación de Responsabilidades)**:
> - **`<grupo>.consumidor.ts`**: Conecta al broker, se suscribe a los topics, valida el sobre con `Contrato<T>`, recorre el flujo con `for await`, llama a `negocio.procesar(evento)` con reintento ante caída de BD y **recién después ejecuta `await m.commit()`**.
> - **`<grupo>.negocio.ts`**: Recibe un objeto TypeScript ya validado y escribe en Postgres usando `DataSource`. **No importa absolutamente nada de `@platformatic/kafka`**. Si mañana el evento llegara por HTTP o por archivo, `negocio.ts` no cambiaría ni una línea.

### 2.2 Validación del Sobre (`contrato.ts`) y Clase Base (`consumidor-kafka.ts`)
- **`EventoInvalido`**: Cuando un mensaje no es JSON válido o incumple el sobre (`eventoId` UUID, `version === 1`, `emitidoEn` ISO válido, `tipo` permitido), el validador lanza `EventoInvalido`.
- **Diferencia entre `EventoInvalido` y caída de Postgres en `ConsumidorKafka<T>`**:
  1. Si `contrato.validar(m.value)` lanza **`EventoInvalido`**: el consumidor registra `WARN [<grupo>] ... INVALIDO (<motivo>)`, **ejecuta `await m.commit()`** y sigue con el siguiente mensaje (un JSON roto jamás se arreglará reintentándolo; en la E2 se registra y confirma, y en la E3 se enviará al `.dlt` antes del commit).
  2. Si `negocio.procesar(evento)` lanza un **error de base de datos** (ej. Postgres detenido): `procesarHastaEscribir()` **no hace commit**, registra `WARN [<grupo>] ... falló al escribir en la base; reintento en 2s` y reintenta cada 2 segundos hasta que Postgres vuelva.
- **Cierre Limpio en `~1,1 s` (`onModuleDestroy` + `enableShutdownHooks`)**:
  - `main.ts` **debe** invocar `app.enableShutdownHooks()` antes de `app.listen(puerto)`.
  - `onModuleDestroy()` pone `this.deteniendo = true`, cierra el stream (`await this.flujo.close()`) y cierra el consumidor (`await this.consumidor.close()`). Así envía `LeaveGroup` a Kafka y libera sus particiones en ~1 segundo en lugar de congelar el grupo durante los **60 segundos** del `sessionTimeout` por defecto de `@platformatic/kafka`.

```typescript
// Patrón oficial de suscripción en ConsumidorKafka<T> (src/streaming/consumidor-kafka.ts)
this.consumidor = new Consumer({
  clientId: `${ this.opciones.grupo }-${ process.pid }`,
  groupId: this.opciones.grupo,
  bootstrapBrokers: brokers,
  deserializers: { key: stringDeserializer, value: stringDeserializer },
  autocommit: false,
});

this.flujo = await this.consumidor.consume({
  topics: this.opciones.topics,
  mode: this.opciones.desdeElPrincipio ? MessagesStreamModes.EARLIEST : MessagesStreamModes.COMMITTED,
  fallbackMode: MessagesStreamModes.EARLIEST,
});
```

### 2.3 Las 3 Formas de Idempotencia en Postgres y la Trampa de TypeORM
Como Kafka entrega **al menos una vez (*at-least-once*)**, si el proceso escribe en Postgres y muere un milisegundo antes de `await m.commit()`, al arrancar volverá a recibir el mismo evento. Además, el dataset del simulador incluye **15 eventos duplicados a propósito** (mismo `eventoId` publicado dos veces).

| Estrategia | Cuándo se usa | Cómo funciona en SQL |
| :--- | :--- | :--- |
| **1. Una fila por evento (`kpi_minuto`)** | **`vidalstore-panel`** (`panel.negocio.ts`) | La tabla `kpi_minuto` tiene `evento_id uuid PRIMARY KEY`. Inserta con `INSERT INTO kpi_minuto ... ON CONFLICT (evento_id) DO NOTHING RETURNING evento_id`. Si devuelve `0` filas, el evento ya estaba contado (`'duplicado'`) y se hace commit sin sumar dos veces. Los totales por minuto se calculan al consultar con `GROUP BY` y función de ventana `sum(iniciadas - terminadas) OVER (ORDER BY minuto)::int AS en_curso`. |
| **2. Contadores + tabla `eventos_procesados` en transacción** | **`vidalstore-alertas`** y **`vidalstore-historial`** | Dentro de `await this.base.transaction(async (tx) => { ... })`: primero ejecuta `INSERT INTO eventos_procesados (grupo, evento_id, procesado_en) VALUES ($1, $2, now()) ON CONFLICT (grupo, evento_id) DO NOTHING RETURNING evento_id`. Si no devuelve fila, corta la transacción y retorna `'duplicado'`. Si devuelve fila, actualiza el contador en la **misma transacción** (ambos cambios se confirman o revierten juntos). La PK es compuesta **`(grupo, evento_id)`** porque un mismo evento lo leen varios grupos independientes. |
| **3. Estado actual con guarda temporal (`catalogo`)** | **`vidalstore-catalogo`** *(Grupos de 3)* | `INSERT INTO catalogo_libros ... ON CONFLICT (libro_id) DO UPDATE SET ... WHERE catalogo_libros.emitido_en < EXCLUDED.emitido_en`. Así, al reconstruir desde `offset 0` (mientras el segmento activo aún no ha sido compactado), un evento repetido o más antiguo no pisa un estado más nuevo. |

> [!CAUTION]
> **Trampa Crítica de TypeORM en `UPDATE ... RETURNING` (L10 §1.7, pág. 26)**:
> En TypeORM, ejecutar `await tx.query('UPDATE ... RETURNING ...', [...])` **no devuelve `filas`**, sino una tupla **`[filas, cantidadActualizada]`**.
> Si haces `const [p] = await tx.query('UPDATE prestamos_vistos ... RETURNING ...')`, la variable `p` recibe el arreglo `filas` en vez de la primera fila, por lo que `p.semana` y `p.ejemplares` quedan **`undefined`** sin lanzar excepción y el descuento en `prestamos_semana` / `ventas_semana` falla en silencio.
> - **Solución obligatoria**: Envolver siempre el `UPDATE ... RETURNING` en un CTE (`WITH ... SELECT`), porque para un `SELECT` TypeORM sí devuelve directamente el arreglo de filas:
> ```sql
> WITH devuelto AS (
>   UPDATE prestamos_vistos
>   SET devuelto_en = $2
>   WHERE prestamo_id = $1 AND devuelto_en IS NULL
>   RETURNING libro_id, semana, ejemplares
> )
> SELECT libro_id, semana, ejemplares FROM devuelto
> ```

### 2.4 Reglas de Negocio y Cifras Oficiales del Dataset (VidalStore vs Biblioteca)
El archivo `ventanas.ts` centraliza dos funciones puras deterministas basadas siempre en **`emitidoEn` del evento** (jamás en `new Date()` ni `now()`, porque el simulador reproduce una jornada histórica a cámara rápida):
1. **`ventanaDe5MinutosDe(emitidoEn)`**: Trunca al múltiplo de `300.000 ms` (5 min) en UTC:
   `new Date(Math.floor(Date.parse(emitidoEn) / 300_000) * 300_000).toISOString()`.
2. **`Expresión SQL de lunes semanal`**: Convierte `emitidoEn` a zona horaria `America/Santiago` antes de truncar a lunes (`date_trunc('week', $2::timestamptz AT TIME ZONE 'America/Santiago')::date`), evitando que eventos emitidos después de las 20:00/21:00 de Chile del domingo salten al lunes siguiente por estar en las 00:00 UTC.

| Consumer Group | Regla de Negocio Exacta | Cifras Oficiales `Biblioteca` (L10) | Cifras Oficiales `VidalStore` (EP3) |
| :--- | :--- | :--- | :--- |
| **`*-panel`** (lee los 2 topics) | Cuenta lecturas/partidas `iniciadas` y `terminadas` (calculando `en_curso` acumulado minuto a minuto) y préstamos/compras realizadas (unidades y monto CLP). Ignora búsquedas y devoluciones/revocaciones. | - `2.626` nuevos (`1.349` iniciadas, `897` terminadas, `380` préstamos / `662` ejemplares)<br>- `15` duplicados, `714` ignorados, `33` inválidos = `3.388`<br>- Al cierre (`22:00`): **`452` en curso** (máximo **`537` a las `21:48`**). | - Al cierre (`22:00` UTC / `18:00` Chile): **`362` partidas en curso**<br>- Máximo de la jornada: **`480` partidas en curso a las `21:46`**<br>- Compras acumuladas: **`380` compras por `6.291.370 CLP`**. |
| **`*-alertas`** (lee actividad/lecturas) | Agrupa eventos `*.terminada` en ventanas fijas de 5 min por `juegoId`/`libroId`. Dispara alerta si **`terminadas >= MINIMO` y `con_error / terminadas > 0.20`** (más del 20%). Si entra una lectura exitosa que baja el % de 20%, **borra la alerta** (`DELETE FROM alertas`). | - Con `MINIMO = 5`: **1 sola alerta**: **libro `10`** (*The Pragmatic Programmer*) en ventana **`21:30–21:35` UTC** (`17:30` Chile) con **`56` errores de `59` terminadas (`94,9%`)**.<br>- *(Con `MINIMO = 1` habría 2 falsas alarmas de `1/1 = 100%` en libros `5` y `7`)*. | - Con `MINIMO = 3` (o `5`): **1 sola alerta**: **juego `1328670`** (*Mass Effect Legendary Edition*) en ventana **`21:30–21:35` UTC** con **`68` errores de `69` terminadas (`98,6%`)**. |
| **`*-historial`** (lee compras/préstamos) | Suma compras/préstamos por `(juego_id, semana)` y guarda cada `licencia_id`/`prestamo_id` en tabla auxiliar (`*_vistos`). Al llegar `licencia.revocada` / `prestamo.devuelto`, busca la compra original por su ID (que llegó antes gracias a la key `usuarioSub`) y **descuenta en la semana original** (`GREATEST(0, ...)`). | - `380` préstamos (`662` ejemplares), **`15` devoluciones (`24` ejemplares)** $\Rightarrow$ **`638` ejemplares activos**.<br>- Top 1: libro `18` (*Clean Code*) con `52` préstamos (`93` pedidos, `4` devueltos, `89` activos). | - **`380` compras**, **`15` revocaciones**, **`6.032.190 CLP` netos**.<br>- *(La revocación no trae precio en su payload; el consumidor recupera el precio pagado desde la fila original en `compras_vistas` / `licencias_vistas` por `licencia_id`)*. |

---

## 3. Tramo 2 · El Panel en Vivo (`/panel` $\to$ `/v1/panel/en-vivo` $\to$ `/panel/en-vivo`)

### 3.1 Arquitectura de 4 Capas del Panel en Vivo
```text
[ web :4200/panel ]  --(cada 5s con Bearer token)-->  [ gateway :8080/v1/panel/en-vivo ]
                                                              │ (valida JWT + scope, preserva status)
                                                              ▼
[ eventos :3010/panel/en-vivo ]  <--(HTTP interno)--  [ bff :3000/panel/en-vivo ]
  (Promise.all de 3 SELECTs a Postgres)                 (@UseGuards(JwtGuard, RolGuard)
                                                         @Roles('administradores') - CERO Postgres)
```

1. **`eventos` (`GET /panel/en-vivo` en `panel.controller.ts`)**:
   - Corre en la red interna (`:3010`), sin guard de usuario final, y llama a `this.negocio.obtenerPanelEnVivo()`.
   - `obtenerPanelEnVivo()` ejecuta **3 consultas SQL en paralelo con `Promise.all`**:
     - `porMinuto`: últimos 60 minutos de `kpi_minuto` con función de ventana `sum(iniciadas - terminadas) OVER (ORDER BY minuto)::int AS en_curso`.
     - `porJuego` / `porLibro`: `prestamos_semana` / `ventas_semana` con `LEFT JOIN` a la tabla `catalogo` (si eres grupo de 2 y aún no existe la tabla de catálogo, `coalesce('Juego #' || p.juego_id, ...)`).
     - `alertas`: hasta 20 alertas de `alertas` ordenadas por `ventana_inicio DESC, porcentaje_error DESC`.
2. **`bff` (`GET /panel/en-vivo` en `panel.controller.ts`)**:
   - Protegido con `@UseGuards(JwtGuard, RolGuard)` y `@Roles('administradores')` (en Biblioteca `@Roles('bibliotecarios')`).
   - Lee `EVENTOS_URL` con `this.config.getOrThrow<string>('EVENTOS_URL')` (en `.env` y `.env.example`: `EVENTOS_URL=http://eventos:3010`, y en `compose.yml` del BFF `EVENTOS_URL: http://eventos:3010`).
   - **Regla innegociable**: **El BFF jamás importa `pg` ni TypeORM ni consulta Postgres directamente**; pide el JSON a `eventos` por HTTP y si `eventos` no responde lanza `ServiceUnavailableException` (`503`).
3. **`gateway` (`GET /v1/panel/en-vivo` en `proxy.controller.ts`)**:
   - Protegido con `@UseGuards(JwtGuard)`, exige scope de lectura y reenvía la cabecera `authorization` a `${bffUrl}/panel/en-vivo`, preservando el código HTTP exacto (`res.status(r.status).json(cuerpo)`):
     - Sin token $\to$ **`401 Unauthorized`** (cortado en Gateway).
     - Token de jugador / lector $\to$ **`403 Forbidden`** (cortado en `RolGuard` del BFF).
     - Token de administrador / bibliotecario $\to$ **`200 OK`** con `{ actualizadoEn, totales, porMinuto, porJuego, alertas }`.
4. **`web` (`panel.ts` en ruta `/panel` de Angular)**:
   - Usa **signals** (`datos`, `estado: 'cargando' | 'listo' | 'prohibido' | 'error'`, `mensajeError`, `refrescos`) y refresca automáticamente cada **5 segundos** sin acumular suscripciones al salir de la pantalla:
   ```typescript
   timer(0, 5000)
     .pipe(
       switchMap(() =>
         this.http.get<PanelEnVivo>(`${environment.apiUrl}/v1/panel/en-vivo`).pipe(
           catchError((err: HttpErrorResponse) => {
             if (err.status === 401) {
               this.estado.set('error');
               this.mensajeError.set('No has iniciado sesión (401).');
             } else if (err.status === 403) {
               this.estado.set('prohibido');
               this.mensajeError.set('Tu cuenta tiene rol de jugador: el panel en vivo es solo para administradores (403).');
             } else {
               this.estado.set('error');
               this.mensajeError.set(`No se pudo consultar el panel (${err.status || 'sin conexión'}).`);
             }
             return EMPTY;
           }),
         ),
       ),
       takeUntilDestroyed(this.destroyRef),
     )
     .subscribe((respuesta) => {
       this.datos.set(respuesta);
       this.estado.set('listo');
       this.refrescos.update((n) => n + 1);
     });
   ```
5. **Verificación en `levantar.sh`**:
   - Se agregan al final de `levantar.sh`:
     - `comprobar 401 http://localhost:8080/v1/panel/en-vivo`
     - `comprobar 200 http://localhost:3010/panel/en-vivo`

---

## 4. Tramo 3 · Rebobinar Offsets, Escalar a 3 y 4 Instancias, Documentación y Catálogo Compactado (`IE7` / `IE8`)

### 4.1 Rebobinar un Consumer Group a `offset 0` y Reconstruir su Tabla (`IE7`)
1. **Regla de Estado Inactivo**: Si intentas ejecutar `--reset-offsets` mientras `eventos` está corriendo, Kafka lo rechaza con:
   `Error: Assignments can only be reset if the group 'vidalstore-historial' is inactive, but the current state is Stable.`
2. **Procedimiento Exacto de 5 Pasos**:
   ```bash
   # 1. Detener el contenedor de eventos para que el grupo pase a Empty (inactivo)
   docker compose stop eventos

   # 2. Rebobinar el offset de vidalstore-historial a 0 en todas las particiones de vidalstore.compras
   docker compose exec broker-1 /opt/kafka/bin/kafka-consumer-groups.sh \
     --bootstrap-server broker-1:19092 \
     --group vidalstore-historial \
     --topic vidalstore.compras \
     --reset-offsets --to-earliest --execute

   # 3. Vaciar las tablas de ese grupo y borrar su registro de idempotencia en eventos_procesados
   docker compose exec postgres psql -U vidalstore -d vidalstore -c "
     TRUNCATE TABLE ventas_semana, compras_vistas;
     DELETE FROM eventos_procesados WHERE grupo = 'vidalstore-historial';
   "

   # 4. Volver a encender eventos (relee los 401 eventos en ~2 segundos)
   docker compose start eventos

   # 5. Comprobar que reconstruyó exactamente las mismas cifras (380 compras, 15 revocaciones, 6.032.190 CLP)
   #    y que los otros grupos (vidalstore-panel y vidalstore-alertas) NO se movieron de su offset.
   ```

### 4.2 Escalar `eventos` a 3 y 4 Instancias y Evidencia de `--describe --members` (`IE8`)
- **Por qué NO usar `docker compose up --scale eventos=4`**:
  En `compose.yml`, el servicio `eventos` publica fijo `"3010:3010"`. Con `--scale`, los contenedores 2, 3 y 4 fallan porque el puerto `3010` del host ya está ocupado; y si se cambiara a un rango `"3010-3013:3010"`, Docker asignaría puertos al azar rompiendo el chequeo `http://localhost:3010/panel/en-vivo` de `levantar.sh`.
- **Forma oficial sin tocar `compose.yml`**: Usar `docker compose run -d --no-deps --name eventos-N eventos` (que no publica puertos al host salvo que se pase `--service-ports`):
  ```bash
  # En equipos de 8 GB de RAM, detener kafka-ui antes para liberar ~350 MB:
  docker compose stop kafka-ui

  # Levantar 2 instancias adicionales (total = 3 instancias: eventos, eventos-2, eventos-3)
  docker compose run -d --no-deps --name eventos-2 eventos
  docker compose run -d --no-deps --name eventos-3 eventos

  # Verificar reparto 1, 1, 1 en alertas/historial (3 particiones) y 2, 2, 2 en panel (6 particiones)
  docker compose exec broker-1 /opt/kafka/bin/kafka-consumer-groups.sh \
    --bootstrap-server broker-1:19092 --describe --members --group vidalstore-alertas

  # Levantar la 4.ª instancia (total = 4 instancias > 3 particiones)
  docker compose run -d --no-deps --name eventos-4 eventos

  # Verificar que alertas muestra #PARTITIONS = 1, 1, 1 y 0 (1 ociosa)
  # mientras que panel muestra #PARTITIONS = 2, 2, 1 y 1 (0 ociosas porque lee 2 topics = 6 particiones)
  docker compose exec broker-1 /opt/kafka/bin/kafka-consumer-groups.sh \
    --bootstrap-server broker-1:19092 --describe --members --group vidalstore-alertas
  docker compose exec broker-1 /opt/kafka/bin/kafka-consumer-groups.sh \
    --bootstrap-server broker-1:19092 --describe --members --group vidalstore-panel

  # Limpiar instancias extra al terminar
  docker rm -f eventos-2 eventos-3 eventos-4
  docker compose start kafka-ui
  ```

### 4.3 Estructura Obligatoria de `docs/topics.md` y `docs/consumer-groups.md`
Ambos archivos viven en `vidalstore-plataforma/docs/` y deben contener:
1. **`docs/topics.md`**:
   - Tabla resumen de los topics (`vidalstore.compras`, `vidalstore.actividad`, `vidalstore.compras.dlt`, `vidalstore.actividad.dlt`, y `vidalstore.catalogo` en grupos de 3).
   - Justificación de cada parámetro en una sección por topic:
     - **3 particiones**: permite escalar hasta 3 consumidores por grupo en paralelo y probar en la defensa que un 4.º consumidor queda con `#PARTITIONS = 0` (ocioso).
     - **Replication factor 3 + `min.insync.replicas=2` + `acks=all`**: tolera la caída de 1 broker sin perder escrituras y rechaza con `NOT_ENOUGH_REPLICAS` si caen 2 brokers.
     - **Key de partición**: `usuarioSub` en `compras` (garantiza que `licencia.revocada` caiga en la misma partición y después de `compra.realizada`, distribuyendo parejo `147 / 141 / 113`); `juegoId` en `actividad` (mantiene juntas las partidas de un mismo juego para las ventanas de 5 min de `alertas`, documentando la partición caliente `P0` con `1.751` eventos [57,6%] por el juego `292030`); `juegoId` en `catalogo` (obligatorio porque la compactación conserva el último valor por key).
     - **Retención**: `604800000 ms` (7 días) en `compras` y `.dlt`; `86400000 ms` (1 día) en `actividad` y `.dlt`; `cleanup.policy=compact` **sin `retention.ms`** en `catalogo` (si tuviera `retention.ms`, Kafka borraría los juegos cuyo precio no ha cambiado en días).
   - Salida real en bloque ```` ```text ```` de `sh kafka/topics.sh`.
2. **`docs/consumer-groups.md`**:
   - Tabla de grupos (`vidalstore-panel`, `vidalstore-alertas`, `vidalstore-historial`, y `vidalstore-catalogo` en grupos de 3).
   - Explicación del **orden del commit** (`autocommit: false`, `await m.commit()` después de escribir en Postgres, reintento cada 2s si cae Postgres).
   - Explicación de las **formas de idempotencia** (`kpi_minuto` por `evento_id`, transacción con `eventos_procesados (grupo, evento_id)`, y guarda temporal `WHERE emitido_en < EXCLUDED.emitido_en` en `catalogo`).
   - Regla y umbral mínimo de `vidalstore-alertas` (por qué `MINIMO = 3` o `5` filtra falsos positivos de 1 sola partida fallida y deja únicamente la caída real del juego `1328670` de `21:30` a `21:35` con `68/69`).
   - Cómo `vidalstore-historial` descuenta revocaciones buscando la compra previa por `licencia_id`.
   - Salidas reales en bloques ```` ```text ```` de:
     1. `--describe` de los grupos con `LAG 0` después de rebobinar y reconstruir `historial`.
     2. `--describe --members` con **3 instancias** y con **4 instancias** (`1, 1, 1 y 0` en `alertas` vs `2, 2, 1 y 1` en `panel`).

### 4.4 El Catálogo Compactado para Grupos de 3 (`vidalstore.catalogo` y `vidalstore-catalogo`)
1. **En el productor (`vidalstore-catalogo` / `libros`)**:
   - Al arrancar (`onModuleInit`), **antes** de sembrar o publicar los juegos iniciales, lee todo el topic `vidalstore.catalogo` desde `offset 0` (`listOffsets` + `consume({ mode: EARLIEST, autocommit: false })` con grupo propio sin hacer commit) para armar un `Map` con el último estado publicado de cada `juegoId`.
   - Compara cada juego local con el último publicado en Kafka:
     - Si el `juegoId` **no existe** en el topic $\to$ publica `juego.publicado` (en Biblioteca `libro.publicado`).
     - Si el `juegoId` **ya existe pero cambió** su título, precio, categoría o disponibilidad $\to$ publica `precio.cambiado` / `juego.actualizado` (en Biblioteca `libro.actualizado`).
     - Si **no cambió nada** $\to$ **no republica nada** (así reiniciar el contenedor no ensucia el log).
   - Cuando un administrador crea o edita un juego por HTTP (`POST` / `PATCH`), el servicio actualiza su base y llama a `productor.publicarCambio(...)`.
   - **Detalle del sobre**: Los eventos de catálogo son eventos de entidad, no de usuario, por lo que **no llevan `usuarioSub`** (`requiereUsuario: false` en `Contrato<T>`).
2. **En el consumidor (`eventos/src/streaming/catalogo/`)**:
   - Usa `desdeElPrincipio: true` (`mode: MessagesStreamModes.EARLIEST`) para reconstruir la tabla `catalogo` desde `offset 0` en cada arranque.
   - Aplica upsert con guarda temporal: `ON CONFLICT (juego_id) DO UPDATE SET ... WHERE catalogo.emitido_en < EXCLUDED.emitido_en`.

---

## 5. Tramo 4 · Imágenes Multi-Stage sobre `node:24-slim` y Workflow a GHCR (`Imágenes en GHCR`)

### 5.1 Los 7 Repositorios que Publican Imagen en GHCR
Todos los repositorios salvo `plataforma` (`web`/`frontend`, `gateway`, `bff`, `catalogo`/`libros`, `licencias`/`prestamos`, `eventos`, `admin`) llevan **`Dockerfile`**, **`.dockerignore`** y **`.github/workflows/imagen.yml`**.

### 5.2 Plantilla Oficial de `Dockerfile` Multi-Stage para los 6 Servicios NestJS
```dockerfile
# Etapa 1: compilacion (tiene devDependencies, TypeScript y el CLI de Nest)
FROM node:24-slim AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY tsconfig*.json nest-cli.json ./
COPY src ./src
RUN npm run build

# Etapa 2: ejecucion (solo lo necesario para correr en produccion)
FROM node:24-slim
WORKDIR /app
ENV NODE_ENV=production

COPY package.json package-lock.json ./
RUN npm ci --omit=dev && npm cache clean --force

COPY --from=build /app/dist ./dist
# IMPORTANTE: En catalogos/libros, licencias/prestamos y eventos (que leen esquema.sql en onModuleInit):
COPY esquema.sql ./

USER node
EXPOSE 3000
CMD ["node", "dist/main.js"]
```
- **Qué servicios llevan `COPY esquema.sql ./`**: **`catalogo` (`libros`)**, **`licencias` (`prestamos`)** y **`eventos`**, porque sus módulos de base de datos ejecutan `readFileSync(join(process.cwd(), 'esquema.sql'))` al iniciar. (`gateway`, `bff` y `admin` no usan `esquema.sql`).
- **Para `web` (`frontend` Angular 21)**:
  - Etapa 1 (`FROM node:24-slim AS build`): `npm ci` + `npx ng build --configuration production`.
  - Etapa 2 (`FROM nginx:1.29-alpine`): copia `nginx.conf` (con `try_files $uri $uri/ /index.html;`) y `COPY --from=build /app/dist/web/browser /usr/share/nginx/html` (verificando el `outputPath` exacto en `angular.json`).
- **Verificación obligatoria de seguridad y limpieza de la imagen final**:
  ```bash
  docker run --rm --entrypoint sh vidalstore-bff:prueba -c 'id && ls -la /app && find /app/node_modules -maxdepth 2 -name "nest" | wc -l'
  # Debe mostrar: uid=1000(node) gid=1000(node) y 0 al final (cero CLI de Nest en producción)
  ```

### 5.3 Plantilla Oficial de `.dockerignore`
```gitignore
node_modules
dist
.angular
*.log
*.tsbuildinfo
.env
.env.*
!.env.example
.git
.github
README.md
```
> [!WARNING]
> **Por qué `.env` y `.env.*` son innegociables en `.dockerignore`**:
> Aunque `.env` esté en `.gitignore`, cuando ejecutas `docker build` en tu computador sí existe el archivo `.env` local. Sin `.dockerignore`, un `COPY . .` metería tus contraseñas dentro de la capa de la imagen publicada en GHCR.

### 5.4 Workflow Oficial `.github/workflows/imagen.yml`
```yaml
name: Publicar imagen en GHCR

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  packages: write

jobs:
  construir-y-publicar:
    runs-on: ubuntu-latest
    steps:
      - name: Descargar el repositorio
        uses: actions/checkout@v4

      - name: Iniciar sesion en GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Construir y publicar la imagen
        run: |
          IMAGEN="ghcr.io/${GITHUB_REPOSITORY,,}"
          docker build \
            --tag "${IMAGEN}:${GITHUB_SHA}" \
            --label "org.opencontainers.image.revision=${GITHUB_SHA}" \
            .
          docker push "${IMAGEN}:${GITHUB_SHA}"
```
- **3 Reglas Críticas de GHCR**:
  1. **`${GITHUB_REPOSITORY,,}` en minúsculas**: Docker rechaza nombres de imagen con mayúsculas; `${VAR,,}` en bash convierte el `Owner/Repo` a minúsculas.
  2. **Tag con `${GITHUB_SHA}` (prohibido `:latest`)**: Cada imagen queda atada al commit exacto que la produjo (auditable y reproducible).
  3. **Activar Actions en Forks y poner los 7 paquetes en `Public`**: En un fork nuevo, activar el botón verde en la pestaña **Actions**; y tras el primer push, entrar a `Package settings -> Change visibility -> Public` en los 7 paquetes. Comprobar con:
     ```bash
     docker logout ghcr.io
     docker pull --platform linux/amd64 ghcr.io/<tu-usuario>/vidalstore-eventos:<sha>
     ```

---

## 6. Tramo 5 · Despliegue Automatizado de Red y Capa de Datos en AWS (`deploy/aws/`)

### 6.1 Topología de Red y Máquinas EC2 en AWS (`VPC 10.0.0.0/16`)
```text
VPC 10.0.0.0/16 (vidalstore-vpc) + Internet Gateway (vidalstore-igw)
├── Subred publica     10.0.1.0/24  (us-east-1a) [rt-publica: 0.0.0.0/0 -> igw]
│   ├── nat            10.0.1.10    (t3.nano,  sg-nat, --no-source-dest-check, iptables -F + MASQUERADE)
│   └── (gw en E3)     10.0.1.20    (sg-gw: 80/443 internet + 443 desde IP_GW_AZURE/32)
├── Subred aplicacion  10.0.11.0/24 (us-east-1a) [rt-privada: 0.0.0.0/0 -> eni de nat]
│   └── gestion        10.0.11.20   (t3.medium, sg-gestion: Kafka UI :8085 solo por túnel SSM + simulador)
├── Subred datos-a     10.0.21.0/24 (us-east-1a) [rt-privada]
│   ├── mq-1           10.0.21.11   (t3.small, sg-mq: Kafka controller 1 + broker 4 + RabbitMQ rabbit@mq-1)
│   ├── mq-3           10.0.21.13   (t3.small, sg-mq: Kafka controller 3 + broker 6)
│   └── datos          10.0.21.30   (t3.small, sg-datos: PostgreSQL 18 en :5432)
└── Subred datos-b     10.0.22.0/24 (us-east-1b) [rt-privada]
    └── mq-2           10.0.22.12   (t3.small, sg-mq: Kafka controller 2 + broker 5 + RabbitMQ rabbit@mq-2)
```

### 6.2 Reglas Críticas de los Scripts `deploy/aws/`
1. **`comun.sh` (Protección contra CRLF, Rol Vocareum y Ejecución vía SSM)**:
   - Envuelve `aws` en `aws_()` que filtra `\r` (`tr -d '\r'`) para que Git Bash en Windows no corrompa los IDs (`vpc-xxx\r`).
   - Verifica `aws sts get-caller-identity` exigiendo `assumed-role/voclabs/` (bloquea que alguien corra los scripts contra una cuenta personal con tarjeta de crédito).
   - `en_maquina <nombre> <script>`: codifica el comando en **base64** y lo ejecuta remotamente mediante `aws ssm send-command --document-name AWS-RunShellScript` sin abrir jamás el puerto 22.
2. **`01-red.sh` (Trampa de AWS con el prefijo `sg-` en `GroupName`)**:
   - AWS **prohíbe crear Security Groups cuyo `--group-name` empiece con `sg-`** (`GroupName cannot start with reserved prefix "sg-"`).
   - Solución oficial: crear el grupo con `--group-name "${PROYECTO}-${rol}"` (ej. `vidalstore-mq`) y ponerle el tag **`Name=sg-${rol}`** (`sg-gw`, `sg-nat`, `sg-app`, `sg-gestion`, `sg-mq`, `sg-datos`).
   - **Cero puerto 22 abierto** en toda la VPC (el acceso es 100% por AWS Systems Manager Session Manager).
   - En `sg-gw`, además de `80` y `443` desde `0.0.0.0/0`, se declara la regla explícita de **`443` desde `${IP_GW_AZURE}/32`** con descripción `"Desde gw-azure en Azure"` (verificable con `describe-security-group-rules`).
3. **`02-maquinas.sh` y `nat-user-data.sh` (Trampa de `FORWARD REJECT` en Amazon Linux 2023)**:
   - Amazon Linux 2023 trae por defecto una regla en `iptables` que rechaza todo el tráfico en `FORWARD` (`REJECT all -- anywhere anywhere reject-with icmp-host-prohibited`). Si solo haces `iptables -t nat -A POSTROUTING -j MASQUERADE` sin limpiar `FORWARD`, las subredes privadas se quedan sin internet.
   - `nat-user-data.sh` **debe** ejecutar `iptables -F` antes de `iptables -t nat -F` y `iptables -t nat -A POSTROUTING -s 10.0.0.0/16 -o "$IFACE" -j MASQUERADE`, además de `aws ec2 modify-instance-attribute --instance-id "$NAT_ID" --no-source-dest-check`.
   - Todas las instancias se lanzan con `--iam-instance-profile Name=LabInstanceProfile`, `--metadata-options HttpTokens=required` (**IMDSv2 obligatorio**), disco `gp3` cifrado y **sin `--key-name`**.
4. **`03-subir.sh` (Artefactos a S3 excluyendo secretos + Secretos a SSM Parameter Store)**:
   - Sube la carpeta `deploy/` a `s3://$BUCKET/deploy` con `--exclude "aws/secretos/*"`.
   - Sube `mq-1.env`, `mq-2.env` y `datos.env` a **AWS Systems Manager Parameter Store** como **`SecureString`** (`/vidalstore/mq-1.env`, `/vidalstore/mq-2.env`, `/vidalstore/datos.env`). En S3 nunca hay contraseñas.
5. **`en-la-maquina.sh`, `mq/kafka/compose.yml`, `mq/rabbit/secretos.sh` y `04-levantar.sh`**:
   - **Por qué `mq/kafka/compose.yml` usa `network_mode: host`**: En AWS, `controller-N` (`:9093`) y `broker-N` (`:19092`) están en máquinas distintas (`10.0.21.11`, `10.0.22.12`, `10.0.21.13`). Con red bridge de Docker, `controller-1` resolvería `controller-1:9093` a la IP de la EC2 y no a su contenedor. Con `network_mode: host`, ambos escuchan directo en la IP privada de la instancia.
   - **Por qué `mq/rabbit/secretos.sh` escribe `/var/lib/rabbitmq/.erlang.cookie` en vez de usar `RABBITMQ_ERLANG_COOKIE`**: En RabbitMQ 4.3, la imagen oficial deprecó `RABBITMQ_ERLANG_COOKIE`. `secretos.sh` lee `RABBITMQ_COOKIE` del `.env` descargado de Parameter Store, genera `erlang.cookie` **sin salto de línea final (`printf '%s'`)**, con permisos **`chmod 400`** y dueño **`chown 999:999`** (usuario `rabbitmq` dentro del contenedor), y lo monta `:ro`.
   - `04-levantar.sh` levanta Kafka en paralelo en `mq-1..3`, corre `topics.sh` en `mq-1`, levanta RabbitMQ en `mq-1` y luego `mq-2`, aplica políticas en `mq-1`, levanta Postgres 18 en `datos`, levanta Kafka UI en `gestion` y corre el simulador en un contenedor efímero `node:24-slim` poblando los topics reales en AWS.
6. **`05-tunel.sh` y `06-evidencia.sh`**:
   - `05-tunel.sh` abre un port-forwarding SSM de `localhost:18085` $\to$ `gestion:8085` para ver Kafka UI sin abrir puertos públicos.
   - `06-evidencia.sh` recolecta automáticamente las 5 salidas de AWS + RabbitMQ + Postgres para `docs/despliegue.md`.

---

## 7. Tramo 6 · Despliegue de Red y 2 VMs Desasignadas en Azure (`deploy/azure/`)

### 7.1 Topología en Azure (`VNet 10.1.0.0/16`)
```text
Resource Group: rg-vidalstore (Región permitida por policy: northcentralus / eastus2 / centralus...)
VNet 10.1.0.0/16 (vnet-vidalstore)
├── Subred publica  10.1.1.0/24 [nsg-gw-azure: 80/443 Internet, 22 solo MI_IP/32 + SSH_EXTRA, * desde 10.1.2.0/24]
│   └── gw-azure    10.1.1.4    (Standard_B2ats_v2, IP pública estática pip-gw-azure, NIC con --ip-forwarding true,
│                                cloud-init: Docker + sysctl ip_forward=1 + iptables DOCKER-USER ACCEPT + MASQUERADE)
└── Subred privada  10.1.2.0/24 [--default-outbound false, nsg-bff: 100 Allow VNet / 4000 Deny *,
                                 rt-privada: 0.0.0.0/0 -> VirtualAppliance 10.1.1.4]
    └── bff         10.1.2.4    (Standard_B2als_v2, SIN IP pública, accede por ProxyJump gw-azure,
                                 sale a internet con la IP pública de gw-azure)
```

### 7.2 Las 5 Trampas Críticas de Azure y sus Soluciones en `deploy/azure/`
1. **Regiones permitidas y cuota de 4 vCPUs (`comun.sh`)**:
   - Azure for Students restringe la creación a 5 regiones por suscripción (consultar policy `Allowed locations`) y da una cuota de **4 vCPUs** por familia `BS` en cada región (`gw-azure` + `bff` usan $2 + 2 = 4\text{ vCPUs}$ exactas).
2. **`--default-outbound false` obligatorio en la subred `privada` (`red.sh`)**:
   - A diferencia de AWS, Azure regala salida implícita a internet a las subredes nuevas aunque no tengan IP pública. Si no pasas **`--default-outbound false`** al crear `privada`, `bff` saldrá directo a internet ignorando `rt-privada` o fallará al mezclar rutas.
3. **Prohibido poner tildes o `ñ` en `cloud-init-*.yaml` (Trampa Silenciosa de Azure)**:
   - Azure CLI en Windows recodifica los archivos con caracteres no ASCII en `cp1252` antes de subirlos a `CustomData`. En la VM Ubuntu, `cloud-init` intenta decodificar `UTF-8`, encuentra un byte inválido (`UnicodeDecodeError`), **descarta el archivo entero sin instalar Docker ni configurar el NAT**, y aun así `cloud-init status` reporta **`status: done`** como si todo hubiera salido bien.
   - **Verificación obligatoria**: `LC_ALL=C grep -n '[^ -~]' deploy/azure/cloud-init-*.yaml` no debe imprimir ninguna línea.
4. **Regla `DOCKER-USER` en `cloud-init-gw-azure.yaml` (Docker bloquea el NAT)**:
   - Cuando `cloud-init` instala `docker.io` en `gw-azure`, el demonio de Docker cambia la política de la cadena `FORWARD` de `iptables` a **`DROP`**. Sin insertar explícitamente `iptables -I DOCKER-USER -s 10.1.2.0/24 -j ACCEPT` y `iptables -I DOCKER-USER -d 10.1.2.0/24 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT`, `bff` se queda sin internet en el instante en que se instala Docker en `gw-azure`.
   - Por eso `maquinas.sh` crea primero `gw-azure`, **espera a que termine su `cloud-init` (`ssh gw-azure "cloud-init status --wait"`)** y recién entonces crea `bff` (para que cuando `bff` arranque, el NAT de `gw-azure` ya esté enrutando sus paquetes `apt`).
5. **`az vm deallocate` vs `Stop` (`apagar.sh`)**:
   - Apagar desde dentro con `sudo shutdown -h now` o `Stop` deja la VM en `VM stopped` (**sigue cobrando vCPU y RAM por hora**).
   - Es obligatorio usar `bash deploy/azure/apagar.sh` (`az vm deallocate --no-wait`), que libera el hardware físico y deja ambas VMs en **`VM deallocated`** ($0\text{ USD/h}$ de cómputo), conservando la IP pública estática de `gw-azure` para actualizar el puerto 443 de `sg-gw` en AWS (`IP_GW_AZURE="..." bash deploy/aws/01-red.sh`).

---

## 8. Tramo 7 · Evidencia (`docs/despliegue.md`), `.zip` de `.env`, PDF y Cajas de Pulso L10

### 8.1 Las 8 Salidas en Texto Obligatorias en `vidalstore-plataforma/docs/despliegue.md`
Todas van en bloques ```` ```text ```` (nunca capturas de pantalla):
1. **AWS — Instancias EC2** (`Name`, `PrivateIpAddress`, `PublicIpAddress`, `InstanceType`, `State`, `AZ`).
2. **AWS — Subredes** (`Name`, `CidrBlock`, `AvailabilityZone`) mostrando `datos-a` en `us-east-1a` y `datos-b` en `us-east-1b`.
3. **AWS — Tablas de ruteo** (`rt-publica` hacia `igw-...` y `rt-privada` hacia la interfaz `eni-...` del NAT).
4. **AWS — Regla del puerto 443 de `sg-gw`** mostrando `${IP_GW_AZURE}/32` y descripción `"Desde gw-azure en Azure"`.
5. **AWS — Los 4 topics de Kafka y el conteo de eventos por partición** desde `mq-1` (`vidalstore.actividad: 3.039`, `vidalstore.compras: 401`, `.dlt: 0`), más `rabbitmqctl cluster_status` + `list_policies` en `mq-1..2` y `psql \dt` en `datos`.
6. **Azure — Las 2 VMs con su estado e IPs** (`gw-azure` y `bff` en **`VM deallocated`**, IP pública de `gw-azure`, `10.1.1.4` y `10.1.2.4`).
7. **Azure — Tabla de rutas `rt-privada` y subredes** (`0.0.0.0/0 -> VirtualAppliance 10.1.1.4` y `defaultOutboundAccess: false` en `privada`).
8. **Azure — Prueba de salida a internet desde `bff` a través de `gw-azure`** (`hostname: bff`, IP privada `10.1.2.4` y `curl -s ifconfig.me` devolviendo exactamente la IP pública de `gw-azure`).

### 8.2 Empaquetado de `envs-grupoNN-seccion.zip` (10 archivos `.env` con carpeta delante)
- Debe contener los **10 archivos `.env`** con su ruta relativa para distinguir a qué servicio pertenece cada uno:
  - Los 7 servicios locales: `vidalstore-web/.env`, `vidalstore-gateway/.env`, `vidalstore-bff/.env`, `vidalstore-catalogo/.env`, `vidalstore-licencias/.env`, `vidalstore-eventos/.env`, `vidalstore-admin/.env`.
  - Los 3 secretos de AWS: `vidalstore-plataforma/deploy/aws/secretos/mq-1.env`, `mq-2.env`, `datos.env`.
- **Trampa de Git Bash en Windows**: En Git Bash, `tar` a secas es GNU tar, que **ignora `-a`** y crea un archivo `.tar` disfrazado con extensión `.zip` (que al abrirlo en Windows o macOS da error de archivo dañado). En Windows invocar siempre **`/c/Windows/System32/tar.exe -a -c -f envs-grupoNN-seccion.zip ...`**.
- **Verificación de 0 archivos `.env` subidos a Git en los 8 repositorios**:
  ```bash
  for r in vidalstore-*; do echo "=== $r ==="; git -C "$r" ls-files | grep -E '(^|/)\.env$' || echo "OK: sin .env en Git"; done
  ```

### 8.4 Empaquetado Oficial del Archivo `entrega-e2-grupoNN-seccion.zip` (`EP3-Entrega-2.pdf` pág. 11–13)
El encargo se entrega como un único archivo `.zip` al AVA con copia por correo a `cr.calderons@profesor.duoc.cl`.
- **Estructura estricta interna**:
  ```text
  entrega-e2-grupoNN-seccion.zip
  ├── informe.pdf
  ├── repositorios.md
  └── envs/
      ├── vidalstore-plataforma/.env
      ├── vidalstore-eventos/.env
      └── ...
  ```
- **Script oficial recomendado `scripts/generar-entrega2.sh`**:
  Automatiza la recolección de variables `.env` reales, la extracción de los SHAs de `main` en cada repositorio para `repositorios.md`, y el empaquetado del `.zip` asegurando compatibilidad multiplataforma (usando `zip -r` en Linux/macOS y `/c/Windows/System32/tar.exe -a -c -f` en Git Bash/Windows).

### 8.5 Las 7 Cajas de Respuestas de Pulso L10
| Caja | Qué pide pegar o responder en Pulso L10 |
| :---: | :--- |
| **1 (Tramo 1)** | La consulta `SELECT grupo, count(*) FROM eventos_procesados GROUP BY grupo` junto con el conteo de filas de las tablas (`kpi_minuto`, `alertas`, `prestamos_semana`/`ventas_semana`) y explicar en 2 líneas por qué hay `15` eventos duplicados que no se sumaron dos veces. |
| **2 (Tramo 2)** | La salida de `curl -i` de las 3 pruebas de `/v1/panel/en-vivo`: sin token (`401`), con token de lector/jugador (`403`) y con token de bibliotecario/administrador (`200` con el JSON resumido). |
| **3 (Tramo 3)** | La salida de `kafka-consumer-groups.sh --describe --members` con **3 instancias** y con **4 instancias**, explicando por qué en `alertas`/`historial` una instancia queda con `#PARTITIONS = 0` mientras en `panel` las 4 instancias reciben particiones (`2, 2, 1 y 1`). |
| **4 (Tramo 4)** | Las URLs públicas de los 7 paquetes en `ghcr.io/<usuario>/...:<sha>` y la salida de `docker run --rm --entrypoint sh ... -c 'id'` mostrando `uid=1000(node)`. |
| **5 (Tramo 5)** | Las salidas de AWS (`06-evidencia.sh`): las 6 instancias EC2, los 4 topics con el conteo de mensajes por partición (`2.984`/`3.039` y `404`/`401`), el `cluster_status` de RabbitMQ con `rabbit@mq-1` y `rabbit@mq-2`, y la regla 443 de `sg-gw`. |
| **6 (Tramo 6)** | Las salidas de Azure: la prueba desde `bff` (`curl -s ifconfig.me` igual a la IP pública de `gw-azure`), `rt-privada` + `defaultOutboundAccess: false`, y las 2 VMs en estado **`VM deallocated`**. |
| **7 (Tramo 7)** | Enlace al repositorio `plataforma` con `docs/topics.md`, `docs/consumer-groups.md` y `docs/despliegue.md`, y lista de Pull Requests cruzados del equipo. |

---

## 9. Tablas Maestras de Diagnóstico «Si algo te falló» de L10 (35+ Síntomas y Soluciones)

### 9.1 Tabla de Diagnóstico de los Tramos 1, 2 y 3 (Kafka Local, Consumidores y Panel)
| Síntoma Observado | Causa Raíz | Solución Exacta |
| :--- | :--- | :--- |
| `Error: Assignments can only be reset if the group '...' is inactive, but the current state is Stable` | Intentaste correr `--reset-offsets` con el contenedor `eventos` encendido. | Ejecutar `docker compose stop eventos`, correr `--reset-offsets --to-earliest --execute` y luego `docker compose start eventos`. |
| El descuento de devolución/revocación en `historial` no resta nada y no lanza error | Usaste `const [p] = await tx.query('UPDATE ... RETURNING ...')` directo en TypeORM (que devuelve `[filas, cantidad]`). | Envolver el `UPDATE ... RETURNING` en un CTE: `WITH devuelto AS (UPDATE ... RETURNING ...) SELECT ... FROM devuelto`. |
| Detener `eventos` tarda 60 segundos o congela el grupo en `PreparingRebalance` | Falta `app.enableShutdownHooks()` en `main.ts` o falta `await consumidor.close()` en `onModuleDestroy()`. | Agregar `app.enableShutdownHooks()` antes de `app.listen()` e implementar `onModuleDestroy()` cerrando `flujo` y `consumidor`. |
| Las ventas del domingo a las 21:00 de Chile aparecen en la semana del lunes siguiente | Truncaste la semana en UTC (`date_trunc('week', $2::timestamptz)`) en vez de hora local. | Usar `date_trunc('week', $2::timestamptz AT TIME ZONE 'America/Santiago')::date`. |
| Aparecen 3 alertas en vez de 1 sola en `alertas` | No pusiste el umbral mínimo de lecturas/partidas terminadas (`MINIMO = 5` en Biblioteca, `3` o `5` en VidalStore). | Exigir `terminadas >= MINIMO` además de `con_error / terminadas > 0.20` para filtrar ventanas con 1 sola partida fallida (`1/1 = 100%`). |
| `GET /v1/panel/en-vivo` devuelve `403` incluso al administrador/bibliotecario | El orden de los guards en el BFF está invertido (`@UseGuards(RolGuard, JwtGuard)`) o el nombre del grupo en `@Roles(...)` no coincide. | Poner `@UseGuards(JwtGuard, RolGuard)` en ese orden estricto y `@Roles('administradores')` (o `'bibliotecarios'`). |
| Al escalar con `docker compose up --scale eventos=4` falla por puerto `3010` ocupado | `eventos` publica `"3010:3010"` fijo al host en `compose.yml`. | Levantar las instancias adicionales con `docker compose run -d --no-deps --name eventos-2 eventos` (sin `--service-ports`). |
| En un PC de 8 GB de RAM, al levantar `eventos-3` o `eventos-4` un contenedor muere con `Exited (137)` | Falta memoria RAM física (`OOMKilled`). | Ejecutar `docker compose stop kafka-ui` antes de levantar las instancias adicionales de `eventos`. |

### 9.2 Tabla de Diagnóstico de los Tramos 4, 5, 6 y 7 (GHCR, AWS y Azure)
| Síntoma Observado | Causa Raíz | Solución Exacta |
| :--- | :--- | :--- |
| `invalid tag "ghcr.io/Usuario/repo:sha": repository name must be lowercase` | Tu usuario o repositorio de GitHub tiene mayúsculas. | Convertir a minúsculas en bash: `IMAGEN="ghcr.io/${GITHUB_REPOSITORY,,}"`. |
| `ENOENT: no such file or directory, open '/app/esquema.sql'` al arrancar imagen en producción | El `Dockerfile` multi-stage copió `/app/dist` pero olvidó copiar `esquema.sql` en la etapa 2. | Agregar `COPY esquema.sql ./` en la etapa 2 del `Dockerfile` de `catalogo`/`libros`, `licencias`/`prestamos` y `eventos`. |
| `docker pull` sin login falla con `unauthorized` o `manifest unknown` | El paquete en GHCR nace `Private` por defecto o el workflow nunca corrió porque es un fork. | Habilitar workflows en la pestaña **Actions** del fork, hacer push y cambiar visibilidad del paquete a **Public** en `Package settings`. |
| `InvalidParameterValue: Value (sg-gw) for parameter groupName is invalid. GroupName cannot start with reserved prefix "sg-"` | AWS reserva el prefijo `sg-` para los IDs internos de Security Groups. | Usar `--group-name "${PROYECTO}-gw"` y poner el nombre `sg-gw` en el tag `Key=Name,Value=sg-gw`. |
| Las máquinas privadas en AWS (`mq-1..3`, `datos`, `gestion`) no tienen internet aunque `nat` está encendido | La cadena `FORWARD` de Amazon Linux 2023 en `nat` tiene la regla por defecto `REJECT all`, o olvidaste `--no-source-dest-check`. | Ejecutar `iptables -F` antes del `MASQUERADE` en `nat-user-data.sh` y desactivar `SourceDestCheck` en la instancia `nat`. |
| `TargetNotConnected` al correr `04-levantar.sh` o `05-tunel.sh` en AWS | La instancia EC2 acaba de arrancar o no tiene salida a internet hacia el endpoint de SSM. | Esperar 30s a que registre en SSM (`esperar_ssm`) y verificar que `rt-privada` apunte a la ENI de `nat`. |
| `rabbit@mq-2` no se une al clúster de `rabbit@mq-1` en AWS | El archivo `erlang.cookie` tiene un salto de línea `\n` al final o no tiene permisos `400` / dueño `999:999`. | Crear `erlang.cookie` con `printf '%s' "$RABBITMQ_COOKIE"`, `chmod 400` y `chown 999:999`. |
| `LocationNotAvailableForResourceType` o `RequestDisallowedByPolicy` en Azure | La región elegida no está entre las 5 permitidas por la política de tu suscripción Azure for Students. | Consultar las regiones permitidas en la policy `Allowed locations` y definir `UBICACION` en `deploy/azure/comun.sh`. |
| En Azure, `gw-azure` muestra `cloud-init status: done` pero `docker` no está instalado y `ip_forward` vale `0` | Pusiste una tilde o una `ñ` en un comentario de `cloud-init-gw-azure.yaml`. | Eliminar todo carácter no ASCII (`LC_ALL=C grep -n '[^ -~]' deploy/azure/cloud-init-*.yaml` debe dar vacío) y recrear la VM. |
| En Azure, `bff` se queda sin internet justo después de que se instala Docker en `gw-azure` | Docker cambia la política de `FORWARD` en `iptables` a `DROP`. | Incluir las dos reglas `iptables -I DOCKER-USER -s 10.1.2.0/24 -j ACCEPT` en `cloud-init-gw-azure.yaml`. |
| En Azure, las VMs dicen `Stopped` en el portal pero los créditos siguen bajando | Se apagaron desde dentro del SO o sin liberar cómputo (`Stopped` vs `Stopped (deallocated)`). | Ejecutar `bash deploy/azure/apagar.sh` (`az vm deallocate`) y verificar que `--show-details` diga **`VM deallocated`**. |
| El archivo `envs-grupoNN-seccion.zip` da error de archivo dañado al abrirlo | Se creó con el `tar` de Git Bash (GNU tar), que genera un `.tar` aunque el nombre termine en `.zip`. | Crearlo con `/c/Windows/System32/tar.exe -a -c -f envs-grupoNN-seccion.zip ...`. |
