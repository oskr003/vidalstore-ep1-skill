# Escalamiento, Replicación, Diagnóstico y Consumer Lag en Apache Kafka (D13 / Lab A13)

Guía técnica y normativa que consolida el 100% de la clase magistral **D13 («Medir en vez de suponer: escalamiento, replicación y consumer lag»)** de la Semana 13 y la **Actividad de Laboratorio A13 (`LABA13.pdf`)**, aplicada tanto al caso de estudio (`Biblioteca`) como al proyecto oficial **`VidalStore`** para la Evaluación Parcial N°3 (EP3).

---

## 1. Mapa de Conceptos, Vocabulario Técnico y Hashing de Partición

### 1.1 Glosario de Términos en Inglés (Estándar de Consola y Herramientas)
| Término | Significado Técnico | Uso Práctico en Consola / Código |
| :--- | :--- | :--- |
| **`consumer lag`** | Mensajes ya publicados que el consumer group aún no confirma. | Columna `LAG` en `kafka-consumer-groups.sh --describe`. |
| **`throughput`** | Cantidad de eventos procesados por unidad de tiempo (`eventos/s`). | $\text{eventos} / \text{segundos}$ o $1000 / \text{ms\_por\_evento}$. |
| **`counter` y `gauge`** | Tipos de métrica: una que solo sube (`counter`) y otra que sube y baja (`gauge`). | Base conceptual para Prometheus y Grafana en Semana 14 (L11). |
| **`hot partition`** | Partición que concentra mucho más tráfico que las demás por una key muy repetida. | P1 en `biblioteca.lecturas` (76,4%); P0 en `vidalstore.actividad` (57,6%). |
| **`idle consumer`** | Consumidor vivo en el grupo que no recibe ninguna partición (`#PARTITIONS = 0`). | Ocurre siempre que $\text{consumidores} > \text{particiones\_suscritas}$. |
| **`replication factor`** | Copias de cada partición repartidas en brokers distintos. | `--replication-factor 3` en `kafka/topics.sh`. |
| **`ISR` (*in-sync replicas*)** | Conjunto de réplicas que están al día con el líder de la partición. | Columna `Isr` en `kafka-topics.sh --describe`. |
| **`acks`** | Confirmaciones que el productor exige antes de dar un envío por exitoso. | `acks: 'all'` (o `-1`) en `@platformatic/kafka`. |
| **`min.insync.replicas`** | Mínimo de réplicas en `ISR` requerido para aceptar una escritura con `acks=all`. | `--config min.insync.replicas=2` en `kafka/topics.sh`. |

### 1.2 Cómo Asigna Kafka la Partición: `murmur2` sobre los Bytes de la Key
Kafka **no** calcula el módulo directamente sobre el número entero de la key, sino que aplica el algoritmo de hash **`murmur2`** sobre los bytes del string de la key:

$$\text{partición} = (\text{murmur2}(\text{bytes}(\text{key})) \ \& \ \text{0x7fffffff}) \bmod \text{numParticiones}$$

> [!IMPORTANT]
> **Por qué la key `"18"` cae en `P1` y no en `P0` (D13 Slide 4)**:
> Aunque aritméticamente $18 \bmod 3 = 0$, en Kafka la key es el texto `"18"`. Al aplicar `murmur2("18") % 3`, el resultado es **`1`** (`P1`).
> - En **`biblioteca.lecturas`** (3 particiones, `2.984` eventos): el libro `18` (*Clean Code*) concentra por sí solo el **40,2%** de las lecturas (`1.200` eventos) y, sumado a otros libros cuyo hash también cae en `P1` (`10`, `2`, `14`...), deja a **`P1` con `2.279` eventos (76,4%)**, mientras `P0` tiene `492` (16,5%) y `P2` tiene `213` (7,1%).
> - En **`vidalstore.actividad`** (3 particiones, `3.039` eventos, key `juegoId`): el juego `292030` cae en **`P0`**, concentrando **`1.751` eventos (57,6%)** en `P0`, `520` en `P1` y `768` en `P2`.
> - En **`vidalstore.compras`** (3 particiones, `401` eventos, key `usuarioSub`): la carga queda pareja porque hay cientos de usuarios distintos (`P0: 147`, `P1: 141`, `P2: 113`).

---

## 2. Métricas Operativas: `Counter` vs `Gauge`

Antes de abrir paneles o leer consolas, toda métrica pertenece a uno de dos tipos fundamentales:

| Propiedad | `Counter` (Contador Acumulativo) | `Gauge` (Medidor Instantáneo) |
| :--- | :--- | :--- |
| **Comportamiento** | **Solo sube** (monotónico creciente); solo vuelve a cero si el proceso se reinicia. | **Sube y baja** libremente según el estado actual del sistema. |
| **Ejemplos en Kafka** | Eventos publicados en un topic (`LOG-END-OFFSET`), total de compras históricas, bytes recibidos. | **`Consumer lag`**, memoria libre del broker, cantidad de consumidores activos en un grupo. |
| **Pregunta que responde** | *¿A qué **ritmo (tasa)** está subiendo ahora mismo?* | *¿Cuánto vale **ahora** y hacia dónde va su **tendencia**?* |
| **Cálculo derivado** | $\text{Tasa} = \frac{\text{valor}(t_2) - \text{valor}(t_1)}{t_2 - t_1}$ (ej. `(1420 - 1120) / 60s = 5 ev/s`). | $\text{Pendiente} = \frac{\text{lag}(t_2) - \text{lag}(t_1)}{t_2 - t_1} = \text{entrada} - \text{procesamiento}$. |

