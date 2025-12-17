![logo bsg](../images/logobsg.png)

# Certified Python Data Engineer – AWS Data Engineering Pipeline

## AWS Glue + AWS Lambda
---

## Objetivo técnico de la sesión

- Diseñar e implementar un pipeline **event-driven** con separación clara entre **control plane** (Lambda) y **data plane** (Glue/Spark).
- Integrar múltiples fuentes (mínimo S3; extensible a RDS/CSV/JSON/APIs), aplicar transformaciones reproducibles y producir salidas optimizadas para analítica.
- Evaluar el pipeline con criterios de:
  - **Throughput** (archivos/día, filas/seg)
  - **Latencia** (tiempo extremo a extremo)
  - **Costo** (DPU-minutes, storage, scans)
  - **Confiabilidad** (reintentos, duplicados, fallos parciales)

No basta “que corra”. Se evalúa **criterio**: cuándo Spark, cuándo serverless, dónde están los cuellos de botella y cómo justificar trade-offs.

---

## Problema real de ingeniería de datos

**Síntomas típicos en empresas:**
- Llegada de datos por lotes pequeños (micro-batch): 1–N archivos/día → 200+ archivos/día.
- Datasets con *schema drift* (columnas que aparecen/desaparecen, tipos inconsistentes).
- Requisitos de consumo:
  - Analítica (Athena/BI)
  - Reportes diarios
  - Data quality

**Riesgos técnicos:**
- **Small files problem** (S3): demasiados objetos pequeños → overhead de list/scan.
- ETL acoplado (scripts manuales) → poca trazabilidad.
- Reprocesamiento caro por falta de particiones/formato columnar.

Hacer que “llegue al S3” no resuelve el problema. El objetivo es convertir ingestión cruda en **activos analíticos** con gobernanza y costo controlado.

---

## Por qué NO usar EC2 para este caso

**EC2 (cluster propio) tiene costos ocultos:**
- Operación: parches, AMIs, hardening, escalado.
- Capacidad ociosa: pagas incluso sin datos.
- Complejidad: autoscaling, scheduling, logging distribuido.

**Cuándo EC2 sí sería razonable:**
- Procesamiento continuo o muy intensivo (24/7)
- Dependencias nativas complejas
- Requerimientos de red muy específicos

**Decisión para el laboratorio:**
- **Serverless** para control (Lambda) y **Spark administrado** (Glue) para ETL.

En Free Tier + entornos educativos, EC2 introduce fricción y costo. En industria, EC2 se usa cuando el *unit economics* lo justifican.

---

## Servicios AWS y responsabilidad técnica

| Servicio | Responsabilidad | Decisión de ingeniería |
|---|---|---|
| S3 | Storage desacoplado (data lake) | Zonas (raw/processed), naming, particiones |
| Lambda | Control plane | Idempotencia, validación, throttling |
| Glue | Data plane (Spark ETL) | DPUs/workers, shuffles, formatos |
| IAM | Seguridad | Least privilege, roles separados |
| CloudWatch | Observabilidad | métricas, logs, alarms |

Separar responsabilidades permite escalar componentes de forma independiente (por ejemplo: más archivos → más triggers; más datos → más DPUs).

---

## Arquitectura lógica del pipeline

```
S3 (Raw Zone)
   │  Evento: ObjectCreated
   ▼
AWS Lambda (Control Plane)
   │  start_job_run + validaciones
   ▼
AWS Glue (Spark Execution Engine)
   │  ETL distribuido
   ▼
S3 (Processed Zone – Parquet, particionado)
```

**Detalles técnicos clave:**
- **Evento**: `s3:ObjectCreated:*` con filtro por sufijo `.csv` y/o prefijo `incoming/`.
- **Contrato**: Lambda pasa parámetros al Job (bucket/key, dataset_id, run_date).
- **Output**: Parquet particionado para *partition pruning*.

Este patrón desacopla ingestión de procesamiento. El procesamiento es reproducible si el input está versionado y el job es determinístico.

---

## AWS Glue como Spark administrado

**Glue = Spark + servicios administrados:**
- Driver/Executors gestionados por AWS.
- Integración con Data Catalog como metastore.

**Implicaciones Spark (no desaparecen):**
- Transformaciones pueden disparar **shuffles**.
- El layout del dataset afecta I/O.
- El costo y tiempo dependen de paralelismo y stage DAG.

Pensar como ingenieros Spark: particiones, joins, agregaciones, skew, shuffle partitions.

---

## Glue Job lifecycle (y por qué importa)

1. **Bootstrap**: aprovisiona recursos y runtime (overhead inevitable).
2. **Read**: carga desde S3/Catalog.
3. **Transform**: DAG de Spark (stages, shuffles).
4. **Write**: commit a S3 (archivos + particiones).
5. **Shutdown**: libera recursos.

**Cómo se optimiza el lifecycle:**
- Reducir arranques innecesarios (trigger solo si aplica).
- Evitar jobs demasiado pequeños (overhead domina).
- Consolidar transformaciones para minimizar shuffles.

En jobs pequeños, 60–120s pueden ser solo overhead. La optimización real es *hacer menos jobs* y escribir mejor.

---

## DynamicFrame: cuándo usarlo

**Qué resuelve DynamicFrame:**
- Datos con esquema variable.
- Manejo de campos anidados y inconsistencias.
- Integración directa con Catalog.

**Costo:**
- Menor performance que DataFrame.
- Menos control de optimizaciones Spark.

**Uso recomendado:**
- Ingesta + normalización básica.
- Conversión a DataFrame para lógica pesada.

