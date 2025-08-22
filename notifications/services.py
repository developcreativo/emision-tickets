import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Notification, NotificationPreference, NotificationTemplate


class NotificationService:
    """Servicio para gestión de notificaciones en tiempo real"""
    
    @classmethod
    def send_notification(
        cls, recipient_id, title, message, notification_type='system_alert',
        priority='medium', sender=None, data=None, action_url=''
    ):
        """Enviar notificación a un usuario específico"""
        
        try:
            recipient = User.objects.get(id=recipient_id)
            
            # Verificar preferencias del usuario
            preference, created = NotificationPreference.objects.get_or_create(
                user=recipient
            )
            
            # Verificar si el usuario quiere este tipo de notificación
            if not cls._should_send_notification(preference, notification_type):
                return None
            
            # Verificar horario de silencio
            if preference.is_quiet_hours():
                return None
            
            # Crear notificación
            notification = Notification.objects.create(
                recipient=recipient,
                sender=sender,
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority,
                data=data or {},
                action_url=action_url
            )
            
            # Enviar por WebSocket
            cls._send_websocket_notification(notification)
            
            # Marcar como enviada
            notification.mark_as_sent()
            
            return notification
            
        except User.DoesNotExist:
            raise ValueError(f"Usuario con ID {recipient_id} no existe")
        except Exception as e:
            raise Exception(f"Error enviando notificación: {str(e)}")
    
    @classmethod
    def send_bulk_notification(
        cls, user_ids, title, message, notification_type='system_alert',
        priority='medium', sender=None, data=None, action_url=''
    ):
        """Enviar notificación a múltiples usuarios"""
        
        notifications = []
        
        for user_id in user_ids:
            try:
                notification = cls.send_notification(
                    recipient_id=user_id,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    priority=priority,
                    sender=sender,
                    data=data,
                    action_url=action_url
                )
                if notification:
                    notifications.append(notification)
            except Exception as e:
                print(f"Error enviando notificación a usuario {user_id}: {e}")
                continue
        
        return notifications
    
    @classmethod
    def send_notification_from_template(
        cls, template_name, recipient_id, context=None, sender=None
    ):
        """Enviar notificación usando una plantilla"""
        
        try:
            template = NotificationTemplate.objects.get(
                name=template_name, is_active=True
            )
            
            # Renderizar plantilla
            context = context or {}
            title, message = template.render(context)
            
            # Enviar notificación
            return cls.send_notification(
                recipient_id=recipient_id,
                title=title,
                message=message,
                notification_type=template.notification_type,
                priority=template.priority,
                sender=sender,
                data=context
            )
            
        except NotificationTemplate.DoesNotExist:
            raise ValueError(f"Plantilla '{template_name}' no existe o no está activa")
    
    @classmethod
    def send_ticket_notification(
        cls, ticket, notification_type, recipient_id, sender=None
    ):
        """Enviar notificación relacionada con tickets"""
        
        context = {
            'ticket_id': ticket.id,
            'ticket_number': getattr(ticket, 'number', 'N/A'),
            'amount': getattr(ticket, 'amount', 0),
            'zone': getattr(ticket.zone, 'name', 'N/A') if ticket.zone else 'N/A',
            'draw_type': getattr(ticket.draw_type, 'name', 'N/A') if ticket.draw_type else 'N/A',
            'date': timezone.now().strftime('%Y-%m-%d %H:%M'),
        }
        
        return cls.send_notification_from_template(
            template_name=f'ticket_{notification_type}',
            recipient_id=recipient_id,
            context=context,
            sender=sender
        )
    
    @classmethod
    def send_report_notification(
        cls, report_type, recipient_id, data=None, sender=None
    ):
        """Enviar notificación de reporte generado"""
        
        context = {
            'report_type': report_type,
            'generated_at': timezone.now().strftime('%Y-%m-%d %H:%M'),
            'data': data or {}
        }
        
        return cls.send_notification_from_template(
            template_name=f'report_{report_type}',
            recipient_id=recipient_id,
            context=context,
            sender=sender
        )
    
    @classmethod
    def _should_send_notification(cls, preference, notification_type):
        """Verificar si se debe enviar la notificación según preferencias"""
        
        if notification_type == 'ticket_created' or notification_type == 'ticket_updated':
            return preference.ticket_notifications
        elif notification_type == 'report_generated':
            return preference.report_notifications
        elif notification_type == 'system_alert':
            return preference.system_notifications
        elif notification_type == 'user_activity':
            return preference.user_activity_notifications
        
        return True  # Por defecto, enviar
    
    @classmethod
    def _send_websocket_notification(cls, notification):
        """Enviar notificación por WebSocket"""
        
        try:
            channel_layer = get_channel_layer()
            
            # Preparar datos de la notificación
            notification_data = {
                'type': 'notification.message',
                'notification': {
                    'id': notification.id,
                    'title': notification.title,
                    'message': notification.message,
                    'notification_type': notification.notification_type,
                    'priority': notification.priority,
                    'created_at': notification.created_at.isoformat(),
                    'action_url': notification.action_url,
                    'data': notification.data
                }
            }
            
            # Enviar al grupo del usuario
            group_name = f"user_{notification.recipient.id}"
            async_to_sync(channel_layer.group_send)(
                group_name, notification_data
            )
            
        except Exception as e:
            print(f"Error enviando WebSocket notification: {e}")
    
    @classmethod
    def create_default_templates(cls):
        """Crear plantillas por defecto"""
        
        templates_data = [
            {
                'name': 'ticket_created',
                'title_template': 'Nuevo Ticket Creado',
                'message_template': 'Se ha creado un nuevo ticket #{{ ticket_id }} en {{ zone }} por ${{ amount }}',
                'notification_type': 'ticket_created',
                'priority': 'medium'
            },
            {
                'name': 'ticket_updated',
                'title_template': 'Ticket Actualizado',
                'message_template': 'El ticket #{{ ticket_id }} ha sido actualizado',
                'notification_type': 'ticket_updated',
                'priority': 'low'
            },
            {
                'name': 'ticket_cancelled',
                'title_template': 'Ticket Cancelado',
                'message_template': 'El ticket #{{ ticket_id }} ha sido cancelado',
                'notification_type': 'ticket_cancelled',
                'priority': 'high'
            },
            {
                'name': 'report_generated',
                'title_template': 'Reporte Generado',
                'message_template': 'Se ha generado el reporte de {{ report_type }}',
                'notification_type': 'report_generated',
                'priority': 'low'
            },
            {
                'name': 'system_alert',
                'title_template': 'Alerta del Sistema',
                'message_template': '{{ message }}',
                'notification_type': 'system_alert',
                'priority': 'high'
            }
        ]
        
        for template_data in templates_data:
            NotificationTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )
