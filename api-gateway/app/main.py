from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import httpx
import asyncio
import redis
import json
import time

app = FastAPI(title="API Gateway BFF", version="1.0.0")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настройки сервисов
USER_SERVICE_URL = "http://user-service:8001"
ORDER_SERVICE_URL = "http://order-service:8002"
PRODUCT_SERVICE_URL = "http://product-service:8003"

# Подключение к Redis
try:
    redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=False)
    redis_client.ping()
    print("✅ Redis подключен успешно")
    USE_REDIS = True
except:
    print("⚠️  Redis недоступен, использую in-memory кэш")
    USE_REDIS = False
    in_memory_cache = {}

# Метрики
metrics = {
    "requests_total": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "errors": 0
}

def get_cache(key: str):
    """Получение данных из кэша"""
    if USE_REDIS:
        try:
            data = redis_client.get(key)
            if data:
                return json.loads(data.decode('utf-8'))
        except:
            return None
    else:
        cached = in_memory_cache.get(key)
        if cached and time.time() - cached["timestamp"] < 30:
            return cached["data"]
    return None

def set_cache(key: str, value: dict, ttl: int = 30):
    """Сохранение данных в кэш"""
    if USE_REDIS:
        try:
            redis_client.setex(key, ttl, json.dumps(value))
        except:
            pass
    else:
        in_memory_cache[key] = {
            "data": value,
            "timestamp": time.time()
        }

async def fetch_service(url: str, timeout: float = 5.0):
    """Запрос к микросервису"""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            return response.json() if response.status_code == 200 else None
    except:
        return None

@app.get("/")
async def root():
    return {
        "message": "API Gateway (Backend for Frontend) с агрегацией данных",
        "автор": "Ваше Имя",
        "проект": "Микросервисы: API Gateway BFF",
        "дата": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "endpoints": [
            "GET /health - Проверка здоровья",
            "GET /api/profile/{user_id} - Агрегированный профиль",
            "GET /metrics - Метрики сервиса",
            "GET /api/cache/stats - Статистика кэша"
        ]
    }

@app.get("/health")
async def health():
    """Проверка здоровья системы"""
    services_status = {}
    
    # Проверяем доступность сервисов
    services = [
        ("user_service", f"{USER_SERVICE_URL}/health"),
        ("order_service", f"{ORDER_SERVICE_URL}/health"),
        ("product_service", f"{PRODUCT_SERVICE_URL}/health")
    ]
    
    for service_name, url in services:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(url)
                services_status[service_name] = "healthy" if response.status_code == 200 else "unhealthy"
        except:
            services_status[service_name] = "unreachable"
    
    return {
        "status": "healthy",
        "service": "api-gateway",
        "timestamp": datetime.now().isoformat(),
        "services": services_status,
        "cache": "redis" if USE_REDIS else "in_memory"
    }

@app.get("/api/profile/{user_id}")
async def get_user_profile(user_id: str):
    """Агрегированный профиль пользователя с кэшированием на 30 секунд"""
    metrics["requests_total"] += 1
    
    # Ключ для кэша
    cache_key = f"profile:{user_id}"
    
    # Пробуем получить из кэша
    cached_data = get_cache(cache_key)
    if cached_data:
        metrics["cache_hits"] += 1
        cached_data["metadata"]["cached"] = True
        return cached_data
    
    metrics["cache_misses"] += 1
    
    # Параллельно запрашиваем данные из сервисов
    user_task = fetch_service(f"{USER_SERVICE_URL}/users/{user_id}")
    orders_task = fetch_service(f"{ORDER_SERVICE_URL}/orders/user/{user_id}")
    
    user_data, orders_data = await asyncio.gather(user_task, orders_task)
    
    if not user_data:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Извлекаем ID товаров из заказов
    product_ids = set()
    if orders_data:
        for order in orders_data:
            for item in order.get("items", []):
                product_ids.add(item.get("product_id"))
    
    # Получаем информацию о товарах
    products_data = {}
    if product_ids:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{PRODUCT_SERVICE_URL}/products/batch",
                    json={"product_ids": list(product_ids)}
                )
                if response.status_code == 200:
                    products = response.json()
                    products_data = {p["id"]: p for p in products}
        except:
            pass
    
    # Формируем агрегированный ответ
    response = {
        "user": user_data,
        "orders": orders_data or [],
        "products": products_data,
        "metadata": {
            "user_id": user_id,
            "orders_count": len(orders_data) if orders_data else 0,
            "products_count": len(products_data),
            "aggregated_at": datetime.now().isoformat(),
            "cache_ttl": 30,
            "cached": False,
            "services_used": 3
        }
    }
    
    # Сохраняем в кэш на 30 секунд
    set_cache(cache_key, response)
    
    return response

@app.get("/metrics")
async def get_metrics():
    """Метрики для мониторинга"""
    total_requests = metrics["requests_total"]
    cache_hits = metrics["cache_hits"]
    cache_misses = metrics["cache_misses"]
    
    hit_rate = 0
    if cache_hits + cache_misses > 0:
        hit_rate = (cache_hits / (cache_hits + cache_misses)) * 100
    
    return {
        "service": "api-gateway",
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics,
        "performance": {
            "cache_hit_rate": f"{hit_rate:.1f}%",
            "cache_type": "redis" if USE_REDIS else "in_memory",
            "status": "operational"
        }
    }

@app.get("/api/cache/stats")
async def cache_stats():
    """Статистика кэша"""
    if USE_REDIS:
        try:
            keys = redis_client.keys("profile:*")
            return {
                "cache_type": "redis",
                "cached_profiles": len(keys),
                "status": "connected"
            }
        except:
            return {"cache_type": "redis", "status": "error"}
    else:
        return {
            "cache_type": "in_memory",
            "cached_items": len(in_memory_cache),
            "keys": list(in_memory_cache.keys())
        }