> [!NOTE]
> **Detalle Técnico para Semana 14 (`kafka_exporter` y Prometheus)**:
> El exportador `kafka_exporter` publica el offset de una partición etiquetado internamente como `gauge` en formato Prometheus, pero **por su naturaleza matemática es un `counter`** (nunca retrocede salvo recreación del topic) y en Grafana se grafica su **tasa de cambio (`rate`)**, no su número crudo.

---

## 3. Consumer Lag: Cálculo, Lectura de `--describe` y Tendencia

### 3.1 Fórmula por Partición y Total del Grupo
El **consumer lag** es la distancia entre lo que el broker ya tiene escrito y lo que el consumer group ya confirmó:

$$\text{LAG}_{p} = \text{LOG-END-OFFSET}_{p} - \text{CURRENT-OFFSET}_{p}$$

```text
Partición 1:  ... [2270][2271][2272][2273][2274][2275][2276][2277][2278]
                               ^                                         ^
                        CURRENT-OFFSET = 2272                    LOG-END-OFFSET = 2279
                        (próximo a leer por el grupo)            (próximo a escribir por el broker)
                        |<------------------- LAG = 7 ------------------>|
```

- **`LOG-END-OFFSET` (*high watermark*)**: Es el **próximo offset que el broker escribirá** en esa partición (si hay `2.279` mensajes en `P1`, del `0` al `2278`, el `LOG-END-OFFSET` es `2279`).
- **`CURRENT-OFFSET`**: Es el **próximo offset que leerá el grupo**, es decir, el valor confirmado en el último commit manual (`offset_procesado + 1`).
- **Qué columnas se pueden sumar y cuál NO**:
  - **SÍ tiene sentido sumar `LOG-END-OFFSET`**: da el total de eventos escritos en el topic (`492 + 2279 + 213 = 2.984`).
  - **SÍ tiene sentido sumar `LAG`**: da el total de eventos pendientes de procesar por el grupo.
  - **NO tiene sentido sumar `CURRENT-OFFSET`**: es una posición de cursor dentro de cada partición independiente, no una cantidad global auditable sin compararla contra su respectivo `LOG-END-OFFSET`.

### 3.2 Lectura de `kafka-consumer-groups.sh --describe`
Comando oficial para medir el lag de un grupo en vivo:
```bash
docker compose exec broker-1 /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server broker-1:19092 \
  --describe --group vidalstore-panel
```

| Columna | Significado |
| :--- | :--- |
| `GROUP` | Nombre del consumer group (`vidalstore-panel`, `vidalstore-alertas`, `vidalstore-historial`). |
| `TOPIC` | Topic al que pertenece la fila (un grupo suscrito a 2 topics muestra 6 filas). |
| `PARTITION` | Número de partición (`0`, `1`, `2`). |
| `CURRENT-OFFSET` | Último offset confirmado por el grupo en `__consumer_offsets`. |
| `LOG-END-OFFSET` | Total de mensajes escritos en esa partición del broker. |
| `LAG` | `LOG-END-OFFSET - CURRENT-OFFSET`. Si es `0`, esa partición está al día. |
| `CONSUMER-ID` | Identificador único del cliente que tiene asignada esa partición (o `-` si no hay miembros activos). |
| `HOST` | IP interna del contenedor consumidor en la red Docker. |

### 3.3 La Regla de Oro del Diagnóstico: La Tendencia Importa Más que el Valor
Un número suelto de `lag` (por ejemplo, `lag = 5.000`) **no dice si hay un incidente**. Con una sola foto no se distingue un sistema que se está ahogando de uno que se está recuperando solo tras un pico puntual. **Siempre se requieren al menos dos mediciones separadas en el tiempo**:

$$\text{pendiente} = \frac{\text{lag}_{\text{final}} - \text{lag}_{\text{inicial}}}{\Delta t\text{ (segundos)}} = \text{tasa de entrada} - \text{tasa de procesamiento}$$

| Caso (En el segundo 40 el lag vale `5.000`) | Mediciones ($t=0\text{s} \to 40\text{s}$) | Pendiente ($\text{ev/s}$) | Tendencia | Diagnóstico y Acción Operativa |
| :--- | :--- | :---: | :---: | :--- |
| **Serie A** | `3000 -> 3500 -> 4000 -> 4500 -> 5000` | **`+50.0 ev/s`** | **`SUBE`** | **Emergencia**: entran 50 ev/s más de los que el grupo procesa. El atraso crece sin techo y jamás se vacía solo. Hay que intervenir. |
| **Serie B** | `7000 -> 6500 -> 6000 -> 5500 -> 5000` | **`-50.0 ev/s`** | **`BAJA`** | **Recuperación autónoma**: el grupo drena 50 ev/s más de los que entran. Aunque hoy tenga 5.000 pendientes, llegará a `0` solo en $5000 / 50 = 100\text{ s}$. **No hay que tocar nada**. |
| **Serie C** | `5000 -> 4990 -> 5010 -> 4995 -> 5005` | **`+0.1 ev/s`** ($\|\text{pend}\| \le 1$) | **`ESTABLE`** | **Atraso fijo constante**: el grupo procesa al mismo ritmo que entra, pero arrastra una bolsa antigua de 5.000 eventos sin drenarla. |

