![logo bsg](images/logobsg.png)

# Introducción a AWS Glue para Pipelines de Datos

# Sección 1: Introducción a AWS Glue para la Creación de Pipelines de Datos

## 📋 Objetivos de Aprendizaje

Al finalizar esta sección, serás capaz de:
- Diseñar y construir pipelines ETL escalables usando AWS Glue
- Implementar transformaciones avanzadas con PySpark en Glue
- Optimizar el rendimiento de jobs de Glue
- Integrar múltiples fuentes de datos (S3, RDS, DynamoDB)

---

## ⚙️ PREREQUISITOS Y CONFIGURACIÓN INICIAL

### 📝 Requisitos Previos

Antes de comenzar, asegúrate de tener:

- ✅ **Cuenta de AWS activa** con acceso a la consola
- ✅ **AWS CLI instalado** (versión 2.x o superior)
- ✅ **Python 3.8+** instalado localmente
- ✅ **Boto3** instalado: `pip install boto3`
- ✅ **Conocimientos básicos** de PySpark y SQL
- ✅ **Tarjeta de crédito** registrada en AWS (servicios tienen costo)

### 💰 Estimación de Costos - AWS FREE TIER

**⚠️ IMPORTANTE: Este laboratorio está optimizado para AWS Free Tier**

**Servicios con Free Tier (12 meses):**
- ✅ **S3**: 5 GB de almacenamiento estándar, 20,000 solicitudes GET, 2,000 PUT
- ✅ **AWS Glue Data Catalog**: 1 millón de objetos almacenados/mes (GRATIS)
- ✅ **CloudWatch Logs**: 5 GB de ingesta de datos

**Servicios con costo mínimo:**
- ⚠️ **AWS Glue Jobs (ETL)**: NO tiene Free Tier
  - Costo: ~$0.44 por DPU-hora
  - **Estrategia para minimizar costos:**
    - Usar 2 DPUs (mínimo) en lugar de 10
    - Jobs cortos (< 5 minutos por ejecución)
    - Usar datos pequeños (< 100 MB)
    - **Costo por ejercicio: ~$0.10 - $0.30 USD**
    - **Total estimado del curso: $2-5 USD**

**📋 Recomendaciones para mantenerse en Free Tier:**
1. **Eliminar recursos después de cada sesión** (Glue jobs, tablas del catálogo)
2. Usar datasets pequeños (< 50 MB)
3. Configurar **AWS Budgets** con alerta en $5 USD
4. Ejecutar solo 1-2 jobs por sesión de práctica
5. Borrar datos de S3 al terminar el curso

**🔔 Configurar Alerta de Presupuesto:**
```bash
# Crear alerta de presupuesto (solo una vez)
aws budgets create-budget \
    --account-id $(aws sts get-caller-identity --query Account --output text) \
    --budget file://budget-config.json \
    --notifications-with-subscribers file://budget-notifications.json \
    --profile glue-lab
```

**Archivo `budget-config.json`:**
```json
{
  "BudgetName": "GlueLab-Monthly-Budget",
  "BudgetLimit": {
    "Amount": "5",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST"
}
```

**Archivo `budget-notifications.json`:**
```json
[
  {
    "Notification": {
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 80,
      "ThresholdType": "PERCENTAGE",
      "NotificationType": "ACTUAL"
    },
    "Subscribers": [
      {
        "SubscriptionType": "EMAIL",
        "Address": "tu-email@example.com"
      }
    ]
  }
]
```

---

## 🚀 PARTE 1: CONFIGURACIÓN DE CUENTA Y PERMISOS

### Paso 1.1: Configurar AWS CLI

```bash
# Instalar AWS CLI (si no lo tienes)
# macOS/Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Windows (usar PowerShell como administrador)
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi

# Verificar instalación
aws --version
# Debe mostrar: aws-cli/2.x.x Python/3.x.x...
```

### Paso 1.2: Crear Usuario IAM para el Laboratorio

**Desde la Consola de AWS:**

1. Ve a **IAM** → **Users** → **Create user**
2. Nombre del usuario: `glue-lab-user`
3. Selecciona: ✅ **Provide user access to the AWS Management Console**
4. Selecciona: **I want to create an IAM user**
5. Contraseña: Elige una contraseña segura
6. ⬜ Desmarcar "Users must create a new password at next sign-in"
7. Click **Next**

### Paso 1.3: Asignar Permisos al Usuario

En la pantalla de permisos:

1. Selecciona: **Attach policies directly**
2. Busca y selecciona las siguientes políticas:
   - ✅ `AWSGlueConsoleFullAccess`
   - ✅ `AmazonS3FullAccess`
   - ✅ `IAMFullAccess` (solo para crear roles)
   - ✅ `AmazonRDSFullAccess` (si vas a usar RDS)
   - ✅ `CloudWatchLogsFullAccess`
3. Click **Next** → **Create user**
4. **⚠️ IMPORTANTE**: Descarga las credenciales CSV o copia el Access Key ID y Secret Access Key

### Paso 1.4: Configurar Credenciales Localmente

```bash
# Configurar el perfil de AWS
aws configure --profile glue-lab

# Te pedirá:
AWS Access Key ID [None]: <TU_ACCESS_KEY_ID>
AWS Secret Access Key [None]: <TU_SECRET_ACCESS_KEY>
Default region name [None]: us-east-1
Default output format [None]: json

# Verificar configuración
aws sts get-caller-identity --profile glue-lab

# Debe mostrar tu usuario ARN
```

### Paso 1.5: Crear el Rol de Servicio para AWS Glue

**Opción A: Usando la Consola de AWS**

1. Ve a **IAM** → **Roles** → **Create role**
2. **Trusted entity type**: AWS service
3. **Use case**: Selecciona **Glue** de la lista
4. Click **Next**
5. En **Permissions policies**, busca y selecciona:
   - ✅ `AWSGlueServiceRole` (política administrada por AWS)
   - ✅ `AmazonS3FullAccess`
   - ✅ `CloudWatchLogsFullAccess`
6. Click **Next**
7. **Role name**: `AWSGlueServiceRole-DataEngineer`
8. **Description**: "Rol de servicio para AWS Glue con acceso a S3 y CloudWatch"
9. Click **Create role**

**Opción B: Usando AWS CLI (más rápido)**

Crea un archivo `trust-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "glue.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

Ejecuta estos comandos:

```bash
# Crear el rol
aws iam create-role \
    --role-name AWSGlueServiceRole-DataEngineer \
    --assume-role-policy-document file://trust-policy.json \
    --profile glue-lab

# Adjuntar políticas necesarias
aws iam attach-role-policy \
    --role-name AWSGlueServiceRole-DataEngineer \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole \
    --profile glue-lab

aws iam attach-role-policy \
    --role-name AWSGlueServiceRole-DataEngineer \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess \
    --profile glue-lab

aws iam attach-role-policy \
    --role-name AWSGlueServiceRole-DataEngineer \
    --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess \
    --profile glue-lab

# Verificar
aws iam get-role \
    --role-name AWSGlueServiceRole-DataEngineer \
    --profile glue-lab
