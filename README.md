 API Gateway (Backend for Frontend)

 Цели проекта

- Реализация API Gateway (BFF)
- Агрегация данных из нескольких микросервисов
- Реализация кэширования с использованием Redis
- Настройка мониторинга на базе Prometheus и Grafana
- Обеспечение отказоустойчивости 
- Предоставление единого REST API для клиентских приложений

---

 Архитектура


 Клиент (Web / Mobile App)
          │ HTTP / REST
          ▼
   API Gateway (BFF)
   FastAPI • Python • Redis
   Port: 8000

   Функции:
   • Агрегация данных из 3 микросервисов
   • Кэширование (Redis, TTL 30 сек)
   • Экспорт метрик (Prometheus)
   • Health checks всех компонентов
   • Fallback на кэш из памяти

        │            │             │
        ▼            ▼             ▼
  User Service   Order Service  Product Service
  FastAPI        FastAPI        FastAPI
  Port: 8001     Port: 8002     Port: 8003


---

 Технологический стек

 Backend

- Python 3.11
- FastAPI
- Uvicorn
- HTTPX
- Redis
- Prometheus Client

 Контейнеризация и оркестрация

- Docker
- Docker Compose

 Мониторинг и наблюдаемость

- Prometheus
- Grafana
- Redis Exporter
- Node Exporter

---

 Быстрый старт

chmod +x start_with_monitoring.sh
./start_with_monitoring.sh


После запуска доступны:

- API Gateway: [http://localhost:8000](http://localhost:8000)
- Prometheus: [http://localhost:9090](http://localhost:9090)
- Grafana: [http://localhost:3000](http://localhost:3000) (admin / admin123)

---

 Микросервисы и API

 User Service (порт 8001)

| Endpoint        | Описание               |
| --------------- | ---------------------- |
| GET /users/{id} | Получение пользователя |
| GET /health     | Health check           |

 Order Service (порт 8002)

| Endpoint              | Описание            |
| --------------------- | ------------------- |
| GET /orders/user/{id} | Заказы пользователя |
| GET /health           | Health check        |

 Product Service (порт 8003)

| Endpoint             | Описание                 |
| -------------------- | ------------------------ |
| GET /products/{id}   | Получение товара         |
| POST /products/batch | Получение списка товаров |
| GET /health          | Health check             |

---

 API Gateway

 Агрегирующий endpoint


GET /api/profile/{user_id}


Endpoint агрегирует:

- данные пользователя
- список заказов
- данные товаров, связанных с заказами

---

 Кэширование

- Redis используется для хранения агрегированных данных
- TTL кэша — 30 секунд
- При недоступности Redis используется кэш из памяти

Собираемые метрики:

- cache_hits_total
- cache_misses_total
- aggregation_duration_seconds

---

 Мониторинг

 Доступ к компонентам

| Компонент           | URL                                                            | Назначение          |
| ------------------- | -------------------------------------------------------------- | ------------------- |
| Prometheus          | [http://localhost:9090](http://localhost:9090)                 | Сбор метрик         |
| Grafana             | [http://localhost:3000](http://localhost:3000)                 | Визуализация метрик |
| API Gateway Metrics | [http://localhost:8000/metrics](http://localhost:8000/metrics) | Метрики API Gateway |
| Redis Exporter      | [http://localhost:9121/metrics](http://localhost:9121/metrics) | Метрики Redis       |
| Node Exporter       | [http://localhost:9100/metrics](http://localhost:9100/metrics) | Системные метрики   |

---

 Собираемые метрики

 HTTP метрики API Gateway

- http_requests_total
- http_request_duration_seconds
- http_active_requests

 Метрики кэширования

- cache_hits_total
- cache_misses_total

 Метрики ошибок

- service_errors_total

 Redis метрики

- Использование памяти
- Количество подключений
- Hit / Miss ratio
- Команды в секунду


---

 Отказоустойчивость

- Параллельные запросы к микросервисам
- Обработка ошибок отдельных сервисов
- Возврат частичных данных при сбоях
- Graceful degradation

---

 Логирование

- Структурированное логирование
- Формат JSON


---

 Сценарий использования

1. Клиент отправляет запрос на API Gateway
2. API Gateway проверяет наличие данных в Redis
3. При отсутствии кэша выполняются параллельные запросы к микросервисам
4. Полученные данные агрегируются
5. Результат сохраняется в кэш
6. Ответ возвращается клиенту
7. Метрики собираются Prometheus
8. Данные визуализируются в Grafana

---


Проект выполнен в учебных целях для изучения микросервисной архитектуры, паттерна Backend for Frontend и инструментов мониторинга.
