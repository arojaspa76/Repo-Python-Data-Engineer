![logo bsg](images/logobsg.png)

# Introducción a AWS Glue para Pipelines de Datos

# Sección 2: Automatización de Procesos de Datos con AWS Lambda

## 📋 Objetivos de Aprendizaje

Al finalizar esta sección, serás capaz de:
- Crear funciones Lambda para orquestar pipelines de datos
- Integrar Lambda con S3, Glue y otros servicios AWS
- Implementar triggers automáticos basados en eventos
- Manejar errores y reintentos en procesos automatizados
- Optimizar costos usando Lambda dentro del Free Tier

---

## 💰 Estimación de Costos - AWS FREE TIER OPTIMIZADO

**Lambda Free Tier (permanente, no solo 12 meses):**
- ✅ **1 millón de solicitudes gratuitas por mes**
- ✅ **400,000 GB-segundos de tiempo de cómputo por mes**
- ✅ Suficiente para **cientos de ejecuciones diarias**

**Configuración optimizada para este laboratorio:**
- Memoria: 512 MB (balance entre costo y rendimiento)
- Timeout: 5 minutos (máximo para orquestación)
- Ejecuciones estimadas: 50-100 por curso
- **Costo total: $0.00 USD** (100% dentro de Free Tier)

**Otros servicios relacionados:**
- ✅ S3 Event Notifications: Gratis
- ✅ CloudWatch Logs: 5 GB/mes gratis
- ✅ EventBridge: Gratis para reglas básicas
- ⚠️ Glue Jobs disparados: ~$0.10 por ejecución

**Total estimado sección 2: $0-2 USD** (solo por Glue jobs)

---

## ⚙️ PREREQUISITOS Y CONFIGURACIÓN

### 📝 Requisitos Previos

- ✅ Completar Sección 1 (AWS Glue configurado)
- ✅ Bucket S3 con estructura creada
- ✅ AWS CLI configurado
- ✅ Python 3.8+ con boto3
- ✅ Familiaridad con eventos asíncronos

---

## 🚀 PARTE 1: CONFIGURACIÓN DE LAMBDA

### Paso 1.1: Crear Rol IAM para Lambda

**Usando la Consola AWS:**

1. Ve a **IAM** → **Roles** → **Create role**
2. **Trusted entity type**: AWS service
3. **Use case**: Lambda
4. Click **Next**
5. Busca y selecciona estas políticas:
   - ✅ `AWSLambdaBasicExecutionRole` (logs de CloudWatch)
   - ✅ `AmazonS3FullAccess` (acceso a S3)
   - ✅ `AWSGlueConsoleFullAccess` (iniciar Glue jobs)
6. Click **Next**
7. **Role name**: `LambdaDataPipelineRole`
8. Click **Create role**

**Usando AWS CLI (más rápido):**

Crea el archivo `lambda-trust-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
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
    --role-name LambdaDataPipelineRole \
    --assume-role-policy-document file://lambda-trust-policy.json \
    --profile glue-lab

# Adjuntar políticas
aws iam attach-role-policy \
    --role-name LambdaDataPipelineRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
    --profile glue-lab

aws iam attach-role-policy \
    --role-name LambdaDataPipelineRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess \
    --profile glue-lab

aws iam attach-role-policy \
    --role-name LambdaDataPipelineRole \
    --policy-arn arn:aws:iam::aws:policy/AWSGlueConsoleFullAccess \
    --profile glue-lab

# Crear política custom para permisos granulares
cat > lambda-glue-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "glue:StartJobRun",
        "glue:GetJobRun",
        "glue:GetJobRuns",
        "glue:BatchStopJobRun"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam put-role-policy \
    --role-name LambdaDataPipelineRole \
    --policy-name GlueJobExecutionPolicy \
    --policy-document file://lambda-glue-policy.json \
    --profile glue-lab

# Verificar
aws iam get-role --role-name LambdaDataPipelineRole --profile glue-lab
```

---

## 💡 CONCEPTOS FUNDAMENTALES

### ¿Qué es AWS Lambda?

Lambda es un servicio de cómputo **serverless** que:
- Ejecuta código en respuesta a eventos
- Escala automáticamente
- Cobra solo por tiempo de ejecución
- No requiere gestión de servidores

### Patrones de Uso en Pipelines de Datos