```

---

## 🪣 PARTE 2: CONFIGURACIÓN DE S3

### Paso 2.1: Crear Bucket de S3

**Usando la Consola:**

1. Ve a **S3** → **Create bucket**
2. **Bucket name**: `glue-lab-<tu-nombre>-<numero-random>` 
   - Ejemplo: `glue-lab-juan-12345`
   - ⚠️ Debe ser único globalmente
3. **AWS Region**: `us-east-1` (N. Virginia)
4. Deja el resto de configuraciones por defecto
5. Click **Create bucket**

**Usando AWS CLI:**

```bash
# Reemplaza con tu nombre único
BUCKET_NAME="glue-lab-$(whoami)-$RANDOM"

# Crear bucket
aws s3 mb s3://$BUCKET_NAME --region us-east-1 --profile glue-lab

# Verificar
aws s3 ls --profile glue-lab

# Guardar el nombre del bucket (importante para después)
echo "export GLUE_LAB_BUCKET=$BUCKET_NAME" >> ~/.bashrc
echo "Tu bucket se llama: $BUCKET_NAME"
```

### Paso 2.2: Crear Estructura de Carpetas

```bash
# Crear estructura de directorios
aws s3api put-object --bucket $BUCKET_NAME --key raw/ --profile glue-lab
aws s3api put-object --bucket $BUCKET_NAME --key raw/sales/ --profile glue-lab
aws s3api put-object --bucket $BUCKET_NAME --key raw/events/ --profile glue-lab
aws s3api put-object --bucket $BUCKET_NAME --key raw/customers/ --profile glue-lab
aws s3api put-object --bucket $BUCKET_NAME --key curated/ --profile glue-lab
aws s3api put-object --bucket $BUCKET_NAME --key scripts/ --profile glue-lab
aws s3api put-object --bucket $BUCKET_NAME --key temp/ --profile glue-lab

# Verificar estructura
aws s3 ls s3://$BUCKET_NAME/ --recursive --profile glue-lab
```

### Paso 2.3: Preparar Datos de Ejemplo (Optimizados para Free Tier)

**⚠️ IMPORTANTE: Usaremos datasets pequeños para minimizar costos**

Crea estos archivos localmente y súbelos a S3:

**Archivo: `sales_data.csv` (< 1 KB)**

```csv
transaction_id,customer_id,product_id,quantity,price,transaction_date
TXN001,CUST123,PROD456,2,29.99,2024-01-15
TXN002,CUST456,PROD789,1,49.99,2024-01-15
TXN003,CUST123,PROD101,5,15.50,2024-01-16
TXN004,CUST789,PROD456,1,29.99,2024-01-16
TXN005,CUST456,PROD202,3,22.00,2024-01-17
TXN006,CUST321,PROD789,2,49.99,2024-01-17
TXN007,CUST123,PROD303,1,99.99,2024-01-18
TXN008,CUST654,PROD101,10,15.50,2024-01-18
TXN009,CUST789,PROD456,1,29.99,2024-01-19
TXN010,CUST123,PROD789,2,49.99,2024-01-19
TXN011,CUST456,PROD456,3,29.99,2024-01-20
TXN012,CUST321,PROD101,2,15.50,2024-01-20
TXN013,CUST789,PROD202,1,22.00,2024-01-21
TXN014,CUST654,PROD789,4,49.99,2024-01-21
TXN015,CUST123,PROD456,1,29.99,2024-01-22
```

**Archivo: `customers_data.csv` (< 1 KB)**

```csv
customer_id,customer_name,email,customer_segment,registration_date,country,city
CUST123,John Doe,john.doe@email.com,Premium,2023-06-15,US,New York
CUST456,Jane Smith,jane.smith@email.com,Regular,2023-08-22,US,Los Angeles
CUST789,Bob Johnson,bob.j@email.com,Premium,2023-05-10,UK,London
CUST321,Alice Williams,alice.w@email.com,Regular,2023-09-01,CA,Toronto
CUST654,Charlie Brown,charlie.b@email.com,VIP,2023-03-20,US,Chicago
```

**Archivo: `events_data.json` (< 1 KB) - una línea por registro**

```json
{"event_id":"EVT001","customer_id":"CUST123","event_type":"page_view","page_url":"/products/electronics","timestamp":"2024-01-15T09:30:00Z"}
{"event_id":"EVT002","customer_id":"CUST123","event_type":"page_view","page_url":"/products/prod456","timestamp":"2024-01-15T09:35:00Z"}
{"event_id":"EVT003","customer_id":"CUST456","event_type":"page_view","page_url":"/products/home","timestamp":"2024-01-15T10:00:00Z"}
{"event_id":"EVT004","customer_id":"CUST456","event_type":"add_to_cart","product_id":"PROD789","timestamp":"2024-01-15T10:05:00Z"}
{"event_id":"EVT005","customer_id":"CUST789","event_type":"page_view","page_url":"/products/electronics","timestamp":"2024-01-16T11:20:00Z"}
{"event_id":"EVT006","customer_id":"CUST321","event_type":"page_view","page_url":"/products/prod789","timestamp":"2024-01-17T14:30:00Z"}
{"event_id":"EVT007","customer_id":"CUST654","event_type":"add_to_cart","product_id":"PROD101","timestamp":"2024-01-18T16:45:00Z"}
{"event_id":"EVT008","customer_id":"CUST123","event_type":"purchase","product_id":"PROD303","timestamp":"2024-01-18T17:00:00Z"}
```

**Subir archivos a S3:**

```bash
# Subir datos de ventas
aws s3 cp sales_data.csv s3://$BUCKET_NAME/raw/sales/ --profile glue-lab

# Subir datos de clientes
aws s3 cp customers_data.csv s3://$BUCKET_NAME/raw/customers/ --profile glue-lab

# Subir eventos
aws s3 cp events_data.json s3://$BUCKET_NAME/raw/events/ --profile glue-lab

# Verificar tamaño de archivos (debe ser < 5 KB total)
aws s3 ls s3://$BUCKET_NAME/raw/ --recursive --human-readable --profile glue-lab
```

**💡 Generar más datos si es necesario (opcional):**

Si necesitas datasets más grandes para pruebas (pero manteniéndote en Free Tier):

```python
# Script: generate_sample_data.py
import csv
import json
import random
from datetime import datetime, timedelta

def generate_sales_data(num_records=100):
    """Genera datos de ventas (< 10 KB)"""
    products = ['PROD456', 'PROD789', 'PROD101', 'PROD202', 'PROD303']
    customers = ['CUST123', 'CUST456', 'CUST789', 'CUST321', 'CUST654']
    
    with open('sales_data_extended.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['transaction_id', 'customer_id', 'product_id', 
                        'quantity', 'price', 'transaction_date'])
        
        start_date = datetime(2024, 1, 1)
        for i in range(num_records):
            date = start_date + timedelta(days=random.randint(0, 30))
            writer.writerow([
                f'TXN{i+1:04d}',
                random.choice(customers),
                random.choice(products),
                random.randint(1, 10),
                round(random.uniform(10, 100), 2),
                date.strftime('%Y-%m-%d')
            ])
    print(f"✅ Generados {num_records} registros de ventas")

