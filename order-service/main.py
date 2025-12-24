from fastapi import FastAPI

app = FastAPI(title="Order Service")

# Тестовые данные заказов
orders_db = [
    {
        "id": "order123",
        "user_id": "user123",
        "status": "доставлен",
        "total_amount": 299.99,
        "items": [
            {"product_id": "prod1", "quantity": 2, "price": 99.99},
            {"product_id": "prod2", "quantity": 1, "price": 100.00}
        ],
        "created_at": "2023-11-15T10:30:00Z"
    },
    {
        "id": "order456",
        "user_id": "user123",
        "status": "обработка",
        "total_amount": 150.50,
        "items": [
            {"product_id": "prod3", "quantity": 1, "price": 150.50}
        ],
        "created_at": "2023-12-01T09:15:00Z"
    },
    {
        "id": "order789",
        "user_id": "user456",
        "status": "ожидает",
        "total_amount": 75.25,
        "items": [
            {"product_id": "prod1", "quantity": 1, "price": 75.25}
        ],
        "created_at": "2023-12-05T16:45:00Z"
    }
]

@app.get("/")
def root():
    return {
        "service": "order-service",
        "description": "Сервис управления заказами",
        "endpoints": ["/health", "/orders/user/{user_id}", "/orders"]
    }

@app.get("/health")
def health():
    return {"status": "healthy", "service": "order-service"}

@app.get("/orders/user/{user_id}")
def get_user_orders(user_id: str):
    user_orders = [order for order in orders_db if order["user_id"] == user_id]
    return user_orders

@app.get("/orders")
def get_orders():
    return orders_db