### 3.4 La Trampa del `Lag = 0` Permanente (D13 Slide 13)
> [!WARNING]
> **¿`Lag = 0` durante 10 minutos seguidos es siempre buena noticia?**
> **No necesariamente.** Hay dos explicaciones opuestas para `LAG = 0`:
> 1. **Grupo sano y al día**: `LOG-END-OFFSET` sigue creciendo y `CURRENT-OFFSET` avanza al mismo ritmo.
> 2. **Productor muerto o desconectado (incidente disfrazado de calma)**: El productor dejó de publicar hace 10 minutos; `LOG-END-OFFSET` está congelado en el mismo número y el consumidor ya leyó todo lo viejo.
> - **Verificación obligatoria**: Mirar siempre si `LOG-END-OFFSET` (o la tasa de mensajes entrantes al topic) sigue subiendo.

---

## 4. Throughput, Latencia, Espera en Partición y Percentiles (`p50` vs `p99`)

### 4.1 Tres Relojes que No se Deben Confundir
1. **Throughput ($\text{eventos/s}$)**: Cantidad de eventos que el consumidor (o el grupo) despacha por segundo:
   $$\text{throughput} = \frac{\text{eventos}}{\text{segundos}} = \frac{1000}{\text{ms por evento}}$$
2. **Latencia de procesamiento ($\text{ms}$)**: Tiempo que tarda **un solo evento** desde que el consumidor lo toma hasta que termina de escribirlo en Postgres y hacer commit.
3. **Tiempo de espera en la partición ($\text{ms}$)**: Tiempo que el evento pasa haciendo fila en la partición antes de que un consumidor lo tome.

$$\text{Tiempo total que percibe el negocio} = \text{Espera en la partición} + \text{Latencia de procesamiento}$$

> [!IMPORTANT]
> **Escalar consumidores multiplica el throughput pero NO baja la latencia individual (D13 Slide 16)**:
> Si un consumidor tarda `10 ms` en insertar en Postgres ($\text{throughput} = 100\text{ ev/s}$), al poner **3 consumidores** en paralelo sobre 3 particiones, cada uno sigue tardando **`10 ms`** por evento (la latencia no bajó a `3,3 ms`), pero el grupo ahora despacha **`300 ev/s`** (el triple de throughput). Lo que sí cae drásticamente para el usuario final es el **tiempo de espera en la partición**, porque la fila drena 3 veces más rápido.

### 4.2 Por qué el Promedio Miente y se Usan Percentiles (`p50` y `p99`)
Supongamos 10 eventos cuyas latencias en milisegundos son:
`[2, 2, 2, 2, 2, 3, 3, 3, 4, 380]` (el décimo evento coincidió con un checkpoint de Postgres o pausa de GC).
- **Promedio aritmético**: $403 / 10 = \mathbf{40,3\text{ ms}}$. **No describe a nadie**: es 13 veces mayor que los 9 casos normales (`2–4 ms`) y 9 veces menor que el caso lento (`380 ms`).
- **Percentil 50 (`p50` / mediana)**: **`2 ms`**. El 50% de los eventos tarda $\le 2\text{ ms}$ (el caso típico real).
- **Percentil 99 (`p99`)**: **`380 ms`**. El 99% tarda $\le 380\text{ ms}$; expone la cola lenta (*tail latency*) sin disimularla.

### 4.3 Cómo Medir en Node.js: `performance.now()` y Ejecución Secuencial
```js
import { performance } from 'node:perf_hooks';

function percentil(lista, p) {
  const orden = [...lista].sort((a, b) => a - b);
  const pos = Math.ceil((p / 100) * orden.length) - 1;
  return orden[Math.max(0, pos)];
}

const tiempos = [];
const inicioTotal = performance.now();

for (const linea of lineas) {
  const t0 = performance.now();
  await procesar(linea);           // Secuencial: igual que for await (const m of flujo)
  tiempos.push(performance.now() - t0);
}
const totalMs = performance.now() - inicioTotal;
const throughput = (tiempos.length / totalMs) * 1000;
```
- **Por qué `performance.now()` y NO `Date.now()`**:
  1. `Date.now()` entrega milisegundos enteros; una operación en memoria (`JSON.parse` + validación $\approx 0,0012\text{ ms}$) mide `0 ms`. `performance.now()` tiene **resolución de microsegundos** (fracciones de ms).
  2. `performance.now()` usa un **reloj monotónico**: nunca retrocede ni salta si el demonio NTP ajusta la hora del sistema operativo a mitad de la medición.
- **Por qué `for...of` con `await` y JAMÁS `Promise.all`**:
  Un consumidor de `@platformatic/kafka` procesa su flujo con `for await (const m of flujo)` **de uno en uno** para conservar el orden de la partición y hacer commit después de escribir. Si se midiera con `Promise.all`, las 200 esperas de `setTimeout(2)` correrían en paralelo en ~2 ms totales, midiendo el temporizador de Node y no el throughput real del consumidor.

### 4.4 Cálculo de Consumidores Necesarios a partir de la Latencia
1. De la latencia media (o `p50`/`p99`) en ms se obtiene el throughput de **1 consumidor**:
   $$\text{throughput}_{1} = \frac{1000}{\text{latencia (ms)}}$$
2. Para absorber una tasa de llegada $L\text{ (ev/s)}$ sin acumular lag:
   $$\text{consumidores necesarios} = \left\lceil \frac{L}{\text{throughput}_{1}} \right\rceil \quad \text{con tope estricto en } \text{numParticiones}$$