# Ejecutar (genera ~100 registros = ~5 KB)
generate_sales_data(100)
```

---

## 🗄️ PARTE 3: CONFIGURACIÓN DE AWS GLUE

### Paso 3.1: Crear Base de Datos en Glue Data Catalog

**Usando la Consola:**

1. Ve a **AWS Glue** → **Databases** (en el menú izquierdo)
2. Click **Add database**
3. **Name**: `ecommerce_datawarehouse`
4. **Description**: "Data warehouse for e-commerce analytics - Lab"
5. **Location** (opcional): `s3://glue-lab-<tu-bucket>/curated/`
6. Click **Create database**

**Usando AWS CLI:**

```bash
aws glue create-database \
    --database-input '{
        "Name": "ecommerce_datawarehouse",
        "Description": "Data warehouse for e-commerce analytics - Lab",
        "LocationUri": "s3://'$BUCKET_NAME'/curated/"
    }' \
    --profile glue-lab

# Verificar
aws glue get-database \
    --name ecommerce_datawarehouse \
    --profile glue-lab
```

### Paso 3.2: Crear y Ejecutar Crawler

**Usando la Consola:**

1. Ve a **AWS Glue** → **Crawlers** → **Create crawler**
2. **Name**: `sales-data-crawler`
3. Click **Next**

**Configurar fuente de datos:**
4. Click **Add a data source**
5. **S3 path**: `s3://glue-lab-<tu-bucket>/raw/sales/`
6. Click **Add an S3 data source**
7. Click **Next**

**Configurar rol IAM:**
8. Selecciona: **Choose an existing IAM role**
9. Rol: `AWSGlueServiceRole-DataEngineer`
10. Click **Next**

**Configurar destino:**
11. **Target database**: `ecommerce_datawarehouse`
12. **Table name prefix**: `raw_` (opcional)
13. Click **Next**

**Revisar y crear:**
14. Revisa la configuración
15. Click **Create crawler**
16. Selecciona el crawler creado y click **Run crawler**
17. Espera 1-2 minutos hasta que el status sea **Completed**

**Usando Script Python (Automatizado):**

Crea un archivo `setup_crawler.py`:

```python
import boto3
import time
import os

# Configuración
BUCKET_NAME = os.environ.get('GLUE_LAB_BUCKET', 'glue-lab-tu-bucket')
REGION = 'us-east-1'
DATABASE_NAME = 'ecommerce_datawarehouse'
ROLE_NAME = 'AWSGlueServiceRole-DataEngineer'

# Cliente de Glue
session = boto3.Session(profile_name='glue-lab', region_name=REGION)
glue_client = session.client('glue')
iam_client = session.client('iam')

def get_role_arn():
    """Obtener ARN del rol"""
    try:
        response = iam_client.get_role(RoleName=ROLE_NAME)
        return response['Role']['Arn']
    except Exception as e:
        print(f"❌ Error obteniendo rol: {e}")
        return None

def create_crawler(name, path, description):
    """Crear y ejecutar un crawler"""
    role_arn = get_role_arn()
    if not role_arn:
        return False
    
    try:
        glue_client.create_crawler(
            Name=name,
            Role=role_arn,
            DatabaseName=DATABASE_NAME,
            Description=description,
            Targets={
                'S3Targets': [
                    {
                        'Path': path,
                        'Exclusions': ['*.tmp', '*.log', '_*']
                    }
                ]
            },
            SchemaChangePolicy={
                'UpdateBehavior': 'UPDATE_IN_DATABASE',
                'DeleteBehavior': 'LOG'
            },
            RecrawlPolicy={
                'RecrawlBehavior': 'CRAWL_NEW_FOLDERS_ONLY'
            }
        )
        print(f"✅ Crawler '{name}' creado exitosamente")
        
        # Ejecutar crawler
        glue_client.start_crawler(Name=name)
        print(f"🚀 Crawler '{name}' iniciado...")
        
        return True
        
    except glue_client.exceptions.AlreadyExistsException:
        print(f"⚠️  Crawler '{name}' ya existe")
        return True
    except Exception as e:
        print(f"❌ Error creando crawler: {e}")
        return False

def wait_for_crawler(name, max_wait=300):
    """Esperar a que el crawler termine"""
    print(f"⏳ Esperando que el crawler '{name}' termine...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        response = glue_client.get_crawler(Name=name)
        state = response['Crawler']['State']
        
        if state == 'READY':
            print(f"✅ Crawler '{name}' completado!")
            return True
        
        print(f"   Estado: {state} - Esperando...")
        time.sleep(10)
    
    print(f"⚠️  Timeout esperando al crawler")
    return False

# Ejecutar
if __name__ == "__main__":
    print("=" * 60)
    print("CONFIGURACIÓN DE CRAWLERS PARA AWS GLUE LAB")
    print("=" * 60)
    
    # Crawler para ventas
    if create_crawler(
        name='sales-data-crawler',
        path=f's3://{BUCKET_NAME}/raw/sales/',
        description='Crawler for sales transaction data'
    ):
        wait_for_crawler('sales-data-crawler')
    
    print()
    
    # Crawler para clientes
    if create_crawler(
        name='customers-data-crawler',
        path=f's3://{BUCKET_NAME}/raw/customers/',
        description='Crawler for customer data'
    ):
        wait_for_crawler('customers-data-crawler')
    
    print()
    
    # Crawler para eventos
    if create_crawler(
        name='events-data-crawler',
        path=f's3://{BUCKET_NAME}/raw/events/',
        description='Crawler for clickstream events'
    ):
        wait_for_crawler('events-data-crawler')
    
    print()
    print("=" * 60)
    print("✅ CONFIGURACIÓN COMPLETADA")
    print("=" * 60)
    
    # Listar tablas creadas
    print("\n📊 Tablas en el catálogo:")
    try:
        response = glue_client.get_tables(DatabaseName=DATABASE_NAME)
        for table in response['TableList']:
            print(f"   - {table['Name']}")
    except Exception as e:
        print(f"   Error listando tablas: {e}")
```

Ejecuta el script:

```bash
# Configurar variable de entorno
export GLUE_LAB_BUCKET="glue-lab-tu-bucket"  # Reemplaza con tu bucket

# Ejecutar
python setup_crawler.py
```

### Paso 3.3: Verificar Tablas Creadas

**Desde la Consola:**

1. Ve a **AWS Glue** → **Tables**
2. Deberías ver las tablas:
   - `sales` (o `raw_sales`)
   - `customers` (o `raw_customers`)
   - `events` (o `raw_events`)
3. Click en cada tabla para ver el esquema detectado

**Desde CLI:**

```bash
# Listar tablas
aws glue get-tables \
    --database-name ecommerce_datawarehouse \
    --profile glue-lab

# Ver esquema de una tabla específica
aws glue get-table \
    --database-name ecommerce_datawarehouse \
    --name sales \
    --profile glue-lab
```

---

## 📦 PARTE 4: PREPARAR ENTORNO PARA JOBS DE GLUE

### Paso 4.1: Crear Script de Glue Job

