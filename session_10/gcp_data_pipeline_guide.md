# Guía Técnica: Orquestación y Optimización de Pipelines en GCP

## 1. Introducción a Google Cloud Data Fusion

### ¿Qué es Google Cloud Data Fusion?
Google Cloud Data Fusion es un servicio completamente gestionado para la integración de datos (ETL/ELT) basado en una interfaz visual. Está construido sobre CDAP (Cloud Data Application Platform) y permite diseñar pipelines de datos sin necesidad de escribir grandes cantidades de código.

### Arquitectura
- **Interfaz UI (Wrangler + Pipeline Studio)**: Para diseño visual
- **Motor de ejecución (Apache Spark)**: Procesamiento distribuido
- **Dataproc (backend)**: Ejecución de jobs Spark
- **Plugins**: Conectores para fuentes y destinos

### Casos de uso
- Integración de datos desde múltiples fuentes
- ETL para Data Warehousing (BigQuery)
- Limpieza y transformación de datos

### Ejemplo: Pipeline básico

**Objetivo:** Cargar datos desde Cloud Storage a BigQuery

**Pasos:**
1. Crear instancia de Data Fusion
2. Crear pipeline batch
3. Añadir componentes:
   - Fuente: Cloud Storage
   - Transformación: Wrangler
   - Destino: BigQuery

### Ejemplo JSON (conceptual)
```json
{
  "name": "pipeline_gcs_to_bq",
  "nodes": [
    {"type": "GCS", "path": "gs://bucket/data.csv"},
    {"type": "Wrangler", "operations": ["parse-as-csv"]},
    {"type": "BigQuery", "table": "dataset.table"}
  ]
}
```

### Ventajas
- Low-code / no-code
- Escalabilidad automática
- Integración nativa con servicios GCP

### Limitaciones
- Menor control fino vs código puro
- Costos asociados a Dataproc

---

## 2. Automatización con Google Cloud Functions

### ¿Qué es Cloud Functions?
Google Cloud Functions es un servicio serverless basado en eventos que permite ejecutar código en respuesta a eventos sin gestionar infraestructura.

### Características clave
- Event-driven
- Escalado automático
- Integración con Pub/Sub, GCS, HTTP

### Casos de uso
- Trigger de pipelines
- Procesamiento de eventos en tiempo real
- Automatización de workflows

### Ejemplo 1: Trigger desde Cloud Storage

```python
import functions_framework

@functions_framework.cloud_event
def process_file(cloud_event):
    data = cloud_event.data
    bucket = data["bucket"]
    name = data["name"]
    print(f"Archivo recibido: {name} en {bucket}")
```

### Ejemplo 2: Trigger HTTP

```python
from flask import jsonify


def trigger_pipeline(request):
    # Llamada a Data Fusion API
    return jsonify({"status": "Pipeline triggered"})
```

### Integración con Data Fusion
Se puede invocar pipelines mediante REST API:

```bash
POST https://datafusion.googleapis.com/v1/projects/.../namespaces/default/apps/.../workflows/DataPipelineWorkflow/start
```

### Mejores prácticas
- Uso de variables de entorno
- Manejo de errores robusto
- Logging con Cloud Logging

---

## 3. Sesión 5.3: Optimización de procesos de datos en GCP

### Principios de optimización

1. **Minimizar movimiento de datos**
   - Procesar cerca de la fuente
   - Evitar ETL innecesarios

2. **Uso eficiente de BigQuery**
   - Particionamiento
   - Clustering
   - Uso de SELECT específicos (evitar SELECT *)

3. **Optimización en Data Fusion**
   - Reducir transformaciones innecesarias
   - Uso de pipelines incrementales
   - Configuración adecuada de recursos Spark

### Ejemplo: Particionamiento en BigQuery

```sql
CREATE TABLE dataset.ventas
PARTITION BY DATE(fecha)
CLUSTER BY cliente_id
AS SELECT * FROM source_table;
```

### Optimización en Spark (Data Fusion backend)

- Ajustar memoria:
```
spark.executor.memory=4g
spark.driver.memory=2g
```

- Paralelismo:
```
spark.sql.shuffle.partitions=200
```

### Estrategias avanzadas

#### Incremental Processing
Solo procesar datos nuevos:
- Uso de timestamps
- CDC (Change Data Capture)

#### Caching
- Uso de Memorystore (Redis)
- Cache de resultados intermedios

#### Orquestación eficiente
- Uso de dependencias
- Control de retries
- Manejo de fallos

### Ejemplo de arquitectura optimizada

1. Ingesta → Cloud Storage
2. Trigger → Cloud Functions
3. Orquestación → Data Fusion
4. Procesamiento → Dataproc (Spark)
5. Almacenamiento → BigQuery

### Buenas prácticas generales

- Diseñar pipelines idempotentes
- Monitoreo con Cloud Monitoring
- Alertas con Cloud Alerting
- Versionado de pipelines

---

## Conclusión

La combinación de Data Fusion, Cloud Functions y estrategias de optimización permite construir pipelines robustos, escalables y eficientes en GCP. La clave está en diseñar arquitecturas desacopladas, event-driven y optimizadas para minimizar costos y maximizar rendimiento.

