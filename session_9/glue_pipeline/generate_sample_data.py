# Script: generate_sample_data.py
import csv
import json
import random
from datetime import datetime, timedelta

def generate_sales_data(num_records=100):
    """Genera datos de ventas (< 10 KB)"""
    products = ['PROD456', 'PROD789', 'PROD101', 'PROD202', 'PROD303']
    customers = ['CUST123', 'CUST456', 'CUST789', 'CUST321', 'CUST654']
    
    with open('sales_data_extended.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['transaction_id', 'customer_id', 'product_id', 
                        'quantity', 'price', 'transaction_date'])
        
        start_date = datetime(2024, 1, 1)
        for i in range(num_records):
            date = start_date + timedelta(days=random.randint(0, 30))
            writer.writerow([
                f'TXN{i+1:04d}',
                random.choice(customers),
                random.choice(products),
                random.randint(1, 10),
                round(random.uniform(10, 100), 2),
                date.strftime('%Y-%m-%d')
            ])
    print(f"✅ Generados {num_records} registros de ventas")

# Ejecutar (genera ~100 registros = ~5 KB)
generate_sales_data(100)