#!/bin/bash

echo "========================================="
echo "   ТЕСТИРОВАНИЕ API GATEWAY BFF"
echo "========================================="
echo ""

echo "1. Проверка доступности сервисов..."
echo ""

echo "API Gateway:"
curl -s http://localhost:8000/health | python3 -m json.tool
echo ""

echo "User Service:"
curl -s http://localhost:8001/health
echo ""

echo "Order Service:"
curl -s http://localhost:8002/health
echo ""

echo "Product Service:"
curl -s http://localhost:8003/health
echo ""

echo "2. Получение агрегированного профиля пользователя (первый запрос)..."
echo ""
curl -s http://localhost:8000/api/profile/user123 | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f' Пользователь: {data[\"user\"][\"full_name\"]}')
print(f' Заказов: {data[\"metadata\"][\"orders_count\"]} шт.')
print(f' Товаров: {data[\"metadata\"][\"products_count\"]} шт.')
print(f' Из кэша: {data[\"metadata\"][\"cached\"]}')
print(f'  Агрегировано: {data[\"metadata\"][\"aggregated_at\"][11:19]}')
"
echo ""

echo "3. Повторный запрос того же профиля (должен быть из кэша)..."
echo ""
curl -s http://localhost:8000/api/profile/user123 | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f' Из кэша: {data[\"metadata\"][\"cached\"]}')
"
echo ""

echo "4. Проверка метрик API Gateway..."
echo ""
curl -s http://localhost:8000/metrics | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f' Всего запросов: {data[\"metrics\"][\"requests_total\"]}')
print(f' Попаданий в кэш: {data[\"metrics\"][\"cache_hits\"]}')
print(f' Промахов кэша: {data[\"metrics\"][\"cache_misses\"]}')
print(f' Эффективность кэша: {data[\"performance\"][\"cache_hit_rate\"]}')
"
echo ""

echo "5. Статистика кэша..."
curl -s http://localhost:8000/api/cache/stats | python3 -m json.tool
echo ""

echo "========================================="
echo "   ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!"
echo "========================================="
