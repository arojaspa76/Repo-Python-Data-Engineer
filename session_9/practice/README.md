![logo bsg](../images/logobsg.png)

# Certified Python Data Engineer – AWS Data Engineering Pipeline

**Objetivo:**
Crear y automatizar una canalización de datos escalable con **AWS Glue** y **AWS Lambda**, integrando múltiples fuentes de datos, aplicando transformaciones y optimizando el rendimiento bajo las limitaciones del **nivel gratuito de AWS**.

---

## Resultados de aprendizaje (Aplicar y evaluar)
Al finalizar este laboratorio, los estudiantes podrán:
- Diseñar e implementar pipelines ETL con AWS Glue
- Automatizar flujos de trabajo de datos con AWS Lambda y eventos S3
- Aplicar técnicas de rendimiento, escalabilidad y optimización de costos
- Evaluar críticamente las decisiones de arquitectura en pipelines de datos de AWS

---

## Que es AWS glue, AWS Athena, AWS LAmbda?

**AWS glue:**  
Es un servicio de integración de datos completamente administrado, diseñado para facilitar los procesos de ETL (Extracción, Transformación y Carga). Permite descubrir, preparar, mover e integrar datos de múltiples fuentes. Incluye un Catálogo de Datos centralizado para almacenar metadatos y "crawlers" (rastreadores) que infieren automáticamente los esquemas de los datos almacenados, por ejemplo, en Amazon S3.   

**AWS Athena:**  
Es un servicio de consultas interactivas sin servidor que permite analizar datos directamente en Amazon S3 utilizando SQL estándar. Es ideal para análisis de datos ad-hoc, análisis de registros e informes de inteligencia empresarial, ya que no requiere configurar ni administrar ninguna infraestructura de base de datos, y solo se paga por las consultas ejecutadas (por la cantidad de datos escaneados).  

**AWS Lambda:**  
Es un servicio de informática (cómputo) sin servidor que ejecuta código en respuesta a eventos específicos, sin que el usuario tenga que aprovisionar o gestionar servidores. Se utiliza para construir microservicios ligeros, automatizar tareas disparadas por eventos (como la carga de un archivo en S3 o una solicitud a una API), y se factura por el tiempo de ejecución (milisegundos).  

---

## Descripción general de la arquitectura

```
S3 (Zona sin procesar)
│
│ Evento ObjectCreated
▼
AWS Lambda (Orquestación)
│
│ Iniciar trabajo de Glue
▼
AWS Glue (ETL - Spark)
│
▼
S3 (Zona procesada - Parquet)
```

---

## Requisitos previos

### Técnico
- Cuenta de AWS (nivel gratuito)
- Conocimientos básicos de Python
- Conocimientos básicos de SQL
- Familiaridad con S3 e IAM Conceptos

### Servicios de AWS utilizados
- Amazon S3
- AWS Glue (Job + Crawler)
- AWS Lambda
- AWS IAM
- Amazon CloudWatch

---

## Paso 1: Crear buckets de S3

Cree dos buckets:
- `bsg-data-raw`
- `bsg-data-processed`

Suba archivos CSV de muestra a `bsg-data-raw/`.

---

## Paso 2 – Roles de IAM

### Rol de Glue
Políticas de conexión:
- `AWSGlueServiceRole`
- `AmazonS3FullAccess`

### Rol de Lambda
Políticas de conexión:
- `AWSLambdaBasicExecutionRole`
- Política personalizada que permite:
- `glue:StartJobRun`

---

## Paso 3 – Rastreador de AWS Glue

- Origen: `bsg-data-raw`
- Salida: Catálogo de datos de Glue
- Ejecutar el rastreador una vez para inferir el esquema

---

## Paso 4 – Trabajo de AWS Glue (ETL)

### Script de Glue (Python/Spark)

```python
from awsglue.context import GlueContext
from pyspark.context import SparkContext
from awsglue.dynamicframe import DynamicFrame

sc = SparkContext()
glueContext = GlueContext(sc)

source = glueContext.create_dynamic_frame.from_catalog(
database="bsg_db",
table_name="raw_sales"
)

# Convertir a DataFrame para mejorar el rendimiento
df = source.toDF()

# Ejemplos de transformaciones
df_clean = df.filter(df["cantidad"] > 0)

# Agregar columnas de partición
from pyspark.sql.functions import year, month

df_final = df_clean \
.withColumn("año", year("fecha")) \
.withColumn("mes", month("fecha"))

final_dyf = DynamicFrame.fromDF(df_final, glueContext, "final_dyf")

glueContext.write_dynamic_frame.from_options(
frame=final_dyf,
connection_type="s3",
connection_options={
"path": "s3://bsg-data-processed/",
"partitionKeys": ["año", "mes"]
},
format="parquet"
)
```

**Configuración del trabajo de Glue:**
- Versión de Glue: 4.0
- Trabajadores: 2 DPU

---

## Paso 5 – AWS Lambda (Automatización)

### Propósito
Activar automáticamente el trabajo de Glue cuando llega un nuevo archivo a S3.

### Variable de entorno
| Nombre | Valor |
|----|----|
| GLUE_JOB_NAME | bsg-glue-etl-job |

### Código Lambda

```python
import boto3
import os

glue = boto3.client("glue")

GLUE_JOB_NAME = os.environ["GLUE_JOB_NAME"]

def lambda_handler(event, context):
record = event["Records"][0]
bucket = record["s3"]["bucket"]["name"]
key = record["s3"]["object"]["key"]

if not key.endswith(".csv"):
return {"status": "ignored"}

response = glue.start_job_run(JobName=GLUE_JOB_NAME)

return {
"status": "started",
"job_run_id": response["JobRunId"]
}
```

---

## Paso 6: Configurar S3 Desencadenador

- Cubo: `bsg-data-raw`
- Evento: `ObjectCreated`
- Sufijo: `.csv`
- Destino: Función Lambda

---

## Conclusiones clave

- Lambda orquesta, Glue transforma
- La optimización de Spark es importante incluso en servicios gestionados
- El conocimiento de los costos es parte de la excelencia en ingeniería

## Siguientes pasos
[AWS Glue + AWS Lambda](technical_info.md)