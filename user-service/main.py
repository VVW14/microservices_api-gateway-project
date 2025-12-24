from fastapi import FastAPI

app = FastAPI(title="User Service")

# Тестовые данные пользователей
users_db = {
    "user123": {
        "id": "user123",
        "username": "ivan_ivanov",
        "email": "ivan@example.com",
        "full_name": "Иван Иванов",
        "is_active": True,
        "created_at": "2023-01-15T10:30:00Z"
    },
    "user456": {
        "id": "user456",
        "username": "anna_smirnova",
        "email": "anna@example.com",
        "full_name": "Анна Смирнова",
        "is_active": True,
        "created_at": "2023-02-20T09:15:00Z"
    }
}

@app.get("/")
def root():
    return {
        "service": "user-service",
        "description": "Сервис управления пользователями",
        "endpoints": ["/health", "/users/{user_id}", "/users"]
    }

@app.get("/health")
def health():
    return {"status": "healthy", "service": "user-service"}

@app.get("/users/{user_id}")
def get_user(user_id: str):
    user = users_db.get(user_id)
    if not user:
        return {"error": "Пользователь не найден"}
    return user

@app.get("/users")
def get_users():
    return list(users_db.values())
