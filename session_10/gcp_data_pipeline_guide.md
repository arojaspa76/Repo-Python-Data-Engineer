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


---

## 4. Ejemplo paso a paso de la vida real: ingesta automática de ventas desde archivos CSV hacia BigQuery usando Cloud Functions + Data Fusion

### Escenario real
Una empresa de retail recibe todos los días archivos CSV con ventas desde sucursales o sistemas POS. Estos archivos llegan a un bucket de **Google Cloud Storage**. Cada vez que llega un archivo nuevo, una **Google Cloud Function** valida el evento y dispara un pipeline de **Google Cloud Data Fusion**. El pipeline transforma los datos, limpia columnas, estandariza tipos, elimina registros inválidos y carga la información a **BigQuery** para analítica y dashboards.

### Objetivo del flujo
- Detectar automáticamente la llegada de nuevos archivos.
- Ejecutar un pipeline ETL sin intervención manual.
- Cargar datos limpios y normalizados en BigQuery.
- Optimizar almacenamiento, consulta y costo.

---

### Arquitectura del ejemplo

```text
[POS / ERP / Sucursal]
        |
        v
[CSV diario en Cloud Storage]
        |
        v
[Cloud Function se activa por evento]
        |
        v
[Invoca pipeline de Cloud Data Fusion por API REST]
        |
        v
[Data Fusion ejecuta ETL con Spark]
        |
        v
[BigQuery tabla particionada y clusterizada]
        |
        v
[Looker Studio / BI / ML / Reportes]
```

---

### Caso de ejemplo
Supongamos que cada archivo tiene esta estructura:

```csv
sale_id,store_id,product_id,customer_id,sale_timestamp,quantity,unit_price,total_amount,payment_method
1001,S001,P300,C789,2026-03-30 10:21:00,2,15.50,31.00,CARD
1002,S002,P120,C456,2026-03-30 10:25:00,1,200.00,200.00,CASH
1003,S001,P450,C999,2026-03-30 10:40:00,-1,12.00,-12.00,CARD
```

En este caso, el tercer registro es inválido porque la cantidad y el total son negativos.

---

## 4.1 Paso 1: Crear el bucket de entrada en Cloud Storage

Crear un bucket, por ejemplo:

```bash
gs://retail-sales-raw-data
```

Estructura sugerida:

```text
gs://retail-sales-raw-data/incoming/
gs://retail-sales-raw-data/archive/
gs://retail-sales-raw-data/error/
```

