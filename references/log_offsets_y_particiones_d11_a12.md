# El Log Inmutable, Offsets y Particiones en Kafka (D11 / Lab A12)

Guía técnica y conceptual sobre los fundamentos del commit log distribuido, la estructura interna de almacenamiento en disco, la semántica de offsets y las estrategias de particionado, integrando la clase magistral D11 y el laboratorio de actividad A12.

---

## 1. RabbitMQ vs Apache Kafka: Cambio de Paradigma Arquitectónico

| Dimensión | RabbitMQ (Cola de Trabajo) | Apache Kafka (Commit Log / Stream) |
| :--- | :--- | :--- |
| **Concepto Central** | Mensajes transitorios que se entregan y se destruyen. | Registro de hechos inmutables anexados en orden (*append-only*). |
| **Inteligencia del Broker** | **Smart broker, dumb consumer**: El broker rastrea qué consumidor tiene cada mensaje, maneja reintentos y borra al recibir `ack`. | **Dumb broker, smart consumer**: El broker solo guarda bytes en disco secuencial; cada consumidor mantiene su propio cursor (**offset**). |
| **Lectura de Mensajes** | `cola.shift()`: Leer un mensaje lo extrae y lo borra para los demás. | `leerDesde(offset)`: Leer es una copia sin borrado; múltiples grupos leen a diferente velocidad el mismo dato. |
| **Reprocesamiento** | Imposible volver a leer un mensaje ya confirmado (salvo que se haya desviado a DLQ). | Trivial: basta con cambiar el cursor del consumidor a un offset anterior (`offset: 0`). |
| **Enrutamiento** | Dinámico, complejo y flexible (Exchanges `direct`, `topic`, `headers`, bindings con comodines `#`, `*`). | Estricto: el productor envía directamente a un topic particionado; no hay exchanges intermedios. |
| **Casos de Uso Ideales** | Órdenes de trabajo, comandos síncronos asíncronos (`correo.enviar`), flujos transaccionales heterogéneos. | Registro de eventos históricos, auditoría inmutable, analítica, telemetría y reconstrucción de estado. |

---

## 2. Anatomía Interna de un Log en Disco

Kafka no almacena los datos en memoria ni en una base de datos relacional; los escribe directamente en el sistema de archivos del sistema operativo bajo una estructura de **segmentos**:

```
/var/lib/kafka/data/vidalstore.compras-0/
  ├── 00000000000000000000.log        <- Datos binarios de eventos
  ├── 00000000000000000000.index      <- Mapeo: Offset -> Posición física en bytes
  ├── 00000000000000000000.timeindex  <- Mapeo: Timestamp -> Offset
  ├── 00000000000000014520.log        <- Nuevo segmento activo (cuando el previo llega a 1 GiB)
  ├── 00000000000000014520.index
  └── leader-epoch-checkpoint
```

### Factores Clave de Alto Rendimiento:
1. **Escritura Secuencial en Disco (Sequential Append)**:
   - Escribir siempre al final del archivo activo aprovecha el ancho de banda máximo del almacenamiento (HDD o SSD), alcanzando cientos de megabytes por segundo sin búsquedas aleatorias (*random seeks*).
2. **Page Cache del Sistema Operativo**:
   - Kafka no cachea mensajes en el espacio de usuario de la JVM (lo que generaría sobrecarga de *Garbage Collection*). Deja que el kernel de Linux use la memoria RAM libre como caché de páginas de disco.
3. **Cero-Copia (`sendfile` syscall)**:
   - Al transferir datos desde el log hacia el socket de red del consumidor, el kernel transfiere los bytes directamente desde el Page Cache al búfer de la interfaz de red, sin pasar por la memoria de la aplicación Node.js/Java.

---

## 3. Retención de Datos: Tiempo vs Tamaño

A diferencia de RabbitMQ, donde los mensajes se borran tras el `ack`, en Kafka los mensajes expiran según políticas de retención globales o por topic:

- **`retention.ms`**: Tiempo máximo que un evento se conserva (ej. 7 días = `604800000` ms).
- **`retention.bytes`**: Tamaño máximo total permitido para la partición.

