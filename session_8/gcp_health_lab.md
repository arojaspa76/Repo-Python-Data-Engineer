## Lab de Salud en GCP: Google Cloud Storage, BigQuery y Vertex AI (opcional)

### Objetivo del Laboratorio
Guiar paso a paso al estudiante para crear un pipeline de datos clínicos en Google Cloud usando Python local. Se usarán:

- Almacenamiento en Google Cloud Storage (GCS)
- Análisis de datos con BigQuery
- (**Opcional**) Machine Learning con Vertex AI AutoML

---

### Requisitos previos

- Cuenta GCP activa
- Habilitar APIs de GCS, BigQuery y Vertex AI
- Instalar SDKs:
  ```bash
  pip install google-cloud-storage google-cloud-bigquery google-cloud-aiplatform pandas
  ```

- Configurar autenticación:
  ```bash
  export GOOGLE_APPLICATION_CREDENTIALS="ruta/tu-clave-servicio.json"
  ```

---

### Paso 1: Dataset de Salud

- Usar el dataset `patients.csv` que está en la carpeta [gcp_lab](gcp_lab/patients.csv)
- Inspeccionar localmente:
  ```python
  import pandas as pd
  import tempfile
  import os
  
  # 1. Cargar el CSV original y eliminar la columna 'id'
  df = pd.read_csv("patients.csv")
  df.drop(columns=["id"], inplace=True)

  # 2. Guardar en un archivo temporal sin 'id'
  with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
    temp_path = tmp.name
  
  df.to_csv(temp_path, index=False)
  ```

---

### Paso 2: Subir archivo a Google Cloud Storage

```python
from google.cloud import storage

# 3. Subir el archivo limpio al bucket
client = storage.Client()
bucket_name = "salud-lab-demo"
bucket = client.create_bucket(bucket_name, location="US")
blob = bucket.blob("datasets/patients_no_id.csv")

blob.upload_from_filename(temp_path)

# 4. borrar el archivo temporal
os.remove(temp_path)
```

---

### Paso 3: Crear dataset y tabla en BigQuery

```python
from google.cloud import bigquery

bq_client = bigquery.Client()
project_id = bq_client.project
dataset_id = "healthcare_analysis"
dataset_ref = bigquery.Dataset(f"{project_id}.{dataset_id}")

bq_client.create_dataset(dataset_ref, exists_ok=True)

schema = [
    bigquery.SchemaField("age", "INT64"),
    bigquery.SchemaField("sex", "STRING"),
    bigquery.SchemaField("dataset", "STRING"),
    bigquery.SchemaField("cp", "STRING"),
    bigquery.SchemaField("trestbps", "FLOAT64"),
    bigquery.SchemaField("chol", "FLOAT64"),
    bigquery.SchemaField("fbs", "STRING"),
    bigquery.SchemaField("restecg", "STRING"),
    bigquery.SchemaField("thalch", "FLOAT64"),
    bigquery.SchemaField("exang", "STRING"),
    bigquery.SchemaField("oldpeak", "FLOAT64"),
    bigquery.SchemaField("slope", "STRING"),
    bigquery.SchemaField("ca", "FLOAT64"),
    bigquery.SchemaField("thal", "STRING"),
    bigquery.SchemaField("num", "INT64")    
]

table_id = f"{project_id}.{dataset_id}.patients"
table = bigquery.Table(table_id, schema=schema)
bq_client.create_table(table, exists_ok=True)
```

---

### Paso 4: Cargar datos desde GCS a BigQuery

```python
uri = f"gs://{bucket_name}/datasets/patients_no_id.csv"
job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.CSV,
    skip_leading_rows=1,
    schema=schema,
)
load_job = bq_client.load_table_from_uri(uri, table_id, job_config=job_config)
load_job.result()
```

---

### Paso 5: Consultas SQL en BigQuery

```python
query = f"""
SELECT cp, COUNT(*) as pacientes, AVG(chol) as avg_chol
FROM `{table_id}`
GROUP BY cp
ORDER BY avg_chol DESC
"""
df = bq_client.query(query).to_dataframe()
print(df)
```

---

### Paso 6: Optimización con particionado y clustering (opcional)

Recrear tabla con partición (si hay fecha) y clustering por Diagnosis:
```python
from google.cloud import bigquery
clustering_schema = schema  # mismo esquema
clustering_table = bigquery.Table(table_id, schema=clustering_schema)
clustering_table.clustering_fields = ["cp"]
bq_client.update_table(clustering_table, ["clustering_fields"])
```

---

### Paso 7 (opcional): Modelo con Vertex AI

Antes de usar aiplatform, se debe habilitar la API de Vertex AI si es que aún no se ha habilitado:  

```bash
gcloud services enable aiplatform.googleapis.com
```

```python
from google.cloud import aiplatform
aiplatform.init(project=project_id, location="us-central1")

dataset = aiplatform.TabularDataset.create(
    display_name="DatasetPacientes",
    bq_source=f"bq://{table_id}"
)

training_job = aiplatform.AutoMLTabularTrainingJob(
    display_name="modelo-num",
    optimization_prediction_type="classification",
    optimization_objective="minimize-log-loss"
)

model = training_job.run(
    dataset=dataset,
    target_column="num",
    model_display_name="modelo_outcome_autoML",
    training_fraction_split=0.8,
    validation_fraction_split=0.1,
    test_fraction_split=0.1,
)
```
Si todo ok hasta aqui, el entrenamiento del modelo puede llegar a tomar al menos 1 hora.

---

### Fin del laboratorio

Has implementado un flujo de datos en GCP desde el almacenamiento hasta el análisis en BigQuery y (opcionalmente) entrenamiento de modelo predictivo en Vertex AI.

