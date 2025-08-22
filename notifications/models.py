from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Notification(models.Model):
    """Modelo para notificaciones en tiempo real"""
    
    NOTIFICATION_TYPES = [
        ('ticket_created', 'Ticket Creado'),
        ('ticket_updated', 'Ticket Actualizado'),
        ('ticket_cancelled', 'Ticket Cancelado'),
        ('report_generated', 'Reporte Generado'),
        ('system_alert', 'Alerta del Sistema'),
        ('user_activity', 'Actividad de Usuario'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]
    
    # Campos básicos
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20, choices=NOTIFICATION_TYPES
    )
    priority = models.CharField(
        max_length=10, choices=PRIORITY_LEVELS, default='medium'
    )
    
    # Destinatarios
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notifications'
    )
    sender = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sent_notifications'
    )
    
    # Estado y timestamps
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Datos adicionales
    data = models.JSONField(default=dict, blank=True)
    action_url = models.URLField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type', 'created_at']),
            models.Index(fields=['priority', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"
    
    def mark_as_read(self):
        """Marcar notificación como leída"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def mark_as_sent(self):
        """Marcar notificación como enviada"""
        if not self.is_sent:
            self.is_sent = True
            self.sent_at = timezone.now()
            self.save(update_fields=['is_sent', 'sent_at'])


class NotificationTemplate(models.Model):
    """Plantillas para notificaciones"""
    
    name = models.CharField(max_length=100, unique=True)
    title_template = models.CharField(max_length=200)
    message_template = models.TextField()
    notification_type = models.CharField(
        max_length=20, choices=Notification.NOTIFICATION_TYPES
    )
    priority = models.CharField(
        max_length=10, choices=Notification.PRIORITY_LEVELS, default='medium'
    )
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def render(self, context):
        """Renderizar plantilla con contexto"""
        from django.template import Template, Context
        title = Template(self.title_template).render(Context(context))
        message = Template(self.message_template).render(Context(context))
        return title, message


class NotificationPreference(models.Model):
    """Preferencias de notificación por usuario"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Tipos de notificación habilitados
    ticket_notifications = models.BooleanField(default=True)
    report_notifications = models.BooleanField(default=True)
    system_notifications = models.BooleanField(default=True)
    user_activity_notifications = models.BooleanField(default=False)
    
    # Configuración de envío
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    in_app_notifications = models.BooleanField(default=True)
    
    # Frecuencia
    notification_frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Inmediato'),
            ('hourly', 'Cada hora'),
            ('daily', 'Diario'),
            ('weekly', 'Semanal'),
        ],
        default='immediate'
    )
    
    # Horario de silencio
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"Preferencias de {self.user.username}"
    
    def is_quiet_hours(self):
        """Verificar si estamos en horario de silencio"""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        from django.utils import timezone
        now = timezone.localtime().time()
        
        if self.quiet_hours_start <= self.quiet_hours_end:
            return self.quiet_hours_start <= now <= self.quiet_hours_end
        else:  # Horario que cruza la medianoche
            return now >= self.quiet_hours_start or now <= self.quiet_hours_end