```
┌─────────────────────────────────────────────────────────────┐
│                    PATRONES DE LAMBDA                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. EVENT-DRIVEN (Trigger por Evento)                      │
│     S3 Upload → Lambda → Start Glue Job                    │
│                                                             │
│  2. SCHEDULED (Ejecución Programada)                       │
│     EventBridge (cron) → Lambda → Orchestration            │
│                                                             │
│  3. ORCHESTRATION (Orquestación Compleja)                  │
│     Lambda → Múltiples Jobs en Paralelo/Secuencial         │
│                                                             │
│  4. DATA VALIDATION (Validación Pre-ETL)                   │
│     S3 Upload → Lambda → Validate → Start ETL              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 EJEMPLO 1: Lambda Trigger por S3 (Event-Driven)

### Caso de Uso Real: Auto-procesamiento de Archivos CSV

**Escenario**: Cada vez que se sube un archivo CSV de ventas a S3, automáticamente:
1. Lambda valida el formato del archivo
2. Si es válido, inicia un Glue Job para procesarlo
3. Envía notificación del resultado

### Paso 1.1: Crear la Función Lambda

**Código: `s3_trigger_glue_job.py`**

```python
import json
import boto3
import os
from datetime import datetime
from urllib.parse import unquote_plus

# Clientes AWS
s3_client = boto3.client('s3')
glue_client = boto3.client('glue')

# Configuración desde variables de entorno
GLUE_JOB_NAME = os.environ.get('GLUE_JOB_NAME', 'sales-etl-basic')
PROCESSED_PREFIX = os.environ.get('PROCESSED_PREFIX', 'processed/')

def lambda_handler(event, context):
    """
    Handler principal de Lambda que se activa cuando un archivo
    se sube a S3.
    
    Args:
        event: Evento S3 con información del archivo subido
        context: Contexto de Lambda con metadata de ejecución
    
    Returns:
        dict: Respuesta con estado de la operación
    """
    
    print(f"🚀 Lambda iniciado: {context.function_name}")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    print(f"📦 Event: {json.dumps(event, indent=2)}")
    
    try:
        # Extraer información del evento S3
        record = event['Records'][0]
        bucket_name = record['s3']['bucket']['name']
        object_key = unquote_plus(record['s3']['object']['key'])
        file_size = record['s3']['object']['size']
        
        print(f"📁 Archivo detectado:")
        print(f"   Bucket: {bucket_name}")
        print(f"   Key: {object_key}")
        print(f"   Size: {file_size} bytes")
        
        # Validar que sea un archivo CSV en la carpeta correcta
        if not object_key.startswith('raw/sales/'):
            print(f"⚠️  Archivo no está en raw/sales/, ignorando...")
            return {
                'statusCode': 200,
                'body': json.dumps('File not in target folder, skipping')
            }
        
        if not object_key.endswith('.csv'):
            print(f"⚠️  Archivo no es CSV, ignorando...")
            return {
                'statusCode': 200,
                'body': json.dumps('Not a CSV file, skipping')
            }
        
        # Validación básica del archivo
        validation_result = validate_csv_file(bucket_name, object_key)
        
        if not validation_result['is_valid']:
            print(f"❌ Validación fallida: {validation_result['error']}")
            
            # Mover archivo a carpeta de errores
            move_to_error_folder(bucket_name, object_key, validation_result['error'])
            
            return {
                'statusCode': 400,
                'body': json.dumps(f"Validation failed: {validation_result['error']}")
            }
        
        print(f"✅ Archivo válido, iniciando Glue Job...")
        
        # Iniciar Glue Job
        job_run_response = glue_client.start_job_run(
            JobName=GLUE_JOB_NAME,
            Arguments={
                '--INPUT_FILE': f's3://{bucket_name}/{object_key}',
                '--TIMESTAMP': datetime.now().isoformat(),
                '--enable-metrics': 'true',
                '--enable-continuous-cloudwatch-log': 'true'
            }
        )
        
        job_run_id = job_run_response['JobRunId']
        print(f"🎯 Glue Job iniciado: {job_run_id}")
        
        # Marcar archivo como procesado (agregar metadata)
        add_processing_metadata(bucket_name, object_key, job_run_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Glue job started successfully',
                'job_run_id': job_run_id,
                'file': object_key
            })
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }


