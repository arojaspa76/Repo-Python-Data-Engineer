import boto3
import time
import os

# Configuración
BUCKET_NAME = 'bsg-data-raw'
REGION = 'us-east-1'
DATABASE_NAME = 'sales_department_datawarehouse'
ROLE_NAME = 'LabRole'
TABLE_PREFIX = "python_"

# Cliente de Glue
session = boto3.Session(profile_name='pgpcc', region_name=REGION)
glue_client = session.client('glue')
iam_client = session.client('iam')

def get_role_arn():
    """Obtener ARN del rol"""
    try:
        response = iam_client.get_role(RoleName=ROLE_NAME)
        return response['Role']['Arn']
    except Exception as e:
        print(f"❌ Error obteniendo rol: {e}")
        return None

def create_crawler(name, path, description):
    """Crear y ejecutar un crawler"""
    role_arn = get_role_arn()
    if not role_arn:
        return False
    
    try:
        glue_client.create_crawler(
            Name=name,
            Role=role_arn,
            DatabaseName=DATABASE_NAME,
            Description=description,
            Targets={
                'S3Targets': [
                    {
                        'Path': path,
                        'Exclusions': ['*.tmp', '*.log', '_*']
                    }
                ]
            },
            RecrawlPolicy={
                'RecrawlBehavior': 'CRAWL_EVERYTHING'
            },            
            SchemaChangePolicy={
                'UpdateBehavior': 'UPDATE_IN_DATABASE',
                'DeleteBehavior': 'LOG'
            },
            TablePrefix=TABLE_PREFIX
        )
        print(f"✅ Crawler '{name}' creado exitosamente")
        
        # Ejecutar crawler
        glue_client.start_crawler(Name=name)
        print(f"🚀 Crawler '{name}' iniciado...")
        
        return True
        
    except glue_client.exceptions.AlreadyExistsException:
        print(f"⚠️  Crawler '{name}' ya existe")
        return True
    except Exception as e:
        print(f"❌ Error creando crawler: {e}")
        return False

def wait_for_crawler(name, max_wait=300):
    """Esperar a que el crawler termine"""
    print(f"⏳ Esperando que el crawler '{name}' termine...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        response = glue_client.get_crawler(Name=name)
        state = response['Crawler']['State']
        
        if state == 'READY':
            print(f"✅ Crawler '{name}' completado!")
            return True
        
        print(f"   Estado: {state} - Esperando...")
        time.sleep(10)
    
    print(f"⚠️  Timeout esperando al crawler")
    return False

# Ejecutar
if __name__ == "__main__":
    print("=" * 60)
    print("CONFIGURACIÓN DE CRAWLERS PARA AWS GLUE LAB")
    print("=" * 60)
    
    # Crawler para ventas
    if create_crawler(
        name='sales-data-crawler-python',
        path=f's3://{BUCKET_NAME}/raw/sales/',
        description='Crawler for sales transaction data'
    ):
        wait_for_crawler('sales-data-crawler-python')
    
    print()
    
    # Crawler para clientes
    if create_crawler(
        name='customers-data-crawler',
        path=f's3://{BUCKET_NAME}/raw/customers/',
        description='Crawler for customer data'
    ):
        wait_for_crawler('customers-data-crawler')
    
    print()
    
    # Crawler para eventos
    if create_crawler(
        name='events-data-crawler',
        path=f's3://{BUCKET_NAME}/raw/events/',
        description='Crawler for clickstream events'
    ):
        wait_for_crawler('events-data-crawler')
    
    print()
    print("=" * 60)
    print("✅ CONFIGURACIÓN COMPLETADA")
    print("=" * 60)
    
    # Listar tablas creadas
    print("\n📊 Tablas en el catálogo:")
    try:
        response = glue_client.get_tables(DatabaseName=DATABASE_NAME)
        for table in response['TableList']:
            print(f"   - {table['Name']}")
    except Exception as e:
        print(f"   Error listando tablas: {e}")