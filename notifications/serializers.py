from rest_framework import serializers
from .models import Notification, NotificationTemplate, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer para notificaciones"""
    
    recipient_username = serializers.CharField(
        source='recipient.username', read_only=True
    )
    sender_username = serializers.CharField(
        source='sender.username', read_only=True
    )
    notification_type_display = serializers.CharField(
        source='get_notification_type_display', read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display', read_only=True
    )
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type',
            'notification_type_display', 'priority', 'priority_display',
            'recipient', 'recipient_username', 'sender', 'sender_username',
            'is_read', 'is_sent', 'created_at', 'read_at', 'sent_at',
            'data', 'action_url'
        ]
        read_only_fields = [
            'id', 'created_at', 'read_at', 'sent_at',
            'recipient_username', 'sender_username',
            'notification_type_display', 'priority_display'
        ]


class NotificationListSerializer(serializers.ModelSerializer):
    """Serializer para listar notificaciones (versión resumida)"""
    
    notification_type_display = serializers.CharField(
        source='get_notification_type_display', read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display', read_only=True
    )
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'notification_type', 'notification_type_display',
            'priority', 'priority_display', 'is_read', 'created_at',
            'action_url'
        ]
        read_only_fields = fields


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear notificaciones"""
    
    class Meta:
        model = Notification
        fields = [
            'title', 'message', 'notification_type', 'priority',
            'recipient', 'sender', 'data', 'action_url'
        ]


class NotificationUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar notificaciones"""
    
    class Meta:
        model = Notification
        fields = ['is_read']
        read_only_fields = ['id', 'created_at']


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer para plantillas de notificación"""
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'title_template', 'message_template',
            'notification_type', 'priority', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer para preferencias de notificación"""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'ticket_notifications', 'report_notifications',
            'system_notifications', 'user_activity_notifications',
            'email_notifications', 'push_notifications',
            'in_app_notifications', 'notification_frequency',
            'quiet_hours_start', 'quiet_hours_end'
        ]


class NotificationStatsSerializer(serializers.Serializer):
    """Serializer para estadísticas de notificaciones"""
    
    total_notifications = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
    notifications_by_type = serializers.DictField()
    notifications_by_priority = serializers.DictField()
    recent_notifications = NotificationListSerializer(many=True)
