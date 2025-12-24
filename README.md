API Gateway (Backend for Frontend)

Описание проекта
Проект реализует архитектурный паттерн Backend for Frontend (BFF) и предназначен для изучения принципов построения промежуточного слоя между клиентскими приложениями и микросервисной системой.
API Gateway агрегирует данные из нескольких микросервисов, предоставляет единый REST API, поддерживает кэширование, мониторинг и отказоустойчивость.

Цели проекта
Реализация API Gateway;
Агрегация данных из нескольких микросервисов;
Реализация кэширования с использованием Redis;
Настройка мониторинга на базе Prometheus и Grafana;
Обеспечение отказоустойчивости;
Предоставление единого REST API для клиентских приложений;

Архитектура
Клиент (Web / Mobile App);
HTTP / REST;
API Gateway (BFF);
FastAPI; Python; Redis;
Port: 8000;

Функции API Gateway;
Агрегация данных из 3 микросервисов;
Кэширование данных (Redis, TTL 30 секунд);
Экспорт метрик для Prometheus;
Health check всех компонентов;
Fallback на in-memory кэш при недоступности Redis;

Микросервисы;
User Service; Port: 8001;
Order Service; Port: 8002;
Product Service; Port: 8003;

Технологический стек
Backend;
Python 3.11;
FastAPI;
Uvicorn;
HTTPX;
Redis;
Prometheus Client;

Контейнеризация и оркестрация;
Docker;
Docker Compose;

Мониторинг и наблюдаемость;
Prometheus;
Grafana;
Redis Exporter;
Node Exporter;

Быстрый старт
Запуск всех сервисов и системы мониторинга осуществляется с помощью скрипта;
chmod +x start_with_monitoring.sh
./start_with_monitoring.sh


После запуска доступны следующие компоненты;
API Gateway: http://localhost:8000

Prometheus: http://localhost:9090

Grafana: http://localhost:3000

Данные для входа; admin / admin123;

Микросервисы и API
User Service (порт 8001);
GET /users/{id}; получение пользователя;
GET /health; health check;

Order Service (порт 8002);
GET /orders/user/{id}; заказы пользователя;
GET /health; health check;

Product Service (порт 8003);
GET /products/{id}; получение товара;
POST /products/batch; получение списка товаров;
GET /health; health check;

API Gateway
Агрегирующий endpoint;
GET /api/profile/{user_id};

Endpoint агрегирует
данные пользователя;
список заказов пользователя;
данные товаров, связанных с заказами;

Кэширование
Redis используется для хранения агрегированных данных;
TTL кэша составляет 30 секунд;
При недоступности Redis используется in-memory кэш;
Собираемые метрики кэширования;
cache_hits_total;
cache_misses_total;
aggregation_duration_seconds;

Мониторинг
Доступ к компонентам мониторинга;

Prometheus; http://localhost:9090
 сбор и запрос метрик;

Grafana; http://localhost:3000
 визуализация метрик;

API Gateway Metrics; http://localhost:8000/metrics
 метрики API Gateway;

Redis Exporter; http://localhost:9121/metrics
 метрики Redis;

Node Exporter; http://localhost:9100/metrics
 системные метрики;

Собираемые метрики
HTTP метрики API Gateway
http_requests_total;
http_request_duration_seconds;
http_active_requests;

Метрики кэширования
cache_hits_total;
cache_misses_total;

Метрики ошибок
service_errors_total;

Redis метрики
использование памяти;
количество подключений;
hit / miss ratio;
количество команд в секунду;

Системные метрики;
CPU;
память;
диск;
сеть;

Отказоустойчивость
Параллельные запросы к микросервисам;
Обработка ошибок отдельных сервисов;
Возврат частичных данных при сбоях;

Логирование
Структурированное логирование;
Формат логов JSON;

Сценарий использования
Клиент отправляет запрос на API Gateway;
API Gateway проверяет наличие данных в Redis;
При отсутствии кэша выполняются параллельные запросы к микросервисам;
Полученные данные агрегируются;
Результат сохраняется в кэш;
Ответ возвращается клиенту;
Метрики собираются Prometheus;
Данные визуализируются в Grafana;


Проект выполнен в учебных целях для изучения микросервисной архитектуры, паттерна Backend for Frontend и инструментов мониторинга.
