API Gateway (Backend for Frontend - BFF) - это микросервисная система, демонстрирующая архитектурный паттерн "Backend for Frontend". 
Основная цель проекта - научиться проектировать промежуточный слой между фронтендом и микросервисами, который объединяет данные из нескольких источников в единый API с поддержкой кэширования, мониторинга и отказоустойчивости.

Основные задачи проекта:
Разработать API Gateway, который агрегирует данные из трёх микросервисов

Реализовать кэширование агрегированных данных с помощью Redis

Настроить систему мониторинга на основе Prometheus и Grafana

Обеспечить отказоустойчивость и graceful degradation

Предоставить единый REST API для клиентских приложений


                   Клиент (Web/Mobile App)                  

                              │ HTTP/REST
                              ▼
                    API Gateway (BFF)                        
                    FastAPI • Python • Redis                 
                     Порт: 8000                               

  Функции:                                                  
  • Агрегация данных из 3 микросервисов                     
  • Кэширование (Redis, 30 сек)                             
  • Мониторинг метрик (Prometheus)                          
  • Health checks всех компонентов                          
  • Fallback на in-memory кэш                               

               │               │                 │
               ▼               ▼                 ▼
         User Service     Order Service   Product Service
         FastAPI          FastAPI         FastAPI       
         Порт: 8001       Порт: 8002      Порт: 8003    
    

 Технологический стек
Backend:
Python 3.11 - основной язык разработки
FastAPI - современный асинхронный веб-фреймворк
Uvicorn - ASGI-сервер для запуска FastAPI
HTTPX - асинхронный HTTP-клиент
Redis - система кэширования in-memory
Prometheus Client - экспорт метрик

Контейнеризация и оркестрация:
Docker - контейнеризация приложений
Docker Compose - оркестрация многоконтейнерного приложения

Мониторинг и наблюдение:
Prometheus - сбор метрик и мониторинг
Grafana - визуализация метрик и дашборды
Redis Exporter - экспорт метрик Redis
Node Exporter - сбор системных метрик

Для быстрого запуска есть скрипт chmod +x start_with_monitoring.sh
./start_with_monitoring.sh

Микросервисы
Сервис	                         Endpoint	                                        Описание
User Service	          http://localhost:8001/users/{id}	                Получить пользователя
User Service	          http://localhost:8001/health	                    Health check
Order Service	          http://localhost:8002/orders/user/{id}	          Заказы пользователя
Order Service	          http://localhost:8002/health	                    Health check
Product Service	        http://localhost:8003/products/{id}              	Получить товар
Product Service	        http://localhost:8003/products/batch	            Получить несколько товаров (POST)
Product Service	        http://localhost:8003/health	                    Health check

Система мониторинга
Доступ к компонентам мониторинга:
Компонент	       	            URL	          		          Доступ	          		          Назначение
Prometheus		          http://localhost:9090	          	Веб-интерфейс		              Сбор и запрос метрик
Grafana		              http://localhost:3000	            admin / admin123		          Визуализация метрик
API Gateway Metrics    	http://localhost:8000/metrics	    Текстовый формат		          Метрики API Gateway
Redis Exporter	        http://localhost:9121/metrics	    Текстовый формат	            Метрики Redis
Node Exporter	           http://localhost:9100/metrics	  Текстовый формат	            Системные метрики


Собираемые метрики:
1. HTTP метрики API Gateway:
http_requests_total - общее количество HTTP запросов
http_request_duration_seconds - гистограмма времени выполнения запросов
http_active_requests - количество активных запросов

2. Метрики кэширования:
cache_hits_total - количество попаданий в кэш
cache_misses_total - количество промахов кэша
aggregation_duration_seconds - время агрегации данных

3. Метрики ошибок:
service_errors_total - количество ошибок по сервисам

4. Redis метрики:
Использование памяти
Количество подключений
Hit/miss ratio
Команды в секунду

5. Системные метрики:
Использование CPU, памяти, диска
Сетевая активность
Количество процессов


Соответствие требованиям задания
REST API с агрегацией данных	        Endpoint /api/profile/{user_id} объединяет данные из 3 микросервисов
Кэширование (Redis)	                  Redis кэширование с TTL 30 секунд, fallback на in-memory кэш
Retry и fallback	                    Обработка ошибок при запросах, возврат частичных данных
Микросервисная архитектура	          3 отдельных сервиса + API Gateway + Redis
Контейнеризация                       Docker Compose для оркестрации всех сервисов
Язык Python	                          Все сервисы реализованы на Python/FastAPI
Мониторинг	                          Prometheus + Grafana + Node Exporter + Redis Exporter
Логирование	                          Структурированное логирование в JSON формате


Сценарий использования:
Клиент запрашивает профиль пользователя через API Gateway
API Gateway проверяет кэш Redis:
Если данные в кэше (и не старше 30 сек) → возвращает из кэша
Если нет в кэше → параллельно запрашивает данные из трёх микросервисов
Микросервисы возвращают свои части данных
API Gateway агрегирует данные, сохраняет в кэш, возвращает клиенту
Prometheus собирает метрики со всех компонентов
Grafana отображает метрики на дашбордах

