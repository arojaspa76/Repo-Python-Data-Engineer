![logo bsg](images/logobsg.png)

# Proyecto 3: Pipeline Multicloud Azure → AWS con Redshift

## 🌐 Objetivo
Construir un pipeline multicloud que transfiera datos desde Azure Blob Storage a Amazon Redshift, pasando por S3 como zona de staging. El proyecto simula un caso de integración de datos entre nubes, utilizando Python para la orquestación y automatización del proceso.

## ⚖️ Herramientas
- Azure Blob Storage (origen de datos)
- AWS S3 (intermedio)
- Amazon Redshift (destino)
- Python (Azure SDK, Boto3, Psycopg2)
- AWS CLI, AzCopy (opcional)
- IAM roles, Azure Shared Access Signature (SAS)

## 📊 Dataset sugerido
- Dataset de ventas minoristas (CSV comprimido)
- Ej. “Sample Superstore” o algún dataset de Kaggle simple (∼100K filas, 10MB)

## 📅 Duración estimada
6 horas

## ✅ Pasos del proyecto

### 1. Preparación en Azure
- Crear un Blob Container
- Subir archivo CSV o CSV.gz con datos

### 2. Transferencia a AWS S3
- Usar Python (azure-storage-blob + boto3) o CLI para copiar el archivo
- Verificar archivo en bucket S3

### 3. Preparación en Redshift
- Crear cluster y tabla destino
- Especificar el esquema adecuado (columnas y tipos)

### 4. Carga con COPY
- Ejecutar comando COPY desde archivo en S3
- Usar IAM Role con permisos para Redshift
- Validar datos cargados

### 5. Validación y ajustes
- Consultas SQL para verificación
- Evaluar velocidad y volumen
- Comprimir archivos, dividir si aplica

## 📄 Entregables esperados
- Scripts Python (transferencia y carga)
- Capturas de Azure Blob, AWS S3 y Redshift
- SQL de carga (COPY) y consulta de validación
- Diagrama de arquitectura multicloud y resumen técnico

## 📈 Valor formativo
Este proyecto entrena a los estudiantes en integración de datos entre plataformas cloud, aplicando principios de arquitectura de datos, seguridad con roles/credenciales, y uso eficiente de recursos para mover y cargar datos estructurados hacia un almacén analítico como Redshift.

