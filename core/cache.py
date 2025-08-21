import hashlib
import json
from functools import wraps
from typing import Any, Callable, Optional

from django.conf import settings
from django.core.cache import cache


def cache_report(timeout: Optional[int] = None, key_prefix: str = "report"):
    """
    Decorador para cachear reportes con timeout personalizable
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave única basada en función y argumentos
            kwargs_str = json.dumps(kwargs, sort_keys=True)
            kwargs_hash = hashlib.md5(kwargs_str.encode()).hexdigest()
            cache_key = f"{key_prefix}:{func.__name__}:{kwargs_hash}"
            
            # Intentar obtener del cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Si no está en cache, ejecutar función y guardar resultado
            result = func(*args, **kwargs)
            cache_timeout = timeout or getattr(
                settings, 'REPORTS_CACHE_TIMEOUT', 600
            )
            cache.set(cache_key, result, cache_timeout)
            
            return result
        return wrapper
    return decorator


def cache_daily_report(func: Callable) -> Callable:
    """
    Decorador para cachear reportes diarios (1 hora)
    """
    return cache_report(
        timeout=getattr(settings, 'DAILY_REPORTS_CACHE_TIMEOUT', 3600),
        key_prefix="daily_report"
    )(func)


def invalidate_cache_pattern(pattern: str) -> None:
    """
    Invalida todas las claves de cache que coincidan con un patrón
    """
    # Nota: En Redis real, usaríamos SCAN para esto
    # Por simplicidad, aquí solo invalidamos la clave específica
    cache.delete(pattern)


def get_cache_stats() -> dict:
    """
    Obtiene estadísticas del cache
    """
    # En Redis real, podríamos usar INFO command
    default_timeout = getattr(settings, 'REPORTS_CACHE_TIMEOUT', 600)
    daily_timeout = getattr(settings, 'DAILY_REPORTS_CACHE_TIMEOUT', 3600)
    
    return {
        "backend": "redis",
        "host": getattr(settings, 'REDIS_HOST', 'redis'),
        "port": getattr(settings, 'REDIS_PORT', '6379'),
        "timeout_default": default_timeout,
        "timeout_daily": daily_timeout,
    }


class ReportCache:
    """
    Clase utilitaria para manejo de cache de reportes
    """
    
    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Obtiene valor del cache"""
        return cache.get(key, default)
    
    @staticmethod
    def set(key: str, value: Any, timeout: Optional[int] = None) -> None:
        """Establece valor en cache"""
        cache_timeout = timeout or getattr(
            settings, 'REPORTS_CACHE_TIMEOUT', 600
        )
        cache.set(key, value, cache_timeout)
    
    @staticmethod
    def delete(key: str) -> None:
        """Elimina clave del cache"""
        cache.delete(key)
    
    @staticmethod
    def clear_pattern(pattern: str) -> None:
        """Limpia cache por patrón"""
        invalidate_cache_pattern(pattern)
