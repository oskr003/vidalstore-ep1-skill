# Contratos de Eventos, DTOs y Commit Manual de Offsets (D12)

Guía técnica sobre la definición de contratos formales de eventos, validación estricta en tiempo de ejecución, el ciclo de vida del commit manual de offsets y la gestión de rebalanceo y lag en Apache Kafka, integrando los conceptos de la clase magistral D12.

---

## 1. El Contrato de Eventos y por qué los Tipos de TypeScript No Bastan

En una arquitectura de microservicios distribuida, un contrato es el acuerdo formal de qué campos tiene un evento, de qué tipo es cada uno, qué valores están permitidos y cuáles son obligatorios.

> [!CAUTION]
> **La ilusión de seguridad de TypeScript**:
> Los `interface` o `type` de TypeScript son herramientas de tiempo de compilación. **Al compilar a JavaScript se borran por completo (`type erasure`)**. Si un microservicio productor envía un payload con campos faltantes, cadenas vacías o tipos alterados, el consumidor en Node.js recibirá los datos corruptos sin ninguna advertencia, provocando fallos en producción.

### Solución Mandatoria: Validación en Runtime con DTOs
Cada microservicio debe validar los eventos en el borde de entrada y salida mediante clases decoradas con `class-validator` y transformadas con `class-transformer`:

```typescript
// evento.dto.ts
import { Type } from 'class-transformer';
import {
  IsEnum,
  IsISO8601,
  IsNotEmpty,
  IsNumber,
  IsPositive,
  IsString,
  IsUUID,
  ValidateNested,
} from 'class-validator';

export enum TipoEventoVidalStore {
  COMPRA_REALIZADA = 'compra.realizada',
  LICENCIA_REVOCADA = 'licencia.revocada',
  JUEGO_PUBLICADO = 'juego.publicado',
}

export class DatosCompraRealizadaDto {
  @IsUUID(4)
  licenciaId!: string;

  @IsString()
  @IsNotEmpty()
  juegoId!: string;

  @IsNumber()
  @IsPositive()
  precioPagado!: number;
}

/**
 * Sobre Estándar Obligatorio para Todo Evento en Kafka
 */
export class SobreEventoDto {
  @IsUUID(4)
  eventoId!: string;

  @IsEnum(TipoEventoVidalStore)
  tipo!: TipoEventoVidalStore;

  @IsString()
  version!: string; // ej: '1.0'

  @IsISO8601()
  emitidoEn!: string;

  @IsString()
  @IsNotEmpty()
  usuarioSub!: string;

  @ValidateNested()
  @Type(() => DatosCompraRealizadaDto)
  datos!: DatosCompraRealizadaDto;
}
```

---

## 2. Momento Exacto del Commit: La Regla Innegociable de Offsets

Un consumidor lee mensajes en lotes o uno a uno. El broker **no sabe qué hace tu código con el mensaje**; solo guarda el offset confirmado por el grupo en el topic interno `__consumer_offsets`.

```
Partición de compras:  [ ... | 42 | 43 | 44 | 45 | 46 | 47 | ... ]
                              ^              ^
                       Procesado en BD   Leído en memoria
```

### 2.1 El Peligro del Auto-Commit (`enableAutoCommit: true`)
Si el auto-commit está activado (por omisión cada 5 segundos):
- Si el hilo consumidor lee hasta el offset 47 pero el código solo ha persistido hasta el 43 y el proceso se cae: **Kafka registra el offset 47 como confirmado**.
- Al reiniciar, el consumidor pide desde el 48. **Los eventos 44, 45, 46 y 47 se pierden en silencio sin haberse procesado**. Esto es entrega *at-most-once* (inaceptable en compras).

### 2.2 Desactivar Auto-Commit y Confirmar Manualmente (`offset + 1`)
En VidalStore el auto-commit se apaga explícitamente (`enableAutoCommit: false`).
El commit manual se ejecuta **únicamente después** de que la base de datos o el efecto colateral haya concluido satisfactoriamente:

