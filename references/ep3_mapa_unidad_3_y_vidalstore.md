# Mapa de la Unidad 3, Cronograma de la EP3 y Reglas VidalStore (P3 / L9)

Guía normativa integral que define el mapa conceptual de las 7 regiones de la Unidad 3, el cronograma de entregables semanales (E1, E2, E3 y Defensas), la topología oficial de topics para VidalStore y los estándares técnicos obligatorios del cliente de Kafka, integrando la presentación oficial P3 y el laboratorio L9.

---

## 1. El Mapa Conceptual de la Unidad 3 (Las 7 Regiones)

La Unidad 3 cubre el ciclo de vida completo de streaming de eventos distribuido, organizado en 7 regiones arquitectónicas:

```
[ Región 1: Cola o Stream ]   --->  RabbitMQ (efímero, transaccional) vs Kafka (historia, inmutable)
             │
[ Región 2: El Log ]          --->  Append-only, offsets inmutables, segmentos (.log/.index), zero-copy
             │
[ Región 3: Consumer Groups ] --->  Cursores independientes, particionado, balanceo y commit manual
             │
[ Región 4: El Clúster ]      --->  KRaft (3 controllers + 3 brokers), ISR, quórum de metadatos, acks=all
             │
[ Región 5: Retención ]       --->  retention.ms, purga por segmentos, compactación (cleanup.policy=compact)
             │
[ Región 6: Resiliencia/DLT ] --->  Dead Letter Topics (.dlt), desvío de veneno, reintentos con backoff
             │
[ Región 7: Nube y Observabilidad ] -> Métricas (Lag), Prometheus, Grafana, GHCR, AWS/Azure y CI/CD
```

---

## 2. Cronograma Oficial y Hitos de Evaluación de la EP3

La EP3 adopta un **ciclo semanal estricto**, erradicando los commits de última hora. Cada semana concluye un hito evaluable:

| Hito | Fecha Límite | Entregable de Kafka | Entregable de Ingeniería / Cloud |
| :--- | :--- | :--- | :--- |
| **E1** | **Viernes 6 de noviembre (23:59)** | Clúster Compose KRaft con 3 controllers y 3 brokers; topics creados desde `kafka/topics.sh`; productor de `compras`; simulador publicando; 1 consumidor. | Clon limpio operativo (`start-all.sh`); higiene de Git en todos los repos; cuentas activas en AWS y Azure; diagrama de arquitectura de red en `docs/red.md`. |
| **E2** | **Viernes 13 de noviembre (23:59)** | Tres consumer groups independientes; commit manual de offsets (`offset + 1`); retención justificada; panel de observabilidad en vivo (Prometheus, Grafana y carga). | Imágenes construidas y publicadas en GHCR (GitHub Container Registry); VPC y subredes en AWS con capa de datos operativa. *(Verificación en vivo en laboratorio L12 del lunes 16)*. |
| **E3** | **Viernes 20 de noviembre (23:59)** | Resiliencia con Dead Letter Topics (`.dlt`); administración completa de Kafka vía HTTP en `vidalstore-admin`. | Microservicios y API Gateways desplegados en las dos nubes (AWS y Azure); pipeline de despliegue continuo (CI/CD) funcional. |
| **Defensas** | **Semana 16 (23 al 27 de noviembre)** | **Defensa Individual Oficial**: Demostración de flujos de streaming, operación en vivo en la nube e inspección del historial atómico de Git. |

---

## 3. Catálogo Oficial de Topics de VidalStore

En VidalStore los topics no se crean con nombres libres ni de forma dinámica en tiempo de ejecución. La topología oficial se declara en `kafka/topics.sh`:

| Topic | Particiones | Réplicas | Retención / Política | Propósito en VidalStore |
| :--- | :---: | :---: | :--- | :--- |
| **`vidalstore.compras`** | 3 | 3 | `min.insync.replicas=2`<br>`retention.ms=604800000` (7 días) | Publicación de eventos `compra.realizada` y `licencia.revocada` (`key = usuarioSub`, `401` eventos en el dataset: `P0=147, P1=141, P2=113`). Emite el microservicio de licencias tras guardar en PostgreSQL. |
| **`vidalstore.actividad`** | 3 | 3 | `min.insync.replicas=2`<br>`retention.ms=86400000` (1 día) | Telemetría de partidas (`partida.iniciada`, `partida.terminada`) y búsquedas (`key = juegoId`, `3.039` eventos en el dataset; partición caliente `P0=1.751 [57,6%]` por el juego `292030`, `P1=520`, `P2=768`). |
| **`vidalstore.compras.dlt`** | 3 | 3 | `min.insync.replicas=2`<br>`retention.ms=604800000` (7 días) | Dead Letter Topic para eventos de compra malformados o no procesables tras agotar reintentos. |
| **`vidalstore.actividad.dlt`** | 3 | 3 | `min.insync.replicas=2`<br>`retention.ms=86400000` (1 día) | Dead Letter Topic para telemetría venenosa. |
| **`vidalstore.catalogo`** *(Requisito Grupos de 3)* | 3 | 3 | `min.insync.replicas=2`<br>`cleanup.policy=compact`<br>*(SIN `retention.ms`)* | Registro compactado del estado actual de los juegos (`juego.publicado`, `precio.cambiado` / `juego.actualizado`). La clave es `juegoId`; Kafka conserva el último valor de cada clave. No lleva `retention.ms` para que juegos sin cambios de precio no se borren por antigüedad. |

