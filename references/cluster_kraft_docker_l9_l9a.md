# Clúster Kafka en Modo KRaft, Docker Compose y Topología Local (L9 / L9A)

Guía técnica y normativa para la configuración del clúster de **Apache Kafka en modo KRaft (Kafka Raft)**, sin ZooKeeper, desplegado con **3 controllers y 3 brokers** en Docker Compose, conforme a las especificaciones del Laboratorio L9, la clase pre-laboratorio L9A y el caso VidalStore para la Evaluación Parcial N°3 (EP3).

---

## 1. Arquitectura KRaft: Por qué 3 Controllers y 3 Brokers

En Kafka tradicional (previo a 3.x), la coordinación del clúster requería un servicio externo: Apache ZooKeeper. Desde Kafka 3.3+ (y en KRaft modo de producción), el consenso y la gestión de metadatos se gestionan internamente mediante el protocolo Raft (KIP-500).

```
                      +---------------------------------------+
                      |       KRaft Controller Quorum         |
                      |  (Votantes: 1@c-1, 2@c-2, 3@c-3:9093) |
                      +-------------------+-------------------+
                                          |
                      +-------------------+-------------------+
                      |   Quorum Metadata Log (@metadata)     |
                      +-------------------+-------------------+
                                          |
         +--------------------------------+--------------------------------+
         |                                |                                |
+--------v-------+               +--------v-------+               +--------v-------+
|    broker-1    |               |    broker-2    |               |    broker-3    |
| ID: 4          |               | ID: 5          |               | ID: 6          |
| Port: 9092     |               | Port: 9094     |               | Port: 9096     |
| (Líder / ISR)  |               | (Líder / ISR)  |               | (Líder / ISR)  |
+----------------+               +----------------+               +----------------+
```

### Reglas Clave de la Arquitectura:
1. **Separación de Roles (`KAFKA_PROCESS_ROLES`)**:
   - `controller`: Nodos dedicados a decidir y registrar metadatos (quién es líder de cada partición, qué réplicas están en ISR, asignación de topics). **No reciben tráfico de productores ni consumidores**.
   - `broker`: Nodos dedicados a almacenar segmentos de log y atender tráfico cliente (producir y consumir). **No votan en el quórum de metadatos**.
2. **Quórum de Decisión ($\lfloor N/2 \rfloor + 1$)**:
   - Con 3 controllers, la mayoría es 2. Tolera la caída de **1 controller**. Si caen 2, el clúster entra en modo de solo lectura de metadatos y no puede crear topics ni reelegir líderes.
   - Con 3 brokers y factor de replicación 3 (`replication-factor: 3`), cualquier mensaje confirmado con `acks=all` y `min.insync.replicas=2` tolera la caída de **1 broker** sin pérdida de disponibilidad para escritura.

---

## 2. Parámetros Críticos de Configuración en Docker Compose

### 2.1 Variables Globales y de Clúster
- **`CLUSTER_ID`**: En KRaft, todos los nodos que pertenecen al mismo clúster deben inicializarse con el mismo UUID codificado en Base64.
  - Para VidalStore: `CLUSTER_ID: VmlkYWxTdG9yZS1LYWZrYQ` (L9 Slide 12).
- **`KAFKA_CONTROLLER_QUORUM_VOTERS`**: Lista explícita de los votantes que forman el quórum Raft.
  - Formato idéntico en los 6 contenedores:
    ```env
    KAFKA_CONTROLLER_QUORUM_VOTERS: 1@controller-1:9093,2@controller-2:9093,3@controller-3:9093
    ```

### 2.2 Listeners y Advertised Listeners (El Patrón de Doble Red)
Un broker de Kafka dentro de Docker necesita atender dos tipos de clientes:
1. **Otros contenedores dentro de la red Docker (`vidalstore-net`)**: Se conectan usando nombres de servicio (`broker-1:19092`).
2. **Herramientas locales del host (pruebas, scripts, host OS)**: Se conectan vía localhost mapeado (`localhost:9092`).

| Broker | Puerto Interno (Docker) | Puerto Externo (Host) | `KAFKA_NODE_ID` |
| :--- | :--- | :--- | :--- |
| **broker-1** | `broker-1:19092` | `localhost:9092` | 4 |
| **broker-2** | `broker-2:19092` | `localhost:9094` | 5 |
| **broker-3** | `broker-3:19092` | `localhost:9096` | 6 |

**Configuración canónica del listener en `broker-1`:**
```yaml
environment:
  KAFKA_NODE_ID: 4
  KAFKA_PROCESS_ROLES: broker
  KAFKA_LISTENERS: INTERNAL://0.0.0.0:19092,EXTERNAL://0.0.0.0:9092
  KAFKA_ADVERTISED_LISTENERS: INTERNAL://broker-1:19092,EXTERNAL://localhost:9092
  KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: INTERNAL:PLAINTEXT,EXTERNAL:PLAINTEXT,CONTROLLER:PLAINTEXT
  KAFKA_INTER_BROKER_LISTENER_NAME: INTERNAL
  KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
  KAFKA_HEAP_OPTS: "-Xmx256m -Xms256m"
  KAFKA_LOG_DIRS: /var/lib/kafka/data
```

