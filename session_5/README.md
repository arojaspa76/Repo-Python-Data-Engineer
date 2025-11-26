# Cloud Algorithms – Búsqueda y Ordenación en Azure, AWS y GCP
### (Lectura desde Storage + Functions/Lambda)

Este documento contiene los ejemplos completos para:

- Leer un archivo `data.csv` desde el almacenamiento de cada cloud  
- Ejecutar algoritmos de **ordenación** (quicksort) y **búsqueda** (binary search)  
- Exponerlos mediante funciones serverless:
  - **Azure Functions**
  - **AWS Lambda**
  - **Google Cloud Functions**

---

## 📌 0. Archivo de datos usado en los ejemplos

```
42
7
13
99
5
```

---

# 📘 1. Azure — Blob Storage + Azure Function (HTTP Trigger)

## 1.1. Código de la Azure Function (`__init__.py`)

```python
import logging
import os
import azure.functions as func
from azure.storage.blob import BlobServiceClient


# ---- ALGORITMOS ----
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


# ---- HANDLER HTTP ----
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Processing Azure Function request...")

    target_str = req.params.get("target")
    if not target_str:
        try:
            req_body = req.get_json()
            target_str = req_body.get("target")
        except:
            pass

    if target_str is None:
        return func.HttpResponse(
            "Please pass '?target=<integer>'.",
            status_code=400
        )

    target = int(target_str)

    acc_name = os.environ["AZURE_STORAGE_ACCOUNT_NAME"]
    acc_key  = os.environ["AZURE_STORAGE_ACCOUNT_KEY"]
    container = os.environ["AZURE_STORAGE_CONTAINER"]
    blob_name = os.environ["AZURE_STORAGE_BLOB"]

    conn_str = (
        f"DefaultEndpointsProtocol=https;"
        f"AccountName={acc_name};"
        f"AccountKey={acc_key};"
        f"EndpointSuffix=core.windows.net"
    )

    blob_service = BlobServiceClient.from_connection_string(conn_str)
    container_client = blob_service.get_container_client(container)
    blob_client = container_client.get_blob_client(blob_name)

    data = blob_client.download_blob().readall().decode().splitlines()
    numbers = [int(x) for x in data if x.strip()]

    sorted_numbers = quicksort(numbers)
    index = binary_search(sorted_numbers, target)

    return func.HttpResponse(
        body=str({
            "original": numbers,
            "sorted": sorted_numbers,
            "target": target,
            "index": index,
        }),
        status_code=200,
        mimetype="application/json"
    )
```

---

# 🟦 2. AWS — S3 + AWS Lambda

## 2.1. Código (`lambda_function.py`)

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
    left, right = 0, len(sorted_list) - 1
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
    bucket = event.get("bucket")
    key = event.get("key", "data.csv")
    target = int(event.get("target", 13))

    obj = s3.get_object(Bucket=bucket, Key=key)
    raw = obj["Body"].read().decode().splitlines()
    numbers = [int(x) for x in raw if x.strip()]

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

# 🟨 3. Google Cloud — Cloud Storage + Cloud Function

## 3.1. Código (`main.py`)

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
    request_args = request.args or {}

    bucket = request_args.get("bucket")
    blob_name = request_args.get("blob", "data.csv")
    target = int(request_args.get("target", 13))

    if not bucket:
        return ("Parameter 'bucket' is required", 400)

    client = storage.Client()
    bucket_obj = client.bucket(bucket)
    blob = bucket_obj.blob(blob_name)

    data = blob.download_as_text().strip().splitlines()
    numbers = [int(x) for x in data if x.strip()]

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

## 3.2. requirements.txt

```
google-cloud-storage
```

---

# 🧪 4. Invocación rápida

## Azure:
```
https://<functionapp>.azurewebsites.net/api/sort_and_search?target=13
```

## AWS:
```
aws lambda invoke  --function-name algorithms-demo  --payload '{"bucket":"mybucket","key":"data.csv","target":13}'  out.json
```

## GCP:
```
https://<region>-<project>.cloudfunctions.net/sort-and-search-http?bucket=mybucket&blob=data.csv&target=13
```
