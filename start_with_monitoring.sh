#!/bin/bash

echo "🚀 Запуск API Gateway с мониторингом..."
echo ""

# Проверяем Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен!"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен!"
    exit 1
fi

# Останавливаем старые контейнеры
echo "1. Останавливаем старые контейнеры..."
docker-compose down 2>/dev/null || true

# Удаляем volumes (опционально)
if [[ "$1" == "--clean" ]]; then
    echo "🧹 Очистка volumes..."
    docker-compose down -v 2>/dev/null || true
fi

# Проверяем конфигурацию docker-compose
echo "2. Проверка конфигурации..."
if ! docker-compose config -q; then
    echo "❌ Ошибка в docker-compose.yml!"
    exit 1
fi

# Запускаем все сервисы
echo "3. Запускаем все сервисы..."
docker-compose up --build -d

echo "4. Ожидаем запуска всех сервисов..."
for i in {1..60}; do
    echo -n "."
    sleep 1
    
    # Проверяем ключевые сервисы
    if [ $i -eq 30 ]; then
        echo ""
        echo "   Проверяем запуск сервисов..."
        
        # Проверяем Redis
        if docker-compose ps redis | grep -q "Up"; then
            echo "   ✅ Redis запущен"
        else
            echo "   ❌ Redis не запущен"
        fi
        
        # Проверяем API Gateway
        if docker-compose ps api-gateway | grep -q "Up"; then
            echo "   ✅ API Gateway запущен"
        else
            echo "   ❌ API Gateway не запущен"
        fi
    fi
done
echo ""

echo "5. Проверяем статус контейнеров..."
docker-compose ps

echo ""
echo "6. Проверяем доступность сервисов..."
echo ""

# Функция для проверки доступности
check_service() {
    local name=$1
    local url=$2
    local timeout=5
    
    if curl -s --max-time $timeout $url > /dev/null 2>&1; then
        echo "✅ $name доступен: $url"
        return 0
    else
        echo "❌ $name не доступен: $url"
        return 1
    fi
}

# Даем больше времени для запуска
sleep 10

# Проверяем API Gateway
check_service "API Gateway" "http://localhost:8000/health"

# Проверяем Prometheus
check_service "Prometheus" "http://localhost:9090"

# Проверяем Grafana (может запускаться дольше)
sleep 5
check_service "Grafana" "http://localhost:3000"

echo ""
echo "7. Генерируем тестовый трафик для метрик..."
echo ""

# Генерируем тестовые запросы
for i in {1..5}; do
    echo "   Запрос $i..."
    curl -s "http://localhost:8000/api/profile/user123" > /dev/null 2>&1 || true
    curl -s "http://localhost:8000/api/profile/user456" > /dev/null 2>&1 || true
    sleep 2
done

echo ""
echo "8. Проверяем метрики API Gateway..."
if curl -s http://localhost:8000/metrics 2>/dev/null | head -5 | grep -q "TYPE"; then
    echo "✅ Метрики API Gateway доступны"
else
    echo "❌ Метрики API Gateway не доступны"
fi

echo ""
echo "📊 МОНИТОРИНГ ЗАПУЩЕН!"
echo ""
echo "🔗 Ссылки для доступа:"
echo "   - API Gateway:      http://localhost:8000"
echo "   - Prometheus:       http://localhost:9090"
echo "   - Grafana:          http://localhost:3000 (логин: admin, пароль: admin123)"
echo "   - Redis метрики:    http://localhost:9121/metrics"
echo "   - Node метрики:     http://localhost:9100/metrics"
echo ""
echo "📈 Дашборды Grafana:"
echo "   - Перейдите в Grafana -> Dashboards -> Browse"
echo "   - Или импортируйте дашборд с ID: 1860 (Node Exporter Full)"
echo ""
echo "🛑 Для остановки выполните: docker-compose down"
echo ""
echo "📋 Для просмотра логов:"
echo "   docker-compose logs -f api-gateway"
echo "   docker-compose logs -f prometheus"
echo "   docker-compose logs -f grafana"