Si el dataset es estable y tabular, quedarse en DynamicFrame todo el tiempo suele ser un anti‑pattern.

---

## DataFrame: por qué es crítico

**Ventajas técnicas:**
- **Catalyst Optimizer**: reordena operaciones, empuja filtros, optimiza plan lógico.
- **Tungsten**: ejecución optimizada en memoria (menor overhead).
- APIs avanzadas: window functions, joins complejos, UDFs (con cuidado).

**Regla:**
- Transformaciones complejas, joins, agregaciones → DataFrame.

También se evalúa *evitar UDFs* cuando hay funciones nativas (UDFs rompen optimizaciones).

---

## Conversión correcta y patrón de implementación

```python
# 1) Ingesta flexible
source_dyf = glueContext.create_dynamic_frame.from_catalog(
    database="bsg_db",
    table_name="raw_sales"
)

# 2) Performance y control Spark
df = source_dyf.toDF()

# 3) Transformaciones (ejemplo)
df_clean = df.filter(df["amount"] > 0)

# 4) Regreso a DynamicFrame para writer Glue
final_dyf = DynamicFrame.fromDF(df_clean, glueContext, "final")
```

Este patrón maximiza compatibilidad con Glue y performance de Spark.

---

## Particionamiento: impacto real en queries

**Sin particiones:**
- Athena/engines hacen **full scan**.
- Mayor latencia y costo por TB escaneado.

**Con particiones:**
- **Partition pruning**: solo lee particiones relevantes.
- Reduce I/O y tiempo de consulta.

Particionar no es gratis: demasiadas particiones también penaliza (metadatos + small files). Se requiere criterio.

---

## Diseño de particiones (criterios formales)

**Criterios recomendados:**
- Columna usada frecuentemente en filtros (WHERE).
- Cardinalidad moderada (no millones de valores distintos).
- Estabilidad (no cambia por fila de forma caótica).

**Ejemplos buenos:**
- `year`, `month`, `day`
- `country`, `region` (si cardinalidad controlada)

**Ejemplos malos:**
- `user_id` (alta cardinalidad)
- `timestamp` completo (explota particiones)

Diseñar particiones es diseñar costos. Un diseño malo puede arruinar el performance incluso con Parquet.

---

## Formatos columnar: Parquet profundo

**Por qué Parquet es superior para analítica:**
- Columnar storage → lee solo columnas usadas (projection pushdown).
- Compresión por columna → menor storage y I/O.
- Estadísticas (min/max) → optimización adicional en algunos engines.

**Regla:**
- CSV entra (raw), Parquet sale (processed).

Pensar en I/O: en analítica, el costo es leer datos, no calcular.

---

## AWS Lambda: rol real en pipelines

**Lambda como control plane:**
- Validar que el evento cumple contrato (sufijo, tamaño, prefijo).
- Enriquecer contexto (run_date, dataset_id).
- Disparar Glue con parámetros.

**Qué NO hacer en Lambda:**
- ETL pesado (limitado por tiempo/memoria).
- Operaciones masivas sobre S3.

Lambda debe ser rápida, determinística y observable. Si tarda mucho, probablemente está mal diseñada.

---

## Event-Driven design (por qué es escalable)

**Ventajas técnicas:**
- Eliminación de polling (menos costo).
- Escalado automático (concurrencia Lambda).
- Desacoplamiento: productores y consumidores evolucionan sin romperse.

**Riesgos:**
- Duplicados
- Orden no garantizado
- Pico de eventos (burst)

Event-driven exige disciplina: idempotencia y control de concurrencia.

---

## Idempotencia (diseño formal)

**Problema:** S3 puede entregar eventos duplicados o reintentos.

**Definición:** Una operación idempotente produce el mismo resultado si se ejecuta 1 o N veces.

**Estrategias simples (laboratorio):**
- Ignorar si `key` ya está en `processed/`.
- Validar extensión y tamaño.

**Estrategias robustas (industria):**
- Registro de procesamiento (DynamoDB) con condición `put if not exists`.
- Checkpoints por `etag`/hash.

---

## Concurrencia y límites

**Fenómeno:**
- S3 → muchos eventos simultáneos.
- Lambda escala y dispara Glue.

**Riesgo:**
- Glue tiene límites de ejecuciones simultáneas por cuenta/región.

**Mitigaciones:**
- Buffering (EventBridge / SQS).
- Control de concurrencia en Lambda.
- Micro-batching (un job procesa varios archivos).

Identificar el cuello de botella es parte de "Evaluar". No se optimiza a ciegas.

---

## Optimización Spark/Glue (técnicas concretas)

**Reducir shuffles:**
- Filtrar temprano.
- Evitar joins innecesarios.
- Reparticionar de forma consciente (cuando aplique).

**Evitar UDFs:**
- Preferir funciones nativas `pyspark.sql.functions`.

**Pequeños archivos:**
- Controlar número de archivos de salida (coalesce/repartition con criterio).

Optimización no es “más DPUs”. Es reducir I/O y shuffles.

---

## Observabilidad (operación real)

**Logs mínimos (Lambda):**
- dataset_id, key, size, decision (ignored/started)
- job_run_id

**Métricas Glue:**
- duración por ejecución
- fallos por etapa

**Alarms (conceptual):**
- tasa de fallos > umbral
- duración anómala (p95)

Sin telemetría, no se puede evaluar ni mejorar el sistema.

## Siguientes pasos
[Athena Lab – Querying Optimized Data Lakes with AWS Glue](athena_lab.md)