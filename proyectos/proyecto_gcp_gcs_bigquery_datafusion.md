![logo bsg](images/logobsg.png)

# Proyecto 2: Pipeline en GCP con Cloud Storage, Data Fusion y BigQuery

## 🌐 Objetivo
Construir una canalización de datos en GCP que lea archivos desde Cloud Storage, los transforme con Cloud Data Fusion y los cargue a BigQuery para su análisis. Este proyecto simula un ETL visual gestionado en GCP con soporte para tareas Python donde sea necesario.

## ⚖️ Herramientas
- Google Cloud Storage (GCS)
- Cloud Data Fusion (plataforma ETL visual)
- BigQuery (data warehouse sin servidor)
- Google IAM (service accounts)
- Python (en transformaciones si aplica)
- (Opcional) Cloud Functions

## 📊 Dataset sugerido
- Dataset de libros del NY Times Bestsellers (JSON)
- O cualquier dataset tabular en CSV desde Kaggle (Retail, E-commerce, etc.)

## 📅 Duración estimada
6 horas

## ✅ Pasos del proyecto

### 1. Preparación
- Crear bucket en GCS y subir el dataset
- Crear dataset y tabla en BigQuery (puede generarse desde Data Fusion)

### 2. Diseño en Data Fusion
- Crear instancia de Cloud Data Fusion
- Diseñar pipeline: origen GCS → transformación → destino BigQuery
- Aplicar transformaciones con Wrangler o plugins (filtrado, cast, etc.)

### 3. Ejecución
- Validar transformaciones con vista previa
- Ejecutar el pipeline completo
- Verificar tabla destino en BigQuery

### 4. Optimizaciones y buenas prácticas
- Particionar y clusterizar tablas (si aplica)
- Documentar limpieza de datos
- Uso de Service Accounts con permisos mínimos

### 5. (Opcional) Automatización
- Configurar scheduler de Data Fusion o activar por eventos con Cloud Functions

## 📄 Entregables esperados
- Pipeline exportado desde Data Fusion (JSON)
- Capturas de GCS, Data Fusion y BigQuery
- Consulta de validación en BigQuery
- Diagrama del flujo de datos y resumen técnico

## 📈 Valor formativo
El estudiante aprenderá a construir pipelines sin servidor y sin escribir código desde cero, aprovechando servicios completamente gestionados en GCP para ingesta, limpieza y carga a data warehouses con buenas prácticas.

