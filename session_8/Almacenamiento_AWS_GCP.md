![logo bsg](images/logobsg.png)

# Curso Ingeniería de Datos en Plataformas en la Nube y Data Warehousing con Python - Sesion 8

## 1. Introducción a Soluciones de Almacenamiento en la Nube: Amazon S3 y Google Cloud Storage
En esta sección exploraremos los servicios de almacenamiento de objetos de AWS y GCP – Amazon S3 (Simple Storage Service) y Google Cloud Storage (GCS) – incluyendo cómo configurar buckets y cómo gestionar datos a gran escala en cada plataforma. Ambos servicios permiten almacenar y recuperar cantidades masivas de datos sin administrar infraestructura.

### 1.1 Amazon S3: creación de buckets y gestión de datos
Amazon S3 es el servicio de almacenamiento de objetos de AWS, diseñado para manejar volúmenes de datos prácticamente ilimitados con alta disponibilidad y durabilidad [\[1\]](#ref1)[\[2\]](#ref2). Los datos se almacenan como objetos dentro de buckets (contenedores lógicos). S3 ofrece una durabilidad de 11 nueves (99.999999999%) mediante la replicación automática de datos en múltiples zonas de disponibilidad dentro de una región[\[3\]](#ref3). Esto lo hace ideal para datos críticos y de gran tamaño.
Creación de un bucket en S3: Para crear un bucket, se necesita un nombre globalmente único y una región. Esto puede hacerse vía consola AWS o programáticamente con Python usando Boto3. Por ejemplo, con Boto3:  

```python
import boto3
s3 = boto3.client('s3', region_name='us-east-1')
s3.create_bucket(Bucket='mi-bucket-ejemplo')
```
> (Si la región no es la predeterminada `us-east-1`, se debe especificar `CreateBucketConfiguration={'LocationConstraint': 'us-west-2'}` u otra región.)

Una vez creado el bucket, podemos subir objetos. Por ejemplo, para subir un archivo local:  
```python
s3.upload_file('datos.csv', 'mi-bucket-ejemplo', 'datos/datos.csv')
```
Este código creará el bucket llamado "mi-bucket-ejemplo" y subirá el archivo datos.csv al bucket bajo la ruta datos/datos.csv. Es necesario haber configurado credenciales AWS válidas (por ejemplo, mediante variables de entorno o archivo de configuración).

Gestión de datos a gran escala en S3: Amazon S3 está pensado para escalabilidad automática, sin necesidad de aprovisionar espacio de antemano. Puedes almacenar desde unos pocos GB hasta petabytes o más; de hecho, S3 puede manejar cantidades virtualmente ilimitadas de datos[\[2\]](#ref2). Un solo objeto puede tener hasta 5 TB de tamaño[\[4\]](#ref4), y no hay límite práctico en la cantidad de objetos por bucket[2]. S3 garantiza alta disponibilidad (99.99%) para acceder a los datos[3] y distribuye los objetos en múltiples servidores y ubicaciones para resiliencia.

Para administrar datos masivos de forma eficiente, S3 ofrece clases de almacenamiento y características como versionado de objetos y lifecycle policies (reglas de ciclo de vida). Las clases de almacenamiento (Standard, Standard-IA, One Zone-IA, Glacier, etc.) permiten optimizar costo vs. frecuencia de acceso[\[5\]](#ref5)[\[6\]](#ref6). Por ejemplo, datos accedidos con poca frecuencia pueden moverse a Standard-IA o Glacier para ahorrar costos, manteniendo la opción de ser recuperados cuando se necesiten. Esto es importante en entornos de Big Data donde quizás almacenemos enormes volúmenes de datos históricos: podemos archivarlos en Glacier (muy bajo costo) y solo pagar cuando se restauran.
Otra práctica para grandes volúmenes es usar multipart upload para subir archivos muy pesados en partes paralelamente, mejorando velocidad y confiabilidad. S3 maneja automáticamente la escalabilidad de peticiones; no obstante, para rendimiento óptimo conviene diseñar las keys de los objetos de manera que eviten hot spots (por ejemplo, prefixos aleatorios si subimos millones de objetos con nombres similares). AWS publica guías de buenas prácticas para optimizar el rendimiento de S3 en grandes datasets[\[7\]](#ref7).

**_Ejemplo práctico (escenario Retail):_** imagine una cadena minorista que genera archivos CSV diarios con registros de ventas (millones de filas). Estos archivos pueden almacenarse en S3 en un bucket ventas-retail organizado por fecha (por ejemplo, s3://ventas-retail/2025/12/ventas_2025-12-01.csv). Usando Python, un script ETL podría ejecutarse a diario para cargar el archivo del día en S3. Gracias a la escalabilidad de S3, aunque el volumen de ventas crezca de gigabytes a terabytes, no habrá que modificar la infraestructura; S3 escalará automáticamente para acomodar los nuevos datos[\[2\]](#ref2). Más adelante, esos datos en S3 podrían ser procesados con herramientas de big data (AWS Athena, EMR, Redshift Spectrum, etc.). Además, utilizando lifecycle policies, podríamos configurar que archivos de ventas mayores a 1 año se trasladen a Glacier para reducir costos, manteniendo los últimos 12 meses en Standard para acceso rápido.

**_Costo y Free Tier:_** En AWS, S3 forma parte del nivel gratuito: nuevos usuarios obtienen 5 GB de almacenamiento Standard gratis por 12 meses, junto con un número de operaciones (PUT, GET) gratuitas mensuales. Esto permite practicar con creación de buckets y manipulación de objetos sin incurrir en costos significativos, siempre y cuando los datos almacenados sean modestos. Por ejemplo, almacenar unos cuantos archivos de ejemplo (CSV o imágenes) totales de <5 GB no generará cargos dentro del periodo gratuito.

### 1.2 Google Cloud Storage: creación de buckets y gestión de datos
Google Cloud Storage (GCS) es el servicio equivalente en GCP, proporcionando almacenamiento de objetos con alta durabilidad y escalabilidad. Al igual que S3, GCS puede almacenar objetos de hasta 5 TB y en cantidad prácticamente ilimitada[8]. Ofrece diferentes clases de almacenamiento (Standard, Nearline, Coldline, Archive) para balancear costo y rendimiento según la frecuencia de acceso a los datos.

Creación de un bucket en GCS: Se puede hacer desde la consola de Google Cloud o mediante código Python utilizando la biblioteca oficial. Para usar Python, primero se instala la librería google-cloud-storage y se configuran credenciales (por ejemplo, usando una Service Account con permisos de Storage). Un ejemplo sencillo para crear un bucket y subir un archivo:

```python
from google.cloud import storage

# Autenticación mediante credenciales predeterminadas (ej. variable de entorno GOOGLE_APPLICATION_CREDENTIALS)
client = storage.Client()

# Crear un bucket nuevo
bucket = client.create_bucket('mi-bucket-ejemplo-gcp', location='US')  # ubicación US multi-regional

# Subir un archivo al bucket
blob = bucket.blob('datos/data.csv')
blob.upload_from_filename('data_local.csv')
print("Archivo subido a GCS")
```
El código anterior crea un bucket llamado `mi-bucket-ejemplo-gcp` en la región/ubicación `US` (que es multirregional en Estados Unidos) y luego sube el archivo data_local.csv al bucket bajo la ruta datos/data.csv. Para que esto funcione, debemos haber activado la API de Cloud Storage en nuestro proyecto de GCP y tener credenciales válidas (por ejemplo, haber exportado la ruta del JSON de la service account a la variable GOOGLE_APPLICATION_CREDENTIALS).

**_Gestión de datos a gran escala en GCS:_** Google Cloud Storage ofrece características similares a S3 en términos de escalabilidad y durabilidad. GCS almacena automáticamente múltiples copias de los datos en zonas de disponibilidad distintas dentro de una región o incluso de forma geo-redundante (si se elige un bucket multirregional), garantizando también durabilidad para los datos. Al igual que AWS, GCP permite almacenar cantidades masivas de datos sin preocuparse por administrar servidores de almacenamiento; el servicio se encarga de escalar según la demanda[\[2\]](#ref2)[\[8\]](#ref8).

En GCS, elegir la clase de almacenamiento adecuada es clave cuando manejamos grandes volúmenes: - Standard (por defecto) para acceso frecuente / baja latencia (ideal para datos activos, analítica en tiempo real, contenido web). - Nearline y Coldline para datos accedidos solo ocasionalmente (por ejemplo, backups mensuales o datos históricos de los que se consulta algo una vez al trimestre). - Archive para datos casi nunca accedidos (ej. registros de años muy antiguos que se guardan por compliance).

Estas clases difieren en costo de almacenamiento y costo por acceso, permitiendo optimizar presupuestos en proyectos big data. Por ejemplo, un hospital (dominio salud) podría almacenar imágenes médicas recientes en Standard GCS para análisis inmediato, pero migrar estudios antiguos a Coldline o Archive, reduciendo el gasto en almacenamiento a largo plazo. Los cambios de clase se pueden automatizar con reglas de ciclo de vida en GCS, similares a S3.

GCS también soporta versionado de objetos, permitiendo mantener historial de versiones de archivos, y uniform bucket-level access para gestionar permisos de manera uniforme. Para la transferencia de datos a gran escala, GCP proporciona herramientas como gsutil (en la CLI) que soportan transfers paralelos y reanudables, y también existe Storage Transfer Service para mover datos masivamente entre GCS buckets o desde AWS S3 a GCS de forma eficiente.

**_Ejemplo práctico (escenario Finanzas):_** supongamos una institución financiera que almacena diariamente archivos de transacciones en GCS para posteriormente analizarlos con BigQuery. Cada día genera, digamos, 1 millón de registros (~200 MB en CSV). Esos archivos se suben a un bucket transacciones-finanzas organizados por fecha `(gs://transacciones-finanzas/2025/12/01.csv, etc.)` utilizando un script Python similar al mostrado. En un año, esto acumularía ~73 GB. GCS Standard podría almacenar todo un año de datos activos. Luego, utilizando Python o la consola, podrían configurar que datos mayores a 1 año cambien a Nearline (si se quieren conservar por posibles auditorías pero raramente se acceden). La escalabilidad de GCS permite que, si la cantidad de transacciones crece diez veces, no haya que ajustar nada del almacenamiento: el servicio se adapta automáticamente, con la única consideración de los costos asociados al mayor volumen.

**_Costo y Free Tier:_** Google Cloud Storage ofrece un nivel gratuito continuo: todos los usuarios reciben 5 GB de almacenamiento gratis al mes en la clase Standard, además de un número de operaciones gratis mensuales (el nivel gratuito exacto puede variar; GCP en general brinda $300 USD de crédito promocional a nuevos clientes por 90 días, que podría cubrir pruebas con GCS). Adicionalmente, nuevos proyectos GCP pueden usar el GCS sandbox sin necesidad de tarjeta de crédito por ciertas limitaciones. Esto significa que se pueden hacer ejercicios básicos (crear buckets, subir archivos de ejemplo) sin incurrir en costo. Siempre es recomendable monitorear la consola de facturación, especialmente al trabajar con datos grandes, para asegurarse de no exceder los límites gratuitos.

En resumen, tanto S3 como GCS ofrecen almacenamiento de objetos confiable y escalable para data engineering, con diferencias en nombres y detalles pero conceptos análogos. Con Python y sus SDKs, podemos integrar fácilmente el almacenamiento en nube dentro de pipelines de datos. En el siguiente apartado, veremos cómo aprovechar estos datos almacenados para análisis usando data warehouses en la nube.

# Referencias
<a id="ref1">[1]</a> Diagramming System Design: [S3 Storage System, What is Amazon S3?](https://www.codesmith.io/blog/amazon-s3-storage-diagramming-system-design#:~:text=Amazon%20S3%20is%20a%20cloud,with%20high%20availability%20and%20scalability)  
<a id="ref2">[2]</a> Diagramming System Design: [S3 stores objects](https://www.codesmith.io/blog/amazon-s3-storage-diagramming-system-design#:~:text=S3%20stores%20objects%20,scale%20data%20processing%20systems)  
<a id="ref3">[3]</a> Diagramming System Design: [TLDR - Amazon S3 Storage System](https://www.codesmith.io/blog/amazon-s3-storage-diagramming-system-design#:~:text=,without%20requiring%20any%20manual%20intervention)  
<a id="ref4">[4]</a> Diagramming System Design: [Scalable way](https://www.codesmith.io/blog/amazon-s3-storage-diagramming-system-design#:~:text=It%20provides%20a%20reliable%20and,to%205%20TB%20in%20size)  
<a id="ref5">[5]</a> [Amazon S3 Storage Classes](https://www.codesmith.io/blog/amazon-s3-storage-diagramming-system-design#:~:text=Amazon%20S3%20Storage%20Classes)  
<a id="ref6">[6]</a> Storage Class Options for Infrequently Accessed Data: [S3 Standard](https://www.codesmith.io/blog/amazon-s3-storage-diagramming-system-design#:~:text=The%20S3%20Standard%20storage%20class,web%20applications%2C%20and%20content%20distribution)  
<a id="ref7">[7]</a> [S3 Glacier Flexible Retrieval](https://www.codesmith.io/blog/amazon-s3-storage-diagramming-system-design#:~:text=S3%20Glacier%20Flexible%20Retrieval)  
<a id="ref8">[8]</a> [GCP Cloud Storage](https://support.google.com/cloud/answer/6250993?hl=en#:~:text=You%20can%20use%20Google%20Cloud,and%20up%20to%205%20TB)  