# Ejemplo Paso a Paso: GCP (Salud) en Python
En esta guía, desarrollaremos **un ejemplo de proyectos de datos** de manera detallada y paso a paso, usando servicios de GCP (Google Cloud Platform) para un caso de **salud**. Todo el flujo se implementará en Python (por ejemplo, desde Jupyter Notebooks locales), aprovechando servicios administrados en GCP usaremos **Google Cloud Storage (GCS)**, **BigQuery** (almacenamiento de datos tipo data warehouse) y opcionalmente **Vertex AI** (plataforma de ML). También se mencionarán prácticas de optimización de rendimiento, manejo de grandes volúmenes de datos y la gestión de cargas de trabajo en cada entorno.

**Tabla de Contenido:**

- [Ejemplo 2: Análisis de Salud en GCP (GCS, BigQuery, Vertex AI)](#proyecto2)
- [Configuración del Entorno GCP en Python](#gcp1)
- [Obtención y Preparación del Dataset de Salud](#gcp2)
- [Carga de Datos en Google Cloud Storage](#gcp3)
- [Configuración de BigQuery y Carga de Datos](#gcp4)
- [Consultas SQL Básicas en BigQuery](#gcp5)
- [Optimización de Rendimiento en BigQuery](#gcp6)
- [**(Opcional)** Machine Learning con Vertex AI](#gcp7)

## <a name="xf6811c9fd09d84c1238d190a4a01d672164ae1e" id="proyecto2"></a>Proyecto 2: Análisis de Salud en GCP (GCS, BigQuery, Vertex AI)
**Descripción:** En este segundo proyecto, implementaremos un pipeline enfocado en datos de salud usando GCP. Como ejemplo, podemos usar un dataset de salud pública o clínica obtenido de Kaggle, por ejemplo, un dataset sintético de pacientes con varios atributos (edad, presión arterial, ritmo cardíaco, diagnóstico, etc.) y quizás un resultado (por ejemplo, si tuvieron cierta enfermedad o no). Usaremos **Google Cloud Storage (GCS)** para almacenar los datos, **BigQuery** para cargarlos y hacer consultas SQL a gran escala, optimizando con particiones y clustering, y opcionalmente **Vertex AI** para entrenar un modelo de Machine Learning (por ejemplo, para predecir alguna condición médica) con los datos. Todo orquestado desde Python local usando las librerías de Google Cloud.

<a name="gcp1"></a>
### <a name="configuración-del-entorno-gcp-en-python" id="gcp1"></a>1. Configuración del Entorno GCP en Python
- **Instalar librerías de Google Cloud:** Asegúrate de instalar las bibliotecas necesarias:

```python
  pip install google-cloud-storage google-cloud-bigquery google-cloud-aiplatform
```

- google-cloud-storage nos permite interactuar con GCS desde Python.
- google-cloud-bigquery es el cliente para ejecutar consultas y cargas en BigQuery.
- google-cloud-aiplatform es la SDK de Vertex AI para Python, útil para crear datasets, entrenar modelos, etc.
- **Autenticación en GCP:** Para usar las APIs de Google, debemos autenticarnos. La manera típica es usar un **Service Account** JSON key o Application Default Credentials. Por ejemplo, podemos descargar una clave JSON de servicio con permisos a BigQuery, Storage y Vertex AI, luego:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="ruta/al/archivo-clave.json"
```

  Alternativamente, usar gcloud auth login si se está en un entorno con gcloud. Dentro del código Python, la librería usará esa credencial por defecto.
- **Parámetros de proyecto:** Necesitamos el *ID del proyecto de GCP* y quizá especificar la *ubicación* (región) para BigQuery y Vertex. Ejemplo:

```python
project_id = "mi-proyecto-gcp"
bigquery_dataset_name = "healthcare_analysis"
region = "us-central1"
```

  BigQuery no requiere especificar región en el cliente (usa multi-región default o la del conjunto de datos), pero Vertex AI sí necesita región en algunos llamados.

<a name="gcp2"></a>
### <a name="x8287409858b809ab63b749a6225f564f9266bd5" id="gcp2"></a>2. Obtención y Preparación del Dataset de Salud
- **Seleccionar dataset de salud:** Podemos usar un dataset de Kaggle de salud. Por ejemplo, un *dataset sintético de registros médicos de pacientes*. Supongamos el **Healthcare Dataset** (ficticio) con 10,000 pacientes y columnas como PatientID, Age, Gender, Blood\_Pressure, Heart\_Rate, Cholesterol, Diagnosis, Outcome. El campo Outcome podría ser algo como si el paciente desarrolló cierta enfermedad (1/0) o alguna métrica de resultado.
- **Descargar dataset:** Similar al caso AWS, descargamos el CSV de Kaggle u otra fuente. Obtendremos un archivo patients.csv. Revisamos brevemente su contenido con pandas para verificar esquema:

```python
import pandas as pd
df = pd.read_csv("patients.csv")
print(df.head())
print(df.dtypes)
```

  Supongamos que las columnas son: PatientID (int), Age (int), Gender (string), Blood\_Pressure (int), Heart\_Rate (int), Cholesterol (int), Diagnosis (string), Outcome (int).
- **Opcional - división o preprocesamiento:** Si el dataset es muy grande, podríamos partirlo en archivos múltiples como hicimos antes para cargas paralelas. BigQuery puede cargar directamente archivos CSV grandes, pero también se beneficia de dividir la carga en varios ficheros para paralelismo. Dado que 10k registros es pequeño, no hace falta, pero si fueran millones conviene dividir en varios archivos de, digamos, 100 MB cada uno para acelerar la carga (BigQuery sugiere < 256 MB por fichero sin comprimir para paralelizar mejor[\[3\]](https://cloud.google.com/blog/products/data-analytics/performance-considerations-for-loading-data-into-bigquery#:~:text=test%20and%20the%20number%20of,a%20summary%20of%20our%20findings)).

<a name="gcp3"></a>
### <a name="x82136558076dd37fc7ceb8c7445fbf7e9b22f3e" id="gcp3"></a>3. Carga de Datos en Google Cloud Storage (GCS)
- **Crear bucket en GCS:** Utilizamos el cliente de Storage para crear un bucket donde poneremos los datos. Debe tener un nombre único global:

```python
from google.cloud import storage
storage_client = storage.Client(project=project_id)
bucket_name = "datos-salud-analisis"
bucket = storage_client.create_bucket(bucket_name, location="US")  # multi-region US por ejemplo
print(f"Bucket {bucket.name} creado.")
```

  Podemos alternativamente usar la consola GCP para crear el bucket. Asegúrate de que la cuenta de servicio tiene permiso Storage Admin o al menos Storage Object Admin.
- **Subir archivo CSV a GCS:**

```python
bucket = storage_client.bucket(bucket_name)
blob = bucket.blob("datasets/patients.csv")
blob.upload_from_filename("patients.csv")
print("Archivo cargado en GCS.")
```

  Ahora el archivo está en gs://datos-salud-analisis/datasets/patients.csv. Si tuviéramos múltiples archivos, podríamos subirlos todos o usar una herramienta como gsutil cp también.
- **Verificación:** Podemos listar objetos:

```python
for blob in bucket.list_blobs(prefix="datasets/"):
    print(blob.name)
```
  Debe mostrar datasets/patients.csv.

GCS es análogo a S3 en este contexto: almacenamos los datos brutos allí para que BigQuery los pueda tomar.

<a name="gcp4"></a>
### <a name="x7ae6bf0c5cb7dab1285df3f4c6266c7cc9c27b8" id="gcp4"></a>4. Configuración de BigQuery y Carga de Datos
- **Crear *dataset* en BigQuery:** En BigQuery, un *dataset* es un contenedor de tablas dentro de un proyecto. Creamos uno llamado healthcare\_analysis (si no existe):

```python
from google.cloud import bigquery
bq_client = bigquery.Client(project=project_id)
dataset_ref = bigquery.Dataset(f"{project_id}.{bigquery_dataset_name}")
dataset_ref.location = "US"
dataset = bq_client.create_dataset(dataset_ref, exists_ok=True)
print(f"Dataset {dataset.dataset_id} listo.")
```

  Aquí ubicamos el dataset en "US" (debe ser coherente con la ubicación de GCS bucket para cargas, e.g., ambos en US multi-region).
- **Definir esquema de la tabla:** Podemos dejar que BigQuery auto-detecte el esquema al cargar CSV, pero es educativo definirlo manualmente para asegurarnos:

```python
schema = [
    bigquery.SchemaField("PatientID", "INTEGER"),
    bigquery.SchemaField("Age", "INTEGER"),
    bigquery.SchemaField("Gender", "STRING"),
    bigquery.SchemaField("Blood_Pressure", "INTEGER"),
    bigquery.SchemaField("Heart_Rate", "INTEGER"),
    bigquery.SchemaField("Cholesterol", "INTEGER"),
    bigquery.SchemaField("Diagnosis", "STRING"),
    bigquery.SchemaField("Outcome", "INTEGER"),
]
table_ref = bigquery.Table(f"{project_id}.{bigquery_dataset_name}.patients", schema=schema)
table = bq_client.create_table(table_ref, exists_ok=True)
```

  Esto prepara una tabla vacía patients con esas columnas.
- **Cargar datos desde GCS a BigQuery:** Utilizamos un *Load Job* de BigQuery apuntando al archivo en GCS:

```python
job_config = bigquery.LoadJobConfig(source_format=bigquery.SourceFormat.CSV, skip_leading_rows=1, schema=schema)
uri = f"gs://{bucket_name}/datasets/patients.csv"
load_job = bq_client.load_table_from_uri(uri, table_ref, job_config=job_config)
load_job.result()  # esperar a que termine
```

  Esto leerá el CSV desde GCS y lo cargará en la tabla BigQuery aplicando el esquema. skip\_leading\_rows=1 ignora la fila de encabezados CSV.

Si tuviéramos múltiples archivos, podríamos usar comodines en la URI (p.ej. gs://bucket/datasets/patients\_\*.csv) o pasar una lista de URIs al método. BigQuery cargará en paralelo múltiples ficheros si se especifican.

- **Verificar carga:** Podemos consultar la cantidad de filas cargadas:

```python
table = bq_client.get_table(table_ref)
print(f"Filas cargadas: {table.num_rows}")
```

  Debería mostrar 10,000 si ese era el tamaño.
- **Costo y rendimiento de la carga:** BigQuery no tiene un costo por carga usando load jobs desde GCS (son gratuitos), y es muy rápido. Internamente convierte los datos a su formato **colunar optimizado (Capacitor)** para almacenarlos. Los diferentes formatos de archivo influyen en la velocidad: **Parquet/Avro** suelen ser más eficientes que CSV porque BigQuery puede saltar el parsing pesado y ya vienen columnar/comprimidos. Para cargas muy grandes, preferir formatos columnar o al menos CSV comprimido y particionado. En general, Parquet ofrece **mejor compresión y consultas más rápidas** que CSV para big data[\[20\]](https://last9.io/blog/parquet-vs-csv/#:~:text=Parquet%20vs%20CSV%3A%20Which%20Format,efficient%20storage%20for%20large%20datasets), ya que BigQuery solo leerá las columnas necesarias, logrando análisis hasta *10-100 veces más rápidos* que con formatos fila a fila como CSV[\[21\]](https://www.kaggle.com/discussions/getting-started/610945#:~:text=Kaggle%20www,without%20compression%20or%20schema%20information). (En nuestro ejemplo no convertimos a Parquet por simplicidad, pero es algo a considerar en entornos de producción de gran escala).

<a name="gcp5"></a>
### <a name="consultas-sql-básicas-en-bigquery" id="gcp5"></a>5. Consultas SQL Básicas en BigQuery
Una vez los datos están en BigQuery, podemos analizarlos usando SQL estándar. BigQuery permite ejecutar SQL directamente desde Python con la librería, o desde su consola web. Usaremos Python para integrarlo en nuestro flujo:

- **Ejemplo 1: Estadísticas básicas de pacientes:**\
  ¿Cuál es la presión arterial media y colesterol medio de los pacientes, desglosado por diagnóstico?

```python
query = """
    SELECT Diagnosis, 
           AVG(Blood_Pressure) AS avg_bp, 
           AVG(Cholesterol) AS avg_chol 
    FROM `mi-proyecto-gcp.healthcare_analysis.patients`
    GROUP BY Diagnosis;
"""
result = bq_client.query(query).result()
for row in result:
    print(row)
```

  Esto agrupa por el campo categórico Diagnosis (podría ser distintos padecimientos) y calcula promedios. BigQuery distribuirá este cálculo internamente. Si el dataset fuera enorme, BigQuery asigna slots de procesamiento automáticamente y escala sin que nosotros tengamos que gestionar servidores.
- **Ejemplo 2: Conteo de pacientes por rango de edad:**\
  Podemos usar SQL estándar con CASE o funciones:

```python
query = """
    SELECT 
      CASE 
        WHEN Age < 30 THEN 'Under30'
        WHEN Age BETWEEN 30 AND 60 THEN '30to60'
        ELSE 'Above60'
      END AS age_group,
      COUNT(*) AS num_patients
    FROM `mi-proyecto-gcp.healthcare_analysis.patients`
    GROUP BY age_group;
"""
df = bq_client.query(query).to_dataframe()
print(df)
```

  Aquí convertimos directamente el resultado a un DataFrame pandas usando to\_dataframe(), lo que facilita graficar luego si quisiéramos. BigQuery soporta muchas funciones (incluso de ML con BigQuery ML, pero nos centraremos en Vertex AI luego).
- **Ejemplo 3: Consulta con filtrado:**\
  Supongamos que queremos filtrar pacientes con colesterol alto:

```python
query = """
    SELECT PatientID, Age, Cholesterol, Outcome
    FROM `mi-proyecto-gcp.healthcare_analysis.patients`
    WHERE Cholesterol > 240
    ORDER BY Cholesterol DESC
    LIMIT 10;
"""
high_chol = bq_client.query(query).to_dataframe()
```

  Esto nos da los 10 pacientes con colesterol más alto, por ejemplo, junto con su resultado de salud.

**Notas de BigQuery:** BigQuery cobra por la cantidad de datos procesados en cada consulta (bytes leídos). Por ello, conviene **proyectar solo las columnas necesarias** en vez de SELECT \* y usar filtros que aprovechen **particiones** para reducir el escaneo (ver optimización). BigQuery es *serverless*, no administramos infraestructura; podemos lanzar consultas enormes y Google aprovisiona los recursos necesarios bajo el capó (con ciertas cuotas). Las consultas pueden manejar **terabytes de datos en segundos** gracias a la paralelización masiva.

Además, BigQuery mantiene caches: si repetimos exactamente la misma consulta y los datos no han cambiado, suele devolver el resultado de cache sin costo adicional.

<a name="gcp6"></a>
### <a name="optimización-de-rendimiento-en-bigquery" id="gcp6"></a>6. Optimización de Rendimiento en BigQuery
Para grandes volúmenes en BigQuery (imaginemos datos de salud de millones de pacientes o registros diarios de hospitales), podemos aplicar técnicas para **mejorar el rendimiento y minimizar costos**:

- **Particionar tablas:** BigQuery permite particionar nativamente por columna (normalmente por fecha) o por *ingestion time*. Si nuestro dataset tuviera un campo de fecha (ej: fecha de admisión del paciente), podríamos particionar la tabla por esa columna. Esto hace que internamente BigQuery divida el almacenamiento por particiones (p. ej. por día, mes o año). Al hacer consultas que filtren por esa fecha, **solo se escanean las particiones relevantes**, reduciendo datos leídos y acelerando resultados[\[22\]](https://cloud.google.com/blog/products/data-analytics/skip-the-maintenance-speed-up-queries-with-bigquerys-clustering#:~:text=Partition%20and%20clustering%20pruning%20in,BigQuery). En nuestro dataset de pacientes, si tuviéramos un campo VisitDate, podríamos definir la tabla particionada por VisitDate diariamente. Como regla general: *“usa particiones mensuales o anuales junto con clustering para lograr mejor performance”* cuando los datos históricos son muy amplios[\[23\]](https://docs.cloud.google.com/bigquery/docs/partitioned-tables#:~:text=In%20these%20scenarios%2C%20use%20monthly,For%20more). Para tablas más pequeñas, la partición no aporta mucho, pero para >1GB por día de datos sí es muy útil.
- **Clustering de tablas:** El **clustering** en BigQuery es similar a las sort keys de Redshift. Podemos definir hasta 4 columnas de clustering en una tabla. BigQuery almacenará los datos ordenados según esos campos dentro de cada partición (o en toda la tabla si no hay partición)[\[24\]](https://cloud.google.com/blog/products/data-analytics/skip-the-maintenance-speed-up-queries-with-bigquerys-clustering#:~:text=Clustering%20is%20supported%20on%20primitive,STRING%2C%20DATE%2C%20GEOGRAPHY%2C%20and%20TIMESTAMP)[\[25\]](https://cloud.google.com/blog/products/data-analytics/skip-the-maintenance-speed-up-queries-with-bigquerys-clustering#:~:text=Data%20in%20a%20BigQuery%20table,is%20written%20to%20a%20table). ¿Por qué sirve? Porque BigQuery conoce el rango de valores en cada bloque de almacenamiento para esas columnas clusterizadas[\[26\]](https://cloud.google.com/blog/products/data-analytics/skip-the-maintenance-speed-up-queries-with-bigquerys-clustering#:~:text=In%20this%20query%2C%20BigQuery%20first,as%20between%2010301%20and%2010400). Así, si haces una consulta filtrando por una de esas columnas o prefijo de ellas, BigQuery **prunea** los bloques que no contienen valores en ese rango. Resultado: menos datos leídos, consultas más rápidas. Por ejemplo, podríamos clusterizar nuestra tabla de pacientes por Diagnosis y luego Age. Si consultamos solo pacientes con Diagnosis = 'Diabetes', BigQuery saltará bloques que solo tienen otras diagnosis. También clustering ayuda en agregaciones por esas columnas, ya que los datos iguales quedan cercanos, reduciendo shuffles[\[27\]](https://cloud.google.com/blog/products/data-analytics/skip-the-maintenance-speed-up-queries-with-bigquerys-clustering#:~:text=Clustering%20improves%20performance%20of%20aggregation,queries).

En general, la recomendación de Google es usar partición por fecha (si aplica) y clustering por campos frecuentemente filtrados o agrupados[\[28\]](https://cloud.google.com/blog/products/data-analytics/skip-the-maintenance-speed-up-queries-with-bigquerys-clustering#:~:text=To%20get%20the%20most%20out,clustered%20tables%20for%20best%20performance). Además, BigQuery tiene **re-clustering automático**: a medida que ingresan nuevos datos desordenados, BigQuery en segundo plano los reordena para mantener la eficiencia, *sin intervención manual[\[29\]](https://cloud.google.com/blog/products/data-analytics/skip-the-maintenance-speed-up-queries-with-bigquerys-clustering#:~:text=partitioning%20%20and%20%2045,clustered%20tables%20for%20best%20performance)[\[30\]](https://cloud.google.com/blog/products/data-analytics/skip-the-maintenance-speed-up-queries-with-bigquerys-clustering#:~:text=Maintaining%20table%20clustering)*. Esto es valioso, ya que en otros data warehouses el reordenamiento podría ser manual; BigQuery lo hace autónomamente.

- **Prácticas de consulta eficientes:** Más allá del esquema, al escribir consultas hay que:
- Seleccionar solo columnas necesarias (evitar SELECT \* en tablas muy anchas).
- Usar filtros que aprovechen partición (si la tabla está particionada por fecha, siempre incluir ese filtro de fecha en WHERE).
- Tener cuidado con *joins* muy grandes; a veces conviene pre-agregar datos o usar instrucciones analíticas.
- BigQuery puede recomendar particiones o clusterings si detecta patrones; en la interfaz existen *Insights* que sugieren “añade partición en esta columna” si ven muchas consultas filtrando por ella[\[31\]](https://docs.cloud.google.com/bigquery/docs/manage-partition-cluster-recommendations#:~:text=Manage%20partition%20and%20cluster%20recommendations,can%20apply%20partition%20and).
- Considerar **materialized views** en BigQuery también, para casos de agregaciones repetidas. BigQuery MV actualiza automáticamente al insertar nuevos datos (no en tiempo real, pero pronto después).
- Para enormes conjuntos, BigQuery permite usar *approximate functions* (HLL sketches) para cálculos aproximados rápidos (por ejemplo, APPROX\_COUNT\_DISTINCT).
- **Formatos de almacenamiento y extracción:** Como mencionamos, usar formatos columnares (Parquet, ORC, Avro) en GCS y luego federar o cargar a BigQuery puede ahorrar costos y tiempo. En algunos casos, podríamos incluso dejar los datos en GCS y usar **BigQuery External Tables** sobre GCS (similar a Spectrum de Redshift). Sin embargo, las consultas sobre external data suelen ser más lentas que datos nativos en BigQuery, y se cobra por los bytes leídos de Cloud Storage. Mejor cargar a BigQuery si se va a consultar seguido.
- **Escalabilidad:** BigQuery se autoescala, pero tiene cuotas. Si necesitamos mayor rendimiento, existe la opción de **Reservar Slots** o usar BigQuery BI Engine para caches en memoria. Pero en la mayoría de escenarios, BigQuery provee rendimiento excelente out-of-the-box sin tunear. Por ejemplo, empresas analizan **petabytes** de datos de clics con BigQuery en segundos-minutos, pagando solo por lo que escanean.
- **Costos:** Optimizar rendimiento suele optimizar costo, porque menos datos leídos = menos facturación. Particionar y clusterizar son estrategias clave para ello[\[32\]](https://cloud.google.com/blog/products/data-analytics/skip-the-maintenance-speed-up-queries-with-bigquerys-clustering#:~:text=You%E2%80%99ll%20find%20partitioning%20and%20clustering,less%20thing%20to%20worry%20about). También eliminar datos no necesarios (BigQuery ahora soporta *Time to Live* en particiones para borrar datos antiguos automáticamente).

En resumen, BigQuery ofrece **particionamiento y clustering** como potentes herramientas para **mejorar drásticamente el performance y costo** de consultas en grandes tablas[\[28\]](https://cloud.google.com/blog/products/data-analytics/skip-the-maintenance-speed-up-queries-with-bigquerys-clustering#:~:text=To%20get%20the%20most%20out,clustered%20tables%20for%20best%20performance). Un diseño cuidadoso del esquema físico, junto con las prácticas de consulta adecuadas, permitirá manejar **grandes volúmenes de datos clínicos** eficientemente, manteniendo tiempos de respuesta bajos incluso a escala de terabytes.

<a name="gcp7"></a>
### <a name="opcional-machine-learning-con-vertex-ai" id="gcp7"></a>7. **(Opcional)** Machine Learning con Vertex AI
Para agregar una capa de Machine Learning al proyecto de salud, usaremos **Vertex AI**, la plataforma unificada de Google Cloud para entrenar y desplegar modelos ML. Supongamos que queremos construir un modelo que, basado en los datos de un paciente, prediga el Outcome (por ejemplo, si el paciente tendrá cierta complicación de salud o la probabilidad de rehospitalización).

Vertex AI admite múltiples enfoques: - **AutoML**: entrenar un modelo automáticamente con solo proporcionarle los datos y la columna objetivo. - **Custom Training**: subir un script de entrenamiento (ej. en TensorFlow, scikit-learn, PyTorch, etc.) y Vertex lo ejecuta en máquinas en la nube. - **BigQuery ML** (dentro de BigQuery, aunque técnicamente no es Vertex AI, vale mencionar que podríamos, por ejemplo, hacer CREATE MODEL en SQL para obtener un modelo de regresión logística en el propio BigQuery).

Aquí haremos un ejemplo con AutoML para brevedad, ya que requiere mínimos pasos de código y Vertex se encarga de todo (entrenará varios modelos bajo el capó y nos dará el mejor).

Pasos para Vertex AI AutoML (Tabular):

- **Crear conjunto de datos de Vertex AI:** Vertex AI tiene entidades llamadas Dataset para administrar datos de entrenamiento, especialmente para AutoML. Podemos crear un dataset tabular a partir de nuestra tabla de BigQuery:

```python
from google.cloud import aiplatform
aiplatform.init(project=project_id, location=region)
dataset = aiplatform.TabularDataset.create(
    display_name="Patients Dataset",
    bq_source=f"bq://{project_id}.{bigquery_dataset_name}.patients"
)
dataset.wait()
print(f"Dataset de Vertex creado: {dataset.resource_name}")
```

  Esto le indica a Vertex AI que use los datos de BigQuery en patients como entrada. Vertex AI no moverá todos los datos de inmediato, pero registrará la fuente.
- **Entrenar un modelo AutoML de clasificación:** Ahora usamos el método AutoML de Vertex para entrenar un modelo de clasificación binaria (asumimos Outcome es 0/1):

```python
training_job = aiplatform.AutoMLTabularTrainingJob(
    display_name="Outcome Prediction Model",
    optimization_prediction_type="classification",
    optimization_objective="maximize-au-roc"  # por ejemplo, maximizar Area Under ROC
)
model = training_job.run(
    dataset=dataset,
    target_column="Outcome",
    training_fraction_split=0.8,
    validation_fraction_split=0.1,
    test_fraction_split=0.1,
    model_display_name="patients_outcome_model",
    disable_early_stopping=False
)
```

  Aquí especificamos la columna objetivo, y cómo dividir los datos en entrenamiento/validación/test. Vertex AI AutoML probará distintas arquitecturas (p.ej., modelos tipo ensembles de árboles, redes neuronales, etc.) y hyperparametros automáticamente. Este proceso puede tardar desde minutos hasta horas dependiendo del tamaño de datos (para 10k registros será rápido). Al final, model contendrá el modelo entrenado.
- **Evaluar resultados:** Podríamos obtener métricas del modelo:

```python
evaluation = model.list_model_evaluations()[0]
print("Accuracy:", evaluation.metrics.get("accuracy"))
print("AUC:", evaluation.metrics.get("auRoc"))
```

  Vertex guarda las métricas de evaluación en estos objetos. También en la consola GCP podemos ver matrices de confusión, etc.
- **Desplegar el modelo para predicción:** Si queremos disponibilizar este modelo via API, hacemos:

```python
endpoint = model.deploy(machine_type="n1-standard-2", sync=True)
print(f"Endpoint desplegado: {endpoint.resource_name}")
```

  Esto crea un Endpoint en Vertex AI. Similar a SageMaker, ahora tenemos un servicio REST al cual enviar datos de pacientes y obtener predicciones del Outcome. Por ejemplo:

```python
instances = [
    {"Age": 45, "Gender": "M", "Blood_Pressure": 130, "Heart_Rate": 80, "Cholesterol": 250, "Diagnosis": "HeartDisease"}
]
prediction = endpoint.predict(instances)
print("Predicción:", prediction.predictions)
```

  Vertex AI se encarga de formatear la entrada, pasarla al modelo y retornar la inferencia.
- **Alternativa Custom Training:** Cabe mencionar que podríamos en lugar de AutoML haber usado aiplatform.CustomTrainingJob para enviar nuestro propio código de entrenamiento (por ejemplo, un script de TensorFlow que lee datos de BigQuery o GCS). Esto nos daría más control pero requiere escribir más código y configuración (entorno docker, etc.). AutoML simplifica todo a costa de ser una caja negra en cuanto a qué modelo específico entrena.
- **BigQuery ML (breve mención):** Como alternativa a Vertex, GCP ofrece BigQuery ML que nos hubiera permitido, por ejemplo, ejecutar:

```sql
CREATE OR REPLACE MODEL healthcare_analysis.outcome_model
OPTIONS(model_type='logistic_reg') AS
SELECT Age, Gender, Blood_Pressure, Heart_Rate, Cholesterol, Outcome
FROM healthcare_analysis.patients;
```

  Y luego hacer predicciones con una simple consulta SQL. BigQuery ML entrena modelos rápidos en el propio almacén de datos. Sin embargo, Vertex AI suele lograr mayor rendimiento y soporte para más tipos de modelos (y es el camino recomendado para producción).

**Integración con el flujo de datos:** Vertex AI puede tomar datos directamente de BigQuery (como hicimos) o de GCS. En nuestro pipeline, después de analizar los datos con BigQuery, usamos esos mismos datos para generar un modelo predictivo, todo orquestado en Python. Vertex AI complementa a BigQuery permitiendo **llevar los insights al siguiente nivel**, creando un modelo que podría integrarse en una aplicación (por ejemplo, un sistema que ayude a médicos a identificar pacientes de alto riesgo automáticamente).

Finalmente, al terminar, podemos **limpiar recursos** si es un entorno de prueba: borrar el endpoint para no incurrir en costos, y los modelos/datasets en Vertex AI si ya no se usan, así como los buckets o datasets de ejemplo si corresponden.