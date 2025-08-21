# 🚀 Performance Testing Guide

Esta guía describe cómo ejecutar y utilizar los tests de rendimiento implementados para completar la **Fase 2** del proyecto.

## 📋 Índice

1. [Descripción General](#descripción-general)
2. [Tests Implementados](#tests-implementados)
3. [Ejecución de Tests](#ejecución-de-tests)
4. [Interpretación de Resultados](#interpretación-de-resultados)
5. [CI/CD Integration](#cicd-integration)
6. [Troubleshooting](#troubleshooting)

## 🎯 Descripción General

La **Fase 2** incluye una suite completa de tests de rendimiento que cubren:

- ✅ **Cache Redis para reportes frecuentes**
- ✅ **Validaciones de negocio más robustas**
- ✅ **Sistema de auditoría y logs**
- ✅ **API rate limiting**
- ✅ **Tests de rendimiento y carga**

## 🧪 Tests Implementados

### 1. Database Benchmarks (`scripts/db_benchmarks.py`)

Mide el rendimiento de queries complejas y operaciones de base de datos.

**Características:**
- Queries simples y complejas
- Tests de concurrencia de base de datos
- Análisis de índices
- Reportes de rendimiento

**Ejecución:**
```bash
python scripts/db_benchmarks.py
```

### 2. Memory Stress Tests (`scripts/memory_stress_test.py`)

Detecta memory leaks y mide el uso de memoria bajo carga.

**Características:**
- Detección de memory leaks
- Tests de memoria en queries
- Tests de concurrencia de memoria
- Tests de cache de memoria

**Ejecución:**
```bash
python scripts/memory_stress_test.py
```

### 3. Concurrency Tests (`sales/tests_concurrency.py`)

Prueba el comportamiento del sistema bajo carga concurrente.

**Características:**
- Creación concurrente de tickets
- Generación concurrente de reportes
- Operaciones mixtas (lectura/escritura)
- Tests de pool de conexiones
- Tests de rate limiting

**Ejecución:**
```bash
python manage.py test sales.tests_concurrency --verbosity=2
```

### 4. Load Tests (`locustfile.py`)

Tests de carga usando Locust para simular usuarios reales.

**Características:**
- Múltiples tipos de usuarios
- Escenarios de carga ligera y pesada
- Tests de reportes
- Tests de administración

**Ejecución:**
```bash
# Modo interactivo
locust -f locustfile.py

# Modo headless
locust -f locustfile.py --headless --users 10 --spawn-rate 2 --run-time 60s
```

## 🚀 Ejecución de Tests

### Ejecución Individual

```bash
# 1. Database Benchmarks
python scripts/db_benchmarks.py

# 2. Memory Stress Tests
python scripts/memory_stress_test.py

# 3. Concurrency Tests
python manage.py test sales.tests_concurrency --verbosity=2

# 4. Load Tests
locust -f locustfile.py --headless --users 10 --spawn-rate 2 --run-time 60s
```

### Ejecución Completa

```bash
# Ejecutar toda la suite de tests
python scripts/run_performance_tests.py
```

### Ejecución en Docker

```bash
# Construir y ejecutar tests en contenedor
docker compose -f docker-compose.dev.yml up -d
docker compose -f docker-compose.dev.yml exec backend python scripts/run_performance_tests.py
```

## 📊 Interpretación de Resultados

### Database Benchmarks

**Métricas importantes:**
- `execution_time`: Tiempo de ejecución en segundos
- `query_count`: Número de queries ejecutadas
- `result_size`: Tamaño del resultado

**Umbrales recomendados:**
- ✅ Queries simples: < 0.1s
- ✅ Queries complejas: < 1.0s
- ✅ Reportes: < 5.0s

### Memory Stress Tests

**Métricas importantes:**
- `memory_leak_mb`: Memoria no liberada en MB
- `peak_memory_mb`: Uso máximo de memoria
- `cleanup_decrease_mb`: Memoria liberada

**Umbrales recomendados:**
- ✅ Memory leak: < 10MB
- ✅ Peak memory: < 500MB
- ✅ Cleanup efficiency: > 90%

### Concurrency Tests

**Métricas importantes:**
- `successful_requests`: Requests exitosos
- `failed_requests`: Requests fallidos
- `execution_time`: Tiempo promedio

**Umbrales recomendados:**
- ✅ Success rate: > 95%
- ✅ Average response time: < 2.0s
- ✅ Concurrent users: > 10

### Load Tests

**Métricas importantes:**
- `RPS`: Requests por segundo
- `Response time`: Tiempo de respuesta
- `Error rate`: Tasa de errores

**Umbrales recomendados:**
- ✅ RPS: > 100
- ✅ Response time (95th percentile): < 1.0s
- ✅ Error rate: < 1%

## 🔄 CI/CD Integration

### GitHub Actions

Los tests de rendimiento se ejecutan automáticamente:

1. **En Pull Requests**: Para verificar cambios
2. **En Push a main/develop**: Para monitoreo continuo
3. **Diariamente**: Para tendencias de rendimiento

### Workflow (`/.github/workflows/performance-tests.yml`)

```yaml
# Se ejecuta en:
# - Push a main/develop
# - Pull requests
# - Diariamente a las 2 AM UTC
```

### Artifacts Generados

- `performance-reports/`: Reportes JSON y HTML
- `performance-dashboard/`: Dashboard de métricas
- Comentarios automáticos en PRs

## 🛠️ Troubleshooting

### Problemas Comunes

#### 1. Locust no está instalado

```bash
pip install locust==2.17.0
```

#### 2. Tests de memoria fallan

```bash
# Verificar que psutil está instalado
pip install psutil==5.9.8

# Verificar permisos de memoria
sudo sysctl -w vm.max_map_count=262144
```

#### 3. Tests de concurrencia fallan

```bash
# Verificar configuración de base de datos
python manage.py check

# Verificar que Redis está corriendo
redis-cli ping
```

#### 4. Rate limiting no funciona

```bash
# Verificar configuración en settings.py
RATE_LIMITING = {
    'ENABLED': True,
    # ... otras configuraciones
}
```

### Logs y Debugging

#### Habilitar logs detallados

```python
# En settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

#### Verificar métricas de Prometheus

```bash
# Acceder a métricas
curl http://localhost:8000/metrics

# Verificar cache
curl http://localhost:8000/api/sales/reports/cache/stats/
```

## 📈 Monitoreo Continuo

### Métricas Clave a Monitorear

1. **Database Performance**
   - Query execution time
   - Connection pool usage
   - Cache hit rate

2. **Memory Usage**
   - Memory leaks
   - Peak memory usage
   - Garbage collection efficiency

3. **API Performance**
   - Response times
   - Throughput (RPS)
   - Error rates

4. **Rate Limiting**
   - Requests blocked
   - Rate limit headers
   - IP whitelist effectiveness

### Alertas Recomendadas

```yaml
# Ejemplo de alertas
alerts:
  - name: "High Response Time"
    condition: "response_time > 2.0s"
    threshold: "5 minutes"
  
  - name: "Memory Leak Detected"
    condition: "memory_leak > 50MB"
    threshold: "1 hour"
  
  - name: "High Error Rate"
    condition: "error_rate > 5%"
    threshold: "2 minutes"
```

## 🎯 Próximos Pasos

### Mejoras Planificadas

1. **Grafana Dashboards**
   - Dashboards en tiempo real
   - Alertas automáticas
   - Histórico de métricas

2. **Tests de Stress Avanzados**
   - Tests de recuperación
   - Tests de fallback
   - Tests de escalabilidad

3. **Automatización Avanzada**
   - Tests de regresión automática
   - Comparación de versiones
   - Reportes automáticos

### Contribución

Para contribuir a los tests de rendimiento:

1. Crear tests específicos para nuevas funcionalidades
2. Actualizar umbrales según necesidades del negocio
3. Agregar métricas relevantes
4. Documentar nuevos escenarios de prueba

---

## 📞 Soporte

Para problemas o preguntas sobre los tests de rendimiento:

1. Revisar logs en `logs/performance.log`
2. Verificar configuración en `core/settings.py`
3. Consultar métricas en `/api/health/`
4. Revisar reportes en `performance-reports/`

**Estado de la Fase 2: ✅ COMPLETADO (100%)**
