![logo bsg](../images/logobsg.png)

# Certified Python Data Engineer – AWS Data Engineering Pipeline

**Objective:**
Create and automate a scalable data pipeline using **AWS Glue** and **AWS Lambda**, integrating multiple data sources, applying transformations, and optimizing performance under **AWS Free Tier** constraints.

---

## Learning Outcomes (Apply & Evaluate)
By the end of this lab, students will be able to:
- Design and implement ETL pipelines using AWS Glue
- Automate data workflows using AWS Lambda and S3 events
- Apply performance, scalability, and cost-optimization techniques
- Critically evaluate architectural decisions in AWS data pipelines

---

## Architecture Overview

```
S3 (Raw Zone)
   │
   │ ObjectCreated Event
   ▼
AWS Lambda (Orchestration)
   │
   │ Start Glue Job
   ▼
AWS Glue (ETL - Spark)
   │
   ▼
S3 (Processed Zone - Parquet)
```

---

## Prerequisites

### Technical
- AWS Account (Free Tier)
- Basic Python knowledge
- Basic SQL knowledge
- Familiarity with S3 and IAM concepts

### AWS Services Used
- Amazon S3
- AWS Glue (Job + Crawler)
- AWS Lambda
- AWS IAM
- Amazon CloudWatch

---

## Step 1 – Create S3 Buckets

Create two buckets:
- `bsg-data-raw`
- `bsg-data-processed`

Upload sample CSV files into `bsg-data-raw/`.

---

## Step 2 – IAM Roles

### Glue Role
Attach policies:
- `AWSGlueServiceRole`
- `AmazonS3FullAccess`

### Lambda Role
Attach policies:
- `AWSLambdaBasicExecutionRole`
- Custom policy allowing:
  - `glue:StartJobRun`

---

## Step 3 – AWS Glue Crawler

- Source: `bsg-data-raw`
- Output: Glue Data Catalog
- Run crawler once to infer schema

---

## Step 4 – AWS Glue Job (ETL)

### Glue Script (Python / Spark)

```python
from awsglue.context import GlueContext
from pyspark.context import SparkContext
from awsglue.dynamicframe import DynamicFrame

sc = SparkContext()
glueContext = GlueContext(sc)

source = glueContext.create_dynamic_frame.from_catalog(
    database="bsg_db",
    table_name="raw_sales"
)

# Convert to DataFrame for performance
df = source.toDF()

# Example transformations
df_clean = df.filter(df["amount"] > 0)

# Add partition columns
from pyspark.sql.functions import year, month

df_final = df_clean \
    .withColumn("year", year("date")) \
    .withColumn("month", month("date"))

final_dyf = DynamicFrame.fromDF(df_final, glueContext, "final_dyf")

glueContext.write_dynamic_frame.from_options(
    frame=final_dyf,
    connection_type="s3",
    connection_options={
        "path": "s3://bsg-data-processed/",
        "partitionKeys": ["year", "month"]
    },
    format="parquet"
)
```

**Glue Job Configuration:**
- Glue version: 4.0
- Workers: 2 DPUs

---

## Step 5 – AWS Lambda (Automation)

### Purpose
Automatically trigger Glue Job when a new file arrives in S3.

### Environment Variable
| Name | Value |
|----|----|
| GLUE_JOB_NAME | bsg-glue-etl-job |

### Lambda Code

```python
import boto3
import os

glue = boto3.client("glue")

GLUE_JOB_NAME = os.environ["GLUE_JOB_NAME"]

def lambda_handler(event, context):
    record = event["Records"][0]
    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]

    if not key.endswith(".csv"):
        return {"status": "ignored"}

    response = glue.start_job_run(JobName=GLUE_JOB_NAME)

    return {
        "status": "started",
        "job_run_id": response["JobRunId"]
    }
```

---

## Step 6 – Configure S3 Trigger

- Bucket: `bsg-data-raw`
- Event: `ObjectCreated`
- Suffix: `.csv`
- Destination: Lambda function

---

## Key Takeaways

- Lambda orchestrates, Glue transforms
- Spark optimization matters even in managed services
- Cost awareness is part of engineering excellence