- **Ejemplo oficial (Pregunta 5 de Lab A13)**: Si la escritura en Postgres tarda `40 ms` por evento $\Rightarrow \text{throughput}_{1} = 1000 / 40 = \mathbf{25\text{ ev/s}}$. Si llegan `50 ev/s`, se necesitan $\lceil 50 / 25 \rceil = \mathbf{2\text{ consumidores}}$ (siempre que el topic tenga al menos 2 particiones y la carga esté bien repartida).

---

## 5. Escalamiento, Reparto de Particiones, Consumidores Ociosos y Partición Caliente

### 5.1 La Partición como Unidad Mínima de Paralelismo
En Kafka, **una partición jamás se divide entre dos consumidores del mismo grupo** (si dos instancias leyeran la misma partición a la vez, se perdería el orden por key y pisarían sus commits de offset). Por lo tanto:

$$\text{Consumidores trabajando} = \min(\text{consumidores en el grupo}, \text{particiones suscritas})$$
$$\text{Consumidores ociosos (idle)} = \max(0, \text{consumidores en el grupo} - \text{particiones suscritas})$$

| Particiones del Topic | Consumidores en el Grupo | Reparto Round-Robin (`p % n` en `@platformatic/kafka`) | Consumidores Trabajando | Consumidores Ociosos (`#PARTITIONS = 0`) |
| :---: | :---: | :--- | :---: | :---: |
| **3** | **1** | `c1: [P0, P1, P2]` | 1 | **0** |
| **3** | **2** | `c1: [P0, P2]`, `c2: [P1]` | 2 | **0** |
| **3** | **3** | `c1: [P0]`, `c2: [P1]`, `c3: [P2]` *(óptimo: 1 a 1)* | 3 | **0** |
| **3** | **4** | `c1: [P0]`, `c2: [P1]`, `c3: [P2]`, `c4: []` | 3 | **1 (`c4` ocioso)** |

> [!TIP]
> **Reparto Round-Robin vs Range**:
> `@platformatic/kafka` usa por omisión el asignador **round-robin** (vuelta circular: la partición $p$ va al consumidor $p \bmod n$). Con 6 particiones y 3 consumidores asigna `c1=[0,3], c2=[1,4], c3=[2,5]`. El cliente oficial de Java usa **range** por omisión (`c1=[0,1], c2=[2,3], c3=[4,5]`).

### 5.2 Por qué en el Paso 6 de L10 (4 instancias de `eventos`) `panel` no tiene ociosos y `alertas`/`historial` sí
Al levantar **4 contenedores** del servicio `eventos` (`eventos`, `eventos-2`, `eventos-3`, `eventos-4`):
- **`vidalstore-alertas`** (lee solo `vidalstore.actividad` = **3 particiones**) y **`vidalstore-historial`** (lee solo `vidalstore.compras` = **3 particiones**): tienen 3 particiones para 4 miembros $\Rightarrow$ `kafka-consumer-groups.sh --describe --members` muestra `#PARTITIONS`: **`1, 1, 1 y 0`** (**1 miembro ocioso**).
- **`vidalstore-panel`** (lee **ambos topics**: `vidalstore.actividad` [3] + `vidalstore.compras` [3] = **6 particiones en total**): tiene 6 particiones para 4 miembros $\Rightarrow$ `--describe --members` muestra `#PARTITIONS`: **`2, 2, 1 y 1`** (**0 miembros ociosos**; recién habría un ocioso con una 7.ª instancia).

### 5.3 Por qué Escalar Consumidores NO Resuelve una Partición Caliente (*Hot Partition*)
Supongamos un topic de 6 particiones donde cada consumidor aguanta **`40 ev/s`** y entran `120 ev/s` en total, pero la partición **`P1` está caliente y recibe `70 ev/s`** (y las otras cinco reciben `10 ev/s` cada una):
- Con **3 consumidores**: `c2` recibe `P1 + P4` = $70 + 10 = \mathbf{80\text{ ev/s}} > 40 \Rightarrow$ **`SE ATRASA`** (`+40 ev/s` de lag).
- Con **6 consumidores**: `c2` queda dedicado exclusivamente a `P1`, pero `P1` sola trae **`70 ev/s` $> 40$** $\Rightarrow$ **`SE SIGUE ATRASANDO`** (`+30 ev/s` de lag).
- Con **9 consumidores**: `c2` sigue recibiendo **`70 ev/s`** en `P1` (`SE ATRASA`) y además `c7`, `c8` y `c9` quedan **ociosos (`0 ev/s`)**.
- **Conclusión de Defensa**: Ninguna cantidad de consumidores adicionales divide una partición caliente. Solo quedan dos salidas: **(1) optimizar el consumidor** para que supere los `70 ev/s` (p. ej., cachear consultas o insertar por lotes), o **(2) cambiar la key de particionamiento** si el negocio no exige orden estricto por esa clave (si el negocio sí exige orden por `juegoId` o `libroId`, se mantiene la key y se documenta el desbalance en `docs/topics.md`).

---

## 6. Diagnóstico Sistemático de Lag Creciente: 5 Causas, 4 Palancas y 6 Pasos

