import time
import logging
from typing import Optional
from django.core.cache import cache
from django.db import connection
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from prometheus_client import (
    Counter, Histogram, Gauge, 
    generate_latest, CONTENT_TYPE_LATEST
)


# Configuración del logger de monitoreo
monitoring_logger = logging.getLogger('monitoring')


class MetricsCollector:
    """
    Recolector de métricas para Prometheus
    """
    
    def __init__(self):
        # Métricas de HTTP
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total de peticiones HTTP',
            ['method', 'endpoint', 'status']
        )
        
        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'Duración de peticiones HTTP',
            ['method', 'endpoint']
        )
        
        # Métricas de base de datos
        self.db_query_duration_seconds = Histogram(
            'db_query_duration_seconds',
            'Duración de consultas a base de datos',
            ['operation', 'table']
        )
        
        self.db_connections_active = Gauge(
            'db_connections_active',
            'Conexiones activas a base de datos'
        )
        
        # Métricas de cache
        self.cache_hits_total = Counter(
            'cache_hits_total',
            'Total de hits en cache',
            ['cache_name']
        )
        
        self.cache_misses_total = Counter(
            'cache_misses_total',
            'Total de misses en cache',
            ['cache_name']
        )
        
        self.cache_size_bytes = Gauge(
            'cache_size_bytes',
            'Tamaño del cache en bytes',
            ['cache_name']
        )
        
        # Métricas de negocio
        self.tickets_created_total = Counter(
            'tickets_created_total',
            'Total de tickets creados',
            ['status', 'category']
        )
        
        self.tickets_processed_total = Counter(
            'tickets_processed_total',
            'Total de tickets procesados',
            ['status', 'category']
        )
        
        self.reports_generated_total = Counter(
            'reports_generated_total',
            'Total de reportes generados',
            ['type', 'format']
        )
        
        # Métricas de usuarios
        self.active_users = Gauge(
            'active_users',
            'Usuarios activos en el sistema'
        )
        
        self.user_sessions_total = Counter(
            'user_sessions_total',
            'Total de sesiones de usuario',
            ['user_type']
        )
        
        # Métricas de sistema
        self.system_memory_usage_bytes = Gauge(
            'system_memory_usage_bytes',
            'Uso de memoria del sistema'
        )
        
        self.system_cpu_usage_percent = Gauge(
            'system_cpu_usage_percent',
            'Uso de CPU del sistema'
        )
    
    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration: float
    ):
        """Registra métricas de petición HTTP"""
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
        
        self.http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_db_query(
        self,
        operation: str,
        table: str,
        duration: float
    ):
        """Registra métricas de consulta a base de datos"""
        self.db_query_duration_seconds.labels(
            operation=operation,
            table=table
        ).observe(duration)
    
    def record_cache_operation(
        self,
        cache_name: str,
        hit: bool,
        size_bytes: Optional[int] = None
    ):
        """Registra métricas de operaciones de cache"""
        if hit:
            self.cache_hits_total.labels(cache_name=cache_name).inc()
        else:
            self.cache_misses_total.labels(cache_name=cache_name).inc()
        
        if size_bytes is not None:
            self.cache_size_bytes.labels(cache_name=cache_name).set(size_bytes)
    
    def record_ticket_operation(
        self,
        operation: str,
        status: str,
        category: str
    ):
        """Registra métricas de operaciones de tickets"""
        if operation == 'create':
            self.tickets_created_total.labels(
                status=status,
                category=category
            ).inc()
        elif operation == 'process':
            self.tickets_processed_total.labels(
                status=status,
                category=category
            ).inc()
    
    def record_report_generation(
        self,
        report_type: str,
        format: str
    ):
        """Registra métricas de generación de reportes"""
        self.reports_generated_total.labels(
            type=report_type,
            format=format
        ).inc()
    
    def update_system_metrics(self):
        """Actualiza métricas del sistema"""
        try:
            # Métricas de base de datos
            with connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM pg_stat_activity")
                active_connections = cursor.fetchone()[0]
                self.db_connections_active.set(active_connections)
            
            # Métricas de cache (simplificado)
            cache_stats = cache.get('cache_stats', {})
            if cache_stats:
                self.cache_size_bytes.labels(
                    cache_name='default'
                ).set(cache_stats.get('size_bytes', 0))
            
            # Métricas de usuarios activos
            from accounts.models import User
            active_users_count = User.objects.filter(
                last_login__gte=timezone.now() - timezone.timedelta(hours=1)
            ).count()
            self.active_users.set(active_users_count)
            
        except Exception as e:
            monitoring_logger.error(f"Error actualizando métricas: {e}")