def validate_csv_file(bucket_name, object_key):
    """
    Valida que el archivo CSV tenga el formato correcto.
    
    Args:
        bucket_name: Nombre del bucket S3
        object_key: Key del objeto en S3
    
    Returns:
        dict: Resultado de validación con is_valid y error
    """
    try:
        # Descargar las primeras líneas del archivo (optimización)
        response = s3_client.get_object(
            Bucket=bucket_name,
            Key=object_key,
            Range='bytes=0-1024'  # Solo primeros 1KB
        )
        
        content = response['Body'].read().decode('utf-8')
        lines = content.split('\n')
        
        if len(lines) < 2:
            return {
                'is_valid': False,
                'error': 'File has less than 2 lines (no data)'
            }
        
        # Validar headers esperados
        header = lines[0].strip()
        expected_columns = [
            'transaction_id', 'customer_id', 'product_id',
            'quantity', 'price', 'transaction_date'
        ]
        
        actual_columns = [col.strip() for col in header.split(',')]
        
        if actual_columns != expected_columns:
            return {
                'is_valid': False,
                'error': f'Invalid columns. Expected: {expected_columns}, Got: {actual_columns}'
            }
        
        # Validar que haya al menos una línea de datos
        if len(lines) < 2 or not lines[1].strip():
            return {
                'is_valid': False,
                'error': 'File has no data rows'
            }
        
        print(f"✅ Validación exitosa: {len(lines)-1} líneas de datos")
        
        return {
            'is_valid': True,
            'error': None
        }
        
    except Exception as e:
        return {
            'is_valid': False,
            'error': f'Validation error: {str(e)}'
        }


def move_to_error_folder(bucket_name, object_key, error_message):
    """
    Mueve archivo inválido a carpeta de errores.
    """
    try:
        # Crear nuevo key en carpeta de errores
        file_name = object_key.split('/')[-1]
        error_key = f'errors/{datetime.now().strftime("%Y%m%d")}/{file_name}'
        
        # Copiar archivo
        s3_client.copy_object(
            Bucket=bucket_name,
            CopySource={'Bucket': bucket_name, 'Key': object_key},
            Key=error_key,
            Metadata={
                'error': error_message,
                'original_key': object_key,
                'timestamp': datetime.now().isoformat()
            },
            MetadataDirective='REPLACE'
        )
        
        # Eliminar original
        s3_client.delete_object(Bucket=bucket_name, Key=object_key)
        
        print(f"📦 Archivo movido a: {error_key}")
        
    except Exception as e:
        print(f"⚠️  Error moviendo archivo: {str(e)}")


def add_processing_metadata(bucket_name, object_key, job_run_id):
    """
    Agrega metadata de procesamiento al archivo S3.
    """
    try:
        s3_client.copy_object(
            Bucket=bucket_name,
            CopySource={'Bucket': bucket_name, 'Key': object_key},
            Key=object_key,
            Metadata={
                'processing_status': 'started',
                'glue_job_run_id': job_run_id,
                'processed_timestamp': datetime.now().isoformat()
            },
            MetadataDirective='REPLACE'
        )
        
        print(f"✅ Metadata agregada al archivo")
        
    except Exception as e:
        print(f"⚠️  Error agregando metadata: {str(e)}")
```

### Paso 1.2: Crear la Función en AWS

**Opción A: Usando la Consola**

1. Ve a **Lambda** → **Create function**
2. Selecciona **Author from scratch**
3. **Function name**: `S3-Glue-Trigger`
4. **Runtime**: Python 3.12
5. **Architecture**: x86_64
6. **Permissions**: Use existing role → `LambdaDataPipelineRole`
7. Click **Create function**

8. En el editor de código:
   - Borra el código default
   - Pega el código de `s3_trigger_glue_job.py`
   - Click **Deploy**

9. **Configuration** → **General configuration** → **Edit**:
   - **Memory**: 512 MB
   - **Timeout**: 5 minutes
   - Click **Save**

10. **Configuration** → **Environment variables** → **Edit**:
    - Key: `GLUE_JOB_NAME`, Value: `sales-etl-basic`
    - Key: `PROCESSED_PREFIX`, Value: `processed/`
    - Click **Save**

**Opción B: Usando AWS CLI (automatizado)**

Primero, empaqueta el código:

```bash
# Crear directorio de deployment
mkdir lambda_deployment
cd lambda_deployment

# Copiar código
cat > lambda_function.py << 'EOF'
# (Pegar aquí el código completo de s3_trigger_glue_job.py)
EOF

# Crear ZIP
zip -r function.zip lambda_function.py

# Obtener ARN del rol
ROLE_ARN=$(aws iam get-role --role-name LambdaDataPipelineRole --profile glue-lab --query 'Role.Arn' --output text)

# Crear función Lambda
aws lambda create-function \
    --function-name S3-Glue-Trigger \
    --runtime python3.12 \
    --role $ROLE_ARN \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://function.zip \
    --timeout 300 \
    --memory-size 512 \
    --environment Variables="{GLUE_JOB_NAME=sales-etl-basic,PROCESSED_PREFIX=processed/}" \
    --profile glue-lab

