# Cloud Portals Guide – Crear Storage + Functions + Códigos Python (Azure, AWS, GCP)
## Ejercicio Practico para desarrollarlo en clase
## Se usa el codigo de la session_6

Esta guía contiene:

✔️ Pasos **clic por clic** desde los portales web de Azure, AWS y GCP  
✔️ Cómo crear Storage en cada nube  
✔️ Cómo crear Functions/Lambda/Cloud Functions  
✔️ **Los códigos Python completos que deben copiarse dentro de cada función**  
✔️ Archivo listo para GitHub  

---

# 0. Archivo de datos usado (`data.csv`)

```
42
7
13
99
5
```

---

# 1. Azure Portal – Blob Storage + Azure Function (HTTP Trigger)

## 1.1. Crear Storage Account y contenedor (Portal Web)

1. Ir a: https://portal.azure.com  
2. Create a Resource → “Storage account” → **Create**  
3. Configuración:  
   - RG: `rg-algoritmos-azure`  
   - Nombre: `algostorage<unico>`  
   - Region: East US  
   - Redundancy: LRS  
4. Review + Create  
5. Ir al Storage → Containers → **+ Container**  
6. Nombre: `datasets`  
7. Entrar al contenedor → **Upload** → subir `data.csv`

---

## 1.2. Crear Function App

1. Create a Resource → **Function App**  
2. Configuración:
   - Publish: Code  
   - Runtime: Python 3.11  
   - OS: Linux  
   - Region: misma del Storage  
   - Storage: seleccionar el Storage creado  
3. Review + Create

---

## 1.3. Crear Function HTTP en el portal

1. Function App → **Functions** → **+ Create**  
2. Develop in portal  
3. Template: HTTP trigger  
4. Name: `sort_and_search`  
5. Auth level: Anonymous  

---

## 1.4. Configurar Application Settings

En Function App → **Configuration** → Application Settings:

```
AZURE_STORAGE_ACCOUNT_NAME=<nombre_storage>
AZURE_STORAGE_ACCOUNT_KEY=<key>
AZURE_STORAGE_CONTAINER=datasets
AZURE_STORAGE_BLOB=data.csv
```

Guardar y reiniciar.

---

## 1.5. Copiar el CÓDIGO PYTHON completo dentro de Azure Function

En la función → **Code + Test** → abrir `__init__.py` y pegar:

```python
import logging
import os
import azure.functions as func
from azure.storage.blob import BlobServiceClient

def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr)//2]
    left  = [x for x in arr if x < pivot]
    mid   = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + mid + quicksort(right)

def binary_search(sorted_list, target):
    left, right = 0, len(sorted_list)-1
    while left <= right:
        mid = (left + right) // 2
        if sorted_list[mid] == target:
            return mid
        elif sorted_list[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

def main(req: func.HttpRequest) -> func.HttpResponse:
    target = req.params.get("target")
    if not target:
        body = req.get_json(silent=True) or {}
        target = body.get("target")
    if target is None:
        return func.HttpResponse("Please pass target", status_code=400)
    target = int(target)

    acc = os.environ["AZURE_STORAGE_ACCOUNT_NAME"]
    key = os.environ["AZURE_STORAGE_ACCOUNT_KEY"]
    container = os.environ["AZURE_STORAGE_CONTAINER"]
    blob_name = os.environ["AZURE_STORAGE_BLOB"]

    conn = (
        f"DefaultEndpointsProtocol=https;AccountName={acc};"
        f"AccountKey={key};EndpointSuffix=core.windows.net"
    )

    client = BlobServiceClient.from_connection_string(conn)
    blob_client = client.get_container_client(container).get_blob_client(blob_name)

    data = blob_client.download_blob().readall().decode().splitlines()
    numbers = [int(x) for x in data if x]

    sorted_numbers = quicksort(numbers)
    index = binary_search(sorted_numbers, target)

    return func.HttpResponse(
        body=str({
            "original": numbers,
            "sorted": sorted_numbers,
            "target": target,
            "index": index
        }),
        mimetype="application/json"
    )
```

---

## 1.6. Probar desde el portal

1. Code + Test  
2. Test/Run → GET  
3. Query: `target=13`  
4. Ejecutar  

---

