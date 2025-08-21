import logging
from typing import Any, Dict, Optional
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone


# Configuración del logger de auditoría
audit_logger = logging.getLogger('audit')


class AuditLog(models.Model):
    """
    Modelo para registrar logs de auditoría del sistema
    """
    ACTION_CHOICES = [
        ('CREATE', 'Crear'),
        ('UPDATE', 'Actualizar'),
        ('DELETE', 'Eliminar'),
        ('LOGIN', 'Iniciar sesión'),
        ('LOGOUT', 'Cerrar sesión'),
        ('VIEW', 'Ver'),
        ('EXPORT', 'Exportar'),
        ('REPORT', 'Generar reporte'),
        ('SYSTEM', 'Sistema'),
    ]
    
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        'accounts.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=100, blank=True)
    resource_id = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'action']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
    
    def __str__(self):
        return f"{self.action} - {self.description} - {self.timestamp}"
    
    @classmethod
    def log_action(
        cls,
        user: Optional[AbstractUser],
        action: str,
        description: str,
        resource_type: str = "",
        resource_id: str = "",
        ip_address: Optional[str] = None,
        user_agent: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'AuditLog':
        """
        Método de clase para registrar una acción de auditoría
        """
        log_entry = cls.objects.create(
            user=user,
            action=action,
            description=description,
            resource_type=resource_type,
            resource_id=str(resource_id),
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )
        
        # También loggear al logger de auditoría
        audit_logger.info(
            f"AUDIT: {action} - {description} - User: {user} - "
            f"Resource: {resource_type}:{resource_id}",
            extra={
                'audit_log_id': log_entry.id,
                'user_id': user.id if user else None,
                'action': action,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'ip_address': ip_address,
                'metadata': metadata
            }
        )
        
        return log_entry


class AuditMixin:
    """
    Mixin para agregar funcionalidad de auditoría a los modelos
    """
    
    def log_creation(self, user: AbstractUser, **kwargs):
        """Registra la creación del objeto"""
        content_type = ContentType.objects.get_for_model(self)
        AuditLog.log_action(
            user=user,
            action='CREATE',
            description=f"Creó {self._meta.verbose_name}",
            resource_type=content_type.model,
            resource_id=str(self.pk),
            metadata=kwargs
        )
    
    def log_update(self, user: AbstractUser, **kwargs):
        """Registra la actualización del objeto"""
        content_type = ContentType.objects.get_for_model(self)
        AuditLog.log_action(
            user=user,
            action='UPDATE',
            description=f"Actualizó {self._meta.verbose_name}",
            resource_type=content_type.model,
            resource_id=str(self.pk),
            metadata=kwargs
        )
    
    def log_deletion(self, user: AbstractUser, **kwargs):
        """Registra la eliminación del objeto"""
        content_type = ContentType.objects.get_for_model(self)
        AuditLog.log_action(
            user=user,
            action='DELETE',
            description=f"Eliminó {self._meta.verbose_name}",
            resource_type=content_type.model,
            resource_id=str(self.pk),
            metadata=kwargs
        )


def audit_function_call(
    action: str,
    description: str,
    user: Optional[AbstractUser] = None,
    **kwargs
):
    """
    Decorador para auditar llamadas a funciones
    """
    def decorator(func):
        def wrapper(*args, **func_kwargs):
            # Ejecutar función
            result = func(*args, **func_kwargs)
            
            # Registrar en auditoría
            AuditLog.log_action(
                user=user,
                action=action,
                description=description,
                metadata={
                    'function': func.__name__,
                    'args': str(args),
                    'kwargs': str(func_kwargs),
                    **kwargs
                }
            )
            
            return result
        return wrapper
    return decorator


class AuditMiddleware:
    """
    Middleware para capturar información de auditoría automáticamente
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Capturar información antes de procesar
        request.audit_start_time = timezone.now()
        
        response = self.get_response(request)
        
        # Registrar información después de procesar
        if hasattr(request, 'user') and request.user.is_authenticated:
            self._log_request(request, response)
        
        return response
    
    def _log_request(self, request, response):
        """Registra información de la petición HTTP"""
        duration = timezone.now() - request.audit_start_time
        
        # Solo registrar acciones importantes
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            action = 'UPDATE' if request.method in ['PUT', 'PATCH'] else request.method
            description = (
                f"Petición {request.method} a {request.path}"
            )
            
            AuditLog.log_action(
                user=request.user,
                action=action,
                description=description,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata={
                    'method': request.method,
                    'path': request.path,
                    'duration_ms': (
                        duration.total_seconds() * 1000
                    ),
                    'status_code': response.status_code,
                }
            )
    
    def _get_client_ip(self, request):
        """Obtiene la IP real del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
