from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import httpx
import asyncio
import redis
import json
import time
import logging
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import structlog

# Настройка структурированного логирования
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

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

# Prometheus метрики
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'http_active_requests',
    'Active HTTP requests'
)

CACHE_HITS = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

AGGREGATION_TIME = Histogram(
    'aggregation_duration_seconds',
    'Time taken to aggregate data from services'
)

SERVICE_ERRORS = Counter(
    'service_errors_total',
    'Total service errors',
    ['service_name']
)

# Подключение к Redis
try:
    redis_client = redis.Redis(
        host='redis',
        port=6379,
        db=0,
        password='redispass123',
        decode_responses=False,
        socket_connect_timeout=2,
        socket_timeout=2,
        retry_on_timeout=True
    )
    redis_client.ping()
    logger.info("redis_connected", status="success")
    USE_REDIS = True
except Exception as e:
    logger.error("redis_connection_failed", error=str(e))
    print("⚠️  Redis не доступен, использую in-memory кэш")
    USE_REDIS = False
    in_memory_cache = {}

def get_cache(key: str):
    """Получение данных из кэша"""
    if USE_REDIS:
        try:
            start_time = time.time()
            data = redis_client.get(key)
            redis_latency = time.time() - start_time
            
            if redis_latency > 0.1:  # Логируем медленные запросы
                logger.warning("redis_slow_query", key=key, latency=redis_latency)
                
            if data:
                CACHE_HITS.labels(cache_type='redis').inc()
                return json.loads(data.decode('utf-8'))
            CACHE_MISSES.labels(cache_type='redis').inc()
        except Exception as e:
            logger.error("redis_get_error", key=key, error=str(e))
            SERVICE_ERRORS.labels(service_name='redis').inc()
            return None
    else:
        cached = in_memory_cache.get(key)
        if cached and time.time() - cached["timestamp"] < 30:
            CACHE_HITS.labels(cache_type='memory').inc()
            return cached["data"]
        CACHE_MISSES.labels(cache_type='memory').inc()
    return None

def set_cache(key: str, value: dict, ttl: int = 30):
    """Сохранение данных в кэш"""
    if USE_REDIS:
        try:
            redis_client.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.error("redis_set_error", key=key, error=str(e))
            SERVICE_ERRORS.labels(service_name='redis').inc()
    else:
        in_memory_cache[key] = {
            "data": value,
            "timestamp": time.time()
        }

async def fetch_service(service_name: str, url: str, timeout: float = 5.0):
    """Запрос к микросервису с метриками"""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            start_time = time.time()
            response = await client.get(url)
            latency = time.time() - start_time
            
            if latency > 1.0:  # Логируем медленные ответы
                logger.warning("service_slow_response", service=service_name, latency=latency, url=url)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error("service_error", service=service_name, status_code=response.status_code, url=url)
                SERVICE_ERRORS.labels(service_name=service_name).inc()
                return None
    except Exception as e:
        logger.error("service_unavailable", service=service_name, error=str(e), url=url)
        SERVICE_ERRORS.labels(service_name=service_name).inc()
        return None

@app.get("/")
async def root():
    """Главная страница"""
    logger.info("root_request")
    return {
        "message": "API Gateway (Backend for Frontend) с агрегацией данных и мониторингом",
        "author": "Ваше Имя",
        "project": "Микросервисы: API Gateway BFF с Prometheus/Grafana",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "monitoring": {
            "prometheus": "http://localhost:9090",
            "grafana": "http://localhost:3000 (admin/admin123)",
            "metrics": "http://localhost:8000/metrics"
        },
        "endpoints": [
            "GET /health - Проверка здоровья",
            "GET /api/profile/{user_id} - Агрегированный профиль",
            "GET /metrics - Prometheus метрики",
            "GET /api/cache/stats - Статистика кэша",
            "GET /api/system/info - Системная информация"
        ]
    }

@app.get("/health")
async def health():
    """Проверка здоровья системы"""
    ACTIVE_REQUESTS.inc()
    
    services_status = {}
    health_tasks = []
    
    # Проверяем доступность сервисов параллельно
    services = [
        ("user_service", f"{USER_SERVICE_URL}/health"),
        ("order_service", f"{ORDER_SERVICE_URL}/health"),
        ("product_service", f"{PRODUCT_SERVICE_URL}/health")
    ]
    
    for service_name, url in services:
        health_tasks.append(fetch_service(service_name, url, timeout=2.0))
    
    results = await asyncio.gather(*health_tasks)
    
    for (service_name, _), result in zip(services, results):
        services_status[service_name] = "healthy" if result else "unhealthy"
    
    # Проверяем Redis
    redis_status = "connected" if USE_REDIS else "disconnected"
    if USE_REDIS:
        try:
            redis_client.ping()
            redis_status = "healthy"
        except:
            redis_status = "unhealthy"
    
    services_status["redis"] = redis_status
    
    ACTIVE_REQUESTS.dec()
    
    return {
        "status": "healthy",
        "service": "api-gateway",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": services_status,
        "cache": {
            "type": "redis" if USE_REDIS else "in_memory",
            "status": redis_status
        }
    }