# 2. AWS Console – S3 + AWS Lambda (Editor Web)

## 2.1. Crear bucket S3

1. https://console.aws.amazon.com  
2. Buscar S3 → **Create bucket**  
3. Nombre: `algorithms-demo-<unico>`  
4. Region: us-east-1  
5. Upload → seleccionar `data.csv`

---

## 2.2. Crear Lambda (Author from scratch)

1. AWS Console → Lambda  
2. Create Function → Author from Scratch  
3. Name: `algorithms-demo`  
4. Runtime: Python 3.x  
5. Crear rol básico  

---

## 2.3. Permisos de lectura S3

1. Lambda → Configuration → Permissions  
2. Abrir Role  
3. Attach policy: `AmazonS3ReadOnlyAccess`

---

## 2.4. Copiar el CÓDIGO PYTHON completo dentro de Lambda

En la pestaña **Code**, archivo `lambda_function.py`:

```python
import json
import boto3

s3 = boto3.client("s3")

def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr)//2]
    left  = [x for x in arr if x < pivot]
    mid   = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + mid + quicksort(right)

def binary_search(sorted_list, target):
    left, right = 0, len(sorted_list)-1
    while left <= right:
        mid = (left + right) // 2
        if sorted_list[mid] == target:
            return mid
        elif sorted_list[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

def lambda_handler(event, context):
    bucket = event["bucket"]
    key = event.get("key", "data.csv")
    target = int(event.get("target", 13))

    raw = s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode().splitlines()
    numbers = [int(x) for x in raw if x]

    sorted_numbers = quicksort(numbers)
    index = binary_search(sorted_numbers, target)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "original": numbers,
            "sorted": sorted_numbers,
            "target": target,
            "index": index
        })
    }
```

---

## 2.5. Probar Lambda

Evento de prueba:

```json
{
  "bucket": "algorithms-demo-XXXX",
  "key": "data.csv",
  "target": 13
}
```

Presionar **Test**.

---

# 3. Google Cloud Console – Cloud Storage + Cloud Functions

## 3.1. Crear bucket en Cloud Storage

1. https://console.cloud.google.com  
2. Cloud Storage → Buckets → Create  
3. Nombre: `algorithms-demo-<unico>`  
4. Location: us-central1  
5. Upload `data.csv`

---

## 3.2. Crear Cloud Function (HTTP)

1. Cloud Run → Create Function  
2. Runtime: Python 3.11  
3. Auth: Allow unauthenticated  
4. Entry point: `sort_and_search_http`  
5. Inline editor  

---

## 3.3. Copiar el CÓDIGO PYTHON completo en Cloud Functions

Archivo `main.py`:

```python
import json
from google.cloud import storage

def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr)//2]
    left  = [x for x in arr if x < pivot]
    mid   = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + mid + quicksort(right)

def binary_search(sorted_list, target):
    left, right = 0, len(sorted_list)-1
    while left <= right:
        mid = (left+right)//2
        if sorted_list[mid] == target:
            return mid
        elif sorted_list[mid] < target:
            left = mid+1
        else:
            right = mid-1
    return -1

def sort_and_search_http(request):
    args = request.args or {}
    bucket = args.get("bucket")
    blob_name = args.get("blob", "data.csv")
    target = int(args.get("target", 13))

    if not bucket:
        return ("Missing bucket", 400)

    client = storage.Client()
    data = (
        client.bucket(bucket)
              .blob(blob_name)
              .download_as_text()
              .strip()
              .splitlines()
    )
    numbers = [int(x) for x in data if x]

    sorted_numbers = quicksort(numbers)
    index = binary_search(sorted_numbers, target)

    return (
        json.dumps({
            "original": numbers,
            "sorted": sorted_numbers,
            "target": target,
            "index": index
        }),
        200,
        {"Content-Type": "application/json"}
    )
```

Archivo `requirements.txt`:

```
google-cloud-storage
```

---

## 3.4. Probar Cloud Function

Testing → Query params:

```
bucket=algorithms-demo-XXXXX&blob=data.csv&target=13
```

---

# ✔️ Fin del archivo

Este archivo contiene **todos los pasos de portal** y **todo el código Python listo para copiar** en Azure, AWS y GCP.