echo "✅ Lambda function created!"
```

### Paso 1.3: Configurar S3 Trigger

**Usando la Consola:**

1. En la función Lambda, click en **Add trigger**
2. **Select a trigger**: S3
3. **Bucket**: Selecciona tu bucket (ej: `glue-lab-juan-12345`)
4. **Event type**: All object create events
5. **Prefix**: `raw/sales/`
6. **Suffix**: `.csv`
7. ✅ Marcar: **I acknowledge that using the same S3 bucket...**
8. Click **Add**

**Usando AWS CLI:**

```bash
# Configurar variables
BUCKET_NAME="tu-bucket-aqui"
LAMBDA_ARN=$(aws lambda get-function --function-name S3-Glue-Trigger --profile glue-lab --query 'Configuration.FunctionArn' --output text)

# Dar permiso a S3 para invocar Lambda
aws lambda add-permission \
    --function-name S3-Glue-Trigger \
    --statement-id s3-trigger-permission \
    --action lambda:InvokeFunction \
    --principal s3.amazonaws.com \
    --source-arn arn:aws:s3:::$BUCKET_NAME \
    --profile glue-lab

# Crear configuración de notificación
cat > s3-notification.json << EOF
{
  "LambdaFunctionConfigurations": [
    {
      "LambdaFunctionArn": "$LAMBDA_ARN",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [
            {"Name": "prefix", "Value": "raw/sales/"},
            {"Name": "suffix", "Value": ".csv"}
          ]
        }
      }
    }
  ]
}
EOF

# Aplicar configuración
aws s3api put-bucket-notification-configuration \
    --bucket $BUCKET_NAME \
    --notification-configuration file://s3-notification.json \
    --profile glue-lab

echo "✅ S3 trigger configured!"
```

### Paso 1.4: Probar la Integración

```bash
# Subir archivo de prueba
echo "transaction_id,customer_id,product_id,quantity,price,transaction_date
TEST001,CUST999,PROD999,1,99.99,2024-12-15" > test_sales.csv

aws s3 cp test_sales.csv s3://$BUCKET_NAME/raw/sales/ --profile glue-lab

# Esperar 10 segundos y verificar logs
sleep 10

# Ver logs de Lambda
aws logs tail /aws/lambda/S3-Glue-Trigger --follow --profile glue-lab
```

---

## 🎨 EJEMPLO 2: Orquestación Compleja con Step Functions

### Caso de Uso: Pipeline Multi-Etapa

**Flujo**:
1. Validar datos
2. Ejecutar ETL de ventas
3. Ejecutar ETL de clientes (en paralelo)
4. Combinar resultados
5. Generar reporte

### Lambda para Orquestación: `orchestrator_lambda.py`

```python
import json
import boto3
import time
from datetime import datetime

