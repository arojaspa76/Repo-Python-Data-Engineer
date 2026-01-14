![logo bsg](images/logobsg.png)

# Proyecto 1: Pipeline ETL en AWS con S3, AWS Glue y Amazon Redshift

## 🌐 Objetivo
Diseñar e implementar una canalización de datos en AWS que cargue datos desde un bucket S3, los procese usando AWS Glue (ETL con Python) y almacene el resultado en Amazon Redshift. El objetivo es construir un pipeline escalable y eficiente para preparar y almacenar datos analíticos en la nube.

## ⚖️ Herramientas
- Amazon S3 (almacenamiento de datos crudos)
- AWS Glue (ETL en Python, PySpark)
- Amazon Redshift (data warehouse)
- AWS IAM (roles y permisos)
- Python + Boto3
- (Opcional) AWS Lambda (orquestación)

## 📊 Dataset sugerido
- Dataset de viajes de taxi de NYC (ej. enero 2022, formato Parquet): https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

## 📅 Duración estimada
6 horas

## ✅ Pasos del proyecto

### 1. Preparación del entorno
- Crear un bucket en S3
- Subir el archivo Parquet o CSV con datos crudos
- Crear un clúster Redshift (o Redshift Serverless)
- Crear una tabla en Redshift con estructura compatible

### 2. Catalogación con Glue (opcional)
- Crear un Glue Data Crawler apuntando al bucket S3
- Registrar metadatos en Glue Data Catalog

### 3. Job ETL en AWS Glue
- Crear un Job en Glue Studio (Python o PySpark)
- Leer datos desde S3
- Aplicar transformaciones (limpieza, cast de tipos, filtrado, etc.)
- Escribir el resultado en Redshift usando JDBC o COPY

### 4. Ejecución y orquestación
- Ejecutar el Job manualmente
- Verificar los datos en Redshift
- (Opcional) Configurar triggers o Lambda para ejecuciones automáticas

### 5. Verificación y buenas prácticas
- Ejecutar queries SQL en Redshift para verificar datos
- Evaluar eficiencia: formato Parquet, GZIP, particiones
- Uso de roles IAM para seguridad sin exponer credenciales

## 📄 Entregables esperados
- Script del Job de Glue o notebook
- Evidencias de ejecución: capturas en Glue y Redshift
- Diagrama del pipeline (S3 → Glue → Redshift)
- Documento resumen explicando decisiones técnicas

## 📈 Valor formativo
El proyecto permite aprender a integrar servicios de AWS para construir pipelines ETL completos en la nube, automatizados y escalables, siguiendo buenas prácticas empresariales.

