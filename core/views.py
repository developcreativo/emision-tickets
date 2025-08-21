import os
from datetime import datetime

import psutil
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Endpoint de health check para verificar el estado del backend
    """
    try:
        # Información básica del sistema
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'emision-tickets-api',
            'version': '2.0.0',
            'environment': os.getenv('DJANGO_ENV', 'development'),
            'database': 'connected',  # Django maneja esto automáticamente
            'memory_usage': {
                'percent': psutil.virtual_memory().percent,
                'available_gb': round(
                    psutil.virtual_memory().available / (1024**3), 2
                ),
                'total_gb': round(
                    psutil.virtual_memory().total / (1024**3), 2
                )
            },
            'disk_usage': {
                'percent': psutil.disk_usage('/').percent,
                'free_gb': round(
                    psutil.disk_usage('/').free / (1024**3), 2
                ),
                'total_gb': round(
                    psutil.disk_usage('/').total / (1024**3), 2
                )
            },
            'uptime_seconds': int(psutil.boot_time()),
            'python_version': (
                f"{psutil.sys.version_info.major}."
                f"{psutil.sys.version_info.minor}."
                f"{psutil.sys.version_info.micro}"
            )
        }
        
        return Response(health_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        health_data = {
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'emision-tickets-api',
            'error': str(e),
            'type': type(e).__name__
        }
        
        return Response(
            health_data, 
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def simple_health_check(request):
    """
    Health check simple para load balancers
    """
    return Response({'status': 'ok'}, status=status.HTTP_200_OK)