> [!WARNING]
> **La retención borra segmentos completos, NUNCA eventos individuales**:
> Kafka descarta un archivo de segmento `.log` únicamente cuando **el registro más nuevo de ese segmento** supera el tiempo de retención. Por ello, una partición puede almacenar temporalmente eventos más antiguos que el límite hasta que todo su segmento expire.

### Comportamiento de `auto.offset.reset`:
Cuando un nuevo consumidor o grupo arranca por primera vez (o su offset confirmado fue purgado por la retención):
- **`earliest`**: Comienza a leer desde el offset más antiguo disponible en el log (*log start offset*).
- **`latest`**: Ignora todo el pasado y espera únicamente eventos nuevos emitidos a partir de su conexión.

---

## 4. Particiones y Claves de Enrutamiento (`Record Key`)

Un topic se divide en $N$ particiones ($N \ge 1$). Cada partición es un log independiente en disco.

```
Topic: vidalstore.compras (3 particiones)

Partición 0: [0] [1] [2] [3] ... (Eventos con hash % 3 == 0) -> Leído por Consumidor A
Partición 1: [0] [1] [2] ...     (Eventos con hash % 3 == 1) -> Leído por Consumidor B
Partición 2: [0] [1] [2] [3] ... (Eventos con hash % 3 == 2) -> Leído por Consumidor C
```

### Reglas Innegociables de Orden:
1. **Orden Total**: Solo existe **dentro de una misma partición**. El offset garantiza orden estricto para esa partición.
2. **Orden Relativo**: Entre distintas particiones **no hay garantía de orden cronológico**.
3. **Cálculo de la Partición**:
   - Si el evento lleva `key`: `particion = murmur2(key) % num_particiones`.
   - **Regla de VidalStore**: Toda entidad con ciclo de vida (ej. compras y licencias de un `usuarioSub` o de un `juegoId`) debe usar ese identificador como `key`. Esto garantiza que todos los eventos de un mismo usuario caigan **en la misma partición y se procesen en orden estricto de emisión**.
   - Si no lleva `key` (`null`): Kafka reparte por round-robin o *sticky partitioning*.

---

## 5. Implementación Didáctica: Los 4 Modelos de Lab A12

El Laboratorio de Actividad A12 enseña la mecánica de Kafka implementándola en JavaScript puro sin dependencias:

### 5.1 `cola-vs-log.mjs` (La diferencia entre extraer y leer)
```javascript
// Cola: extraer elimina el elemento
const cola = ['compra-1', 'compra-2'];
const atendido = cola.shift(); // 'compra-1' desaparece para siempre

// Log: append asigna offset y leer no altera el arreglo
const log = [];
function append(evento) {
  log.push(evento);
  return log.length - 1; // Devuelve el offset asignado
}
function leerDesde(offset, cantidad = 10) {
  return log.slice(offset, offset + cantidad); // Copia inmutable
}
```

### 5.2 `retencion.mjs` (Offsets inmutables y purga de segmentos)
```javascript
const log = { inicio: 0, registros: [] };

function purgarPorRetencion(diasRetencion, diaActual) {
  // Los offsets viejos se descartan, pero log.inicio avanza
  // Los registros restantes conservan su offset original invariable
  const limite = diaActual - diasRetencion;
  const restantes = log.registros.filter(r => r.dia >= limite);
  const descartados = log.registros.length - restantes.length;
  log.inicio += descartados;
  log.registros = restantes;
}
```

### 5.3 `particiones.mjs` (Enrutamiento determinista por clave)
```javascript
import crypto from 'node:crypto';

function particionPara(key, totalParticiones) {
  const hash = crypto.createHash('md5').update(key).digest().readUInt32BE(0);
  return hash % totalParticiones;
}
// Mismo usuarioSub siempre produce el mismo número de partición
```

### 5.4 `consumer-groups.mjs` (Asignación y rebalanceo)
```javascript
function repartirParticiones(particiones, consumidores) {
  // 1 consumidor por partición dentro del mismo grupo
  // Si hay más consumidores que particiones, los sobrantes quedan ociosos
  const asignacion = {};
  consumidores.forEach((c, idx) => {
    asignacion[c] = particiones.filter((_, pIdx) => pIdx % consumidores.length === idx);
  });
  return asignacion;
}
```