> [!IMPORTANT]
> **Memoria (`KAFKA_HEAP_OPTS`)**: Fijar estrictamente `-Xmx256m -Xms256m`. Dejar el heap por defecto de la JVM (1 GB o más por nodo) colapsaría el equipo anfitrión al levantar 6 nodos de Kafka simultáneos en Docker.

---

## 3. Healthchecks de Conectividad para KRaft

A diferencia de RabbitMQ (`rabbitmq-diagnostics check_running`), Kafka no incluye un CLI ligero de ping en imágenes mínimas. 
El healthcheck estándar de L9 para los controllers utiliza la verificación de socket TCP nativa de bash:

```yaml
healthcheck:
  test: ["CMD-SHELL", "bash -c '</dev/tcp/localhost/9093'"]
  interval: 5s
  timeout: 5s
  retries: 10
  start_period: 10s
```

Para los brokers, se comprueba su puerto interno:
```yaml
healthcheck:
  test: ["CMD-SHELL", "bash -c '</dev/tcp/localhost/19092'"]
  interval: 5s
  timeout: 5s
  retries: 10
  start_period: 15s
```

---

## 4. Creación de Topics: El Script `kafka/topics.sh`

Los topics no se crean al vuelo mediante auto-creación (`auto.create.topics.enable=false`). Se declaran mediante un script determinista que se ejecuta una sola vez tras levantar el clúster.

### 4.1 Script Canónico para VidalStore (`kafka/topics.sh`)
```bash
#!/usr/bin/env bash
set -euo pipefail

BROKER="broker-1:19092"
SIETE_DIAS=604800000   # 7 * 24 * 60 * 60 * 1000 ms
UN_DIA=86400000        # 24 * 60 * 60 * 1000 ms

crear_topic() {
  local nombre="$1"
  local retencion="$2"
  local extra_args="${3:-}"

  echo "Declarando topic [${nombre}] con retención ${retencion} ms..."
  kafka-topics.sh --bootstrap-server "$BROKER" --create --if-not-exists \
    --topic "$nombre" \
    --partitions 3 \
    --replication-factor 3 \
    --config "retention.ms=${retencion}" \
    ${extra_args}
}

# 1. Topic de Compras (eventos inmutables de dominio)
crear_topic "vidalstore.compras" "$SIETE_DIAS"

# 2. Topic de Actividad (navegación y telemetría de jugadores)
crear_topic "vidalstore.actividad" "$UN_DIA"

# 3. Dead Letter Topics (.dlt) para veneno o fallos terminales
crear_topic "vidalstore.compras.dlt" "$SIETE_DIAS"
crear_topic "vidalstore.actividad.dlt" "$UN_DIA"

# 4. Requisito Grupos de 3: Topic de Catálogo con Compactación
echo "Declarando topic compactado [vidalstore.catalogo]..."
kafka-topics.sh --bootstrap-server "$BROKER" --create --if-not-exists \
  --topic "vidalstore.catalogo" \
  --partitions 3 \
  --replication-factor 3 \
  --config "cleanup.policy=compact" \
  --config "min.cleanable.dirty.ratio=0.1" \
  --config "segment.ms=60000"

echo "✅ Topología de Kafka para VidalStore declarada exitosamente."
```

### 4.2 Trampas Frecuentes de Ejecución y EOL
- **Fin de línea CRLF**: Si el archivo se guarda con retornos de carro de Windows (`\r\n`), bash en Linux/Docker arrojará `\r: command not found`.
  - Diagnóstico: `grep -c $'\r' kafka/topics.sh` (debe ser 0).
  - Corrección: `sed -i 's/\r$//' kafka/topics.sh`.
- **Idempotencia**: Al correr por segunda vez, el script debe ejecutar con código de salida `0` (`--if-not-exists`), sin arrojar errores de `TopicExistsException`.

---

## 5. Respuestas Canónicas a Preguntas de Control ("Voy bien" de L9)

1. **¿Qué pasa con la partición 0 si se cae el Leader actual?**
   - El controller activo detecta el fallo del broker mediante el latido del session timeout.
   - Selecciona inmediatamente un nuevo Leader entre los brokers restantes que pertenezcan a la lista de réplicas sincronizadas (**ISR - In-Sync Replicas**).
   - Los clientes productores y consumidores son redirigidos al nuevo líder de forma transparente sin perder mensajes.
2. **¿Por qué `autocreateTopics: false` es obligatorio en clientes de producción?**
   - Evita la creación accidental de topics no gobernados con 1 partición y réplica 1 por errores tipográficos en el productor (ej. escribir `vidalstore.compra` en lugar de `vidalstore.compras`).
3. **¿Cuál es el rol de `KAFKA_INTER_BROKER_LISTENER_NAME`?**
   - Especifica qué listener deben utilizar los brokers para replicar datos entre sí de forma interna (`INTERNAL`), aislando la replicación del tráfico externo expuesto a los desarrolladores.
