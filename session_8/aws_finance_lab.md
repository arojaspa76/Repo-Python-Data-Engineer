## Lab de Finanzas en AWS: Amazon S3, Redshift y SageMaker (opcional)

### Objetivo del Laboratorio
Guiar paso a paso al estudiante para que cree un pipeline de datos financieros en AWS usando servicios en la nube desde Python local. El laboratorio cubrirá:

- Almacenamiento de archivos en S3
- Carga de datos en Redshift y ejecución de consultas SQL
- Optimizaciones de rendimiento en Redshift
- (**Opcional**) Entrenamiento de un modelo de predicción usando SageMaker

---

### Requisitos previos

- Cuenta AWS activa con acceso a S3, Redshift y SageMaker
- IAM Role con permisos suficientes (S3 full, Redshift full, SageMaker full)
- Instalar las siguientes librerías en tu ambiente local o notebook:
  ```bash
  pip install boto3 psycopg2-binary awswrangler sagemaker pandas
  ```

---

### Paso 1: Configuración del entorno

- Configura tus credenciales AWS:
  ```bash
  aws configure
  ```
  Ingresar Access Key, Secret Key y región por defecto (ej: us-east-1).

---

### Paso 2: Dataset de Finanzas

- Usa un dataset de Kaggle como "Credit Card Fraud Detection" o cualquier dataset financiero estructurado.
- Descarga el archivo y nómbrelo `transactions.csv`
- Revisa el contenido:
  ```python
  import pandas as pd
  df = pd.read_csv("transactions.csv")
  print(df.head())
  ```

---

### Paso 3: Subir archivo a S3

```python
import boto3
s3 = boto3.client('s3')
bucket_name = 'finanzas-lab-demo'
s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': 'us-east-1'})
s3.upload_file("transactions.csv", bucket_name, "datasets/transactions.csv")
```

---

### Paso 4: Crear clúster Redshift (puede usarse interfaz web o código opcional)

Desde la consola AWS:
- Crear clúster Redshift DC2.large (1 nodo)
- Usuario admin: `awsuser`
- Nombre BD: `dev`
- Obtener el endpoint: ejemplo `redshift-cluster.xxxxxxx.us-east-1.redshift.amazonaws.com`

Crear tabla en Redshift y cargar datos desde S3:
```python
import psycopg2
conn = psycopg2.connect(
    host='[ENDPOINT]', dbname='dev', user='awsuser', password='TuPassword', port=5439
)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
  TransactionID VARCHAR(50),
  UserID VARCHAR(50),
  Amount DECIMAL(10,2),
  Timestamp TIMESTAMP,
  Merchant VARCHAR(100),
  Category VARCHAR(50),
  FraudFlag BOOLEAN
);
""")
conn.commit()
```

Usar COPY:
```sql
COPY transactions FROM 's3://finanzas-lab-demo/datasets/transactions.csv'
IAM_ROLE 'arn:aws:iam::TU_ID:role/TU_ROL_REDSHIFT'
CSV
IGNOREHEADER 1;
```

---

### Paso 5: Consultas básicas en Redshift

```python
cursor.execute("SELECT COUNT(*) FROM transactions;")
print(cursor.fetchone())

cursor.execute("""
SELECT Category, SUM(Amount) as Total
FROM transactions
GROUP BY Category
ORDER BY Total DESC
""")
for row in cursor.fetchall():
    print(row)
```

---

### Paso 6: Optimizaciones de Redshift

- Redefinir tabla usando DISTKEY y SORTKEY:
  ```sql
  DROP TABLE IF EXISTS transactions;
  CREATE TABLE transactions (
    TransactionID VARCHAR(50),
    UserID VARCHAR(50),
    Amount DECIMAL(10,2),
    Timestamp TIMESTAMP,
    Merchant VARCHAR(100),
    Category VARCHAR(50),
    FraudFlag BOOLEAN
  )
  DISTKEY(UserID)
  SORTKEY(Timestamp);
  ```

- Volver a cargar los datos con COPY.
- Ejecutar `VACUUM` y `ANALYZE` para optimizar:
  ```sql
  VACUUM;
  ANALYZE;
  ```

---

### Paso 7 (opcional): Modelo de ML con SageMaker

```python
from sagemaker import Session, XGBoost
sagemaker_session = Session()
role = 'arn:aws:iam::TU_ID:role/service-role/TU_ROL_SAGEMAKER'

estimator = XGBoost(entry_point='train.py', role=role,
                    instance_count=1, instance_type='ml.m5.xlarge',
                    framework_version='1.3-1', py_version='py3')

data_uri = f's3://{bucket_name}/datasets/transactions.csv'
estimator.fit({'train': data_uri})
```

---

### Fin del laboratorio

Has implementado un flujo de datos en AWS desde el almacenamiento hasta el análisis SQL y (opcionalmente) aprendizaje automático.