### Propósito de cada carpeta
- **incoming/**: archivos recién cargados.
- **archive/**: archivos ya procesados correctamente.
- **error/**: archivos con errores funcionales o estructurales.

---

## 4.2 Paso 2: Crear el dataset y tabla destino en BigQuery

Crear un dataset, por ejemplo:

```text
retail_analytics
```

Crear la tabla optimizada:

```sql
CREATE TABLE `mi-proyecto.retail_analytics.sales_fact`
(
  sale_id STRING,
  store_id STRING,
  product_id STRING,
  customer_id STRING,
  sale_timestamp TIMESTAMP,
  sale_date DATE,
  quantity INT64,
  unit_price NUMERIC,
  total_amount NUMERIC,
  payment_method STRING,
  ingestion_timestamp TIMESTAMP
)
PARTITION BY sale_date
CLUSTER BY store_id, product_id, payment_method;
```

### ¿Por qué así?
- **PARTITION BY sale_date**: reduce escaneo de datos por fecha.
- **CLUSTER BY store_id, product_id, payment_method**: acelera filtros frecuentes.
- **NUMERIC**: evita errores de precisión monetaria.

---

## 4.3 Paso 3: Crear la instancia de Cloud Data Fusion

1. Ir a **Google Cloud Console**.
2. Buscar **Data Fusion**.
3. Crear una nueva instancia.
4. Elegir versión compatible y entorno.
5. Seleccionar región cercana a tus datos.
6. Asignar service account con permisos sobre:
   - Cloud Storage
   - BigQuery
   - Dataproc
   - Logging
7. Esperar a que la instancia quede operativa.

### Recomendaciones reales
- Mantener **misma región** para Storage, Data Fusion, Dataproc y BigQuery cuando sea posible.
- Usar una instancia por ambiente: **dev**, **qa**, **prod**.
- No usar permisos excesivos de tipo Owner.

---

## 4.4 Paso 4: Diseñar el pipeline en Data Fusion

Crear un pipeline batch llamado:

```text
sales_csv_to_bigquery_pipeline
```

### Componentes del pipeline
1. **Fuente**: Cloud Storage
2. **Parser / Wrangler**: leer CSV y transformar
3. **Validaciones**: calidad de datos
4. **Destino**: BigQuery

### Flujo lógico

```text
GCS Source -> Wrangler -> Validator / Transform -> BigQuery Sink
```

### Transformaciones recomendadas
- Parsear columnas numéricas.
- Convertir `sale_timestamp` a tipo timestamp.
- Derivar `sale_date`.
- Eliminar registros con:
  - `quantity <= 0`
  - `unit_price < 0`
  - `total_amount < 0`
- Normalizar `payment_method` a mayúsculas.
- Agregar `ingestion_timestamp`.

### Ejemplo conceptual de reglas
```text
parse-as-csv :body ',' true
set-column sale_date to date(sale_timestamp)
set-column payment_method to upper(payment_method)
delete-row-if quantity <= 0
delete-row-if total_amount < 0
set-column ingestion_timestamp to now()
```

---

## 4.5 Paso 5: Parametrizar el pipeline

Es buena práctica que el pipeline reciba parámetros en vez de tener rutas fijas.

### Parámetros sugeridos
- `input_path`
- `target_dataset`
- `target_table`
- `file_name`

Esto permite reutilizar el pipeline para distintos archivos y ambientes.

Ejemplo conceptual:

```json
{
  "runtimeArgs": {
    "input_path": "gs://retail-sales-raw-data/incoming/sales_20260330.csv",
    "target_dataset": "retail_analytics",
    "target_table": "sales_fact",
    "file_name": "sales_20260330.csv"
  }
}
```

---

## 4.6 Paso 6: Crear la Cloud Function que dispare el pipeline

La Cloud Function se activará cuando llegue un archivo al bucket.

### Lógica de negocio de la función
1. Detectar evento de nuevo archivo.
2. Validar que el archivo venga de la carpeta `incoming/`.
3. Verificar que sea `.csv`.
4. Invocar el pipeline de Data Fusion vía REST API.
5. Registrar logs estructurados.
6. Evitar ejecutar el pipeline sobre archivos incorrectos.

### Ejemplo en Python

```python
import os
import json
import requests
from google.auth.transport.requests import Request
from google.oauth2 import id_token
import google.auth

PROJECT_ID = os.environ.get("PROJECT_ID")
REGION = os.environ.get("REGION")
INSTANCE_ID = os.environ.get("INSTANCE_ID")
NAMESPACE = os.environ.get("NAMESPACE", "default")
PIPELINE_NAME = os.environ.get("PIPELINE_NAME")


def trigger_data_fusion(cloud_event):
    data = cloud_event.data
    bucket = data["bucket"]
    file_name = data["name"]

    if not file_name.startswith("incoming/"):
        print(f"Archivo ignorado: {file_name} no está en incoming/")
        return

    if not file_name.endswith(".csv"):
        print(f"Archivo ignorado: {file_name} no es CSV")
        return

    input_path = f"gs://{bucket}/{file_name}"

    url = (
        f"https://datafusion.googleapis.com/v1/"
        f"projects/{PROJECT_ID}/locations/{REGION}/instances/{INSTANCE_ID}"
        f"/namespaces/{NAMESPACE}/apps/{PIPELINE_NAME}/workflows/DataPipelineWorkflow:start"
    )

    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(Request())
    access_token = credentials.token

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "runtimeArgs": {
            "input_path": input_path,
            "target_dataset": "retail_analytics",
            "target_table": "sales_fact",
            "file_name": file_name.split("/")[-1]
        }
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)

    print(f"Status code: {response.status_code}")
    print(response.text)

    response.raise_for_status()
```

---

## 4.7 Paso 7: Desplegar la Cloud Function

Ejemplo conceptual de despliegue:

```bash
gcloud functions deploy trigger-data-fusion-sales \
  --gen2 \
  --runtime=python312 \
  --region=us-central1 \
  --source=. \
  --entry-point=trigger_data_fusion \
  --trigger-bucket=retail-sales-raw-data \
  --set-env-vars=PROJECT_ID=mi-proyecto,REGION=us-central1,INSTANCE_ID=datafusion-prod,NAMESPACE=default,PIPELINE_NAME=sales_csv_to_bigquery_pipeline
```

### Buenas prácticas
- Configurar timeouts razonables.
- Usar secretos o variables de entorno para parámetros sensibles.
- Controlar reintentos para evitar duplicados.

---

## 4.8 Paso 8: Cargar un archivo de prueba

Subir archivo:

```bash
gsutil cp sales_20260330.csv gs://retail-sales-raw-data/incoming/
```

Esto dispara automáticamente:
1. Evento en Cloud Storage.
2. Activación de Cloud Function.
3. Invocación de Data Fusion.
4. Ejecución del pipeline Spark.
5. Carga en BigQuery.

---

## 4.9 Paso 9: Verificar resultado en BigQuery

Consulta ejemplo:

```sql
SELECT
  sale_date,
  store_id,
  COUNT(*) AS total_sales,
  SUM(total_amount) AS total_revenue
FROM `mi-proyecto.retail_analytics.sales_fact`
WHERE sale_date = '2026-03-30'
GROUP BY sale_date, store_id
ORDER BY total_revenue DESC;
```

### Qué se espera
- Solo registros válidos.
- Columnas tipadas correctamente.
- Datos disponibles para BI o analítica avanzada.

---

## 4.10 Paso 10: ¿Cómo optimizar los datos y el proceso?

Aquí está la parte más importante en un entorno real: no basta con que funcione; debe ser eficiente, escalable y con costos controlados.

### A. Optimización de almacenamiento y consulta en BigQuery

#### 1. Particionamiento por fecha
Siempre que el acceso principal sea temporal, particionar por fecha.

Ventajas:
- Menor volumen escaneado.
- Menor costo.
- Mejor rendimiento.

#### 2. Clustering por columnas de filtro frecuente
En este caso:
- `store_id`
- `product_id`
- `payment_method`

Ventajas:
- Mejora filtros selectivos.
- Mejora agregaciones sobre esas dimensiones.

#### 3. Evitar `SELECT *`
Malo:

```sql
SELECT * FROM `mi-proyecto.retail_analytics.sales_fact`;
```

Bueno:

```sql
SELECT sale_date, store_id, total_amount
FROM `mi-proyecto.retail_analytics.sales_fact`
WHERE sale_date BETWEEN '2026-03-01' AND '2026-03-31';
```

#### 4. Crear tablas curadas
Separar capas:
- **raw**: copia casi original
- **clean**: validada y tipada
- **curated**: lista para negocio

Esto simplifica auditoría y reproceso.

---

### B. Optimización del pipeline en Data Fusion

#### 1. Procesamiento incremental
No reprocesar todos los archivos históricos.
Procesar solo el archivo nuevo recibido.

#### 2. Validaciones tempranas
Eliminar errores al inicio evita gasto de recursos aguas abajo.

#### 3. Reducir transformaciones innecesarias
Cada transformación en Spark tiene costo.
Conservar solo las que agregan valor real.

#### 4. Ajustar recursos Spark
En cargas grandes, definir memoria y paralelismo de forma correcta.

Ejemplo conceptual:

```text
spark.executor.memory=4g
spark.driver.memory=2g
spark.sql.shuffle.partitions=100
```

No conviene sobredimensionar para cargas pequeñas ni subdimensionar para cargas masivas.

#### 5. Reutilizar pipelines parametrizados
Un pipeline bien parametrizado sirve para múltiples fuentes o fechas sin duplicar lógica.

---

### C. Optimización de la Cloud Function

#### 1. Filtrado por prefijo y extensión
Evita activar pipelines por archivos temporales, logs, `.txt` o archivos erróneos.

#### 2. Idempotencia
Si el mismo evento llega dos veces, la función no debería duplicar cargas.

Estrategias:
- Llevar control en BigQuery o Firestore del `file_name` procesado.
- Usar tabla de auditoría.
- Rechazar archivos ya procesados.

#### 3. Logging estructurado
Registrar:
- nombre del archivo
- hora del evento
- pipeline disparado
- estado
- error si aplica

Esto simplifica soporte y observabilidad.

#### 4. Manejo de errores
Diferenciar:
- error de archivo inválido
- error de autenticación
- error de Data Fusion
- error de BigQuery

---

### D. Optimización de costo

#### 1. Mantener datos y cómputo en la misma región
Evita costos de egreso y reduce latencia.

#### 2. Procesar por lotes razonables
Si llegan miles de microarchivos, conviene consolidar para evitar overhead excesivo.

#### 3. Programar apagado o uso controlado de entornos no productivos
Dev y QA no deben estar corriendo innecesariamente.

#### 4. Usar tablas particionadas y consultas acotadas
Esto impacta directamente el costo en BigQuery.

---

## 4.11 Extensiones reales de este patrón

Este patrón se puede extender fácilmente para:
- Cargar datos de inventario.
- Integrar pedidos de e-commerce.
- Procesar logs IoT.
- Automatizar validaciones de calidad de datos.
- Alimentar modelos de ML en Vertex AI.
- Publicar dashboards en Looker Studio.

También se puede complementar con:
- **Pub/Sub** para desacoplar eventos.
- **Cloud Scheduler** para cargas programadas.
- **Cloud Run** si la lógica de automatización es más compleja que una Function.
- **Dataform o BigQuery SQL** para transformaciones analíticas posteriores.

---

## 4.12 Resumen ejecutivo del flujo

1. Un archivo CSV llega a Cloud Storage.
2. Cloud Function detecta el evento.
3. La función valida archivo y ruta.
4. La función invoca Data Fusion por API.
5. Data Fusion ejecuta ETL sobre Spark.
6. Los datos se limpian, validan y tipan.
7. BigQuery almacena los datos en tabla optimizada.
8. El negocio consume datos más rápido y con menor costo.

---

## 4.13 Qué habilidades demuestra este ejemplo

Este caso demuestra dominio en:
- integración de servicios serverless
- automatización orientada a eventos
- diseño ETL/ELT en GCP
- optimización de BigQuery
- observabilidad y gobernanza operacional
- diseño de pipelines reutilizables y productivos

---

## 4.14 Conclusión

En un escenario real de datos, **Cloud Functions** actúa como mecanismo de activación ligera y orientada a eventos, mientras **Cloud Data Fusion** ejecuta la lógica ETL a escala. La optimización no depende de un único servicio, sino del diseño integral del flujo: almacenamiento correcto, consultas eficientes, validación temprana, procesamiento incremental e idempotencia. Esa combinación es la que convierte un pipeline funcional en una solución realmente productiva y escalable.