glue_client = boto3.client('glue')
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    Orquesta la ejecución de múltiples Glue Jobs en secuencia.
    """
    
    pipeline_id = event.get('pipeline_id', f"pipeline-{int(time.time())}")
    bucket_name = event.get('bucket_name')
    
    print(f"🎭 Iniciando orquestación: {pipeline_id}")
    
    results = {
        'pipeline_id': pipeline_id,
        'started_at': datetime.now().isoformat(),
        'jobs': []
    }
    
    try:
        # Etapa 1: Validar datos crudos
        print("📊 Etapa 1: Validando datos...")
        validation_result = validate_raw_data(bucket_name)
        
        if not validation_result['valid']:
            raise Exception(f"Validation failed: {validation_result['errors']}")
        
        results['validation'] = validation_result
        
        # Etapa 2: Ejecutar Jobs de Glue en paralelo
        print("🚀 Etapa 2: Iniciando Glue Jobs...")
        
        jobs_to_run = [
            {
                'name': 'sales-etl-basic',
                'description': 'Procesar ventas'
            },
            {
                'name': 'customer-etl',  # Asumiendo que existe
                'description': 'Procesar clientes'
            }
        ]
        
        job_run_ids = []
        
        for job_config in jobs_to_run:
            try:
                response = glue_client.start_job_run(
                    JobName=job_config['name'],
                    Arguments={
                        '--pipeline_id': pipeline_id,
                        '--enable-metrics': 'true'
                    }
                )
                
                job_run_id = response['JobRunId']
                job_run_ids.append({
                    'job_name': job_config['name'],
                    'job_run_id': job_run_id,
                    'description': job_config['description']
                })
                
                print(f"  ✅ {job_config['name']}: {job_run_id}")
                
            except Exception as e:
                print(f"  ❌ Error en {job_config['name']}: {str(e)}")
                job_run_ids.append({
                    'job_name': job_config['name'],
                    'error': str(e)
                })
        
        results['jobs'] = job_run_ids
        
        # Etapa 3: Monitorear progreso (non-blocking)
        print("⏳ Etapa 3: Jobs iniciados, monitoreo asíncrono...")
        
        results['status'] = 'RUNNING'
        results['message'] = f"Pipeline {pipeline_id} iniciado con {len(job_run_ids)} jobs"
        
        # Guardar metadata del pipeline
        save_pipeline_metadata(bucket_name, pipeline_id, results)
        
        return {
            'statusCode': 200,
            'body': json.dumps(results, default=str)
        }
        
    except Exception as e:
        print(f"❌ Error en orquestación: {str(e)}")
        
        results['status'] = 'FAILED'
        results['error'] = str(e)
        
        return {
            'statusCode': 500,
            'body': json.dumps(results, default=str)
        }


def validate_raw_data(bucket_name):
    """
    Valida que todos los archivos requeridos existan.
    """
    required_files = [
        'raw/sales/sales_data.csv',
        'raw/customers/customers_data.csv'
    ]
    
    validation_result = {
        'valid': True,
        'errors': [],
        'files_checked': []
    }
    
    for file_key in required_files:
        try:
            s3_client.head_object(Bucket=bucket_name, Key=file_key)
            validation_result['files_checked'].append({
                'file': file_key,
                'status': 'EXISTS'
            })
        except:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Missing file: {file_key}")
            validation_result['files_checked'].append({
                'file': file_key,
                'status': 'MISSING'
            })
    
    return validation_result


def save_pipeline_metadata(bucket_name, pipeline_id, metadata):
    """
    Guarda metadata del pipeline en S3.
    """
    try:
        key = f"pipelines/{pipeline_id}/metadata.json"
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=json.dumps(metadata, indent=2, default=str),
            ContentType='application/json'
        )
        
        print(f"💾 Metadata guardada en: s3://{bucket_name}/{key}")
        
    except Exception as e:
        print(f"⚠️  Error guardando metadata: {str(e)}")
```

---

## 🔔 EJEMPLO 3: Scheduled Lambda (Ejecución Programada)

### Caso de Uso: Reporte Diario Automático

**Lambda para reportes programados: `scheduled_report.py`**

```python
import json
import boto3
from datetime import datetime, timedelta

s3_client = boto3.client('s3')
glue_client = boto3.client('glue')

def lambda_handler(event, context):
    """
    Se ejecuta diariamente a las 2 AM para generar reporte del día anterior.
    """
    
    print(f"📅 Generando reporte diario: {datetime.now().isoformat()}")
    
    # Calcular fecha del reporte (ayer)
    report_date = datetime.now() - timedelta(days=1)
    date_str = report_date.strftime('%Y-%m-%d')
    
    print(f"📊 Fecha del reporte: {date_str}")
    
    try:
        # Iniciar job de agregación diaria
        response = glue_client.start_job_run(
            JobName='daily-aggregation-job',
            Arguments={
                '--report_date': date_str,
                '--enable-metrics': 'true'
            }
        )
        
        job_run_id = response['JobRunId']
        print(f"✅ Job de agregación iniciado: {job_run_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Daily report job started',
                'date': date_str,
                'job_run_id': job_run_id
            })
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

### Configurar EventBridge Rule (Cron)

```bash
# Crear regla de EventBridge para ejecución diaria a las 2 AM
aws events put-rule \
    --name DailyReportTrigger \
    --schedule-expression "cron(0 2 * * ? *)" \
    --state ENABLED \
    --description "Trigger daily report generation at 2 AM" \
    --profile glue-lab

# Obtener ARN de Lambda
LAMBDA_ARN=$(aws lambda get-function --function-name scheduled-report --profile glue-lab --query 'Configuration.FunctionArn' --output text)

# Dar permiso a EventBridge
aws lambda add-permission \
    --function-name scheduled-report \
    --statement-id eventbridge-daily-trigger \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:us-east-1:$(aws sts get-caller-identity --query Account --output text):rule/DailyReportTrigger \
    --profile glue-lab

# Agregar Lambda como target
aws events put-targets \
    --rule DailyReportTrigger \
    --targets "Id"="1","Arn"="$LAMBDA_ARN" \
    --profile glue-lab

echo "✅ Scheduled trigger configured!"
```

---

## 📝 EJERCICIO PRÁCTICO 2: Sistema de Monitoreo y Alertas

### Objetivo

Crear un sistema que:
1. Monitorea el estado de Glue Jobs
2. Detecta fallos y reintentos automáticamente
3. Envía notificaciones por SNS (opcional)

### Requisitos

**Lambda: `job_monitor.py`**

```python
import json
import boto3
import time
from datetime import datetime

glue_client = boto3.client('glue')
# sns_client = boto3.client('sns')  # Descomentar si usas SNS

def lambda_handler(event, context):
    """
    Monitorea el estado de un Glue Job y reintenta si falla.
    
    Event debe contener:
    {
        "job_name": "sales-etl-basic",
        "job_run_id": "jr_xxx",
        "retry_count": 0
    }
    """
    
    job_name = event['job_name']
    job_run_id = event['job_run_id']
    retry_count = event.get('retry_count', 0)
    max_retries = 3
    
    print(f"🔍 Monitoreando Job: {job_name}")
    print(f"   Run ID: {job_run_id}")
    print(f"   Retry: {retry_count}/{max_retries}")
    
    try:
        # Obtener estado del job
        response = glue_client.get_job_run(
            JobName=job_name,
            RunId=job_run_id
        )
        
        job_run = response['JobRun']
        status = job_run['JobRunState']
        
        print(f"📊 Estado actual: {status}")
        
        # Estados posibles: STARTING, RUNNING, STOPPING, STOPPED, SUCCEEDED, FAILED, TIMEOUT
        
        if status == 'SUCCEEDED':
            print("✅ Job completado exitosamente!")
            
            return {
                'statusCode': 200,
                'status': 'SUCCEEDED',
                'job_name': job_name,
                'job_run_id': job_run_id,
                'message': 'Job completed successfully'
            }
        
        elif status in ['FAILED', 'TIMEOUT', 'STOPPED']:
            error_message = job_run.get('ErrorMessage', 'Unknown error')
            print(f"❌ Job falló: {error_message}")
            
            # Reintentar si no se alcanzó el máximo
            if retry_count < max_retries:
                print(f"🔄 Reintentando... ({retry_count + 1}/{max_retries})")
                
                # Iniciar nuevo job run
                retry_response = glue_client.start_job_run(
                    JobName=job_name,
                    Arguments={
                        '--retry_attempt': str(retry_count + 1),
                        '--original_run_id': job_run_id,
                        '--enable-metrics': 'true'
                    }
                )
                
                new_job_run_id = retry_response['JobRunId']
                print(f"🆕 Nuevo job iniciado: {new_job_run_id}")
                
                # Enviar notificación de reintento (descomentar si usas SNS)
                # send_notification(
                #     f"Job {job_name} falló, reintentando ({retry_count + 1}/{max_retries})",
                #     error_message
                # )
                
                return {
                    'statusCode': 202,
                    'status': 'RETRYING',
                    'job_name': job_name,
                    'original_run_id': job_run_id,
                    'new_run_id': new_job_run_id,
                    'retry_count': retry_count + 1,
                    'message': f'Retrying job (attempt {retry_count + 1})'
                }
            else:
                print(f"🚫 Máximo de reintentos alcanzado")
                
                # Enviar alerta crítica
                # send_notification(
                #     f"CRITICAL: Job {job_name} falló después de {max_retries} reintentos",
                #     error_message
                # )
                
                return {
                    'statusCode': 500,
                    'status': 'FAILED',
                    'job_name': job_name,
                    'job_run_id': job_run_id,
                    'retry_count': retry_count,
                    'error': error_message,
                    'message': 'Job failed after max retries'
                }
        
        else:  # STARTING, RUNNING, STOPPING
            print(f"⏳ Job aún en progreso...")
            
            return {
                'statusCode': 202,
                'status': status,
                'job_name': job_name,
                'job_run_id': job_run_id,
                'message': 'Job still in progress'
            }
    
    except Exception as e:
        print(f"❌ Error monitoreando job: {str(e)}")
        
        return {
            'statusCode': 500,
            'error': str(e),
            'message': 'Error monitoring job'
        }


def send_notification(subject, message):
    """
    Envía notificación por SNS (opcional).
    """
    try:
        sns_topic_arn = 'arn:aws:sns:us-east-1:ACCOUNT_ID:data-pipeline-alerts'
        
        # sns_client.publish(
        #     TopicArn=sns_topic_arn,
        #     Subject=subject,
        #     Message=message
        # )
        
        print(f"📧 Notificación enviada: {subject}")
        
    except Exception as e:
        print(f"⚠️  Error enviando notificación: {str(e)}")
```

### Plantilla de Solución

**Tu tarea**: Implementar la función completa con:

1. ✅ Monitoreo de estado de job
2. ✅ Lógica de reintentos (máximo 3)
3. ✅ Logging detallado
4. ✅ Manejo de errores robusto
5. ⭐ BONUS: Integración con SNS para alertas

### Criterios de Evaluación

- ✅ Manejo correcto de todos los estados de Glue
- ✅ Implementación de reintentos con backoff
- ✅ Logging claro y estructurado
- ✅ Manejo de errores y casos edge
- ✅ Optimización para Free Tier

---

## 🎓 MEJORES PRÁCTICAS

### 1. Manejo de Errores y Reintentos

```python
import time
from functools import wraps

def retry_with_backoff(max_retries=3, backoff_factor=2):
    """
    Decorator para reintentar operaciones con exponential backoff.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    
                    wait_time = backoff_factor ** attempt
                    print(f"⚠️  Intento {attempt + 1} falló, esperando {wait_time}s...")
                    time.sleep(wait_time)
            
        return wrapper
    return decorator

