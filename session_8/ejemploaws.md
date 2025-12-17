# Ejemplo Paso a Paso: AWS (Finanzas)

En esta guía, desarrollaremos **un ejemplo de Ejemplo de datos** de manera detallada y paso a paso, usando servicios de AWS (Amazon Web Services) para un caso de **finanzas**. Todo el flujo se implementará en Python (por ejemplo, desde Jupyter Notebooks locales), aprovechando servicios administrados en AWS usaremos **Amazon S3** (almacenamiento de objetos), **Amazon Redshift** (almacenamiento de datos tipo data warehouse) y opcionalmente **Amazon SageMaker** (entrenamiento de modelos ML); También se mencionarán prácticas de optimización de rendimiento, manejo de grandes volúmenes de datos y la gestión de cargas de trabajo en cada entorno.

**Tabla de Contenido:**

- [Ejemplo 1: Análisis Financiero en AWS (S3, Redshift, SageMaker)](#Ejemplo1)
- [Configuración del Entorno AWS en Python](#aws1)
- [Obtención y Preparación del Dataset de Finanzas](#aws2)
- [Carga de Datos en Amazon S3](#aws3)
- [Configuración de Amazon Redshift y Carga de Datos](#aws4)
- [Consultas SQL Básicas en Redshift](#aws5)
- [Optimización de Rendimiento en Redshift](#aws6)
- [**(Opcional)** Machine Learning con Amazon SageMaker](#aws7)

<a name="Ejemplo1"></a>
## <a name="xde3792481777e37c6bdf7d1ca9a0a9177df9941" id="Ejemplo1"></a>Ejemplo 1: Análisis Financiero en AWS (S3, Redshift, SageMaker)
**Descripción:** En este Ejemplo, implementaremos un pipeline de datos financiero en AWS. Usaremos un dataset de finanzas (por ejemplo, transacciones financieras, precios de acciones, o riesgo crediticio) obtenido de Kaggle u otra fuente abierta. El flujo será: almacenar los datos en bruto en Amazon S3, cargarlos en Amazon Redshift para ejecutar consultas SQL analíticas, optimizar el rendimiento en Redshift para manejo de gran volumen, y opcionalmente entrenar un modelo de Machine Learning con SageMaker (por ejemplo, un modelo de predicción de riesgo crediticio o precios) usando los datos preparados. Todo se realizará controlando los servicios desde código Python local usando las SDKs correspondientes.
### <a name="configuración-del-entorno-aws-en-python" id="aws1"></a>1. Configuración del Entorno AWS en Python
- **Instalar SDKs de AWS:** Antes de comenzar, debemos asegurarnos de tener instaladas las bibliotecas de AWS para Python. En particular, instalaremos boto3 (SDK oficial de AWS para Python) y otros clientes necesarios. Por ejemplo, en una celda de Jupyter Notebook o en la terminal:
```python
  pip install boto3 psycopg2-binary awswrangler
```
- boto3 nos permitirá interactuar con S3, Redshift y otros servicios desde Python.
- psycopg2-binary es un driver PostgreSQL que nos servirá para conectarnos a Redshift (ya que Redshift es compatible con PostgreSQL).
- awswrangler (opcional) es una librería de AWS Labs que facilita la interacción con datos en AWS (por ejemplo, leer de Redshift a Pandas, etc.)[\[1\]](https://sagemaker-examples.readthedocs.io/en/latest/ingest_data/ingest-with-aws-services/ingest_data_with_Redshift.html#:~:text=).
- **Configuración de credenciales:** Configuramos las credenciales de AWS (Access Key y Secret Key) y la región. Esto puede hacerse mediante variables de entorno, archivos de configuración (~/.aws/credentials) o directamente en el código:

```python
import boto3
boto3.setup_default_session(region_name="us-east-1")
```
  También podemos usar aws configure por CLI para guardar las credenciales. Asegúrate de tener permisos adecuados para S3 y Redshift.
- **Roles de IAM (si se usa SageMaker o Redshift Spectrum):** Si planeamos usar SageMaker o ciertas características avanzadas, necesitaremos roles de IAM con permisos. Por ejemplo, un rol de SageMaker que permita acceso a S3, y un rol de Redshift que permita lectura de S3 (para COPY o Spectrum). En este tutorial asumiremos que tenemos los permisos necesarios configurados.
### <a name="x7124c2c02c29bbfedc7a9278c5ff7a75e81aee4" id="aws2"></a>2. Obtención y Preparación del Dataset de Finanzas
- **Seleccionar dataset de finanzas:** Podemos utilizar un dataset público de Kaggle. Por ejemplo, un dataset de transacciones financieras o crediticias. Supongamos que elegimos un *dataset sintético de transacciones financieras* que contenga registros de transacciones con campos como TransactionID, UserID, Amount, Timestamp, Merchant, etc., y quizá otro dataset de identidad de usuarios (simulando un caso de fraude). *(Un ejemplo es el dataset de fraude financiero IEEE-CIS o algún dataset de transacciones sintéticas.)* Este dataset puede tener decenas de miles o millones de registros para simular un volumen grande.
- **Descargar dataset:** Usamos la API de Kaggle o descargamos manualmente el CSV. Si usamos la API de Kaggle, debemos tener su token configurado. Otra opción es descargar desde una URL si está disponible. Supondremos que ya tenemos un archivo CSV llamado transactions.csv con nuestras transacciones financieras.
- **Inspeccionar y limpiar datos (localmente):** Antes de cargar a la nube, es útil inspeccionar brevemente el dataset con pandas:

```python
import pandas as pd
df = pd.read_csv("transactions.csv")
print(df.head())
print(df.shape)
```
  Nos aseguramos de que el esquema (columnas y tipos de datos) sea conocido para crear la tabla en Redshift. También podríamos dividir el CSV en varios archivos más pequeños si es muy grande, lo cual es recomendable para paralelismo al cargar en Redshift (ver siguiente sección).
### <a name="carga-de-datos-en-amazon-s3" id="aws3"></a>3. Carga de Datos en Amazon S3
- **Crear un bucket S3:** Con boto3 podemos crear un bucket donde alojaremos los datos:
```python
s3 = boto3.client('s3')
bucket_name = "mi-bucket-finanzas-datos"
s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': 'us-east-1'})
```

  Verificamos que el bucket se creó. (También se puede hacer desde la consola web de AWS).
- **Subir archivos CSV a S3:** Subimos el archivo (o archivos) CSV al bucket. Si dividimos el dataset en múltiples archivos (ej. transactions\_part1.csv, transactions\_part2.csv, etc.), la carga a Redshift será más rápida al paralelizarse. Aquí un ejemplo de carga:

```python
s3.upload_file("transactions.csv", bucket_name, "datasets/transactions.csv")
```
  Tras esto, nuestro dataset estará disponible en la ruta s3://mi-bucket-finanzas-datos/datasets/transactions.csv.

**¿Por qué múltiples archivos?** Redshift puede cargar en paralelo desde S3 cuando se proporcionan *múltiples archivos*, aprovechando su arquitectura MPP (procesamiento masivamente paralelo). Es una **buena práctica** partir archivos grandes en trozos de, por ejemplo, < 256 MB cada uno, para maximizar el throughput de carga[\[2\]](https://www.sitepoint.com/import-data-into-redshift-using-the-copy-command/#:~:text=optimal%20performance%20and%20efficiency,speed%20up%20the%20loading%20process)[\[3\]](https://cloud.google.com/blog/products/data-analytics/performance-considerations-for-loading-data-into-bigquery#:~:text=test%20and%20the%20number%20of,a%20summary%20of%20our%20findings). En general, usar el comando COPY (en vez de inserts secuenciales) y archivos comprimidos acelera enormemente la ingesta de datos a Redshift[\[2\]](https://www.sitepoint.com/import-data-into-redshift-using-the-copy-command/#:~:text=optimal%20performance%20and%20efficiency,speed%20up%20the%20loading%20process).
### <a name="x3812aac4f7b54ea03d1a68f385b521708262fc4" id="aws4"></a>4. Configuración de Amazon Redshift y Carga de Datos
- **Crear un cluster Redshift:** Podemos crear un cluster Redshift desde la consola de AWS, especificando el número de nodos, tipo de nodo, etc., o usar boto3:

```python
redshift = boto3.client('redshift')
response = redshift.create_cluster(
    ClusterIdentifier='cluster-finanzas',
    NodeType='dc2.large',
    MasterUsername='awsuser',
    MasterUserPassword='MyPassword123',
    NumberOfNodes=2,  # por ejemplo, 2 nodos
    IamRoles=['arn:aws:iam::...:role/RedshiftS3AccessRole']  # Rol IAM con acceso a S3
)
```
  *Nota:* Crear el cluster puede tardar varios minutos. Asegúrate de tener el rol IAM que permita al cluster leer de S3 para el COPY (puedes adjuntar la política AmazonS3ReadOnlyAccess o similar al rol). Si este paso es complejo, se puede asumir que el cluster ya existe y centrarse en la carga y consultas.
- **Obtener detalles de conexión:** Una vez activo el cluster, necesitaremos el *endpoint* de Redshift, el puerto (por defecto 5439) y el nombre de la base de datos por defecto (por defecto dev). Por ejemplo, endpoint: cluster-finanzas.abc123xyz.us-east-1.redshift.amazonaws.com:5439/dev. También asegurarse de que la IP desde donde ejecutamos Python tenga acceso (ver reglas de seguridad/VPC).
- **Conectar desde Python a Redshift:** Usamos psycopg2 o SQLAlchemy para conectarnos:

```python
import psycopg2
conn = psycopg2.connect(
    host="cluster-finanzas.abc123xyz.us-east-1.redshift.amazonaws.com",
    port=5439,
    dbname="dev",
    user="awsuser",
    password="MyPassword123"
)
cursor = conn.cursor()
```

  Si la conexión es exitosa, ya podemos ejecutar comandos SQL mediante cursor.execute("SQL...").
- **Crear tabla en Redshift:** Creamos una tabla acorde al esquema del CSV. Supongamos que nuestro CSV de transacciones tiene columnas (TransactionID, UserID, Amount, Timestamp, Merchant, Category, FraudFlag). Podemos crear la tabla en Redshift:

```sql
CREATE TABLE financial.transactions (
    TransactionID VARCHAR(50),
    UserID VARCHAR(50),
    Amount DECIMAL(12,2),
    Timestamp TIMESTAMP,
    Merchant VARCHAR(100),
    Category VARCHAR(50),
    FraudFlag BOOLEAN
);
```

  Ejecutamos esto con cursor.execute(sql) desde Python.
- **Cargar datos con COPY desde S3:** Ahora utilizamos el comando SQL COPY de Redshift para cargar los datos del CSV en la tabla. El comando COPY lee directamente de S3 en paralelo:

```sql
COPY financial.transactions
FROM 's3://mi-bucket-finanzas-datos/datasets/transactions.csv'
IAM_ROLE 'arn:aws:iam::...:role/RedshiftS3AccessRole'
CSV
IGNOREHEADER 1;
```

  Detalles:
- Indicamos la ruta S3 del archivo (o podemos usar un patrón, por ejemplo .../datasets/transactions\_part\*.csv para múltiples archivos).
- Proveemos el ARN del rol IAM que Redshift usará para leer S3.
- Especificamos que el formato es CSV y que ignore la primera fila de encabezados.\
  Este comando automáticamente leerá y distribuirá los datos en los nodos de Redshift. Redshift **aprovecha su arquitectura MPP** para cargar varios archivos a la vez; por eso, dividir el dataset en archivos múltiples mejora la velocidad de carga[\[2\]](https://www.sitepoint.com/import-data-into-redshift-using-the-copy-command/#:~:text=optimal%20performance%20and%20efficiency,speed%20up%20the%20loading%20process). También es aconsejable comprimir los archivos (p.ej. en GZIP) para reducir el tiempo de transferencia; COPY descomprime automáticamente si se indica (CSV GZIP por ejemplo)[\[2\]](https://www.sitepoint.com/import-data-into-redshift-using-the-copy-command/#:~:text=optimal%20performance%20and%20efficiency,speed%20up%20the%20loading%20process).
- **Verificar carga:** Tras ejecutar COPY (puede tomar tiempo según tamaño de datos), comprobamos cuántas filas se cargaron:
```sql
  SELECT COUNT(\*) FROM financial.transactions;
```

  Esto debería devolver el número de registros del CSV. Si hubo errores, Redshift tiene la tabla de sistema stl\_load\_errors que se puede consultar para diagnosticar[\[4\]](https://www.sitepoint.com/import-data-into-redshift-using-the-copy-command/#:~:text=If%20you%20get%20an%20error,logs%20by%20running%20the%20following).

*aNota:* Si los datos no requieren estar **dentro** de Redshift y prefieres consultas más ad-hoc, otra opción es usar **Redshift Spectrum**, que permite crear **external tables** sobre datos que permanecen en S3 (sin cargarlos completamente)[\[5\]](https://sagemaker-examples.readthedocs.io/en/latest/ingest_data/ingest-with-aws-services/ingest_data_with_Redshift.html#:~:text=Redshift%20Spectrum%20is%20used%20to,connecting%20to%20the%20Athena%20database). Spectrum usa el **AWS Glue Data Catalog** para definir el esquema de los archivos en S3, y luego puedes usar SQL sobre esos datos externos. Esto es útil para análisis de data lakes en S3 sin mover datos a Redshift, aunque puede ser un poco más lento que datos en Redshift local. En nuestro Ejemplo principal cargamos a Redshift para un desempeño óptimo en consultas repetidas, pero es bueno saber que **Redshift Spectrum** existe para consultas sobre datos crudos en S3[\[5\]](https://sagemaker-examples.readthedocs.io/en/latest/ingest_data/ingest-with-aws-services/ingest_data_with_Redshift.html#:~:text=Redshift%20Spectrum%20is%20used%20to,connecting%20to%20the%20Athena%20database).
### <a name="consultas-sql-básicas-en-redshift" id="aws5"></a>5. Consultas SQL Básicas en Redshift
Ahora que los datos financieros están en Redshift, podemos hacer análisis usando SQL. Veamos algunas consultas básicas y cómo ejecutarlas desde Python:

- **Ejemplo 1: Conteo de transacciones y suma total:**\
  Supongamos que queremos saber cuántas transacciones hay en total y la suma de los montos:

```python
cursor.execute("SELECT COUNT(*) AS num_transacciones, SUM(Amount) AS monto_total FROM financial.transactions;")
result = cursor.fetchone()
print(result)  # Por ejemplo, (1000000, 55000000.00)
```
  Esta consulta escaneará toda la tabla. Redshift es capaz de agregaciones eficientes aún con millones de filas gracias a su almacenamiento columnar comprimido y procesamiento distribuido.
- **Ejemplo 2: Top 5 usuarios con más transacciones:**

```python
cursor.execute("""
    SELECT UserID, COUNT(*) AS transacciones
    FROM financial.transactions
    GROUP BY UserID
    ORDER BY transacciones DESC
    LIMIT 5;
""")
for row in cursor.fetchall():
    print(row)
```

  Aquí aprovechamos el poder de Redshift para agrupar datos. Si tenemos sort keys o dist keys adecuadas (ver sección de optimización), estas operaciones pueden ser aún más rápidas.
- **Ejemplo 3: Detección de posibles fraudes (ejemplo sencillo):**\
  Si el campo FraudFlag indica si una transacción fue fraudulenta, podríamos ver el porcentaje de fraudes:

```python
cursor.execute("SELECT AVG(CASE WHEN FraudFlag THEN 1 ELSE 0 END)*100 AS pct_fraude FROM financial.transactions;")
print(cursor.fetchone()[0], "%")
```

  Redshift soporta funciones de ventana, subconsultas, JOINs complejos, etc., similares a cualquier base de datos relacional, pero optimizado para análisis de grandes volúmenes. De hecho, Redshift puede manejar petabytes de datos distribuyendo el almacenamiento en varios nodos y paralelizando los cálculos[\[6\]](https://sagemaker-examples.readthedocs.io/en/latest/ingest_data/ingest-with-aws-services/ingest_data_with_Redshift.html#:~:text=Amazon%20Redshift%20is%20a%20fully,depending%20on%20your%20business%20needs).
- **Visualización de resultados:** Desde el notebook podríamos tomar los resultados con pandas.read\_sql\_query para crear DataFrames y graficar si se desea:

```python
import pandas as pd
df_top5 = pd.read_sql_query("SELECT UserID, COUNT(*) as transacciones FROM financial.transactions GROUP BY UserID ORDER BY transacciones DESC LIMIT 5;", conn)
df_top5.plot.bar(x='UserID', y='transacciones')
```

  Esto permitiría ver, por ejemplo, los 5 usuarios con más transacciones en un gráfico de barras.
### <a name="optimización-de-rendimiento-en-redshift" id="aws6"></a>6. Optimización de Rendimiento en Redshift
A medida que los datos crecen (imaginemos que en vez de millones, tenemos **miles de millones de filas**), es crucial optimizar Redshift para mantener consultas rápidas y eficiente manejo de recursos. Algunas técnicas y consideraciones de rendimiento:

- **Distribución de datos (DISTKEY y estilo de distribución):** Al crear tablas, Redshift nos permite especificar cómo distribuir las filas entre nodos. Puede ser **KEY**, **ALL** o **EVEN**. Un buen **DISTKEY** (clave de distribución) es aquel campo por el cual suele uno hacer JOIN entre tablas grandes, de forma que las filas con el mismo valor queden en la misma partícula/nodo. Por ejemplo, si tuviéramos una tabla de usuarios y una de transacciones, podríamos usar UserID como DISTKEY en ambas. Así, al hacer un JOIN por UserID, Redshift no necesita redistribuir datos entre nodos porque los registros correspondientes ya están **colocalizados** en el mismo nodo, acelerando enormemente el join[\[7\]](https://aws.amazon.com/blogs/big-data/top-10-performance-tuning-techniques-for-amazon-redshift/#:~:text=the%20staging%20table%20inherits%20the,the%20query%20uses%20a%20collocated). Redshift Advisor incluso recomienda claves de distribución basadas en el uso[\[8\]](https://aws.amazon.com/blogs/big-data/top-10-performance-tuning-techniques-for-amazon-redshift/#:~:text=Distribution%20key%20recommendation). Para tablas muy pequeñas, DISTSTYLE ALL (replicar en todos los nodos) puede ser útil para evitar movimiento de datos en joins.
- **Claves de ordenamiento (SORTKEY):** Definir un SORTKEY (o varios, hasta compuesto) establece el orden físico de las filas en cada nodo según esa columna. Esto es muy útil para rangos y filtros. Por ejemplo, si muchas consultas filtran por Timestamp (fecha/hora de transacción), conviene hacer de Timestamp el SORTKEY. Así, Redshift puede saltar bloques de datos enteros que no correspondan al rango consultado, leyendo solo el rango necesario (pruning). SORTKEY también beneficia en **aggregations** si se agrupa por esa columna, ya que los datos ya llegan ordenados. En BigQuery esto es análogo a **clustering**, como veremos más adelante.
- **Compresión de columnas:** Redshift automáticamente aplica compresión columnar (codificación) para ahorrar almacenamiento y mejorar I/O. Si cargamos datos con COPY, Redshift puede autoanalizar y aplicar compresiones óptimas (especialmente si usamos COPY con opción COMPUPDATE predeterminada). Asegurarse de comprimir datos en S3 (gzip, etc.) antes de cargar también ayuda en tiempos de carga. Las columnas numéricas se benefician de encodings específicos (LZO, ZSTD, etc.). Redshift ya no requiere que el usuario maneje mucho esto, pero es bueno saberlo. El **Redshift Advisor** también sugiere cambios de sortkey, distkey o encoding si detecta mejoras posibles[\[9\]](https://aws.amazon.com/blogs/big-data/top-10-performance-tuning-techniques-for-amazon-redshift/#:~:text=Amazon%20Redshift%20Advisor%20offers%20recommendations,performance%20and%20decrease%20operating%20costs)[\[8\]](https://aws.amazon.com/blogs/big-data/top-10-performance-tuning-techniques-for-amazon-redshift/#:~:text=Distribution%20key%20recommendation).
- **Estadísticas y mantenimiento:** Tras grandes cargas, Redshift actualiza estadísticas para el optimizador de consultas (por defecto COPY ya actualiza stats a menos que se desactive). Ocasionalmente, borrar filas o insertar muchas filas desordenadas puede fragmentar el orden; en Redshift clásico se usaba VACUUM para reordenar, pero en las nuevas versiones muchas de estas tareas son automáticas. Aún así, monitorear la **tabla de sistema STL/STV** para cuellos de botella (por ejemplo, consultas que hacen mucho **disk spill** o se quedan esperando I/O) puede guiar optimizaciones.
- **Escalabilidad y concurrencia:** Si en ciertos momentos necesitas manejar cargas muy altas (muchos usuarios consultando a la vez o picos de datos), Amazon Redshift ofrece **concurrency scaling** y **elastic resize**. Con *elastic resize* puedes aumentar dinámicamente nodos (por ejemplo, duplicar nodos temporalmente) en minutos y luego reducirlos[\[10\]](https://aws.amazon.com/blogs/big-data/top-10-performance-tuning-techniques-for-amazon-redshift/#:~:text=Tip%20,concurrency%20scaling%20and%20elastic%20resize)[\[11\]](https://aws.amazon.com/blogs/big-data/top-10-performance-tuning-techniques-for-amazon-redshift/#:~:text=Elastic%20resize%20completes%20in%20minutes,AWS%20CLI%29%2C%20or%20API). Con *concurrency scaling*, Redshift puede añadir automáticamente clusters de consulta adicionales en segundo plano para servir consultas concurrentes sin degradar performance, y esto suele no tener costo adicional en la mayoría de casos (tienen ciertos créditos gratuitos)[\[12\]](https://aws.amazon.com/blogs/big-data/top-10-performance-tuning-techniques-for-amazon-redshift/#:~:text=Concurrency%20scaling%20allows%20your%20Amazon,workload%20arriving%20at%20the%20cluster). Estas características permiten manejar picos de trabajo sin sobre-provisionar el cluster permanentemente. La opción *Redshift Serverless* (introducida recientemente) también ajusta recursos automáticamente según la demanda, simplificando la gestión.
- **Consultas materializadas y caches:** Para workloads repetitivos (por ejemplo, un dashboard que ejecuta la misma agregación diariamente), se pueden crear **materialized views** (vistas materializadas) que almacenen resultados precomputados de una consulta compleja[\[13\]](https://aws.amazon.com/blogs/big-data/top-10-performance-tuning-techniques-for-amazon-redshift/#:~:text=To%20view%20the%20total%20amount,group%20by%20city)[\[14\]](https://aws.amazon.com/blogs/big-data/top-10-performance-tuning-techniques-for-amazon-redshift/#:~:text=Now%20we%20can%20query%20the,significantly%20less%20data%20to%20scan). Consultar la vista materializada es mucho más rápido que recalcular la agregación en tablas enormes cada vez. Las views materializadas se pueden refrescar de forma incremental con las nuevas opciones de Redshift, y pueden incluso referenciar datos en S3 (Spectrum) combinados con datos locales[\[15\]](https://aws.amazon.com/blogs/big-data/top-10-performance-tuning-techniques-for-amazon-redshift/#:~:text=You%20can%20also%20extend%20the,explicitly%20refresh%20the%20materialized%20views). Además, Redshift tiene cache de resultados de consultas recientes, así que repetir exactamente la misma consulta podría ser instantáneo si los datos no cambiaron.

En resumen, con **buen diseño de esquemas (distribución/sort keys)**, **carga eficiente (COPY paralelo)[\[2\]](https://www.sitepoint.com/import-data-into-redshift-using-the-copy-command/#:~:text=optimal%20performance%20and%20efficiency,speed%20up%20the%20loading%20process)** y **características de escalado**, Redshift puede manejar **grandes volúmenes** (terabytes a petabytes) manteniendo tiempos de respuesta interactivos para consultas analíticas complejas.

<a name="aws7"></a>
### <a name="xd7e0153557a68ffb2d551d19fd7f61ccd324e08" id="aws7"></a>7. **(Opcional)** Machine Learning con Amazon SageMaker
Para completar el Ejemplo financiero, podemos añadir una etapa de **Machine Learning** usando Amazon SageMaker, que es la plataforma de AWS para construir, entrenar y desplegar modelos de ML a escala. Imaginemos que queremos predecir algo a partir de nuestros datos financieros. Ejemplos: - Predecir probabilidad de fraude de una transacción (FraudFlag) basado en sus atributos. - Predecir el puntaje de crédito o riesgo de un cliente a partir de sus transacciones. - Predecir el volumen de ventas futuro (si tuviéramos datos de series de tiempo financieras).

En nuestro caso, tomemos el ejemplo de **predicción de riesgo de crédito** simplificado: si nuestro dataset tiene una columna que indica si la persona es de **alto riesgo** o **bajo riesgo** (podría derivarse de FraudFlag o de otra fuente), entrenaremos un modelo de clasificación.

Pasos para usar SageMaker desde Python local:

- **Preparar datos de entrenamiento en S3:** SageMaker entrenará en la nube, por lo que necesita acceder a los datos. Ya tenemos nuestros datos en S3. Podemos preparar un archivo CSV específico para entrenamiento, por ejemplo training\_data.csv con características relevantes y la columna objetivo (riesgo alto/bajo). Este podría ser derivado de las transacciones agregadas por usuario junto con datos demográficos (si tuviéramos). Por simplicidad, supongamos que usamos las propias transacciones con la columna FraudFlag como objetivo.
- **Rol de ejecución de SageMaker:** Necesitamos el ARN de un rol de IAM que SageMaker usará para acceder a S3 y otros recursos durante el entrenamiento. Lo obtenemos de la consola (ej. arn:aws:iam::123456789012:role/service-role/AmazonSageMaker-ExecutionRole-20200101T123456).
- **Crear sesión y cliente de SageMaker:** Usamos la librería sagemaker (instalada previamente) para definir el entrenamiento:

```python
import sagemaker
from sagemaker import Session
session = Session()
role = "<ARN de tu SageMaker execution role>"
```
- **Elegir algoritmo/estimator:** SageMaker ofrece algoritmos integrados. Un ejemplo adecuado es el **XGBoost** (muy usado en finanzas para modelos de riesgo). AWS tiene un contenedor integrado para XGBoost. Podemos usar el sagemaker.xgboost.estimator.XGBoost Estimator:

```python
from sagemaker.xgboost.estimator import XGBoost
xgb_estimator = XGBoost(
    entry_point="train.py",  # Podríamos tener un script de entrenamiento personalizado, pero SageMaker XGBoost puede usarse en modo "script mode"
    output_path=f"s3://{bucket_name}/models/",
    role=role,
    instance_count=1,
    instance_type="ml.m5.xlarge",
    framework_version="1.5-1",  # versión de XGBoost container
    py_version="py3",
    hyperparameters={
        "objective": "binary:logistic",
        "num_round": 100
    }
)
```
  Aquí, entry\_point="train.py" sería un script Python que define cómo cargar datos, entrenar y guardar el modelo. Alternativamente, SageMaker permite un *shortcut* si los datos están en formato CSV/LibSVM: se puede omitir el script y solo apuntar al contenedor de XGBoost proporcionando hyperparams. (Para propósitos de ilustración, suponemos un script sencillo que lea el CSV de S3, entrene y guarde modelo, pero SageMaker XGBoost ya maneja mucho de esto automáticamente también).
- **Iniciar el trabajo de entrenamiento:** Debemos especificar la ubicación de los datos de entrenamiento (y validación si tenemos). SageMaker puede leer directamente de S3. Por ejemplo:

```python
train_path = f"s3://{bucket_name}/datasets/transactions.csv"
xgb_estimator.fit({"train": train_path})
```

  Al llamar fit, SageMaker lanzará instancias ML (ml.m5.xlarge en este caso) en la nube, descargará el contenedor de XGBoost, leerá los datos de S3 y ejecutará el entrenamiento[\[16\]](https://sagemaker.readthedocs.io/en/stable/frameworks/xgboost/using_xgboost.html#:~:text=After%20you%20create%20an%20estimator%2C,to%20run%20the%20training%20job). Al finalizar, guardará el modelo entrenado en la ruta S3 especificada (output\_path). Este proceso ocurre completamente en la nube; nuestro notebook simplemente monitorea. Podemos revisar logs de entrenamiento en la consola o CloudWatch.
- **Implantar el modelo en un endpoint (servicio REST):** Una vez entrenado, podemos desplegar el modelo para inferencia en tiempo real:

```python
predictor = xgb_estimator.deploy(initial_instance_count=1, instance_type="ml.m5.large")

# Esto crea un endpoint HTTPS en SageMaker que aloja el modelo XGBoost. El predictor retornado nos permite enviar datos para predicción:

response = predictor.predict(data_for_prediction)
print(response)
```

  Donde data\_for\_prediction puede ser, por ejemplo, un CSV con características de nuevas transacciones o clientes para clasificar. Internamente, deploy lanza una instancia con un servidor que carga el modelo entrenado y espera peticiones[\[17\]](https://sagemaker.readthedocs.io/en/stable/frameworks/xgboost/using_xgboost.html#:~:text=After%20you%20fit%20an%20XGBoost,newly%20created%20model%20in%20SageMaker)[\[18\]](https://sagemaker.readthedocs.io/en/stable/frameworks/xgboost/using_xgboost.html#:~:text=predictor%20%3D%20estimator.deploy%28%20initial_instance_count%3D1%2C%20instance_type%3D,serializer%3Dserializer).
- **Predicciones por lotes (Batch Transform):** Alternativamente, SageMaker ofrece *Batch Transform* para inferencia en lotes grandes, útil si tenemos que puntuar millones de registros de golpe en lugar de peticiones de uno en uno.
- **SageMaker Studio/Notebook:** Cabe mencionar que también podríamos haber realizado todo este flujo de SageMaker dentro de **SageMaker Studio** (un entorno de notebook gestionado por AWS). Incluso SageMaker tiene una herramienta llamada **Data Wrangler** para preparación visual de datos, que se integra con S3, Athena y Redshift[\[19\]](https://aws.amazon.com/blogs/machine-learning/prepare-data-for-predicting-credit-risk-using-amazon-sagemaker-data-wrangler-and-amazon-sagemaker-clarify/#:~:text=Data%20Wrangler%20simplifies%20the%20data,connect%20disparate%20data%20across%20sources). Data Wrangler nos hubiese permitido cargar los datos desde Redshift o S3 directamente, limpiarlos y crear conjuntos de entrenamiento de forma interactiva, y luego exportar el flujo de preparación como un *pipeline*. En este Ejemplo usamos Python puro para mostrar los pasos manuales, pero es bueno saber que existen tales facilidades.

En resumen, con SageMaker hemos entrenado un modelo de ML a partir de nuestros datos financieros. Esto ilustra la integración de los componentes AWS: S3 almacenando datos, Redshift para análisis SQL y SageMaker para ML avanzado. Podemos ahora predecir, por ejemplo, la probabilidad de que una transacción nueva sea fraudulenta, desplegando el modelo y consultándolo desde una aplicación.

**Conclusión del Ejemplo 1:** Hemos creado un pipeline de datos financiero en AWS totalmente en Python: desde la ingesta de datos a S3, la carga y análisis en Redshift, hasta el entrenamiento de un modelo de ML con SageMaker usando los datos. Aplicamos técnicas de optimización (COPY paralelo, distribución/sort keys, escalado) para manejar potencialmente grandes volúmenes de información de manera eficiente.