@app.get("/api/profile/{user_id}")
async def get_user_profile(user_id: str, request: Request):
    """Агрегированный профиль пользователя с кэшированием на 30 секунд"""
    ACTIVE_REQUESTS.inc()
    start_time = time.time()
    
    # Ключ для кэша
    cache_key = f"profile:{user_id}"
    
    # Пробуем получить из кэша
    cached_data = get_cache(cache_key)
    if cached_data:
        latency = time.time() - start_time
        REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=200).inc()
        REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path).observe(latency)
        ACTIVE_REQUESTS.dec()
        
        cached_data["metadata"]["cached"] = True
        cached_data["metadata"]["response_time_ms"] = round(latency * 1000, 2)
        return cached_data
    
    # Начинаем агрегацию
    aggregation_start = time.time()
    
    # Параллельно запрашиваем данные из сервисов
    user_task = fetch_service("user_service", f"{USER_SERVICE_URL}/users/{user_id}")
    orders_task = fetch_service("order_service", f"{ORDER_SERVICE_URL}/orders/user/{user_id}")
    
    user_data, orders_data = await asyncio.gather(user_task, orders_task)
    
    if not user_data:
        REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=404).inc()
        ACTIVE_REQUESTS.dec()
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
        except Exception as e:
            logger.error("batch_products_error", error=str(e))
    
    # Замеряем время агрегации
    aggregation_time = time.time() - aggregation_start
    AGGREGATION_TIME.observe(aggregation_time)
    
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
            "aggregation_time_ms": round(aggregation_time * 1000, 2),
            "cache_ttl": 30,
            "cached": False,
            "services_used": 3
        }
    }
    
    # Сохраняем в кэш на 30 секунд
    set_cache(cache_key, response)
    
    # Метрики
    total_time = time.time() - start_time
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=200).inc()
    REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path).observe(total_time)
    ACTIVE_REQUESTS.dec()
    
    response["metadata"]["response_time_ms"] = round(total_time * 1000, 2)
    
    logger.info("profile_aggregated", 
                user_id=user_id, 
                response_time_ms=round(total_time * 1000, 2),
                cached=False)
    
    return response

@app.get("/metrics")
async def metrics():
    """Endpoint для Prometheus метрик"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@app.get("/api/cache/stats")
async def cache_stats():
    """Статистика кэша"""
    if USE_REDIS:
        try:
            info = redis_client.info()
            keys = redis_client.keys("profile:*")
            
            return {
                "cache_type": "redis",
                "status": "connected",
                "stats": {
                    "cached_profiles": len(keys),
                    "used_memory_human": info.get("used_memory_human", "N/A"),
                    "connected_clients": info.get("connected_clients", 0),
                    "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
                    "hit_rate": info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1), 1)
                }
            }
        except Exception as e:
            logger.error("redis_info_error", error=str(e))
            return {"cache_type": "redis", "status": "error", "error": str(e)}
    else:
        return {
            "cache_type": "in_memory",
            "status": "active",
            "stats": {
                "cached_items": len(in_memory_cache),
                "keys": list(in_memory_cache.keys())[:10]
            }
        }

@app.get("/api/system/info")
async def system_info():
    """Системная информация для мониторинга"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    return {
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent
        },
        "process": {
            "pid": process.pid,
            "memory_mb": round(memory_info.rss / 1024 / 1024, 2),
            "cpu_percent": process.cpu_percent(interval=0.1),
            "threads": process.num_threads(),
            "connections": len(process.connections())
        },
        "api_gateway": {
            "redis_connected": USE_REDIS,
            "cache_type": "redis" if USE_REDIS else "in_memory",
            "start_time": datetime.fromtimestamp(process.create_time()).isoformat()
        }
    }

@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    """Middleware для сбора метрик Prometheus"""
    start_time = time.time()
    
    try:
        response = await call_next(request)
        
        # Не логируем метрики для самого endpoint /metrics
        if request.url.path != "/metrics":
            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(time.time() - start_time)
            
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code
            ).inc()
        
        return response
        
    except Exception as e:
        logger.error("request_error", 
                    method=request.method,
                    path=request.url.path,
                    error=str(e))
        
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=500
        ).inc()
        
        raise

@app.on_event("startup")
async def startup_event():
    """Действия при запуске приложения"""
    logger.info("api_gateway_starting", version="1.0.0")
    
@app.on_event("shutdown")
async def shutdown_event():
    """Действия при остановке приложения"""
    logger.info("api_gateway_shutting_down")
    if USE_REDIS:
        try:
            redis_client.close()
        except:
            pass
