import logging
import os
import azure.functions as func
from azure.storage.blob import BlobServiceClient

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

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        target = req.params.get("target")
        if not target:
            body = req.get_json(silent=True) or {}
            target = body.get("target")
        if target is None:
            return func.HttpResponse("Please pass target", status_code=400)
        target = int(target)

        acc       = os.environ["AZURE_STORAGE_ACCOUNT_NAME"]
        key       = os.environ["AZURE_STORAGE_ACCOUNT_KEY"]
        container = os.environ["AZURE_STORAGE_CONTAINER"]
        blob_name = os.environ["AZURE_STORAGE_BLOB"]

        conn = (
            f"DefaultEndpointsProtocol=https;AccountName={acc};"
            f"AccountKey={key};EndpointSuffix=core.windows.net"
        )

        client      = BlobServiceClient.from_connection_string(conn)
        blob_client = client.get_container_client(container).get_blob_client(blob_name)

        data    = blob_client.download_blob().readall().decode().splitlines()
        numbers = [int(x) for x in data if x]

        sorted_numbers = quicksort(numbers)
        index          = binary_search(sorted_numbers, target)

        return func.HttpResponse(
            body=str({
                "original": numbers,
                "sorted":   sorted_numbers,
                "target":   target,
                "index":    index
            }),
            mimetype="application/json"
        )
    except Exception as e:
        return func.HttpResponse(f"ERROR: {str(e)}", status_code=500)