---

## 4. Biblioteca Oficial de Kafka: Regla Estricta del Cliente Node.js

> [!CAUTION]
> **Prohibición Terminante de `kafkajs` y `@confluentinc/kafka-javascript` (L9 Página 13)**:
> La pauta oficial de evaluación revisa el archivo `package.json`. Está **estrictamente prohibido** utilizar `kafkajs` (proyecto descontinuado con fallos en KRaft moderno) o `@confluentinc/kafka-javascript` (dependencias nativas C++ que rompen compatibilidad entre Windows, Linux y Mac).

### Dependencia Oficial y Mandatoria:
```bash
npm install --save-exact @platformatic/kafka@2.14.0
```
- La opción `--save-exact` fija la versión estricta `"2.14.0"` en el `package.json` (sin el prefijo `^`), garantizando reproducibilidad determinista en las máquinas de todos los integrantes y del docente evaluador.

---

## 5. Higiene de Repositorios y `.gitattributes` en la EP3

Para prevenir incompatibilidades de saltos de línea (CRLF de Windows vs LF de Linux/macOS) que rompan scripts bash o generen diffs ruidosos en Git, **cada uno de los repositorios del ecosistema debe incluir un archivo `.gitattributes` en su directorio raíz**:

```gitattributes
* text=auto eol=lf
*.sh text eol=lf
*.mjs text eol=lf
*.jsonl text eol=lf
```

### Comprobación de Higiene:
```bash
# Verificar que no existan retornos de carro en scripts críticos
grep -c $'\r' start-all.sh kafka/topics.sh
# El resultado debe ser estrictamente 0
```

---

## 6. Preguntas Oficiales de Defensa para la Unidad 3 / EP3

1. **¿Por qué la persistencia del nodename y los logs requiere volúmenes con nombre en Docker Compose?**
   - *Respuesta*: En Kafka KRaft, el estado del quórum de metadatos (`@metadata`) y los segmentos de datos residen en `KAFKA_LOG_DIRS`. Si el contenedor se recrea sin un volumen persistente, pierde su `node.id`, su historial de offsets y corrompe el quórum de controllers.
2. **¿Cómo conviven RabbitMQ y Apache Kafka en VidalStore sin duplicar responsabilidades?**
   - *Respuesta*: RabbitMQ atiende la **mensajería asíncrona transaccional y comandos directos** (`correo.enviar`), donde el mensaje se consume y se destruye inmediatamente tras el `ack`. Kafka funciona como el **log inmutable de eventos de dominio históricos** (`vidalstore.compras`), permitiendo que nuevos servicios (analítica, auditoría, panel en vivo) reconstruyan el estado completo reproduciendo desde el offset 0.
3. **¿Qué garantiza que un usuario no reciba eventos de compra fuera de orden si el topic tiene 3 particiones?**
   - *Respuesta*: El productor utiliza `usuarioSub` como `record key`. La función de hash de Kafka asigna siempre la misma partición a los eventos de un mismo usuario, y dentro de esa partición el orden es total e inmutable gracias a la secuencia monotónica de offsets.
4. **Si el consumidor falla tras persistir en base de datos pero antes de confirmar el offset a Kafka, ¿cómo se previene la duplicación?**
   - *Respuesta*: Kafka garantiza entrega *at-least-once*. Al reiniciar, el consumidor reprocesará el mensaje duplicado. La base de datos receptora aplica idempotencia estricta mediante una restricción `UNIQUE` en la columna de identidad del evento (código de error SQL `23505`), evitando compras o auditorías duplicadas.

---

## 7. Lecciones Aprendidas y Criterios Críticos de Calificación (Entrega 1 hacia E2 y E3)

A partir de la corrección oficial de la Entrega 1 (E1) por parte del docente, se establecen como obligatorios los siguientes puntos para evitar pérdidas de puntaje en E2 y E3:

