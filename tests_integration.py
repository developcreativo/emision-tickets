import json

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from catalog.models import DrawSchedule, DrawType, NumberLimit, Zone
from sales.models import Ticket, TicketItem


class SystemIntegrationTests(TestCase):
    """Tests de integración del sistema completo"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Crear usuarios con diferentes roles
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        self.seller_user = User.objects.create_user(
            username='seller',
            password='seller123',
            role='VENDEDOR'
        )
        self.supervisor_user = User.objects.create_user(
            username='supervisor',
            password='supervisor123',
            role='SUPERVISOR'
        )
        
        # Crear datos de catálogo
        self.zone = Zone.objects.create(name='Zona Central')
        self.zone2 = Zone.objects.create(name='Zona Norte')
        self.draw_type = DrawType.objects.create(code='SANTA', name='Sorteo Santa')
        self.draw_type2 = DrawType.objects.create(code='BOLIDO', name='Sorteo Bólido')
        
        # Crear horarios
        self.schedule = DrawSchedule.objects.create(
            zone=self.zone,
            draw_type=self.draw_type,
            cutoff_time=timezone.localtime().time().replace(hour=18, minute=0, second=0),
            is_active=True
        )
        self.schedule2 = DrawSchedule.objects.create(
            zone=self.zone2,
            draw_type=self.draw_type2,
            cutoff_time=timezone.localtime().time().replace(hour=20, minute=0, second=0),
            is_active=True
        )
        
        # Crear límites
        self.limit = NumberLimit.objects.create(
            zone=self.zone,
            draw_type=self.draw_type,
            number='12',
            max_pieces=50
        )
        self.limit2 = NumberLimit.objects.create(
            zone=self.zone2,
            draw_type=self.draw_type2,
            number='34',
            max_pieces=30
        )

    def get_auth_headers(self, user):
        """Obtener headers de autenticación para un usuario"""
        token = RefreshToken.for_user(user).access_token
        return {'HTTP_AUTHORIZATION': f'Bearer {str(token)}'}

    def test_complete_system_workflow_admin(self):
        """Test del flujo completo del sistema para administrador"""
        self.client.credentials(**self.get_auth_headers(self.admin_user))
        
        # 1. Gestionar catálogos
        # Crear nueva zona
        new_zone_data = {'name': 'Zona Sur', 'description': 'Nueva zona sur'}
        response = self.client.post('/api/catalog/zones/', new_zone_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        zone_sur_id = response.data['id']
        
        # Crear nuevo tipo de sorteo
        new_draw_data = {'code': 'CHARADA', 'name': 'Sorteo Charada'}
        response = self.client.post('/api/catalog/draw-types/', new_draw_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        charada_id = response.data['id']
        
        # Crear horario para nueva zona y sorteo
        new_schedule_data = {
            'zone': zone_sur_id,
            'draw_type': charada_id,
            'cutoff_time': '19:00:00',
            'is_active': True
        }
        response = self.client.post('/api/catalog/draw-schedules/', new_schedule_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Crear límite para nuevo número
        new_limit_data = {
            'zone': zone_sur_id,
            'draw_type': charada_id,
            'number': '56',
            'max_pieces': 25
        }
        response = self.client.post('/api/catalog/number-limits/', new_limit_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 2. Crear tickets como vendedor
        self.client.credentials(**self.get_auth_headers(self.seller_user))
        
        # Crear ticket en zona original
        ticket_data = {
            'zone': self.zone.id,
            'draw_type': self.draw_type.id,
            'items': [
                {'number': '12', 'pieces': 10},
                {'number': '23', 'pieces': 5}
            ]
        }
        response = self.client.post('/api/sales/tickets/', ticket_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        ticket_id = response.data['id']
        
        # Crear ticket en nueva zona
        ticket_data2 = {
            'zone': zone_sur_id,
            'draw_type': charada_id,
            'items': [{'number': '56', 'pieces': 15}]
        }
        response = self.client.post('/api/sales/tickets/', ticket_data2, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 3. Generar reportes
        # Reporte por zona
        response = self.client.get('/api/sales/tickets/reports/summary/?group_by=zone')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['totals']['total_tickets'], 2)
        
        # Reporte por tipo de sorteo
        response = self.client.get('/api/sales/tickets/reports/summary/?group_by=draw_type')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['totals']['total_tickets'], 2)
        
        # 4. Exportar reportes
        response = self.client.get('/api/sales/tickets/reports/export/?format=csv&group_by=zone')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response = self.client.get('/api/sales/tickets/reports/export/?format=excel&group_by=zone')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 5. Generar PDF
        response = self.client.get(f'/api/sales/tickets/{ticket_id}/pdf/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response = self.client.get(f'/api/sales/tickets/{ticket_id}/preview/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_complete_system_workflow_seller(self):
        """Test del flujo completo del sistema para vendedor"""
        self.client.credentials(**self.get_auth_headers(self.seller_user))
        
        # 1. Verificar acceso limitado a catálogos (solo lectura)
        response = self.client.get('/api/catalog/zones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Intentar crear zona (debería fallar)
        new_zone_data = {'name': 'Zona Test', 'description': 'Zona de prueba'}
        response = self.client.post('/api/catalog/zones/', new_zone_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # 2. Crear múltiples tickets
        tickets_created = []
        for i in range(5):
            ticket_data = {
                'zone': self.zone.id,
                'draw_type': self.draw_type.id,
                'items': [{'number': f'{i:02d}', 'pieces': i + 1}]
            }
            response = self.client.post('/api/sales/tickets/', ticket_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            tickets_created.append(response.data['id'])
        
        # 3. Verificar tickets creados
        for ticket_id in tickets_created:
            response = self.client.get(f'/api/sales/tickets/{ticket_id}/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 4. Generar reportes personales
        response = self.client.get('/api/sales/tickets/reports/summary/?group_by=zone&users=self.seller_user.id')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['totals']['total_tickets'], 5)

    def test_system_permissions_and_roles(self):
        """Test de permisos y roles del sistema"""
        
        # Test 1: Admin puede acceder a todo
        self.client.credentials(**self.get_auth_headers(self.admin_user))
        
        response = self.client.get('/api/accounts/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response = self.client.get('/api/catalog/zones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response = self.client.get('/api/sales/tickets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test 2: Vendedor acceso limitado
        self.client.credentials(**self.get_auth_headers(self.seller_user))
        
        response = self.client.get('/api/accounts/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        response = self.client.get('/api/catalog/zones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response = self.client.get('/api/sales/tickets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test 3: Supervisor acceso limitado
        self.client.credentials(**self.get_auth_headers(self.supervisor_user))
        
        response = self.client.get('/api/accounts/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        response = self.client.get('/api/catalog/zones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response = self.client.get('/api/sales/tickets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_system_business_rules_integration(self):
        """Test de integración de reglas de negocio"""
        self.client.credentials(**self.get_auth_headers(self.seller_user))
        
        # Test 1: Límites acumulados
        # Crear primer ticket
        ticket_data = {
            'zone': self.zone.id,
            'draw_type': self.draw_type.id,
            'items': [{'number': '12', 'pieces': 40}]
        }
        response = self.client.post('/api/sales/tickets/', ticket_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Intentar crear segundo ticket que exceda el límite
        ticket_data2 = {
            'zone': self.zone.id,
            'draw_type': self.draw_type.id,
            'items': [{'number': '12', 'pieces': 15}]
        }
        response = self.client.post('/api/sales/tickets/', ticket_data2, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test 2: Horarios de cierre
        # Cambiar horario a tiempo pasado
        self.schedule.cutoff_time = timezone.localtime().time().replace(hour=0, minute=0, second=0)
        self.schedule.save()
        
        # Intentar crear ticket fuera de horario
        ticket_data3 = {
            'zone': self.zone.id,
            'draw_type': self.draw_type.id,
            'items': [{'number': '23', 'pieces': 5}]
        }
        response = self.client.post('/api/sales/tickets/', ticket_data3, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_system_data_consistency(self):
        """Test de consistencia de datos del sistema"""
        self.client.credentials(**self.get_auth_headers(self.seller_user))
        
        # Crear ticket con múltiples números
        ticket_data = {
            'zone': self.zone.id,
            'draw_type': self.draw_type.id,
            'items': [
                {'number': '12', 'pieces': 10},
                {'number': '23', 'pieces': 5},
                {'number': '45', 'pieces': 8}
            ]
        }
        response = self.client.post('/api/sales/tickets/', ticket_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        ticket_id = response.data['id']
        
        # Verificar consistencia de datos
        ticket = Ticket.objects.get(id=ticket_id)
        self.assertEqual(ticket.total_pieces, 23)  # 10 + 5 + 8
        self.assertEqual(ticket.items.count(), 3)
        
        # Verificar que los items están correctamente relacionados
        items = ticket.items.all()
        numbers = [item.number for item in items]
        pieces = [item.pieces for item in items]
        
        self.assertIn('12', numbers)
        self.assertIn('23', numbers)
        self.assertIn('45', numbers)
        self.assertIn(10, pieces)
        self.assertIn(5, pieces)
        self.assertIn(8, pieces)

    def test_system_error_handling(self):
        """Test de manejo de errores del sistema"""
        self.client.credentials(**self.get_auth_headers(self.seller_user))
        
        # Test 1: Datos inválidos
        invalid_ticket_data = {
            'zone': 99999,  # Zona inexistente
            'draw_type': self.draw_type.id,
            'items': [{'number': '12', 'pieces': 5}]
        }
        response = self.client.post('/api/sales/tickets/', invalid_ticket_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test 2: Número inválido
        invalid_number_data = {
            'zone': self.zone.id,
            'draw_type': self.draw_type.id,
            'items': [{'number': '123', 'pieces': 5}]  # Número de 3 dígitos
        }
        response = self.client.post('/api/sales/tickets/', invalid_number_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test 3: Piezas negativas
        invalid_pieces_data = {
            'zone': self.zone.id,
            'draw_type': self.draw_type.id,
            'items': [{'number': '12', 'pieces': -1}]
        }
        response = self.client.post('/api/sales/tickets/', invalid_pieces_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test 4: Ticket sin items
        empty_items_data = {
            'zone': self.zone.id,
            'draw_type': self.draw_type.id,
            'items': []
        }
        response = self.client.post('/api/sales/tickets/', empty_items_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_system_performance_scenarios(self):
        """Test de escenarios de rendimiento del sistema"""
        self.client.credentials(**self.get_auth_headers(self.seller_user))
        
        # Test 1: Crear muchos tickets rápidamente
        import time
        start_time = time.time()
        
        tickets_created = 0
        for i in range(50):
            ticket_data = {
                'zone': self.zone.id,
                'draw_type': self.draw_type.id,
                'items': [{'number': f'{i:02d}', 'pieces': 1}]
            }
            response = self.client.post('/api/sales/tickets/', ticket_data, format='json')
            if response.status_code == 201:
                tickets_created += 1
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verificar rendimiento
        self.assertGreater(tickets_created, 40)  # Al menos 40 tickets creados
        self.assertLess(execution_time, 10.0)  # Debería completarse en menos de 10 segundos
        
        # Test 2: Generar reporte con muchos datos
        start_time = time.time()
        response = self.client.get('/api/sales/tickets/reports/summary/?group_by=zone')
        end_time = time.time()
        report_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(report_time, 2.0)  # Reporte en menos de 2 segundos

    def test_system_concurrent_access(self):
        """Test de acceso concurrente al sistema"""
        import queue
        import threading
        
        results = queue.Queue()
        
        def create_ticket(thread_id):
            """Función para crear ticket en un hilo"""
            try:
                client = APIClient()
                token = RefreshToken.for_user(self.seller_user).access_token
                client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token)}')
                
                ticket_data = {
                    'zone': self.zone.id,
                    'draw_type': self.draw_type.id,
                    'items': [{'number': f'{thread_id:02d}', 'pieces': 1}]
                }
                response = client.post('/api/sales/tickets/', ticket_data, format='json')
                results.put((thread_id, response.status_code))
            except Exception as e:
                results.put((thread_id, f"Error: {e}"))
        
        # Crear múltiples hilos para acceder al sistema simultáneamente
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_ticket, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Esperar a que todos los hilos terminen
        for thread in threads:
            thread.join()
        
        # Verificar resultados
        successful_creations = 0
        failed_creations = 0
        
        while not results.empty():
            thread_id, result = results.get()
            if result == 201:
                successful_creations += 1
            else:
                failed_creations += 1
        
        # Debería haber algunos éxitos y algunos fallos (por límites)
        self.assertGreater(successful_creations, 0)
        self.assertGreater(failed_creations, 0)
        self.assertEqual(successful_creations + failed_creations, 10)

    def test_system_data_integrity(self):
        """Test de integridad de datos del sistema"""
        self.client.credentials(**self.get_auth_headers(self.seller_user))
        
        # Crear ticket
        ticket_data = {
            'zone': self.zone.id,
            'draw_type': self.draw_type.id,
            'items': [{'number': '12', 'pieces': 10}]
        }
        response = self.client.post('/api/sales/tickets/', ticket_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        ticket_id = response.data['id']
        
        # Verificar que no se pueden modificar datos críticos
        ticket = Ticket.objects.get(id=ticket_id)
        original_total = ticket.total_pieces
        
        # Intentar modificar total_pieces directamente
        ticket.total_pieces = 999
        ticket.save()
        
        # Verificar que el cambio se mantiene en la base de datos
        ticket.refresh_from_db()
        self.assertEqual(ticket.total_pieces, 999)
        
        # Restaurar valor original
        ticket.total_pieces = original_total
        ticket.save()
        
        # Verificar que los items están protegidos
        items = ticket.items.all()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].number, '12')
        self.assertEqual(items[0].pieces, 10)

    def test_system_audit_trail(self):
        """Test de auditoría del sistema"""
        self.client.credentials(**self.get_auth_headers(self.seller_user))
        
        # Crear ticket
        ticket_data = {
            'zone': self.zone.id,
            'draw_type': self.draw_type.id,
            'items': [{'number': '12', 'pieces': 5}]
        }
        response = self.client.post('/api/sales/tickets/', ticket_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        ticket_id = response.data['id']
        
        # Verificar timestamps
        ticket = Ticket.objects.get(id=ticket_id)
        self.assertIsNotNone(ticket.created_at)
        self.assertIsNotNone(ticket.updated_at)
        
        # Verificar que created_at y updated_at son iguales al crear
        self.assertEqual(ticket.created_at, ticket.updated_at)
        
        # Modificar ticket
        old_updated = ticket.updated_at
        ticket.total_pieces = 10
        ticket.save()
        
        # Verificar que updated_at cambió
        ticket.refresh_from_db()
        self.assertGreater(ticket.updated_at, old_updated)
        
        # Verificar que created_at no cambió
        self.assertEqual(ticket.created_at, ticket.created_at)

    def test_system_end_to_end_workflow(self):
        """Test de flujo completo de extremo a extremo"""
        
        # 1. Login como admin
        self.client.credentials(**self.get_auth_headers(self.admin_user))
        
        # 2. Configurar sistema
        # Crear zona
        zone_data = {'name': 'Zona Test E2E', 'description': 'Zona para test E2E'}
        response = self.client.post('/api/catalog/zones/', zone_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        zone_id = response.data['id']
        
        # Crear tipo de sorteo
        draw_data = {'code': 'E2E', 'name': 'Sorteo E2E'}
        response = self.client.post('/api/catalog/draw-types/', draw_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        draw_id = response.data['id']
        
        # Crear horario
        schedule_data = {
            'zone': zone_id,
            'draw_type': draw_id,
            'cutoff_time': '23:59:00',
            'is_active': True
        }
        response = self.client.post('/api/catalog/draw-schedules/', schedule_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Crear límite
        limit_data = {
            'zone': zone_id,
            'draw_type': draw_id,
            'number': '99',
            'max_pieces': 100
        }
        response = self.client.post('/api/catalog/number-limits/', limit_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 3. Cambiar a vendedor
        self.client.credentials(**self.get_auth_headers(self.seller_user))
        
        # 4. Crear tickets
        for i in range(3):
            ticket_data = {
                'zone': zone_id,
                'draw_type': draw_id,
                'items': [{'number': f'{i:02d}', 'pieces': i + 1}]
            }
            response = self.client.post('/api/sales/tickets/', ticket_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 5. Generar reportes
        response = self.client.get('/api/sales/tickets/reports/summary/?group_by=zone')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['totals']['total_tickets'], 3)
        
        # 6. Exportar reporte
        response = self.client.get('/api/sales/tickets/reports/export/?format=csv&group_by=zone')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 7. Verificar datos finales
        tickets = Ticket.objects.filter(zone_id=zone_id, draw_type_id=draw_id)
        self.assertEqual(tickets.count(), 3)
        
        total_pieces = sum(ticket.total_pieces for ticket in tickets)
        self.assertEqual(total_pieces, 6)  # 1 + 2 + 3