Guarda este script localmente como `sales_etl_job.py`:

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

# Obtener parámetros
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

# Inicializar contextos
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Tu código ETL aquí...
print("✅ Job iniciado correctamente")

job.commit()
```

### Paso 4.2: Subir Script a S3

```bash
# Subir script
aws s3 cp sales_etl_job.py s3://$BUCKET_NAME/scripts/ --profile glue-lab

# Verificar
aws s3 ls s3://$BUCKET_NAME/scripts/ --profile glue-lab
```

---

## ✅ VERIFICACIÓN FINAL

Ejecuta este script de verificación `verify_setup.py`:

```python
import boto3
import os

from sys import exit

BUCKET_NAME = os.environ.get('GLUE_LAB_BUCKET', 'REEMPLAZAR')
REGION = 'us-east-1'
DATABASE_NAME = 'ecommerce_datawarehouse'
ROLE_NAME = 'AWSGlueServiceRole-DataEngineer'

session = boto3.Session(profile_name='glue-lab', region_name=REGION)

def check_aws_credentials():
    """Verificar credenciales de AWS"""
    try:
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ Credenciales válidas")
        print(f"   Account: {identity['Account']}")
        print(f"   User: {identity['Arn']}")
        return True
    except Exception as e:
        print(f"❌ Error con credenciales: {e}")
        return False

def check_s3_bucket():
    """Verificar bucket de S3"""
    try:
        s3 = session.client('s3')
        s3.head_bucket(Bucket=BUCKET_NAME)
        print(f"✅ Bucket S3 existe: {BUCKET_NAME}")
        
        # Verificar estructura de carpetas
        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Delimiter='/')
        folders = [p.get('Prefix') for p in response.get('CommonPrefixes', [])]
        print(f"   Carpetas encontradas: {folders}")
        return True
    except Exception as e:
        print(f"❌ Error con bucket S3: {e}")
        return False

def check_iam_role():
    """Verificar rol IAM"""
    try:
        iam = session.client('iam')
        role = iam.get_role(RoleName=ROLE_NAME)
        print(f"✅ Rol IAM existe: {ROLE_NAME}")
        print(f"   ARN: {role['Role']['Arn']}")
        return True
    except Exception as e:
        print(f"❌ Error con rol IAM: {e}")
        return False

def check_glue_database():
    """Verificar base de datos Glue"""
    try:
        glue = session.client('glue')
        db = glue.get_database(Name=DATABASE_NAME)
        print(f"✅ Base de datos Glue existe: {DATABASE_NAME}")
        
        # Listar tablas
        tables = glue.get_tables(DatabaseName=DATABASE_NAME)
        table_names = [t['Name'] for t in tables['TableList']]
        print(f"   Tablas: {table_names}")
        return True
    except Exception as e:
        print(f"❌ Error con base de datos Glue: {e}")
        return False

def check_data_files():
    """Verificar archivos de datos en S3"""
    try:
        s3 = session.client('s3')
        
        files_to_check = [
            'raw/sales/sales_data.csv',
            'raw/customers/customers_data.csv',
            'raw/events/events_data.json'
        ]
        
        all_exist = True
        for file_key in files_to_check:
            try:
                s3.head_object(Bucket=BUCKET_NAME, Key=file_key)
                print(f"✅ Archivo existe: {file_key}")
            except:
                print(f"❌ Archivo NO existe: {file_key}")
                all_exist = False
        
        return all_exist
    except Exception as e:
        print(f"❌ Error verificando archivos: {e}")
        return False

