import time
from typing import Dict, Optional, Tuple

from django.core.cache import cache
from django.http import HttpRequest, JsonResponse
from rest_framework import status


class RateLimiter:
    """
    Sistema de rate limiting personalizado usando Redis
    """
    
    def __init__(
        self,
        key_prefix: str = "rate_limit",
        max_requests: int = 100,
        window_seconds: int = 3600
    ):
        self.key_prefix = key_prefix
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    def _get_cache_key(self, identifier: str) -> str:
        """Genera la clave de cache para el identificador"""
        current_window = int(time.time() // self.window_seconds)
        return f"{self.key_prefix}:{identifier}:{current_window}"
    
    def is_allowed(self, identifier: str) -> Tuple[bool, Dict]:
        """
        Verifica si la petición está permitida
        
        Returns:
            Tuple[bool, Dict]: (permitido, información del rate limit)
        """
        cache_key = self._get_cache_key(identifier)
        
        # Obtener conteo actual
        current_count = cache.get(cache_key, 0)
        
        if current_count >= self.max_requests:
            # Calcular tiempo restante
            current_time = time.time()
            window_start = (
                current_time // self.window_seconds
            ) * self.window_seconds
            reset_time = window_start + self.window_seconds
            time_remaining = int(reset_time - current_time)
            
            return False, {
                'limit_exceeded': True,
                'current_count': current_count,
                'max_requests': self.max_requests,
                'window_seconds': self.window_seconds,
                'reset_time': reset_time,
                'time_remaining': time_remaining
            }
        
        # Incrementar contador
        cache.set(cache_key, current_count + 1, self.window_seconds)
        
        return True, {
            'limit_exceeded': False,
            'current_count': current_count + 1,
            'max_requests': self.max_requests,
            'window_seconds': self.window_seconds,
            'remaining_requests': (
                self.max_requests - (current_count + 1)
            )
        }
    
    def get_headers(self, identifier: str) -> Dict[str, str]:
        """Genera headers de rate limiting para la respuesta"""
        cache_key = self._get_cache_key(identifier)
        current_count = cache.get(cache_key, 0)
        
        current_time = time.time()
        window_start = (
            current_time // self.window_seconds
        ) * self.window_seconds
        reset_time = window_start + self.window_seconds
        
        headers = {
            'X-RateLimit-Limit': str(self.max_requests),
            'X-RateLimit-Remaining': str(
                max(0, self.max_requests - current_count)
            ),
            'X-RateLimit-Reset': str(reset_time)
        }
        
        return headers


class RateLimitMiddleware:
    """
    Middleware para aplicar rate limiting automáticamente
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limiters = {
            'default': RateLimiter(max_requests=100, window_seconds=3600),
            'auth': RateLimiter(max_requests=5, window_seconds=300),
            'reports': RateLimiter(max_requests=20, window_seconds=3600),
            'api': RateLimiter(max_requests=1000, window_seconds=3600),
        }
    
    def __call__(self, request):
        # Aplicar rate limiting basado en el tipo de endpoint
        limiter_key = self._get_limiter_key(request)
        identifier = self._get_identifier(request)
        
        if limiter_key and identifier:
            limiter = self.rate_limiters[limiter_key]
            is_allowed, info = limiter.is_allowed(identifier)
            
            if not is_allowed:
                response = JsonResponse(
                    {
                        'error': 'Rate limit exceeded',
                        'message': 'Has excedido el límite de peticiones',
                        'details': info
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
                
                # Agregar headers de rate limiting
                for key, value in limiter.get_headers(identifier).items():
                    response[key] = value
                
                return response
        
        response = self.get_response(request)
        
        # Agregar headers de rate limiting a todas las respuestas
        if limiter_key and identifier:
            limiter = self.rate_limiters[limiter_key]
            for key, value in limiter.get_headers(identifier).items():
                response[key] = value
        
        return response
    
    def _get_limiter_key(self, request: HttpRequest) -> Optional[str]:
        """Determina qué rate limiter usar basado en la petición"""
        path = request.path
        
        if '/auth/' in path or '/login/' in path:
            return 'auth'
        elif '/reports/' in path or '/export/' in path:
            return 'reports'
        elif '/api/' in path:
            return 'api'
        else:
            return 'default'
    
    def _get_identifier(self, request: HttpRequest) -> Optional[str]:
        """Obtiene el identificador único para rate limiting"""
        # Prioridad: IP, User ID, o User Agent
        if hasattr(request, 'user') and request.user.is_authenticated:
            return f"user_{request.user.id}"
        else:
            # Usar IP del cliente
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            return f"ip_{ip}"


def rate_limit(
    max_requests: int = 100,
    window_seconds: int = 3600,
    key_prefix: str = "custom"
):
    """
    Decorador para aplicar rate limiting personalizado a vistas específicas
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # Crear rate limiter personalizado
            limiter = RateLimiter(
                key_prefix=key_prefix,
                max_requests=max_requests,
                window_seconds=window_seconds
            )
            
            # Obtener identificador
            if hasattr(request, 'user') and request.user.is_authenticated:
                identifier = f"user_{request.user.id}"
            else:
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = request.META.get('REMOTE_ADDR')
                identifier = f"ip_{ip}"
            
            # Verificar rate limit
            is_allowed, info = limiter.is_allowed(identifier)
            
            if not is_allowed:
                return JsonResponse(
                    {
                        'error': 'Rate limit exceeded',
                        'message': 'Has excedido el límite de peticiones',
                        'details': info
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            # Ejecutar vista
            response = view_func(request, *args, **kwargs)
            
            # Agregar headers de rate limiting
            for key, value in limiter.get_headers(identifier).items():
                response[key] = value
            
            return response
        
        return wrapper
    return decorator