### 6.1 Las 5 Causas de Lag Creciente y su Huella en `--describe`
| # | Causa Raíz | Huella Exacta en `kafka-consumer-groups.sh --describe` | Palanca Correcta |
| :-: | :--- | :--- | :--- |
| **1** | **Consumidor lento** (BD sin índice, llamada HTTP síncrona, sin caché) | `LAG` **parejo y subiendo en todas las particiones**; todas tienen `CONSUMER-ID` activo. | **Optimizar el consumidor** (caché en memoria, índice SQL, batch). |
| **2** | **Partición caliente** (*hot partition* por key muy repetida) | Casi todo el `LAG` concentrado en **una sola partición**, cuyo `LOG-END-OFFSET` es mucho mayor que el de las demás. | **Acelerar el consumidor** o revisar la elección de `key` (si el orden lo permite). |
| **3** | **Pocos consumidores** para la cantidad de particiones | `LAG` subiendo en las particiones que **comparten el mismo `CONSUMER-ID`** (un consumidor leyendo 2 o 3 particiones). | **Agregar consumidores** al grupo hasta igualar el número de particiones. |
| **4** | **Consumidor caído** sin cierre limpio (`kill -9` / caída de VM) | El `LAG` sube en su partición mientras el broker aún muestra el **`CONSUMER-ID` muerto** hasta que vence el timeout de sesión (`60 s` en `@platformatic/kafka`, `45 s` en Java); luego rebalancea. *(El guion `-` solo aparece si caen todos los miembros: `Consumer group has no active members`)*. | Levantar la instancia caída y asegurar `enableShutdownHooks()` + `consumidor.close()` para rebalancear en `~1,1 s`. |
| **5** | **Rebalanceo continuo** (*rebalance storm* por despliegues o procesamientos lentos) | Todas las particiones se detienen a la vez; consola muestra `Warning: Consumer group is rebalancing`. | Evitar reinicios en bucle, cerrar limpio con `close()` y no bloquear el event loop. |

### 6.2 Las 4 Palancas de Escalamiento (Ordenadas de la Más Barata a la Más Cara)
1. **Palanca 1 — Hacer más rápido al consumidor (Gratis, primera opción siempre)**:
   - Bajar la latencia por evento de `12,5 ms` a `1,1 ms` (p. ej. cacheando el catálogo en un `Map` en memoria en vez de consultar por red en cada evento) multiplica por **11x** el throughput sin tocar contenedores ni particiones.
2. **Palanca 2 — Agregar consumidores al grupo (Barato, reversible)**:
   - Solo sirve si hay más particiones que consumidores activos ($\text{consumidores} < \text{particiones}$). Si ya son iguales, el nuevo queda ocioso.
3. **Palanca 3 — Agregar particiones al topic (Caro, irreversible)**:
   - **No se pueden reducir particiones** en un topic existente.
   - **Rompe el enrutamiento por key**: al cambiar `numPartitions` de `3` a `6`, `murmur2(key) % 6` manda los eventos nuevos de una misma key a otra partición mientras los antiguos quedan en la partición original (los mensajes ya escritos no se mueven), **perdiendo la garantía de orden histórico** para esa key.
4. **Palanca 4 — Agregar brokers al clúster (El más caro)**:
   - Solo sirve cuando el cuello de botella es el disco, la red o la CPU de los brokers. Además, **un broker nuevo no recibe particiones existentes automáticamente**; requiere ejecutar una reasignación manual de particiones (`kafka-reassign-partitions.sh`).

### 6.3 El Orden Estricto de Diagnóstico en 6 Pasos (D13 Slide 35)
Ante cualquier alerta de lag, aplicar siempre esta secuencia en orden:
1. **Paso 1 — Mirar la tendencia del lag** (2 mediciones separadas por 30–60 s): ¿Sube, baja o está estable? Si baja, se drena solo; no tocar nada.
2. **Paso 2 — Mirar el lag por partición** (`--describe`): ¿Suben todas parejas o solo una partición caliente? *(Pasos 2 y 3 salen del mismo comando `--describe`)*.
3. **Paso 3 — Mirar `CONSUMER-ID` en cada partición**: ¿Hay un mismo `CONSUMER-ID` atendiendo varias particiones o un miembro caído esperando timeout?
4. **Paso 4 — Medir el throughput de un consumidor individual**: ¿Cuántos ms tarda en escribir en Postgres (`p50` y `p99`)? Si es lento, optimizar primero el código/SQL.
5. **Paso 5 — Agregar consumidores al grupo**: Solo si el consumidor individual ya es rápido y actualmente atiende más de 1 partición.
6. **Paso 6 — Agregar particiones al topic (último recurso)**: Solo cuando ya hay 1 consumidor rápido por cada partición y la tasa de entrada sigue superando la capacidad conjunta.

---

## 7. Replicación, `ISR`, `acks=all` y `min.insync.replicas=2`

### 7.1 Anatomía de una Partición Replicada en el Clúster KRaft
En el `compose.yml` de la EP3, los 3 controllers tienen `KAFKA_NODE_ID` `1`, `2` y `3`, y los **3 brokers tienen `KAFKA_NODE_ID` `4` (`broker-1`), `5` (`broker-2`) y `6` (`broker-3`)**.

```bash
docker compose exec broker-1 /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server broker-1:19092 --describe --topic vidalstore.compras
```
Salida típica con todos los brokers sanos:
```text
Topic: vidalstore.compras  PartitionCount: 3  ReplicationFactor: 3  Configs: min.insync.replicas=2,retention.ms=604800000
  Topic: vidalstore.compras  Partition: 0  Leader: 4  Replicas: 4,5,6  Isr: 4,5,6
  Topic: vidalstore.compras  Partition: 1  Leader: 5  Replicas: 5,6,4  Isr: 5,6,4
  Topic: vidalstore.compras  Partition: 2  Leader: 6  Replicas: 6,4,5  Isr: 6,4,5
```
- **`Leader`**: El único broker que recibe las escrituras de los productores y atiende las lecturas de los consumidores para esa partición.
- **`Replicas`**: Los brokers que guardan copia de esa partición. El **primer ID de la lista** es el **líder preferido (*preferred leader*)** asignado al crear el topic (`4` en P0, `5` en P1, `6` en P2).
- **`Isr` (*In-Sync Replicas*)**: El subconjunto de `Replicas` que están vivas y al día con el líder. Las réplicas seguidoras (*followers*) hacen **fetch continuo** desde el líder; si un broker se apaga o se atrasa más de `replica.lag.time.max.ms` (`30.000 ms` = 30 s por omisión), el líder lo saca del `Isr`.

