![logo bsg](../images/logobsg.png)

# Certified Python Data Engineer – AWS Data Engineering Pipeline

## Athena Lab – Querying Optimized Data Lakes with AWS Glue

---

## 1. Objetivo del laboratorio

Al finalizar este laboratorio, el estudiante será capaz de:
- Consultar datasets procesados en **Amazon Athena** usando SQL estándar.
- Validar el impacto de **Parquet** y **particiones** en rendimiento y costo.
- Crear capas analíticas (*curated layer*) usando **CTAS (CREATE TABLE AS SELECT)**.
- Evaluar decisiones técnicas basadas en métricas reales (data scanned, latencia).

---

## 2. Contexto del pipeline

Este laboratorio continúa el pipeline construido previamente:

```
S3 (Raw Zone) → AWS Glue (ETL Spark) → S3 (Processed Zone – Parquet, particionado)
```

El objetivo ahora es **consumir analíticamente** los datos procesados.

---

## 3. Prerrequisitos

### Técnicos
- Pipeline Glue ejecutado exitosamente
- Datos en formato **Parquet** en:
  - `s3://bsg-data-processed/`
- Dataset particionado por:
  - `year`
  - `month`

### Servicios AWS
- Amazon Athena
- AWS Glue Data Catalog
- Amazon S3

---

## 4. Configuración inicial de Amazon Athena

### Paso 4.1 – Abrir Query Editor
- Ir a **Amazon Athena → Query editor**
- Seleccionar la región donde está S3/Glue

### Paso 4.2 – Configurar ubicación de resultados
Athena requiere una ubicación para los resultados de las queries.

1. Crear un bucket o prefijo, por ejemplo:
   - `s3://bsg-athena-results/queries/`
2. En Athena → Settings:
   - Configurar **Query result location**

**Nota técnica:** Usar un bucket dedicado mejora gobernanza y control de costos.

---

## 5. Registro de la tabla procesada

### Opción A – Usar Glue Crawler (recomendado)

1. Glue → Crawlers → Create crawler
2. Fuente:
   - `s3://bsg-data-processed/`
3. Database:
   - `bsg_db`
4. Ejecutar crawler

La tabla quedará registrada como:
- `bsg_db.processed_sales`

---

### Opción B – Reparar particiones manualmente

Si la tabla ya existe pero Athena no detecta nuevas particiones:

```sql
MSCK REPAIR TABLE bsg_db.processed_sales;
```

**Qué hace:**
- Escanea el layout de S3
- Registra automáticamente las particiones encontradas

---

## 6. Consultas básicas de validación

### 6.1 Conteo general

```sql
SELECT COUNT(*) AS total_rows
FROM bsg_db.processed_sales;
```

Verificar que Athena pueda leer el dataset correctamente.

---

### 6.2 Exploración de columnas

```sql
SELECT *
FROM bsg_db.processed_sales
LIMIT 10;
```

**Advertencia:** `SELECT *` solo debe usarse para exploración inicial.

---

## 7. Demostración de partition pruning (clave del laboratorio)

### 7.1 Consulta SIN filtro de partición

```sql
SELECT SUM(amount) AS total_amount
FROM bsg_db.processed_sales;
```

Registrar:
- Tiempo de ejecución
- **Data scanned** (Athena UI)

---

### 7.2 Consulta CON filtro de partición

```sql
SELECT SUM(amount) AS total_amount
FROM bsg_db.processed_sales
WHERE year = 2025
  AND month = 12;
```

Comparar contra la consulta anterior.

**Resultado esperado:**
- Menor data scanned
- Menor latencia
- Menor costo

---

## 8. Creación de capa curada con CTAS

### 8.1 ¿Qué es CTAS?

CTAS (*CREATE TABLE AS SELECT*) permite:
- Transformar datos usando SQL
- Escribir directamente en Parquet
- Crear datasets analíticos listos para BI

---

### 8.2 CTAS – Tabla curada

```sql
CREATE TABLE bsg_db.curated_sales
WITH (
  format = 'PARQUET',
  external_location = 's3://bsg-data-curated/sales/',
  partitioned_by = ARRAY['year','month']
) AS
SELECT
  customer_id,
  product_id,
  CAST(amount AS DOUBLE) AS amount,
  year,
  month
FROM bsg_db.processed_sales
WHERE amount > 0;
```

---

### 8.3 Validar tabla curada

```sql
SELECT COUNT(*)
FROM bsg_db.curated_sales
WHERE year = 2025 AND month = 12;
```

Verificar nuevamente **data scanned**.

---

## 9. Buenas prácticas obligatorias en Athena

- Evitar `SELECT *`
- Filtrar por particiones
- Usar Parquet
- Centralizar resultados en un bucket controlado
- Usar CTAS para datasets reutilizables