# Ejecutar verificaciones
if __name__ == "__main__":
    print("=" * 70)
    print("VERIFICACIÓN DE PREREQUISITOS - AWS GLUE LAB")
    print("=" * 70)
    print()
    
    checks = [
        ("Credenciales AWS", check_aws_credentials),
        ("Bucket S3", check_s3_bucket),
        ("Rol IAM", check_iam_role),
        ("Base de Datos Glue", check_glue_database),
        ("Archivos de Datos", check_data_files)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n🔍 Verificando: {name}")
        print("-" * 70)
        result = check_func()
        results.append(result)
        print()
    
    print("=" * 70)
    if all(results):
        print("🎉 ¡TODOS LOS PREREQUISITOS ESTÁN LISTOS!")
        print("   Puedes continuar con los ejercicios de Glue.")
    else:
        print("⚠️  ALGUNOS PREREQUISITOS FALTAN")
        print("   Revisa los errores arriba y completa la configuración.")
    print("=" * 70)
```

**Ejecutar verificación:**

```bash
python verify_setup.py
```

## 🧹 LIMPIEZA DE RECURSOS (IMPORTANTE para Free Tier)

### Al Terminar Cada Sesión de Práctica

**⚠️ CRÍTICO: Ejecuta estos comandos para evitar cargos innecesarios**

```bash
# 1. Eliminar archivos de S3 (curated/temp)
aws s3 rm s3://$BUCKET_NAME/curated/ --recursive --profile glue-lab
aws s3 rm s3://$BUCKET_NAME/temp/ --recursive --profile glue-lab

# 2. Mantener solo raw data (para volver a practicar)
# NO eliminar: s3://$BUCKET_NAME/raw/

# 3. Eliminar tablas del catálogo (se pueden recrear con crawlers)
aws glue delete-table \
    --database-name ecommerce_datawarehouse \
    --name sales \
    --profile glue-lab

# 4. Verificar tamaño total en S3
aws s3 ls s3://$BUCKET_NAME --recursive --human-readable --summarize --profile glue-lab
```

### Al Terminar el Curso Completo

```bash
# Script de limpieza completa: cleanup_all.sh

#!/bin/bash
BUCKET_NAME="tu-bucket-aqui"
DATABASE_NAME="ecommerce_datawarehouse"
PROFILE="glue-lab"

echo "🧹 Iniciando limpieza completa..."

# 1. Eliminar todos los jobs de Glue
echo "Eliminando Glue Jobs..."
for job in $(aws glue list-jobs --profile $PROFILE --query 'JobNames[]' --output text); do
    aws glue delete-job --job-name $job --profile $PROFILE
    echo "  ✓ Job eliminado: $job"
done

# 2. Eliminar crawlers
echo "Eliminando Crawlers..."
for crawler in $(aws glue list-crawlers --profile $PROFILE --query 'CrawlerNames[]' --output text); do
    aws glue delete-crawler --name $crawler --profile $PROFILE
    echo "  ✓ Crawler eliminado: $crawler"
done

# 3. Eliminar tablas del catálogo
echo "Eliminando tablas del catálogo..."
for table in $(aws glue get-tables --database-name $DATABASE_NAME --profile $PROFILE --query 'TableList[].Name' --output text); do
    aws glue delete-table --database-name $DATABASE_NAME --name $table --profile $PROFILE
    echo "  ✓ Tabla eliminada: $table"
done

# 4. Eliminar base de datos
echo "Eliminando base de datos..."
aws glue delete-database --name $DATABASE_NAME --profile $PROFILE
echo "  ✓ Base de datos eliminada"

# 5. Eliminar TODO el bucket de S3
echo "Eliminando bucket S3..."
aws s3 rb s3://$BUCKET_NAME --force --profile $PROFILE
echo "  ✓ Bucket eliminado"

echo "✅ Limpieza completa terminada"
```

### Verificar Costos Acumulados

```bash
# Ver costos del mes actual
aws ce get-cost-and-usage \
    --time-period Start=$(date -d "1 month ago" +%Y-%m-01),End=$(date +%Y-%m-%d) \
    --granularity MONTHLY \
    --metrics "BlendedCost" \
    --group-by Type=DIMENSION,Key=SERVICE \
    --profile glue-lab
```

---

## 📊 RESUMEN DE PREREQUISITOS COMPLETADOS

Al terminar esta configuración, deberías tener:

### ✅ En AWS IAM:
- Usuario: `glue-lab-user` con permisos de consola
- Rol: `AWSGlueServiceRole-DataEngineer` para Glue jobs

### ✅ En AWS S3:
- Bucket: `glue-lab-<tu-nombre>-<random>`
- Estructura de carpetas: `raw/`, `curated/`, `scripts/`, `temp/`
- Datos de ejemplo en `raw/sales/`, `raw/customers/`, `raw/events/`

### ✅ En AWS Glue:
- Database: `ecommerce_datawarehouse`
- Crawlers configurados: `sales-data-crawler`, `customers-data-crawler`, `events-data-crawler`
- Tablas catalogadas: `sales`, `customers`, `events`

### ✅ En tu máquina local:
- AWS CLI configurado con perfil `glue-lab`
- Python 3.8+ con boto3 instalado
- Scripts de verificación ejecutados exitosamente

---

## 🎯 Conceptos Fundamentales

### ¿Qué es AWS Glue?

AWS Glue es un servicio serverless de ETL (Extract, Transform, Load) que permite:
- **Descubrimiento automático** de datos mediante Crawlers
- **Catálogo centralizado** de metadatos
- **Procesamiento distribuido** con Apache Spark
- **Integración nativa** con el ecosistema AWS

### Arquitectura de un Pipeline Glue

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  Fuentes    │────▶│ AWS Glue     │────▶│ Transform   │────▶│  Destino     │
│  de Datos   │     │ Crawler      │     │ (PySpark)   │     │  (S3/RDS)    │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │ Data Catalog │
                    │  (Metadata)  │
                    └──────────────┘
```

---

## 💼 Caso de Uso Real: Pipeline de Análisis de E-commerce

**Contexto**: Una empresa de e-commerce necesita consolidar datos de ventas, inventario y clientes desde múltiples fuentes para análisis en tiempo real.

**Fuentes de datos**:
- Transacciones de ventas (CSV en S3)
- Datos de productos (PostgreSQL RDS)
- Eventos de clickstream (JSON en S3)
- Información de clientes (Parquet en S3)

**Objetivo**: Crear un Data Lake curado con datos limpios y enriquecidos.

---

## 🔧 Ejemplo 1: Configuración Inicial y Crawler

### Paso 1: Estructura de Datos de Entrada

Primero, entendamos la estructura de nuestros datos:

```python
# sales_data.csv (S3: s3://mi-bucket/raw/sales/)
"""
transaction_id,customer_id,product_id,quantity,price,transaction_date
TXN001,CUST123,PROD456,2,29.99,2024-01-15
TXN002,CUST456,PROD789,1,49.99,2024-01-15
"""

# clickstream_events.json (S3: s3://mi-bucket/raw/events/)
"""
{
  "event_id": "EVT001",
  "customer_id": "CUST123",
  "event_type": "page_view",
  "page_url": "/products/electronics",
  "timestamp": "2024-01-15T10:30:00Z"
}
"""
```

### Paso 2: Script de Crawler usando Boto3

```python
import boto3
import json

def create_glue_database():
    """Crea la base de datos en Glue Catalog"""
    glue_client = boto3.client('glue', region_name='us-east-1')
    
    try:
        glue_client.create_database(
            DatabaseInput={
                'Name': 'ecommerce_datawarehouse',
                'Description': 'Data warehouse for e-commerce analytics',
                'LocationUri': 's3://mi-bucket/curated/',
                'Parameters': {
                    'created_by': 'data_engineering_team',
                    'environment': 'production'
                }
            }
        )
        print("✓ Database created successfully")
    except glue_client.exceptions.AlreadyExistsException:
        print("✓ Database already exists")


def create_crawler_for_sales():
    """Crea un crawler para descubrir datos de ventas"""
    glue_client = boto3.client('glue', region_name='us-east-1')
    
    crawler_config = {
        'Name': 'sales-data-crawler',
        'Role': 'AWSGlueServiceRole-DataEngineer',  # Rol IAM con permisos
        'DatabaseName': 'ecommerce_datawarehouse',
        'Description': 'Crawler for sales transaction data',
        'Targets': {
            'S3Targets': [
                {
                    'Path': 's3://mi-bucket/raw/sales/',
                    'Exclusions': ['*.tmp', '*.log']
                }
            ]
        },
        'SchemaChangePolicy': {
            'UpdateBehavior': 'UPDATE_IN_DATABASE',
            'DeleteBehavior': 'LOG'
        },
        'RecrawlPolicy': {
            'RecrawlBehavior': 'CRAWL_NEW_FOLDERS_ONLY'
        },
        'Configuration': json.dumps({
            'Version': 1.0,
            'CrawlerOutput': {
                'Partitions': {'AddOrUpdateBehavior': 'InheritFromTable'}
            }
        })
    }
    
    try:
        glue_client.create_crawler(**crawler_config)
        print("✓ Crawler created successfully")
        
        # Iniciar el crawler inmediatamente
        glue_client.start_crawler(Name='sales-data-crawler')
        print("✓ Crawler started")
        
    except Exception as e:
        print(f"Error creating crawler: {str(e)}")


# Ejecutar
if __name__ == "__main__":
    create_glue_database()
    create_crawler_for_sales()
```

---

## 🚀 Ejemplo 2: Job ETL Básico con PySpark (Optimizado para Free Tier)

### Script de Glue Job: Limpieza y Transformación de Datos de Ventas

**⚠️ Configuración optimizada para minimizar costos:**
- Workers: 2 (mínimo)
- Worker type: G.1X (más económico)
- Timeout: 5 minutos (suficiente para datos pequeños)
- **Costo estimado por ejecución: ~$0.10 USD**

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from datetime import datetime

# Inicialización
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

# Configuración para minimizar uso de recursos
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# Optimizaciones para datasets pequeños
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")

job = Job(glueContext)
job.init(args['JOB_NAME'], args)

print(f"🚀 Job iniciado: {args['JOB_NAME']}")
print(f"⏰ Timestamp: {datetime.now().isoformat()}")

# ============================================
# EXTRACT: Leer datos del catálogo
# ============================================

# Leer datos de ventas desde el catálogo
sales_dyf = glueContext.create_dynamic_frame.from_catalog(
    database="ecommerce_datawarehouse",
    table_name="sales",
    transformation_ctx="sales_dyf"
)

# Convertir a DataFrame de Spark para transformaciones avanzadas
sales_df = sales_dyf.toDF()

initial_count = sales_df.count()
print(f"📊 Registros cargados: {initial_count}")
sales_df.printSchema()

# Mostrar muestra de datos
print("\n📋 Muestra de datos originales:")
sales_df.show(5, truncate=False)

# ============================================
# TRANSFORM: Limpieza y Enriquecimiento
# ============================================

# 1. Validación y limpieza de datos
sales_clean_df = sales_df \
    .filter(F.col("quantity") > 0) \
    .filter(F.col("price") > 0) \
    .filter(F.col("customer_id").isNotNull()) \
    .filter(F.col("transaction_date").isNotNull()) \
    .dropDuplicates(['transaction_id'])

records_after_cleaning = sales_clean_df.count()
print(f"✅ Registros después de limpieza: {records_after_cleaning}")
print(f"   Registros eliminados: {initial_count - records_after_cleaning}")

# 2. Conversión de tipos de datos
sales_clean_df = sales_clean_df \
    .withColumn("quantity", F.col("quantity").cast("integer")) \
    .withColumn("price", F.col("price").cast("decimal(10,2)")) \
    .withColumn("transaction_date", F.to_date("transaction_date", "yyyy-MM-dd"))

# 3. Cálculos de negocio
sales_enriched_df = sales_clean_df \
    .withColumn("total_amount", F.col("quantity") * F.col("price")) \
    .withColumn("year", F.year("transaction_date")) \
    .withColumn("month", F.month("transaction_date")) \
    .withColumn("day", F.dayofmonth("transaction_date")) \
    .withColumn("day_of_week", F.dayofweek("transaction_date")) \
    .withColumn("day_name", 
                F.when(F.col("day_of_week") == 1, "Sunday")
                 .when(F.col("day_of_week") == 2, "Monday")
                 .when(F.col("day_of_week") == 3, "Tuesday")
                 .when(F.col("day_of_week") == 4, "Wednesday")
                 .when(F.col("day_of_week") == 5, "Thursday")
                 .when(F.col("day_of_week") == 6, "Friday")
                 .otherwise("Saturday"))

# 4. Agregaciones por ventana (análisis por cliente)
window_spec = Window.partitionBy("customer_id").orderBy(F.desc("transaction_date"))

sales_with_recency = sales_enriched_df \
    .withColumn("transaction_rank", F.row_number().over(window_spec)) \
    .withColumn("is_latest_transaction", 
                F.when(F.col("transaction_rank") == 1, True).otherwise(False))

# 5. Detección de anomalías (compras muy grandes)
# Calcular estadísticas globales primero (para datasets pequeños)
stats = sales_enriched_df.select(
    F.avg("total_amount").alias("global_avg"),
    F.stddev("total_amount").alias("global_stddev")
).first()

global_avg = stats['global_avg']
global_stddev = stats['global_stddev'] if stats['global_stddev'] else 0

print(f"\n📈 Estadísticas globales:")
print(f"   Promedio de compra: ${global_avg:.2f}")
print(f"   Desviación estándar: ${global_stddev:.2f}")

# Calcular estadísticas por cliente
customer_stats = sales_enriched_df \
    .groupBy("customer_id") \
    .agg(
        F.count("*").alias("num_transactions"),
        F.avg("total_amount").alias("avg_purchase"),
        F.stddev("total_amount").alias("stddev_purchase"),
        F.sum("total_amount").alias("total_spent")
    )

# Unir con datos originales y marcar anomalías
sales_final_df = sales_with_recency \
    .join(customer_stats, on="customer_id", how="left") \
    .withColumn("is_anomaly", 
                F.when(F.col("total_amount") > (global_avg + 2 * global_stddev), 
                       True).otherwise(False))

# 6. Agregar metadata de procesamiento
sales_final_df = sales_final_df \
    .withColumn("processed_timestamp", F.current_timestamp()) \
    .withColumn("data_source", F.lit("sales_csv")) \
    .withColumn("job_id", F.lit(args['JOB_NAME'])) \
    .withColumn("processing_date", F.current_date())

# Mostrar muestra de datos procesados
print("\n📋 Muestra de datos procesados:")
sales_final_df.select(
    "transaction_id", "customer_id", "total_amount", 
    "day_name", "is_anomaly", "num_transactions"
).show(10, truncate=False)

# ============================================
# LOAD: Escribir a S3 en formato optimizado
# ============================================

# Convertir de vuelta a DynamicFrame
sales_final_dyf = DynamicFrame.fromDF(
    sales_final_df, 
    glueContext, 
    "sales_final_dyf"
)

# IMPORTANTE: Para datasets pequeños, no particionar demasiado
# Coalesce a 1 partición para evitar muchos archivos pequeños
sales_final_df_coalesced = sales_final_df.coalesce(1)
sales_final_dyf = DynamicFrame.fromDF(
    sales_final_df_coalesced, 
    glueContext, 
    "sales_final_dyf"
)

# Obtener bucket dinámicamente o usar variable de entorno
# En producción, esto vendría de los parámetros del job
output_bucket = "TU-BUCKET-AQUI"  # Cambiar por tu bucket
output_path = f"s3://{output_bucket}/curated/sales_processed/"

print(f"\n💾 Escribiendo resultados en: {output_path}")

glueContext.write_dynamic_frame.from_options(
    frame=sales_final_dyf,
    connection_type="s3",
    connection_options={
        "path": output_path,
        "partitionKeys": []  # Sin particiones para datos pequeños
    },
    format="parquet",
    format_options={
        "compression": "snappy"
    },
    transformation_ctx="write_sales"
)

# ============================================
# MÉTRICAS Y LOGGING
# ============================================

# Calcular métricas de calidad
total_records = initial_count
clean_records = sales_final_df.count()
anomalies_count = sales_final_df.filter(F.col("is_anomaly") == True).count()

# Calcular estadísticas por día
daily_stats = sales_final_df.groupBy("transaction_date").agg(
    F.count("*").alias("transactions"),
    F.sum("total_amount").alias("daily_revenue")
).orderBy("transaction_date")

print("\n" + "="*70)
print("📊 RESUMEN DE EJECUCIÓN DEL JOB ETL")
print("="*70)
print(f"Total de registros procesados: {total_records}")
print(f"Registros limpios: {clean_records}")
print(f"Registros eliminados: {total_records - clean_records}")
print(f"Anomalías detectadas: {anomalies_count}")
print(f"Ruta de salida: {output_path}")
print("\n📈 Ventas por día:")
daily_stats.show(10, truncate=False)

# Top clientes
top_customers = customer_stats.orderBy(F.desc("total_spent")).limit(5)
print("\n🏆 Top 5 Clientes:")
top_customers.show(truncate=False)

print("="*70)
print("✅ Job completado exitosamente")
print("="*70)

job.commit()
```

### Crear el Job en AWS Glue (Consola)

**Paso a paso:**

1. Ve a **AWS Glue** → **ETL Jobs** → **Script editor**
2. Click **Create job**
3. **Engine**: Spark
4. **Options**: Start fresh
5. Click **Create**

**Configuración del Job:**

6. En el editor, pega el script de arriba
7. En la pestaña **Job details**:
   - **Name**: `sales-etl-basic`
   - **IAM Role**: `AWSGlueServiceRole-DataEngineer`
   - **Type**: Spark
   - **Glue version**: 4.0
   - **Language**: Python 3
   
8. **⚠️ IMPORTANTE - Configuración de Workers (para Free Tier):**
   - **Worker type**: **G.1X** (más económico)
   - **Number of workers**: **2** (mínimo permitido)
   - Esto limita el costo a ~$0.10 por ejecución

9. **Advanced properties**:
   - **Script path**: `s3://tu-bucket/scripts/` (Glue lo guardará aquí)
   - **Temporary directory**: `s3://tu-bucket/temp/`
   - **Job timeout**: **5 minutes** (suficiente para datos pequeños)
   - **Maximum concurrency**: **1** (solo 1 ejecución a la vez)

10. **Monitoring options**:
    - ✅ Enable CloudWatch logs
    - ✅ Enable job metrics
    - ✅ Enable continuous logging

11. Click **Save**

### Ejecutar el Job

**Desde la Consola:**

1. Selecciona el job `sales-etl-basic`
2. Click **Run**
3. Espera 2-3 minutos
4. Ve a **Run details** para ver el progreso
5. Revisa los logs en **CloudWatch Logs**

**Desde CLI:**

```bash
# Iniciar el job
aws glue start-job-run \
    --job-name sales-etl-basic \
    --profile glue-lab

# Obtener el run ID del output, luego verificar estado
RUN_ID="jr_xxxxx"  # Reemplazar con el ID real

aws glue get-job-run \
    --job-name sales-etl-basic \
    --run-id $RUN_ID \
    --profile glue-lab
```

### Verificar Resultados

```bash
# Ver archivos generados
aws s3 ls s3://$BUCKET_NAME/curated/sales_processed/ --recursive --profile glue-lab

# Descargar un archivo para inspeccionar (opcional)
aws s3 cp s3://$BUCKET_NAME/curated/sales_processed/ . --recursive --profile glue-lab

# Ver tamaño total
aws s3 ls s3://$BUCKET_NAME/curated/ --recursive --human-readable --summarize --profile glue-lab
```

### 💡 Consejos para Minimizar Costos

```python
# ✅ BUENAS PRÁCTICAS para Free Tier:

# 1. Siempre usar coalesce para datos pequeños
df.coalesce(1).write.parquet("s3://...")

# 2. Evitar operaciones costosas innecesarias
# ❌ No usar:
df.repartition(100)  # Crea muchas particiones pequeñas
df.cache()  # No necesario para datos pequeños

# 3. Usar operaciones eficientes
# ✅ Filtrar temprano
df = df.filter(F.col("amount") > 0)  # Hace esto primero

# ❌ Filtrar tarde
df = df.withColumn("new_col", ...)  # Procesa todo
df = df.filter(F.col("amount") > 0)  # Luego filtra

# 4. Limitar el número de ejecuciones
# Ejecuta solo cuando sea necesario, no por cada pequeño cambio
```

---

## 🎨 Ejemplo 3: Transformaciones Avanzadas - Join de Múltiples Fuentes

### Script: Enriquecimiento de Ventas con Datos de Productos y Clientes

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from awsglue.dynamicframe import DynamicFrame

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'DATABASE_NAME', 'S3_OUTPUT_PATH'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# ============================================
# EXTRACT: Cargar múltiples fuentes
# ============================================

# 1. Datos de ventas (ya procesados)
sales_dyf = glueContext.create_dynamic_frame.from_catalog(
    database=args['DATABASE_NAME'],
    table_name="sales_curated",
    transformation_ctx="sales_dyf"
)

# 2. Datos de productos desde RDS PostgreSQL
products_dyf = glueContext.create_dynamic_frame.from_catalog(
    database=args['DATABASE_NAME'],
    table_name="products",
    transformation_ctx="products_dyf"
)

# 3. Datos de clientes desde S3 (Parquet)
customers_dyf = glueContext.create_dynamic_frame.from_catalog(
    database=args['DATABASE_NAME'],
    table_name="customers",
    transformation_ctx="customers_dyf"
)

# 4. Eventos de clickstream (JSON)
events_dyf = glueContext.create_dynamic_frame.from_catalog(
    database=args['DATABASE_NAME'],
    table_name="clickstream_events",
    transformation_ctx="events_dyf"
)

# ============================================
# TRANSFORM: Join y Enriquecimiento
# ============================================

# Convertir a DataFrames
sales_df = sales_dyf.toDF()
products_df = products_dyf.toDF()
customers_df = customers_dyf.toDF()
events_df = events_dyf.toDF()

# 1. Join con productos (enriquecer con info del producto)
sales_with_products = sales_df.join(
    products_df.select(
        "product_id",
        "product_name",
        "category",
        "subcategory",
        "brand",
        "cost_price",
        "list_price"
    ),
    on="product_id",
    how="left"
)

# Calcular margen de ganancia
sales_with_products = sales_with_products \
    .withColumn("profit", 
                F.col("total_amount") - (F.col("cost_price") * F.col("quantity"))) \
    .withColumn("profit_margin", 
                (F.col("profit") / F.col("total_amount")) * 100)

# 2. Join con clientes (segmentación)
sales_with_customers = sales_with_products.join(
    customers_df.select(
        "customer_id",
        "customer_name",
        "email",
        "customer_segment",
        "registration_date",
        "country",
        "city"
    ),
    on="customer_id",
    how="left"
)

# Calcular antigüedad del cliente
sales_with_customers = sales_with_customers \
    .withColumn("customer_tenure_days",
                F.datediff(F.col("transaction_date"), F.col("registration_date")))

# 3. Agregación de eventos de clickstream por sesión
# Calcular número de visitas antes de la compra
events_aggregated = events_df \
    .filter(F.col("event_type") == "page_view") \
    .groupBy("customer_id", F.to_date("timestamp").alias("event_date")) \
    .agg(
        F.count("*").alias("page_views"),
        F.countDistinct("page_url").alias("unique_pages_viewed")
    )

# Join con eventos (comportamiento pre-compra)
enriched_sales = sales_with_customers.join(
    events_aggregated,
    (sales_with_customers.customer_id == events_aggregated.customer_id) &
    (sales_with_customers.transaction_date == events_aggregated.event_date),
    how="left"
).drop(events_aggregated.customer_id)

# Rellenar valores nulos para clientes sin actividad web
enriched_sales = enriched_sales \
    .fillna(0, subset=["page_views", "unique_pages_viewed"])

# ============================================
# TRANSFORM: Agregaciones Analíticas
# ============================================

# Calcular métricas agregadas por cliente
customer_analytics = enriched_sales.groupBy("customer_id").agg(
    F.count("transaction_id").alias("total_transactions"),
    F.sum("total_amount").alias("lifetime_value"),
    F.avg("total_amount").alias("avg_order_value"),
    F.max("transaction_date").alias("last_purchase_date"),
    F.min("transaction_date").alias("first_purchase_date"),
    F.sum("profit").alias("total_profit"),
    F.avg("page_views").alias("avg_page_views_before_purchase")
)

# Calcular días desde última compra (Recency)
customer_analytics = customer_analytics \
    .withColumn("days_since_last_purchase",
                F.datediff(F.current_date(), F.col("last_purchase_date")))

# Clasificación RFM simplificada
customer_analytics = customer_analytics \
    .withColumn("rfm_recency_score",
                F.when(F.col("days_since_last_purchase") <= 30, 5)
                 .when(F.col("days_since_last_purchase") <= 60, 4)
                 .when(F.col("days_since_last_purchase") <= 90, 3)
                 .when(F.col("days_since_last_purchase") <= 180, 2)
                 .otherwise(1)) \
    .withColumn("rfm_frequency_score",
                F.when(F.col("total_transactions") >= 10, 5)
                 .when(F.col("total_transactions") >= 7, 4)
                 .when(F.col("total_transactions") >= 5, 3)
                 .when(F.col("total_transactions") >= 3, 2)
                 .otherwise(1)) \
    .withColumn("rfm_monetary_score",
                F.when(F.col("lifetime_value") >= 1000, 5)
                 .when(F.col("lifetime_value") >= 500, 4)
                 .when(F.col("lifetime_value") >= 250, 3)
                 .when(F.col("lifetime_value") >= 100, 2)
                 .otherwise(1))

# Segmentación de clientes
customer_analytics = customer_analytics \
    .withColumn("customer_value_segment",
                F.when((F.col("rfm_recency_score") >= 4) & 
                       (F.col("rfm_frequency_score") >= 4) & 
                       (F.col("rfm_monetary_score") >= 4), "Champions")
                 .when((F.col("rfm_recency_score") >= 3) & 
                       (F.col("rfm_frequency_score") >= 3), "Loyal Customers")
                 .when(F.col("rfm_recency_score") >= 4, "Potential Loyalists")
                 .when(F.col("rfm_frequency_score") <= 2, "At Risk")
                 .otherwise("Regular"))

# ============================================
# LOAD: Guardar resultados
# ============================================

# 1. Guardar ventas enriquecidas
enriched_sales_dyf = DynamicFrame.fromDF(enriched_sales, glueContext, "enriched_sales")
glueContext.write_dynamic_frame.from_options(
    frame=enriched_sales_dyf,
    connection_type="s3",
    connection_options={
        "path": f"{args['S3_OUTPUT_PATH']}/enriched_sales/",
        "partitionKeys": ["year", "month"]
    },
    format="parquet",
    format_options={"compression": "snappy"}
)

# 2. Guardar analytics de clientes
customer_analytics_dyf = DynamicFrame.fromDF(customer_analytics, glueContext, "customer_analytics")
glueContext.write_dynamic_frame.from_options(
    frame=customer_analytics_dyf,
    connection_type="s3",
    connection_options={
        "path": f"{args['S3_OUTPUT_PATH']}/customer_analytics/"
    },
    format="parquet"
)

print(f"""
Advanced ETL Job Completed:
===========================
Enriched sales records: {enriched_sales.count()}
Customer analytics records: {customer_analytics.count()}
Output location: {args['S3_OUTPUT_PATH']}
""")

job.commit()
```

---

## 📝 Ejercicio Práctico 1: Pipeline ETL Completo

### Objetivo
Crear un pipeline ETL que procese datos de transacciones bancarias, detecte fraudes potenciales y genere reportes analíticos.

### Datos de Entrada

**transactions.csv**
```csv
transaction_id,account_id,amount,merchant,category,timestamp,location
TXN001,ACC123,250.00,Amazon,Online Shopping,2024-01-15T10:30:00,US
TXN002,ACC123,5000.00,Wire Transfer,Transfer,2024-01-15T10:35:00,NG
TXN003,ACC456,45.99,Starbucks,Food & Beverage,2024-01-15T11:00:00,US
```

### Requisitos

1. **Limpieza de datos**:
   - Eliminar transacciones con montos negativos
   - Validar que todos los campos requeridos estén presentes
   - Convertir timestamps a formato estándar

2. **Detección de fraude**:
   - Marcar transacciones > $3000
   - Detectar múltiples transacciones en diferentes países en < 1 hora
   - Identificar patrones inusuales de gasto

3. **Agregaciones**:
   - Total de transacciones por cuenta
   - Gasto promedio por categoría
   - Transacciones por hora del día

4. **Salida**:
   - Datos limpios en Parquet particionado por fecha
   - Reporte de fraudes en CSV
   - Métricas agregadas en JSON

### Plantilla de Solución

```python
# Completa este script con la lógica necesaria

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# TODO: Inicializar contexto de Glue

# TODO: Cargar datos desde S3

# TODO: Implementar limpieza de datos

# TODO: Implementar lógica de detección de fraude

# TODO: Calcular agregaciones

# TODO: Guardar resultados en los formatos especificados
```

### Criterios de Evaluación

- ✅ Manejo correcto de datos nulos y valores atípicos
- ✅ Implementación eficiente de ventanas para detección de patrones
- ✅ Uso apropiado de particiones en la salida
- ✅ Código bien documentado y siguiendo mejores prácticas
- ✅ Logging y métricas de calidad de datos

---

## 🎓 Mejores Prácticas

### 1. Optimización de Performance

```python
# ❌ Evitar múltiples collect()
bad_df = spark.read.parquet("s3://...")
count = bad_df.count()
sample = bad_df.collect()  # Trae todos los datos a memoria

# ✅ Usar show() o take() para muestras
good_df = spark.read.parquet("s3://...")
good_df.show(10)
good_df.take(10)
```

### 2. Manejo de Datos Skewed

```python
# Detectar y manejar datos sesgados
from pyspark.sql.functions import broadcast

# Si una tabla es pequeña (<10GB), usar broadcast join
small_df = spark.read.parquet("s3://small-table/")
large_df = spark.read.parquet("s3://large-table/")

result = large_df.join(broadcast(small_df), "key")
```

### 3. Particionamiento Inteligente

```python
# Particionar por columnas de consulta frecuente
df.write \
    .partitionBy("year", "month", "day") \
    .mode("overwrite") \
    .parquet("s3://output/")

# Evitar sobre-particionamiento (>1000 particiones)
# Usar repartition si es necesario
df.repartition(100).write.parquet("s3://output/")
```

---

## 🔍 Preguntas de Reflexión

1. ¿Cuándo usarías un Crawler vs. definir el esquema manualmente?
2. ¿Qué estrategia de particionamiento usarías para un dataset de 10TB con consultas por fecha y por región?
3. ¿Cómo manejarías una tabla con 100 millones de registros donde el 80% tiene el mismo valor en la columna de join?

---

## 📚 Recursos Adicionales

- [AWS Glue Documentation](https://docs.aws.amazon.com/glue/)
- [PySpark API Reference](https://spark.apache.org/docs/latest/api/python/)
- [AWS Glue Best Practices](https://docs.aws.amazon.com/glue/latest/dg/best-practices.html)

---

**Próximo tema**: Automatización de procesos de datos con AWS Lambda