```typescript
// Regla de Oro: Confirmar siempre el offset del mensaje procesado MÁS UNO
await consumer.run({
  autoCommit: false,
  eachMessage: async ({ topic, partition, message }) => {
    try {
      // 1. Validar contrato en runtime
      const evento = await validarContrato(message.value);

      // 2. Ejecutar lógica de negocio / persistencia
      await guardarEnBaseDeDatos(evento);

      // 3. Confirmar a Kafka el siguiente offset por leer
      const siguienteOffset = (Number(message.offset) + 1).toString();
      await consumer.commitOffsets([
        { topic, partition, offset: siguienteOffset },
      ]);
    } catch (error) {
      // Manejo de error / veneno hacia Dead Letter Topic (.dlt)
      await desviarADeadLetterTopic(topic, message, error);
      // Tras desviar, se confirma el offset para no atascar la partición
      const siguienteOffset = (Number(message.offset) + 1).toString();
      await consumer.commitOffsets([
        { topic, partition, offset: siguienteOffset },
      ]);
    }
  },
});
```

> [!IMPORTANT]
> **¿Por qué `offset + 1`?**
> En Kafka, el offset committeado no representa el último mensaje leído, sino **el offset del próximo registro que el consumidor espera recibir en la siguiente petición fetch**. Si confirmas `message.offset` sin el `+ 1`, al reiniciar el consumidor volverá a pedir ese mismo mensaje.

---

## 3. Rebalanceo de Consumer Groups

El reparto de particiones entre los miembros de un grupo lo decide el broker coordinador del grupo.
Un **rebalanceo** se dispara cuando:
1. Un nuevo consumidor se une al grupo.
2. Un consumidor existente se desconecta o no envía latidos (*heartbeat*) dentro del tiempo de `session.timeout.ms`.
3. Se agregan nuevas particiones al topic.

```
Escenario: 3 Particiones en vidalstore.compras

1 Consumidor en el grupo:
  Consumidor A  -->  [Partición 0, Partición 1, Partición 2]

2 Consumidores en el grupo (tras rebalanceo):
  Consumidor A  -->  [Partición 0, Partición 1]
  Consumidor B  -->  [Partición 2]

3 Consumidores en el grupo:
  Consumidor A  -->  [Partición 0]
  Consumidor B  -->  [Partición 1]
  Consumidor C  -->  [Partición 2]

4 Consumidores en el grupo (1 ocioso):
  Consumidor A  -->  [Partición 0]
  Consumidor B  -->  [Partición 1]
  Consumidor C  -->  [Partición 2]
  Consumidor D  -->  (Ocioso / Standby)
```

### Estrategias de Asignación:
- **`Range`**: Agrupa particiones contiguas por topic. Puede generar desbalance si hay pocos topics y muchos consumidores.
- **`RoundRobin`**: Reparte todas las particiones de forma alternada y uniforme entre todos los consumidores disponibles.

---

## 4. Consumer Lag: La Métrica Operativa Reina

El **Consumer Lag** es la diferencia aritmética entre el offset del último mensaje escrito por el productor en una partición (*Log End Offset*) y el último offset confirmado por el grupo (*Committed Offset*):

$$\text{Lag} = \text{Log End Offset} - \text{Committed Offset}$$

### Decisiones Operativas Basadas en Lag:
1. **Lag = 0**: El consumidor está completamente al día en tiempo real.
2. **Lag Creciente Constante**: El productor genera más eventos por segundo que los que el consumidor puede procesar.
   - Solución: Escalar horizontalmente agregando más instancias del consumidor (hasta un máximo igual al número de particiones). Si ya hay 1 consumidor por partición, se deben añadir más particiones al topic.
3. **Lag en una Sola Partición**: Indica una **clave caliente (*hot key*)** donde un único usuario o entidad está generando un volumen anómalo de tráfico o un mensaje venenoso está bloqueando esa partición específica.