### 7.2 El Contrato de Durabilidad: `acks` (Productor) + `min.insync.replicas` (Topic/Broker)
| Configuración del Productor | Quién confirma antes de responder éxito | Riesgo ante Caída del Líder | Caso de Uso |
| :--- | :--- | :--- | :--- |
| **`acks: 0`** | Nadie (dispara al socket TCP y sigue). | **Pérdida total** si el broker cae o reinicia. | Métricas descartables de bajo valor. |
| **`acks: 1`** | **Solo el broker líder** tras escribir en su log local (sin esperar a las seguidoras). | Si el líder cae milisegundos antes de que las seguidoras hagan fetch, **el mensaje confirmado se pierde**. | Telemetría rápida donde perder algún evento aislado es tolerable. |
| **`acks: 'all'` (`-1`)** | **El líder + todas las réplicas actuales del `ISR`**, exigiendo que $\|\text{ISR}\| \ge \text{min.insync.replicas}$. | **Cero pérdida de datos confirmados** ante la caída de 1 broker. | **Obligatorio en EP3** para todos los topics (`compras`, `actividad`, `catalogo`). |

> [!CAUTION]
> **Por qué `acks=all` sin `min.insync.replicas=2` es una trampa mortal (D13 Slide 40)**:
> `acks=all` espera a todas las réplicas que estén **actualmente** en el `ISR`. Si `min.insync.replicas` se deja en su valor por defecto (`1`) y se caen 2 brokers, el `ISR` queda con **1 sola réplica (el líder)**. Un productor con `acks=all` seguiría escribiendo feliz sobre esa única copia sobreviviente: **`acks=all` se degradó en silencio a `acks=1`**. Con `min.insync.replicas=2`, el broker tiene prohibido aceptar la escritura si quedan menos de 2 réplicas sincronizadas.

### 7.3 Matriz Completa de Caídas de Brokers (`replication.factor=3`, `min.insync.replicas=2`, `acks=all`)
| Brokers Caídos | Brokers Vivos | Tamaño del `ISR` | ¿Se cumple $\|\text{ISR}\| \ge 2$? | Resultado al Publicar (`acks=all`) | Qué ocurre internamente y en la Nube (AWS) |
| :---: | :---: | :---: | :---: | :--- | :--- |
| **0 caídos** | **3** (`4, 5, 6`) | **3** (`4,5,6`) | **Sí ($3 \ge 2$)** | **Acepta escritura** (confirmada en 3 discos). | Operación nominal óptima. |
| **1 caído** (`broker-3`, ID `6`) | **2** (`4, 5`) | **2** (`4,5`) | **Sí ($2 \ge 2$)** | **Acepta escritura sin error** (confirmada en 2 discos). | El controller elige nuevo líder para P2 (`Leader: 4`) en milisegundos. Las 401 compras de VidalStore entran íntegras sin perder ni un evento. |
| **2 caídos** (`broker-3` y `broker-2`, IDs `6, 5`) | **1** (`4`) | **1** (`4`) | **No ($1 < 2$)** | **Rechaza escritura** con **`NOT_ENOUGH_REPLICAS`**: *"Messages are rejected since there are fewer in-sync replicas than required"*. | **1)** Protege contra escribir en 1 sola copia.<br>**2)** En Kafka 4.3, mientras $\|\text{ISR}\| < \text{min.insync.replicas}$, **tampoco entrega eventos nuevos a los consumidores** (ni aunque se publicaran con `acks=1`).<br>**3)** En AWS (donde cada VM `mq-1..3` aloja `1 controller + 1 broker`), caer 2 VMs **rompe además el quórum Raft de controllers (1 de 3 vivos)** y `kafka-topics.sh --describe` deja de responder. |
| **3 caídos** | **0** | **0** (vacío) | **No ($0 < 2$)** | **Falla de conexión**: `Connection to broker-1:19092 failed` (`initProducerId failed 11 times`). | Al reencender, con *unclean leader election* desactivado por defecto (`unclean.leader.election.enable=false`), **no hay líder hasta que vuelva uno de los últimos miembros del `ISR`** (`broker-1` o `broker-2`). Si se enciende solo `broker-3` (que había caído primero), la partición sigue con `Leader: none` para no perder los mensajes que `4` y `5` recibieron sin `6`. |

---

## 8. Actividad de Laboratorio A13 (`LABA13.pdf`): Los 3 Programas y Cajas de Pulso

En el Laboratorio A13 se construyen 3 scripts en Node.js puro (sin levantar Docker) dentro de la carpeta `a13/` para ejercitar los cálculos y el diagnóstico antes de la defensa.

### 8.1 Ejercicio 1: Tendencia del Consumer Lag (`a13/lag.mjs`)
Calcula el cambio neto, la pendiente en $\text{eventos/s}$ y clasifica la tendencia (`SUBE` si $> 1$, `BAJA` si $< -1$, `ESTABLE` si $\|\text{pendiente}\| \le 1$):