# Uso
@retry_with_backoff(max_retries=3, backoff_factor=2)
def start_glue_job(job_name):
    return glue_client.start_job_run(JobName=job_name)
```

### 2. Logging Estructurado

```python
import json
import logging

# Configurar logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def log_event(event_type, details):
    """
    Logging estructurado para mejor análisis en CloudWatch.
    """
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'event_type': event_type,
        'details': details
    }
    
    logger.info(json.dumps(log_entry))

# Uso
log_event('JOB_STARTED', {
    'job_name': 'sales-etl-basic',
    'trigger': 's3_upload'
})
```

### 3. Optimización de Memoria

```python
def lambda_handler(event, context):
    """
    Monitorea uso de memoria para optimizar costos.
    """
    import sys
    
    # Obtener memoria disponible
    memory_limit = int(context.memory_limit_in_mb)
    memory_used = sys.getsizeof(event) / (1024 * 1024)
    
    print(f"💾 Memoria - Límite: {memory_limit}MB, Usado: {memory_used:.2f}MB")
    
    # Tu código aquí...
    
    # Si consistentemente usas < 256MB, reduce la configuración
    if memory_used < memory_limit * 0.3:
        print(f"💡 Considera reducir memoria a {int(memory_limit/2)}MB")
```

### 4. Idempotencia

```python
def lambda_handler(event, context):
    """
    Lambda idempotente - puede ejecutarse múltiples veces sin efectos adversos.
    """
    
    # Generar request_id único basado en el evento
    import hashlib
    event_hash = hashlib.md5(
        json.dumps(event, sort_keys=True).encode()
    ).hexdigest()
    
    request_id = f"req-{event_hash[:8]}"
    
    # Verificar si ya se procesó
    try:
        s3_client.head_object(
            Bucket=bucket_name,
            Key=f'processed/{request_id}.json'
        )
        
        print(f"⚠️  Request {request_id} ya procesado, omitiendo...")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Already processed'})
        }
        
    except s3_client.exceptions.NoSuchKey:
        # Continuar con procesamiento...
        pass
    
    # Marcar como procesado al finalizar
    s3_client.put_object(
        Bucket=bucket_name,
        Key=f'processed/{request_id}.json',
        Body=json.dumps({'processed_at': datetime.now().isoformat()})
    )
