#!/bin/bash
# check_infra.sh - Verificación rápida de infraestructura

echo "=== Infrastructure Health Check ==="
echo ""

# Redis
echo -n "Redis: "
docker exec redis_dev redis-cli ping 2>/dev/null && echo "✅ OK" || echo "❌ FAIL"

# Postgres
echo -n "Postgres: "
docker exec postgres_dev psql -U agent_user -d agent_db -c "SELECT 1;" > /dev/null 2>&1 && echo "✅ OK" || echo "❌ FAIL"

# Containers
echo ""
echo "=== Container Status ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "NAME|redis_dev|postgres_dev"

echo ""
echo "=== Quick Stats ==="
echo -n "Tasks in DB: "
docker exec postgres_dev psql -U agent_user -d agent_db -t -c "SELECT COUNT(*) FROM agent_system.tasks;"

echo -n "Redis keys: "
docker exec redis_dev redis-cli DBSIZE | cut -d: -f2