```javascript
// a13/lag.mjs
const intervaloSegundos = 10;

const series = [
  { nombre: 'Serie A', mediciones: [3000, 3500, 4000, 4500, 5000] },
  { nombre: 'Serie B', mediciones: [7000, 6500, 6000, 5500, 5000] },
  { nombre: 'Serie C', mediciones: [5000, 4990, 5010, 4995, 5005] },
];

function analizar(serie) {
  const m = serie.mediciones;
  const inicial = m[0];
  const final = m[m.length - 1];
  const segundos = (m.length - 1) * intervaloSegundos;
  const cambio = final - inicial;
  const pendiente = cambio / segundos; // eventos por segundo

  let tendencia = 'ESTABLE';
  if (pendiente > 1) tendencia = 'SUBE';
  if (pendiente < -1) tendencia = 'BAJA';

  const signo = pendiente >= 0 ? '+' : '';
  console.log(
    `${serie.nombre.padEnd(10)} lag final: ${String(final).padStart(5)}   ` +
      `pendiente: ${(signo + pendiente.toFixed(1) + ' ev/s').padStart(11)}   ` +
      `tendencia: ${tendencia}`,
  );
}

for (const s of series) analizar(s);
```

**Salida oficial exacta (Caja 1 de Pulso A13):**
```text
Serie A    lag final:  5000   pendiente:  +50.0 ev/s   tendencia: SUBE
Serie B    lag final:  5000   pendiente:  -50.0 ev/s   tendencia: BAJA
Serie C    lag final:  5005   pendiente:   +0.1 ev/s   tendencia: ESTABLE
```

### 8.2 Ejercicio 2: Throughput y Latencia `p50`/`p99` (`a13/throughput.mjs`)
Compara el procesamiento de 200 eventos en memoria (**Versión A**) contra el mismo procesamiento con una escritura simulada de `2 ms` en base de datos (**Versión B**):

```javascript
// a13/throughput.mjs
import { performance } from 'node:perf_hooks';

const totalEventos = 200;
const lineas = Array.from({ length: totalEventos }, (_, i) =>
  JSON.stringify({
    eventoId: `00000000-0000-4000-8000-${String(i).padStart(12, '0')}`,
    tipo: 'lectura.iniciada',
    version: 1,
    emitidoEn: '2026-06-08T18:00:00.000Z',
    usuarioSub: `usr-${i % 20}`,
    libroId: String((i % 15) + 1),
    datos: { dispositivo: 'web' },
  }),
);

function dormir(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function procesarEnMemoria(linea) {
  const e = JSON.parse(linea);
  if (!e.eventoId || !e.usuarioSub) throw new Error('invalido');
}

async function procesarConBaseDeDatos(linea) {
  const e = JSON.parse(linea);
  if (!e.eventoId || !e.usuarioSub) throw new Error('invalido');
  await dormir(2); // simula un INSERT que tarda 2 ms
}

function percentil(ordenados, p) {
  const indice = Math.ceil((p / 100) * ordenados.length) - 1;
  return ordenados[Math.max(0, indice)];
}

async function medir(nombre, fn) {
  const latencias = [];
  const inicioTotal = performance.now();

  for (const linea of lineas) {
    const t0 = performance.now();
    await fn(linea);
    latencias.push(performance.now() - t0);
  }

  const totalMs = performance.now() - inicioTotal;
  const ordenados = [...latencias].sort((a, b) => a - b);
  const p50 = percentil(ordenados, 50);
  const p99 = percentil(ordenados, 99);
  const throughput = (totalEventos / totalMs) * 1000;

  console.log(
    `${nombre.padEnd(28)} total: ${totalMs.toFixed(1).padStart(7)} ms   ` +
      `p50: ${p50.toFixed(2).padStart(6)} ms   ` +
      `p99: ${p99.toFixed(2).padStart(6)} ms   ` +
      `throughput: ${throughput.toFixed(0).padStart(8)} ev/s`,
  );
}

await medir('Version A (solo memoria)', procesarEnMemoria);
await medir('Version B (con BD de 2 ms)', procesarConBaseDeDatos);
```

**Salida típica (Caja 2 de Pulso A13):**
```text
Version A (solo memoria)     total:     0.6 ms   p50:   0.00 ms   p99:   0.02 ms   throughput:   348120 ev/s
Version B (con BD de 2 ms)   total:   458.4 ms   p50:   2.26 ms   p99:   2.89 ms   throughput:      436 ev/s
```

### 8.3 Ejercicio 3: Simulación de Reparto de Particiones y Partición Caliente (`a13/reparto.mjs`)
Simula el asignador round-robin (`p % numConsumidores`) para 6 particiones con 3, 6 y 9 consumidores (capacidad individual = `40 ev/s`) bajo carga pareja (`[20, 20, 20, 20, 20, 20]`) y con la partición 1 caliente (`[10, 70, 10, 10, 10, 10]`):

