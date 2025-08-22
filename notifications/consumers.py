import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    """Consumidor WebSocket para notificaciones en tiempo real"""
    
    async def connect(self):
        """Conectar al WebSocket"""
        
        # Obtener token de autenticación
        token = self.scope['url_route']['kwargs'].get('token')
        
        if token:
            # Autenticar usuario por token
            self.user = await self.get_user_from_token(token)
        else:
            # Intentar autenticación por sesión
            self.user = self.scope['user']
        
        if self.user == AnonymousUser():
            await self.close()
            return
        
        # Unirse al grupo del usuario
        self.group_name = f"user_{self.user.id}"
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Enviar mensaje de conexión exitosa
        await self.send(text_data=json.dumps({
            'type': 'connection.established',
            'message': 'Conectado a notificaciones en tiempo real',
            'user_id': self.user.id
        }))
    
    async def disconnect(self, close_code):
        """Desconectar del WebSocket"""
        
        # Salir del grupo
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Recibir mensaje del cliente"""
        
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                # Responder ping
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            
            elif message_type == 'mark_read':
                # Marcar notificación como leída
                notification_id = data.get('notification_id')
                if notification_id:
                    await self.mark_notification_read(notification_id)
            
            elif message_type == 'get_unread_count':
                # Obtener conteo de no leídas
                count = await self.get_unread_count()
                await self.send(text_data=json.dumps({
                    'type': 'unread_count',
                    'count': count
                }))
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Formato JSON inválido'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def notification_message(self, event):
        """Enviar notificación al cliente"""
        
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))
    
    async def system_message(self, event):
        """Enviar mensaje del sistema"""
        
        await self.send(text_data=json.dumps({
            'type': 'system',
            'message': event['message'],
            'level': event.get('level', 'info')
        }))
    
    @database_sync_to_async
    def get_user_from_token(self, token):
        """Obtener usuario desde token JWT"""
        
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            return User.objects.get(id=user_id)
        except Exception:
            return AnonymousUser()
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Marcar notificación como leída"""
        
        from .models import Notification
        
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=self.user
            )
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_unread_count(self):
        """Obtener conteo de notificaciones no leídas"""
        
        from .models import Notification
        
        return Notification.objects.filter(
            recipient=self.user,
            is_read=False
        ).count()


class BroadcastConsumer(AsyncWebsocketConsumer):
    """Consumidor para mensajes broadcast (admin)"""
    
    async def connect(self):
        """Conectar al WebSocket de broadcast"""
        
        # Solo usuarios admin pueden usar broadcast
        self.user = self.scope['user']
        
        if not self.user.is_authenticated or not self.user.is_staff:
            await self.close()
            return
        
        # Unirse al grupo de broadcast
        self.group_name = "broadcast"
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        await self.send(text_data=json.dumps({
            'type': 'connection.established',
            'message': 'Conectado a broadcast de notificaciones'
        }))
    
    async def disconnect(self, close_code):
        """Desconectar del WebSocket"""
        
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Recibir mensaje del cliente"""
        
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'broadcast':
                # Enviar mensaje broadcast
                await self.channel_layer.group_send(
                    "broadcast",
                    {
                        'type': 'broadcast.message',
                        'message': data.get('message'),
                        'level': data.get('level', 'info'),
                        'sender': self.user.username
                    }
                )
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Formato JSON inválido'
            }))
    
    async def broadcast_message(self, event):
        """Enviar mensaje broadcast"""
        
        await self.send(text_data=json.dumps({
            'type': 'broadcast',
            'message': event['message'],
            'level': event['level'],
            'sender': event['sender']
        }))
