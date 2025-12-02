import azure.functions as func
import logging
import os
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

def ordenamiento(arr):
    if len(arr) <= 1:
        return arr
    pivote = arr[len(arr) // 2]
    izquierda = [x for x in arr if x < pivote]
    medio = [x for x in arr if x == pivote]
    derecha = [x for x in arr if x > pivote]
    return ordenamiento(izquierda) + medio + ordenamiento(derecha)

def busqueda_binaria(arreglo_ordnado, numero_objetivo):
    izquierda, derecha = 0, len(arreglo_ordnado) - 1
    while izquierda <= derecha:
        medio = (izquierda + derecha) // 2
        if arreglo_ordnado[medio] == numero_objetivo:
            return medio
        elif arreglo_ordnado[medio] < numero_objetivo:
            izquierda = medio + 1
        else:
            derecha = medio -1
    return -1
        

@app.route(route="funcion_con_lista")
def funcion_con_lista(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('La funcion funcion_con_lista ha sido invocada')

    # Esta lista es simulando la lectura del archivo desde el blob storage
    numeros = [42,7,13,99,5,34,12,11,78,45,63,41,98,87,49,9]
    numero = req.params.get("numero")

    if not numero:
        try:
            body = req.get_json()
        except ValueError:
            body = {}
        numero = body.get("numero")
    
    if numero is None:
        return func.HttpResponse(
            body=str(
                {
                   "funcion solicitada": "funcion_con_lista",
                    "Error:":"Por favor envie numero"
                }
            ),
            status_code=400,
            mimetype="application/json",
        )

    try:
        numero = int(numero)
    except ValueError:
        return func.HttpResponse(
            body=str(
                {
                    "funcion solicitada": "funcion_con_lista",
                    "Error:":"Numero debe ser un valor entero"
                }
            ),
            status_code=400,
            mimetype="application/json",
        )

    numeros_ordenados = ordenamiento(numeros)
    indice = busqueda_binaria(numeros_ordenados, numero)

    if indice == -1:
        indice = "Numero no encontrado"

    return func.HttpResponse(
        body=str(
            {
                "funcion solicitada": "funcion_con_lista",
                "original": numeros,
                "ordenado":numeros_ordenados,
                "numero objetivo":numero,
                "indice": indice,
            }
        ),
        mimetype="application/json",
    )

@app.route(route="funcion_con_archivo", methods=["GET", "POST"])
def funcion_con_archivo(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("La funcion funcion_con_archivo ha sido invocada")

    # 1. Leer parámetro target
    numero = req.params.get("numero")
    if not numero:
        try:
            body = req.get_json()
        except ValueError:
            body = {}
        numero = body.get("numero")

    if numero is None:
        return func.HttpResponse(
            body=str(
                {
                   "funcion solicitada": "funcion_con_archivo",
                    "Error:":"Por favor envie numero"
                }
            ),
            status_code=400,
            mimetype="application/json",
        )

    try:
        numero = int(numero)
    except ValueError:
        return func.HttpResponse(
            body=str(
                {
                    "funcion solicitada": "funcion_con_archivo",
                    "Error:":"Numero debe ser un valor entero"
                }
            ),
            status_code=400,
            mimetype="application/json",
        )

    # 2. Leer variables de entorno
    acc = os.environ["AZURE_STORAGE_ACCOUNT_NAME"]
    key = os.environ["AZURE_STORAGE_ACCOUNT_KEY"]
    container = os.environ["AZURE_STORAGE_CONTAINER"]
    blob_name = os.environ["AZURE_STORAGE_BLOB"]

    conn = (
        f"DefaultEndpointsProtocol=https;AccountName={acc};"
        f"AccountKey={key};EndpointSuffix=core.windows.net"
    )

    # 3. Leer CSV desde Blob Storage
    client = BlobServiceClient.from_connection_string(conn)
    blob_client = client.get_container_client(container).get_blob_client(blob_name)

    data = blob_client.download_blob().readall().decode().splitlines()
    numeros = [int(x) for x in data if x]

    # 4. Ordenar y buscar
    numeros_ordenados = ordenamiento(numeros)
    indice = busqueda_binaria(numeros_ordenados, numero)

    if indice == -1:
        indice = "Numero no encontrado"    

    # 5. Respuesta
    return func.HttpResponse(
        body=str(
            {
                "funcion solicitada": "funcion_con_archivo",                
                "original": numeros,
                "sorted": numeros_ordenados,
                "target": numero,
                "index": indice,
            }
        ),
        mimetype="application/json",
    )