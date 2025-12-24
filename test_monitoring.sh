#!/bin/bash

echo "🧪 Тестирование системы мониторинга"
echo "=================================="
echo ""

echo "1. Проверка доступности компонентов..."
echo ""

components=(
    "API Gateway:8000"
    "Prometheus:9090"
    "Grafana:3000"
    "Redis:6379"
    "Node Exporter:9100"
    "Redis Exporter:9121"
)

for component in "${components[@]}"; do
    name=$(echo $component | cut -d: -f1)
    port=$(echo $component | cut -d: -f2)
    
    if nc -z localhost $port 2>/dev/null; then
        echo "✅ $name доступен на порту $port"
    else
        echo "❌ $name не доступен на порту $port"
    fi
done

echo ""
echo "2. Проверка метрик Prometheus..."
echo ""

metrics_endpoints=(
    "http://localhost:8000/metrics"
    "http://localhost:9100/metrics"
    "http://localhost:9121/metrics"
)

for endpoint in "${metrics_endpoints[@]}"; do
    if curl -s $endpoint | grep -q "TYPE"; then
        echo "✅ Метрики доступны: $(echo $endpoint | cut -d/ -f3)"
    else
        echo "❌ Метрики не доступны: $(echo $endpoint | cut -d/ -f3)"
    fi
done

echo ""
echo "3. Генерация тестового трафика..."
echo ""

echo "Отправляем 20 тестовых запросов..."
for i in {1..20}; do
    echo -n "."
    curl -s "http://localhost:8000/api/profile/user$((i % 2 + 1))" > /dev/null
    sleep 0.5
done
echo ""

echo ""
echo "4. Проверка данных в Prometheus..."
echo ""

prometheus_queries=(
    "http_requests_total"
    "http_request_duration_seconds_count"
    "cache_hits_total"
    "cache_misses_total"
)

for query in "${prometheus_queries[@]}"; do
    result=$(curl -s "http://localhost:9090/api/v1/query?query=$query" | jq '.data.result | length')
    if [[ "$result" -gt 0 ]]; then
        echo "✅ Prometheus собирает метрику: $query ($result серий)"
    else
        echo "❌ Prometheus не нашел метрику: $query"
    fi
done

echo ""
echo "5. Проверка Grafana..."
echo ""

if curl -s "http://admin:admin123@localhost:3000/api/health" | grep -q "database"; then
    echo "✅ Grafana работает"
else
    echo "❌ Grafana не отвечает"
fi

echo ""
echo "6. Статистика Redis..."
echo ""

if docker-compose exec redis redis-cli -a redispass123 ping | grep -q "PONG"; then
    echo "✅ Redis работает"
    
    # Проверяем кэш
    keys=$(docker-compose exec redis redis-cli -a redispass123 keys "profile:*" | wc -l)
    echo "   Кэшированных профилей: $keys"
    
    # Проверяем память
    memory=$(docker-compose exec redis redis-cli -a redispass123 info memory | grep used_memory_human)
    echo "   Используемая память: $memory"
else
    echo "❌ Redis не отвечает"
fi

echo ""
echo "=================================="
echo "✅ Тестирование завершено!"
echo ""
echo "📊 Для просмотра метрик откройте:"
echo "   - Prometheus: http://localhost:9090"
echo "   - Grafana:    http://localhost:3000"
echo "   - Логин в Grafana: admin / admin123"