1. **Variables de Entorno Estrictas sin Fallbacks Hardcodeados (IE1)**:
   - Prohibido dejar cadenas con direcciones de brokers en el código (ej. `process.env.KAFKA_BROKERS || 'broker-1:19092...'`).
   - Leer siempre con `configService.getOrThrow<string>('KAFKA_BROKERS')`.
   - Garantizar que `.env.example` en todos los repos incluya la variable documentada.
2. **Shutdown Hooks Obligatorios en Consumidores NestJS (IE2)**:
   - Todo servicio NestJS que consuma Kafka o RabbitMQ debe ejecutar `app.enableShutdownHooks()` en su `main.ts` antes de `app.listen()`.
   - Sin esto, `onModuleDestroy()` no se dispara al recibir `SIGTERM`, el consumidor no avisa su salida a Kafka y el broker bloquea el rebalanceo de particiones hasta que expira el session timeout.
3. **Sobre de Evento Kafka de Primer Nivel (IE4)**:
   - Todo mensaje debe incluir `juegoId` directamente en la raíz: `{ eventoId, tipo, version, emitidoEn, juegoId, usuarioSub, datos }`.
   - Validar `tipo` con `@IsIn` para prevenir eventos con nombres arbitrarios.
   - Encabezado `x-correlation-id` debe ser un UUID propio del flujo y no un clon de `x-evento-id`.
4. **Script de Arranque `levantar.sh` sin Comandos Destructivos para el Docente (Compila)**:
   - Mantener el script en `main` exactamente en la ruta prometida en el `README.md`.
   - Cero comandos `kill -9` o `kill -15` escaneando puertos del host y cero `docker rm -f` de contenedores ajenos. La limpieza debe circunscribirse al compose (`docker compose down`).
   - El script debe resolver su directorio dinámicamente para ejecutarse tanto desde la raíz del proyecto como desde `vidalstore-plataforma`.
5. **Higiene de Pull Requests y Prohibición de Automerge (Git)**:
   - Todo avance debe entrar por PR con ramas `feature/*`.
   - Los PRs deben ser revisados y aprobados por **otro compañero** de equipo. El automerge (abrir y mergear uno mismo) invalida la revisión.
   - Si un integrante no registra PRs propios durante el ciclo, todo el grupo es penalizado con una bajada de nivel en Git (de 60% a 30%).
6. **Verificaciones Multi-Cloud para E2 y E3 (Nubes)**:
   - En Azure: incluir la salida de `az vm list-skus` en `region.txt` para validar la existencia y cuota de `Standard_B2ats_v2` y `Standard_B2als_v2`.
   - En AWS: asegurar que los scripts de prueba no dependan de dry-run casero y validar el rol asignado.
   - En `docs/red.md`: eliminar cualquier placeholder `<...>` residual del template de red.

---

## 8. Cifras Oficiales del Dataset de VidalStore y Guías de la E2 (D13, Lab A13 y L10)

Al procesar los `3.039` eventos de `vidalstore.actividad` y los `401` eventos de `vidalstore.compras` en `vidalstore-eventos`:
1. **`vidalstore-panel` (`kpi_minuto`)**:
   - Al cierre de la jornada (`22:00` UTC / `18:00` Chile): **`362` partidas en curso**.
   - Pico máximo de la jornada: **`480` partidas en curso a las `21:46`**.
   - Compras brutas registradas: **`380` compras por `6.291.370 CLP`**.
2. **`vidalstore-alertas` (`ventanas_actividad` + `alertas`)**:
   - Con umbral mínimo de partidas terminadas (`MINIMO = 3` o `5`) y más de `20%` de error en ventanas fijas de 5 minutos UTC: dispara **1 sola alerta** correspondiente al **juego `1328670`** (*Mass Effect Legendary Edition*) en la ventana **`21:30` a `21:35` UTC** con **`68` errores de `69` terminadas (`98,6%`)**.
3. **`vidalstore-historial` (`ventas_semana` + `compras_vistas`)**:
   - **`380` compras**, **`15` revocaciones** y **`6.032.190 CLP` netos** (descontando en la semana original el precio pagado de la compra asociada al mismo `licenciaId`).
4. **Guías detalladas de la Semana 13 y Entrega 2**:
   - [Escalamiento, Replicación, Diagnóstico y Consumer Lag (D13 y Lab A13)](./escalamiento_replicacion_y_lag_d13_a13.md)
   - [Taller de la E2: Consumer Groups, Panel en Vivo, GHCR y Despliegue en AWS/Azure (L10)](./taller_e2_consumidores_panel_ghcr_nube_l10.md)


