from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from .models import Notification, NotificationTemplate, NotificationPreference
from .serializers import (
    NotificationSerializer, NotificationListSerializer,
    NotificationCreateSerializer, NotificationUpdateSerializer,
    NotificationTemplateSerializer, NotificationPreferenceSerializer,
    NotificationStatsSerializer
)
from .services import NotificationService


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de notificaciones"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar notificaciones del usuario actual"""
        return Notification.objects.filter(recipient=self.request.user)
    
    def get_serializer_class(self):
        """Seleccionar serializer según la acción"""
        if self.action == 'list':
            return NotificationListSerializer
        elif self.action == 'create':
            return NotificationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return NotificationUpdateSerializer
        return NotificationSerializer
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Marcar notificación como leída"""
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'status': 'marked as read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Marcar todas las notificaciones como leídas"""
        self.get_queryset().filter(is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
        return Response({'status': 'all marked as read'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Obtener conteo de notificaciones no leídas"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Obtener estadísticas de notificaciones"""
        queryset = self.get_queryset()
        
        # Estadísticas básicas
        total_notifications = queryset.count()
        unread_notifications = queryset.filter(is_read=False).count()
        
        # Por tipo
        notifications_by_type = (
            queryset.values('notification_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Por prioridad
        notifications_by_priority = (
            queryset.values('priority')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Notificaciones recientes
        recent_notifications = (
            queryset.order_by('-created_at')[:10]
        )
        
        data = {
            'total_notifications': total_notifications,
            'unread_notifications': unread_notifications,
            'notifications_by_type': {
                item['notification_type']: item['count']
                for item in notifications_by_type
            },
            'notifications_by_priority': {
                item['priority']: item['count']
                for item in notifications_by_priority
            },
            'recent_notifications': NotificationListSerializer(
                recent_notifications, many=True
            ).data
        }
        
        serializer = NotificationStatsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Obtener notificaciones recientes"""
        days = int(request.query_params.get('days', 7))
        since = timezone.now() - timedelta(days=days)
        
        notifications = (
            self.get_queryset()
            .filter(created_at__gte=since)
            .order_by('-created_at')
        )
        
        serializer = NotificationListSerializer(notifications, many=True)
        return Response(serializer.data)


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de plantillas de notificación"""
    
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAdminUser]
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Probar plantilla con datos de ejemplo"""
        template = self.get_object()
        
        # Datos de ejemplo para la plantilla
        context = {
            'user': request.user,
            'ticket_id': 123,
            'amount': 1000,
            'date': timezone.now().strftime('%Y-%m-%d'),
        }
        
        try:
            title, message = template.render(context)
            return Response({
                'title': title,
                'message': message,
                'context': context
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de preferencias de notificación"""
    
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Obtener o crear preferencias del usuario"""
        preference, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return preference
    
    def get_queryset(self):
        """Solo las preferencias del usuario actual"""
        return NotificationPreference.objects.filter(user=self.request.user)


class NotificationServiceViewSet(viewsets.ViewSet):
    """ViewSet para servicios de notificación"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def send_notification(self, request):
        """Enviar notificación manualmente"""
        try:
            notification = NotificationService.send_notification(
                recipient_id=request.data.get('recipient_id'),
                title=request.data.get('title'),
                message=request.data.get('message'),
                notification_type=request.data.get('notification_type'),
                priority=request.data.get('priority', 'medium'),
                sender=request.user,
                data=request.data.get('data', {}),
                action_url=request.data.get('action_url', '')
            )
            
            serializer = NotificationSerializer(notification)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def send_bulk_notification(self, request):
        """Enviar notificación a múltiples usuarios"""
        try:
            user_ids = request.data.get('user_ids', [])
            notifications = NotificationService.send_bulk_notification(
                user_ids=user_ids,
                title=request.data.get('title'),
                message=request.data.get('message'),
                notification_type=request.data.get('notification_type'),
                priority=request.data.get('priority', 'medium'),
                sender=request.user,
                data=request.data.get('data', {}),
                action_url=request.data.get('action_url', '')
            )
            
            serializer = NotificationSerializer(notifications, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