```

### 5. Variables de Entorno Seguras

```python
import os

# ✅ BUENAS PRÁCTICAS
BUCKET_NAME = os.environ.get('BUCKET_NAME')
GLUE_JOB_NAME = os.environ.get('GLUE_JOB_NAME')

if not BUCKET_NAME or not GLUE_JOB_NAME:
    raise ValueError("Required environment variables not set")

# ❌ EVITAR
BUCKET_NAME = "hardcoded-bucket-name"  # No hacer esto!
```

---

## 📊 MONITOREO Y MÉTRICAS

### Dashboard de CloudWatch

Crea un dashboard para monitorear tus Lambdas:

```bash
# Crear dashboard de CloudWatch
cat > dashboard.json << 'EOF'
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Invocations", {"stat": "Sum"}],
          [".", "Errors", {"stat": "Sum"}],
          [".", "Duration", {"stat": "Average"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Lambda Metrics"
      }
    }
  ]
}
EOF

aws cloudwatch put-dashboard \
    --dashboard-name DataPipelineDashboard \
    --dashboard-body file://dashboard.json \
    --profile glue-lab
```

### Consultas de CloudWatch Insights

```bash
# Ver errores recientes
aws logs tail /aws/lambda/S3-Glue-Trigger \
    --filter-pattern "ERROR" \
    --since 1h \
    --profile glue-lab

# Análisis de performance
aws logs insights query \
    --log-group-name /aws/lambda/S3-Glue-Trigger \
    --start-time $(date -d '1 hour ago' +%s) \
    --end-time $(date +%s) \
    --query-string 'fields @timestamp, @message | filter @type = "REPORT" | stats avg(@duration), max(@duration), min(@duration)' \
    --profile glue-lab
```

---

## 🧪 TESTING LOCAL

### Probar Lambda Localmente

Instala AWS SAM CLI:

```bash
# Instalar SAM CLI
pip install aws-sam-cli

# Crear evento de prueba
cat > test_event.json << 'EOF'
{
  "Records": [
    {
      "s3": {
        "bucket": {"name": "tu-bucket"},
        "object": {"key": "raw/sales/test.csv", "size": 1024}
      }
    }
  ]
}
EOF