# Instancia global del recolector de métricas
metrics_collector = MetricsCollector()


class MonitoringMiddleware:
    """
    Middleware para capturar métricas automáticamente
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        # Procesar petición
        response = self.get_response(request)
        
        # Calcular duración
        duration = time.time() - start_time
        
        # Registrar métricas HTTP
        endpoint = self._get_endpoint(request.path)
        metrics_collector.record_http_request(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code,
            duration=duration
        )
        
        return response
    
    def _get_endpoint(self, path: str) -> str:
        """Normaliza el endpoint para métricas"""
        # Remover parámetros y normalizar
        if '?' in path:
            path = path.split('?')[0]
        
        # Agrupar endpoints similares
        if path.startswith('/api/tickets/'):
            return '/api/tickets/{id}'
        elif path.startswith('/api/reports/'):
            return '/api/reports/{type}'
        elif path.startswith('/api/users/'):
            return '/api/users/{id}'
        
        return path


class DatabaseMonitoringMiddleware:
    """
    Middleware para monitorear consultas a base de datos
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Contar consultas antes
        initial_queries = len(connection.queries)
        start_time = time.time()
        
        response = self.get_response(request)
        
        # Contar consultas después
        final_queries = len(connection.queries)
        duration = time.time() - start_time
        
        # Registrar métricas de base de datos
        if final_queries > initial_queries:
            metrics_collector.record_db_query(
                operation='select',
                table='multiple',
                duration=duration
            )
        
        return response


def metrics_view(request: HttpRequest) -> HttpResponse:
    """
    Vista para exponer métricas de Prometheus
    """
    # Actualizar métricas del sistema
    metrics_collector.update_system_metrics()
    
    # Generar respuesta de Prometheus
    response = HttpResponse(
        generate_latest(),
        content_type=CONTENT_TYPE_LATEST
    )
    
    # Agregar headers de cache
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response


class BusinessMetricsCollector:
    """
    Recolector de métricas específicas del negocio
    """
    
    @staticmethod
    def record_ticket_creation(ticket):
        """Registra la creación de un ticket"""
        category = (
            ticket.category.name if ticket.category else 'sin_categoria'
        )
        metrics_collector.record_ticket_operation(
            operation='create',
            status=ticket.status,
            category=category
        )
    
    @staticmethod
    def record_ticket_processing(ticket, old_status, new_status):
        """Registra el procesamiento de un ticket"""
        category = (
            ticket.category.name if ticket.category else 'sin_categoria'
        )
        metrics_collector.record_ticket_operation(
            operation='process',
            status=new_status,
            category=category
        )
    
    @staticmethod
    def record_report_generation(report_type, format_type):
        """Registra la generación de un reporte"""
        metrics_collector.record_report_generation(
            report_type=report_type,
            format=format_type
        )
    
    @staticmethod
    def record_user_session(user, session_type):
        """Registra una sesión de usuario"""
        user_type = (
            user.user_type if hasattr(user, 'user_type') else 'regular'
        )
        metrics_collector.user_sessions_total.labels(
            user_type=user_type
        ).inc()


# Decorador para monitorear funciones
def monitor_function(operation_name: str, **labels):
    """
    Decorador para monitorear funciones específicas
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # Registrar métrica de éxito
                duration = time.time() - start_time
                metrics_collector.db_query_duration_seconds.labels(
                    operation=operation_name,
                    table='function'
                ).observe(duration)
                
                return result
                
            except Exception as e:
                # Registrar métrica de error
                monitoring_logger.error(
                    f"Error en {operation_name}: {e}",
                    extra={'operation': operation_name, 'error': str(e)}
                )
                raise
        
        return wrapper
    return decorator
