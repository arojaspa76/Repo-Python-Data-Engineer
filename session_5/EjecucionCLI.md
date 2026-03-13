# Ejecución en CLI de Azure, AWS y GCP

Este archivo contiene los comandos CLI equivalentes a los pasos descritos en el README.md de session_5 para crear storage y funciones en Azure, AWS y GCP.

## 1. Azure CLI - Blob Storage + Azure Function

### 1.1. Crear Resource Group y Storage Account
```bash
az login
az group create --name rg-algoritmos-azure --location eastus
az storage account create --name algostorage<unico> --resource-group rg-algoritmos-azure --location eastus --sku Standard_LRS --kind StorageV2
```

### 1.2. Crear contenedor y subir archivo
```bash
az storage container create --name datasets --account-name algostorage<unico> --account-key $(az storage account keys list --resource-group rg-algoritmos-azure --account-name algostorage<unico> --query '[0].value' -o tsv)
az storage blob upload --account-name algostorage<unico> --container-name datasets --name data.csv --file session_5/data.csv --account-key $(az storage account keys list --resource-group rg-algoritmos-azure --account-name algostorage<unico> --query '[0].value' -o tsv)
```

### 1.3. Crear Function App
```bash
az functionapp create --resource-group rg-algoritmos-azure --consumption-plan-location eastus --runtime python --runtime-version 3.11 --functions-version 4 --name <functionappname> --storage-account algostorage<unico> --os-type linux
```

### 1.4. Configurar Application Settings
```bash
az functionapp config appsettings set --name <functionappname> --resource-group rg-algoritmos-azure --settings AZURE_STORAGE_ACCOUNT_NAME=algostorage<unico> AZURE_STORAGE_ACCOUNT_KEY=$(az storage account keys list --resource-group rg-algoritmos-azure --account-name algostorage<unico> --query '[0].value' -o tsv) AZURE_STORAGE_CONTAINER=datasets AZURE_STORAGE_BLOB=data.csv
```

### 1.5. Desplegar el código de la función
Para desplegar el código, necesitas tener el proyecto local. Asumiendo que tienes un directorio con function.json y __init__.py con el código del README.

```bash
func azure functionapp publish <functionappname>
```

O usando zip:
```bash
az functionapp deployment source config-zip --resource-group rg-algoritmos-azure --name <functionappname> --src <path-to-zip>
```

### 1.6. Probar la función
```bash
curl "https://<functionappname>.azurewebsites.net/api/sort_and_search?target=13"
```

## 2. AWS CLI - S3 + Lambda

### 2.1. Crear bucket S3 y subir archivo
```bash
aws configure
aws s3 mb s3://algorithms-demo-<unico> --region us-east-1
aws s3 cp session_5/data.csv s3://algorithms-demo-<unico>/
```

### 2.2. Crear rol para Lambda
```bash
aws iam create-role --role-name lambda-s3-role --assume-role-policy-document '{"Version": "2012-10-17","Statement": [{ "Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}'
aws iam attach-role-policy --role-name lambda-s3-role --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
aws iam attach-role-policy --role-name lambda-s3-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

### 2.3. Crear función Lambda con código inline
Crea un archivo lambda_function.py con el código del README, luego:
```bash
zip lambda_function.zip lambda_function.py
aws lambda create-function --function-name algorithms-demo --runtime python3.9 --role arn:aws:iam::<account-id>:role/lambda-s3-role --handler lambda_function.lambda_handler --code ZipFile=fileb://lambda_function.zip --region us-east-1
```

### 2.4. Probar Lambda
```bash
aws lambda invoke --function-name algorithms-demo --payload '{"bucket": "algorithms-demo-<unico>", "key": "data.csv", "target": 13}' response.json
cat response.json
```

## 3. gcloud CLI - Cloud Storage + Cloud Functions

### 3.1. Crear bucket y subir archivo
```bash
gcloud auth login
gcloud config set project <project-id>
gsutil mb -l us-central1 gs://algorithms-demo-<unico>
gsutil cp session_5/data.csv gs://algorithms-demo-<unico>/
```

### 3.2. Crear Cloud Function
Crea main.py y requirements.txt con el código del README, luego:
```bash
gcloud functions deploy sort_and_search_http --runtime python311 --trigger-http --allow-unauthenticated --entry-point sort_and_search_http --source . --region us-central1
```

### 3.3. Probar Cloud Function
```bash
curl "https://us-central1-<project-id>.cloudfunctions.net/sort_and_search_http?bucket=algorithms-demo-<unico>&blob=data.csv&target=13"
```

Nota: Reemplaza <unico>, <functionappname>, <account-id>, <project-id> con valores apropiados.</content>
<parameter name="filePath">EjecucionCLI.md