# Invocar Lambda localmente
sam local invoke S3-Glue-Trigger --event test_event.json
```

### Unit Tests con pytest

```python
# test_lambda.py
import pytest
import json
from unittest.mock import Mock, patch
import lambda_function

def test_validate_csv_valid():
    """Test validación de CSV válido"""
    
    with patch('lambda_function.s3_client') as mock_s3:
        # Mock respuesta de S3
        mock_s3.get_object.return_value = {
            'Body': Mock(read=lambda: b'transaction_id,customer_id\nTXN001,CUST123')
        }
        
        result = lambda_function.validate_csv_file('bucket', 'key')
        
        assert result['is_valid'] == True
        assert result['error'] is None

def test_lambda_handler_invalid_file():
    """Test handler con archivo inválido"""
    
    event = {
        'Records': [{
            's3': {
                'bucket': {'name': 'test-bucket'},
                'object': {'key': 'raw/sales/invalid.txt', 'size': 100}
            }
        }]
    }
    
    result = lambda_function.lambda_handler(event, None)
    
    assert result['statusCode'] == 200
    assert 'skipping' in result['body']

# Ejecutar tests
# pytest test_lambda.py -v
```

---

## 🧹 LIMPIEZA DE RECURSOS

### Al Terminar Cada Sesión

```bash
# Script: cleanup_lambda.sh

#!/bin/bash
PROFILE="glue-lab"

echo "🧹 Limpiando recursos de Lambda..."

# 1. Eliminar triggers de EventBridge
aws events remove-targets \
    --rule DailyReportTrigger \
    --ids "1" \
    --profile $PROFILE 2>/dev/null

aws events delete-rule \
    --name DailyReportTrigger \
    --profile $PROFILE 2>/dev/null

# 2. Eliminar notificaciones de S3
BUCKET_NAME="tu-bucket-aqui"
aws s3api put-bucket-notification-configuration \
    --bucket $BUCKET_NAME \
    --notification-configuration '{}' \
    --profile $PROFILE 2>/dev/null

# 3. NO eliminar funciones Lambda (rápido recrearlas si necesitas)
# Solo si quieres limpieza completa:
# aws lambda delete-function --function-name S3-Glue-Trigger --profile $PROFILE

echo "✅ Limpieza completada"
```

### Verificar Uso de Free Tier

```bash
# Ver invocaciones de Lambda del mes
aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Invocations \
    --dimensions Name=FunctionName,Value=S3-Glue-Trigger \
    --start-time $(date -d '30 days ago' -u +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 2592000 \
    --statistics Sum \
    --profile glue-lab

# Calcular GB-segundos usados
aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Duration \
    --dimensions Name=FunctionName,Value=S3-Glue-Trigger \
    --start-time $(date -d '30 days ago' -u +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 2592000 \
    --statistics Sum \
    --profile glue-lab
```

---

## 📚 RECURSOS ADICIONALES

### Documentación Oficial
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [EventBridge Scheduler](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-rule-schedule.html)

### Herramientas Útiles
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
- [Lambda Powertools Python](https://awslabs.github.io/aws-lambda-powertools-python/)
- [Serverless Framework](https://www.serverless.com/)

### Patrones Avanzados
- [Lambda Destinations](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async.html#invocation-async-destinations)
- [Step Functions con Lambda](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-standard-vs-express.html)
- [Lambda Layers](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html)

---

## 🎯 RESUMEN DE LA SECCIÓN

### ✅ Has Aprendido:

1. **Event-Driven Architecture**
   - Triggers de S3
   - Validación automática de datos
   - Integración Lambda → Glue

2. **Orquestación**
   - Ejecución de múltiples jobs
   - Manejo de dependencias
   - Metadata tracking

3. **Scheduled Jobs**
   - EventBridge rules
   - Cron expressions
   - Reportes automáticos

4. **Monitoring & Alerting**
   - Estado de jobs
   - Reintentos automáticos
   - CloudWatch metrics

5. **Best Practices**
   - Idempotencia
   - Error handling
   - Cost optimization
   - Testing

### 💰 Costo Total Sección 2:
- Lambda invocations: **$0.00** (Free Tier)
- CloudWatch Logs: **$0.00** (Free Tier)
- Glue jobs disparados: **~$1-2 USD**
- **Total: $1-2 USD**

---

## 🔄 Transición a Sección 3

En la siguiente sección, aprenderemos:
- **Optimización de performance** de Glue jobs
- **Estrategias de particionamiento** avanzadas
- **Compresión y formatos** de datos
- **Monitoring y debugging** de pipelines
- **Cost optimization** a escala

**¿Listo para la Sección 3: Optimización de Pipelines?** 🚀