```javascript
// a13/reparto.mjs
const capacidadConsumidor = 40; // eventos/s que aguanta un consumidor

function repartir(tasasPorParticion, numConsumidores) {
  const asignacion = Array.from({ length: numConsumidores }, (_, i) => ({
    consumidor: `c${i + 1}`,
    particiones: [],
    carga: 0,
  }));

  tasasPorParticion.forEach((tasa, p) => {
    const destino = asignacion[p % numConsumidores];
    destino.particiones.push(`P${p}`);
    destino.carga += tasa;
  });

  return asignacion;
}

function mostrarEscenario(titulo, tasas) {
  console.log(`\n=== ${titulo} (tasas por particion: ${tasas.join(', ')} ev/s) ===`);
  for (const n of [3, 6, 9]) {
    const res = repartir(tasas, n);
    const ociosos = res.filter((r) => r.particiones.length === 0).length;
    const atrasados = res.filter((r) => r.carga > capacidadConsumidor);
    const detalle = res
      .map((r) => {
        const lista = r.particiones.length ? r.particiones.join('+') : 'ocioso';
        const marca = r.carga > capacidadConsumidor ? ' [SE ATRASA]' : '';
        return `${r.consumidor}(${lista}=${r.carga}${marca})`;
      })
      .join('  ');
    console.log(
      `  ${n} cons -> ociosos: ${ociosos}, atrasados: ${atrasados.length} | ${detalle}`,
    );
  }
}

mostrarEscenario('Escenario 1: carga pareja', [20, 20, 20, 20, 20, 20]);
mostrarEscenario('Escenario 2: P1 caliente', [10, 70, 10, 10, 10, 10]);
```

**Salida oficial exacta (Caja 3 de Pulso A13):**
```text
=== Escenario 1: carga pareja (tasas por particion: 20, 20, 20, 20, 20, 20 ev/s) ===
  3 cons -> ociosos: 0, atrasados: 0 | c1(P0+P3=40)  c2(P1+P4=40)  c3(P2+P5=40)
  6 cons -> ociosos: 0, atrasados: 0 | c1(P0=20)  c2(P1=20)  c3(P2=20)  c4(P3=20)  c5(P4=20)  c6(P5=20)
  9 cons -> ociosos: 3, atrasados: 0 | c1(P0=20)  c2(P1=20)  c3(P2=20)  c4(P3=20)  c5(P4=20)  c6(P5=20)  c7(ocioso=0)  c8(ocioso=0)  c9(ocioso=0)

=== Escenario 2: P1 caliente (tasas por particion: 10, 70, 10, 10, 10, 10 ev/s) ===
  3 cons -> ociosos: 0, atrasados: 1 | c1(P0+P3=20)  c2(P1+P4=80 [SE ATRASA])  c3(P2+P5=20)
  6 cons -> ociosos: 0, atrasados: 1 | c1(P0=10)  c2(P1=70 [SE ATRASA])  c3(P2=10)  c4(P3=10)  c5(P4=10)  c6(P5=10)
  9 cons -> ociosos: 3, atrasados: 1 | c1(P0=10)  c2(P1=70 [SE ATRASA])  c3(P2=10)  c4(P3=10)  c5(P4=10)  c6(P5=10)  c7(ocioso=0)  c8(ocioso=0)  c9(ocioso=0)
```

### 8.4 Respuestas Modelo para las Preguntas 4, 5, 6 y 7 de Pulso A13
- **Pregunta 4 (Tendencia del lag — Serie A vs Serie B en `5.000`)**:
  > Aunque en el segundo 40 la Serie A y la Serie B muestran exactamente el mismo lag de `5000`, en la **Serie A** hay que intervenir porque su pendiente es **`+50.0 ev/s` (`SUBE`)**: están entrando 50 eventos por segundo más de los que el grupo logra procesar y el atraso crecerá indefinidamente. En cambio, la **Serie B** tiene pendiente **`-50.0 ev/s` (`BAJA`)**: el grupo ya procesa más rápido de lo que entra tras un pico pasado y vaciará los 5.000 pendientes por sí solo en $5000 / 50 = 100\text{ segundos}$.
- **Pregunta 5 (Throughput y latencia — `40 ms` en Postgres y llegada de `50 ev/s`)**:
  > Si cada escritura en Postgres tarda `40 ms`, un solo consumidor alcanza un throughput máximo de $1000 / 40 = \mathbf{25\text{ eventos/s}}$. Para sostener una llegada de `50 eventos/s` sin que el lag suba, hacen falta como mínimo $\lceil 50 / 25 \rceil = \mathbf{2\text{ consumidores}}$ en el grupo (asumiendo que el topic tiene al menos 2 particiones y la carga está repartida de forma pareja).
- **Pregunta 6 (Ociosos y partición caliente en `reparto.mjs`)**:
  > Al pasar de 6 a 9 consumidores sobre un topic de 6 particiones, los consumidores `c7`, `c8` y `c9` quedan **ociosos (`#PARTITIONS = 0`)** porque en Kafka una partición es la unidad mínima de paralelismo y no puede compartirse entre dos consumidores del mismo grupo. En el Escenario 2 (`P1` caliente con `70 ev/s`), subir a 6 o 9 consumidores no quita la marca `[SE ATRASA]` de `c2` porque `c2` ya lee únicamente `P1`, y una sola partición jamás se divide; para resolverlo hay que **optimizar el consumidor** para que supere los `70 ev/s` o **cambiar la key de particionamiento**.
- **Pregunta 7 (Replicación y `min.insync.replicas` con 3 brokers, `replication.factor=3`, `min.insync.replicas=2` y `acks=all`)**:
  > - **Con 1 broker caído (`broker-3`)**: Quedan 2 réplicas vivas en el `ISR` (`2 >= 2`). El productor **sigue publicando sin error** y cada mensaje queda confirmado en los 2 brokers sobrevivientes.
  > - **Con 2 brokers caídos (`broker-2` y `broker-3`)**: Queda solo 1 réplica en el `ISR` (`1 < 2`). El broker líder **rechaza la escritura** lanzando **`NOT_ENOUGH_REPLICAS`**, evitando confirmar un mensaje con `acks=all` sobre una única copia sin respaldo.
