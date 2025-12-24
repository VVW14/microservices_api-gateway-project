from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Product Service")

# Тестовые данные товаров
products_db = {
    "prod1": {
        "id": "prod1",
        "name": "Ноутбук",
        "description": "Мощный ноутбук для работы и игр",
        "price": 999.99,
        "category": "Электроника",
        "stock_quantity": 50
    },
    "prod2": {
        "id": "prod2",
        "name": "Смартфон",
        "description": "Современный смартфон",
        "price": 699.99,
        "category": "Электроника",
        "stock_quantity": 100
    },
    "prod3": {
        "id": "prod3",
        "name": "Наушники",
        "description": "Беспроводные наушники с шумоподавлением",
        "price": 199.99,
        "category": "Аудио",
        "stock_quantity": 200
    }
}

class BatchRequest(BaseModel):
    product_ids: List[str]

@app.get("/")
def root():
    return {
        "service": "product-service",
        "description": "Сервис управления товарами",
        "endpoints": [
            "/health",
            "/products/{product_id}",
            "/products/batch (POST)",
            "/products"
        ]
    }

@app.get("/health")
def health():
    return {"status": "healthy", "service": "product-service"}

@app.get("/products/{product_id}")
def get_product(product_id: str):
    product = products_db.get(product_id)
    if not product:
        return {"error": "Товар не найден"}
    return product

@app.post("/products/batch")
def get_products_batch(request: BatchRequest):
    products = []
    for pid in request.product_ids:
        if pid in products_db:
            products.append(products_db[pid])
    return products

@app.get("/products")
def get_products():
    return list(products_db.values())
