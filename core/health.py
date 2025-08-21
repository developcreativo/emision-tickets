import time

import psutil
import redis
from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.urls import path


def health_check(request):
    """
    Health check básico del sistema
    """
    health_status = {
        'status': 'healthy',
        'timestamp': None,
        'services': {}
    }
    
    # Verificar base de datos
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = 'healthy'
        health_status['services']['database'] = {
            'status': db_status,
            'response_time': 'OK'
        }
    except Exception as e:
        health_status['services']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'degraded'
    
    # Verificar Redis
    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            socket_connect_timeout=5
        )
        redis_client.ping()
        health_status['services']['redis'] = {
            'status': 'healthy',
            'response_time': 'OK'
        }
    except Exception as e:
        health_status['services']['redis'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'degraded'
    
    # Verificar sistema de archivos
    try:
        disk_usage = psutil.disk_usage('/')
        disk_percent = disk_usage.percent
        
        if disk_percent > 90:
            disk_status = 'warning'
        elif disk_percent > 95:
            disk_status = 'critical'
        else:
            disk_status = 'healthy'
        
        health_status['services']['filesystem'] = {
            'status': disk_status,
            'usage_percent': disk_percent,
            'free_gb': disk_usage.free / (1024**3)
        }
        
        if disk_status != 'healthy':
            health_status['status'] = 'degraded'
            
    except Exception as e:
        health_status['services']['filesystem'] = {
            'status': 'unknown',
            'error': str(e)
        }
    
    # Verificar memoria del sistema
    try:
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        if memory_percent > 90:
            memory_status = 'warning'
        elif memory_percent > 95:
            memory_status = 'critical'
        else:
            memory_status = 'healthy'
        
        health_status['services']['memory'] = {
            'status': memory_status,
            'usage_percent': memory_percent,
            'available_gb': memory.available / (1024**3)
        }
        
        if memory_status != 'healthy':
            health_status['status'] = 'degraded'
            
    except Exception as e:
        health_status['services']['memory'] = {
            'status': 'unknown',
            'error': str(e)
        }
    
    # Verificar CPU
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        
        if cpu_percent > 80:
            cpu_status = 'warning'
        elif cpu_percent > 95:
            cpu_status = 'critical'
        else:
            cpu_status = 'healthy'
        
        health_status['services']['cpu'] = {
            'status': cpu_status,
            'usage_percent': cpu_percent
        }
        
        if cpu_status != 'healthy':
            health_status['status'] = 'degraded'
            
    except Exception as e:
        health_status['services']['cpu'] = {
            'status': 'unknown',
            'error': str(e)
        }
    
    # Determinar status general
    if health_status['status'] == 'healthy':
        status_code = 200
    elif health_status['status'] == 'degraded':
        status_code = 200  # Aún funcional pero con problemas
    else:
        status_code = 503  # Service Unavailable
    
    return JsonResponse(health_status, status=status_code)


def detailed_health_check(request):
    """
    Health check detallado con más información del sistema
    """
    detailed_status = {
        'status': 'healthy',
        'timestamp': None,
        'version': '1.0.0',
        'environment': 'production' if not settings.DEBUG else 'development',
        'services': {},
        'system_info': {},
        'performance_metrics': {}
    }
    
    # Información del sistema
    try:
        python_version = (
            f"{psutil.sys.version_info.major}."
            f"{psutil.sys.version_info.minor}."
            f"{psutil.sys.version_info.micro}"
        )
        detailed_status['system_info'] = {
            'python_version': python_version,
            'django_version': settings.DJANGO_VERSION,
            'platform': psutil.sys.platform,
            'hostname': psutil.gethostname(),
            'uptime_seconds': int(time.time() - psutil.boot_time())
        }
    except Exception as e:
        detailed_status['system_info']['error'] = str(e)
    
    # Métricas de rendimiento
    try:
        detailed_status['performance_metrics'] = {
            'process_memory_mb': (
                psutil.Process().memory_info().rss / (1024**2)
            ),
            'process_cpu_percent': psutil.Process().cpu_percent(),
            'open_files': len(psutil.Process().open_files()),
            'threads': psutil.Process().num_threads()
        }
    except Exception as e:
        detailed_status['performance_metrics']['error'] = str(e)
    
    # Verificar servicios (reutilizar lógica del health check básico)
    basic_health = health_check(request)
    basic_data = basic_health.json()
    detailed_status['services'] = basic_data['services']
    detailed_status['status'] = basic_data['status']
    
    # Agregar información de configuración
    detailed_status['configuration'] = {
        'debug_mode': settings.DEBUG,
        'allowed_hosts': settings.ALLOWED_HOSTS,
        'database_engine': settings.DATABASES['default']['ENGINE'],
        'cache_backend': settings.CACHES['default']['BACKEND'],
        'installed_apps_count': len(settings.INSTALLED_APPS),
        'middleware_count': len(settings.MIDDLEWARE)
    }
    
    status_code = (
        200 if detailed_status['status'] in ['healthy', 'degraded'] 
        else 503
    )
    return JsonResponse(detailed_status, status=status_code)


# URLs del módulo de health
urlpatterns = [
    path('', health_check, name='health-check'),
    path('detailed/', detailed_health_check, name='detailed-health-check'),
]
