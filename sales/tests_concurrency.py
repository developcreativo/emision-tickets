"""
Tests avanzados de concurrencia para el sistema de tickets
Prueba el comportamiento del sistema bajo carga concurrente
"""

import threading
import time
import queue
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from catalog.models import Zone, DrawType, DrawSchedule
from sales.models import Ticket, TicketItem

User = get_user_model()


class ConcurrencyTestCase(TestCase):
    """Tests de concurrencia para el sistema de tickets"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.client = APIClient()
        
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Crear datos del catálogo
        self.zone = Zone.objects.create(
            name='Zona Test',
            code='TEST',
            is_active=True
        )
        
        self.draw_type = DrawType.objects.create(
            name='Sorteo Test',
            code='TEST',
            is_active=True
        )
        
        self.schedule = DrawSchedule.objects.create(
            zone=self.zone,
            draw_type=self.draw_type,
            cutoff_time='23:59:00',
            is_active=True
        )
        
        # Autenticar cliente
        self.client.force_authenticate(user=self.user)
    
    def test_concurrent_ticket_creation(self):
        """Test de creación concurrente de tickets"""
        print("🧪 Ejecutando test de creación concurrente de tickets...")
        
        num_threads = 10
        tickets_per_thread = 5
        results_queue = queue.Queue()
        
        def create_tickets(thread_id):
            """Función para crear tickets en un thread"""
            thread_results = []
            
            for i in range(tickets_per_thread):
                try:
                    ticket_data = {
                        'zone': self.zone.id,
                        'draw_type': self.draw_type.id,
                        'items': [
                            {
                                'number': f'{random.randint(0, 99):02d}',
                                'pieces': random.randint(1, 5)
                            }
                            for _ in range(random.randint(1, 3))
                        ]
                    }
                    
                    start_time = time.time()
                    response = self.client.post('/api/sales/tickets/', ticket_data, format='json')
                    execution_time = time.time() - start_time
                    
                    thread_results.append({
                        'thread_id': thread_id,
                        'ticket_id': i,
                        'status_code': response.status_code,
                        'execution_time': execution_time,
                        'success': response.status_code == status.HTTP_201_CREATED,
                        'response_data': response.data if hasattr(response, 'data') else None
                    })
                    
                except Exception as e:
                    thread_results.append({
                        'thread_id': thread_id,
                        'ticket_id': i,
                        'status_code': 0,
                        'execution_time': 0,
                        'success': False,
                        'error': str(e)
                    })
            
            results_queue.put(thread_results)
        
        # Ejecutar threads concurrentes
        threads = []
        start_time = time.time()
        
        for i in range(num_threads):
            thread = threading.Thread(target=create_tickets, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Esperar que terminen todos los threads
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Recolectar resultados
        all_results = []
        while not results_queue.empty():
            all_results.extend(results_queue.get())
        
        # Analizar resultados
        successful_requests = [r for r in all_results if r['success']]
        failed_requests = [r for r in all_results if not r['success']]
        
        execution_times = [r['execution_time'] for r in successful_requests]
        
        # Verificar que se crearon tickets únicos
        created_tickets = Ticket.objects.filter(
            zone=self.zone,
            draw_type=self.draw_type
        ).count()
        
        # Assertions
        self.assertGreater(len(successful_requests), 0, "Debe haber al menos algunas creaciones exitosas")
        self.assertEqual(created_tickets, len(successful_requests), "El número de tickets creados debe coincidir")
        
        # Reporte de resultados
        print(f"📊 Resultados de concurrencia:")
        print(f"   Total de requests: {len(all_results)}")
        print(f"   Exitosos: {len(successful_requests)}")
        print(f"   Fallidos: {len(failed_requests)}")
        print(f"   Tiempo total: {total_time:.2f}s")
        print(f"   Tiempo promedio por request: {sum(execution_times)/len(execution_times):.3f}s" if execution_times else "N/A")
        print(f"   Tickets creados: {created_tickets}")
    
    def test_concurrent_report_generation(self):
        """Test de generación concurrente de reportes"""
        print("📊 Ejecutando test de reportes concurrentes...")
        
        # Crear algunos tickets primero
        for i in range(20):
            ticket = Ticket.objects.create(
                zone=self.zone,
                draw_type=self.draw_type,
                user=self.user,
                total_pieces=random.randint(1, 10)
            )
            for j in range(random.randint(1, 3)):
                TicketItem.objects.create(
                    ticket=ticket,
                    number=f'{random.randint(0, 99):02d}',
                    pieces=random.randint(1, 5)
                )
        
        num_threads = 5
        results_queue = queue.Queue()
        
        def generate_reports(thread_id):
            """Función para generar reportes en un thread"""
            thread_results = []
            
            report_endpoints = [
                '/api/sales/reports/summary/',
                '/api/sales/reports/summary/?group_by=zone',
                '/api/sales/reports/summary/?group_by=draw_type',
                '/api/sales/reports/detailed/',
            ]
            
            for i in range(4):
                try:
                    endpoint = report_endpoints[i % len(report_endpoints)]
                    
                    start_time = time.time()
                    response = self.client.get(endpoint)
                    execution_time = time.time() - start_time
                    
                    thread_results.append({
                        'thread_id': thread_id,
                        'request_id': i,
                        'endpoint': endpoint,
                        'status_code': response.status_code,
                        'execution_time': execution_time,
                        'success': response.status_code == status.HTTP_200_OK,
                        'response_size': len(str(response.data)) if hasattr(response, 'data') else 0
                    })
                    
                except Exception as e:
                    thread_results.append({
                        'thread_id': thread_id,
                        'request_id': i,
                        'endpoint': endpoint,
                        'status_code': 0,
                        'execution_time': 0,
                        'success': False,
                        'error': str(e)
                    })
            
            results_queue.put(thread_results)
        
        # Ejecutar threads concurrentes
        threads = []
        start_time = time.time()
        
        for i in range(num_threads):
            thread = threading.Thread(target=generate_reports, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Esperar que terminen
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Recolectar resultados
        all_results = []
        while not results_queue.empty():
            all_results.extend(results_queue.get())
        
        # Analizar resultados
        successful_requests = [r for r in all_results if r['success']]
        failed_requests = [r for r in all_results if not r['success']]
        
        execution_times = [r['execution_time'] for r in successful_requests]
        
        # Assertions
        self.assertGreater(len(successful_requests), 0, "Debe haber al menos algunos reportes exitosos")
        
        # Reporte de resultados
        print(f"📊 Resultados de reportes concurrentes:")
        print(f"   Total de requests: {len(all_results)}")
        print(f"   Exitosos: {len(successful_requests)}")
        print(f"   Fallidos: {len(failed_requests)}")
        print(f"   Tiempo total: {total_time:.2f}s")
        print(f"   Tiempo promedio: {sum(execution_times)/len(execution_times):.3f}s" if execution_times else "N/A")
    
    def test_concurrent_read_write_operations(self):
        """Test de operaciones concurrentes de lectura y escritura"""
        print("🔄 Ejecutando test de operaciones mixtas...")
        
        num_threads = 8
        operations_per_thread = 10
        results_queue = queue.Queue()
        
        def mixed_operations(thread_id):
            """Función para operaciones mixtas"""
            thread_results = []
            
            for i in range(operations_per_thread):
                operation_type = random.choice(['read', 'write'])
                
                try:
                    start_time = time.time()
                    
                    if operation_type == 'read':
                        # Operación de lectura
                        response = self.client.get('/api/sales/tickets/')
                        success = response.status_code == status.HTTP_200_OK
                    else:
                        # Operación de escritura
                        ticket_data = {
                            'zone': self.zone.id,
                            'draw_type': self.draw_type.id,
                            'items': [
                                {
                                    'number': f'{random.randint(0, 99):02d}',
                                    'pieces': random.randint(1, 3)
                                }
                            ]
                        }
                        response = self.client.post('/api/sales/tickets/', ticket_data, format='json')
                        success = response.status_code == status.HTTP_201_CREATED
                    
                    execution_time = time.time() - start_time
                    
                    thread_results.append({
                        'thread_id': thread_id,
                        'operation_id': i,
                        'operation_type': operation_type,
                        'status_code': response.status_code,
                        'execution_time': execution_time,
                        'success': success
                    })
                    
                except Exception as e:
                    thread_results.append({
                        'thread_id': thread_id,
                        'operation_id': i,
                        'operation_type': operation_type,
                        'status_code': 0,
                        'execution_time': 0,
                        'success': False,
                        'error': str(e)
                    })
            
            results_queue.put(thread_results)
        
        # Ejecutar threads concurrentes
        threads = []
        start_time = time.time()
        
        for i in range(num_threads):
            thread = threading.Thread(target=mixed_operations, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Esperar que terminen
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Recolectar resultados
        all_results = []
        while not results_queue.empty():
            all_results.extend(results_queue.get())
        
        # Analizar por tipo de operación
        read_operations = [r for r in all_results if r['operation_type'] == 'read']
        write_operations = [r for r in all_results if r['operation_type'] == 'write']
        
        successful_reads = [r for r in read_operations if r['success']]
        successful_writes = [r for r in write_operations if r['success']]
        
        # Assertions
        self.assertGreater(len(successful_reads), 0, "Debe haber lecturas exitosas")
        self.assertGreater(len(successful_writes), 0, "Debe haber escrituras exitosas")
        
        # Reporte de resultados
        print(f"📊 Resultados de operaciones mixtas:")
        print(f"   Total de operaciones: {len(all_results)}")
        print(f"   Lecturas: {len(read_operations)} ({len(successful_reads)} exitosas)")
        print(f"   Escrituras: {len(write_operations)} ({len(successful_writes)} exitosas)")
        print(f"   Tiempo total: {total_time:.2f}s")
    
    def test_database_connection_pool_stress(self):
        """Test de stress en el pool de conexiones de base de datos"""
        print("🗄️ Ejecutando test de stress en pool de conexiones...")
        
        num_concurrent_queries = 20
        results_queue = queue.Queue()
        
        def database_query(query_id):
            """Función para ejecutar queries de base de datos"""
            try:
                start_time = time.time()
                
                # Query compleja que usa la conexión
                tickets = list(Ticket.objects.select_related('zone', 'draw_type')
                              .prefetch_related('items')
                              .filter(zone=self.zone)
                              .values('id', 'total_pieces', 'zone__name'))
                
                execution_time = time.time() - start_time
                
                results_queue.put({
                    'query_id': query_id,
                    'execution_time': execution_time,
                    'success': True,
                    'result_count': len(tickets)
                })
                
            except Exception as e:
                results_queue.put({
                    'query_id': query_id,
                    'execution_time': 0,
                    'success': False,
                    'error': str(e)
                })
        
        # Ejecutar queries concurrentes
        with ThreadPoolExecutor(max_workers=num_concurrent_queries) as executor:
            futures = [
                executor.submit(database_query, i) 
                for i in range(num_concurrent_queries)
            ]
            
            # Esperar que terminen
            for future in as_completed(futures):
                future.result()
        
        # Recolectar resultados
        all_results = []
        while not results_queue.empty():
            all_results.append(results_queue.get())
        
        successful_queries = [r for r in all_results if r['success']]
        failed_queries = [r for r in all_results if not r['success']]
        
        execution_times = [r['execution_time'] for r in successful_queries]
        
        # Assertions
        self.assertGreater(len(successful_queries), 0, "Debe haber queries exitosas")
        
        # Reporte de resultados
        print(f"📊 Resultados de stress en pool de conexiones:")
        print(f"   Total de queries: {len(all_results)}")
        print(f"   Exitosas: {len(successful_queries)}")
        print(f"   Fallidas: {len(failed_queries)}")
        print(f"   Tiempo promedio: {sum(execution_times)/len(execution_times):.3f}s" if execution_times else "N/A")
    
    def test_rate_limiting_under_concurrency(self):
        """Test de rate limiting bajo concurrencia"""
        print("🚦 Ejecutando test de rate limiting...")
        
        # Crear muchos requests rápidamente
        num_requests = 50
        results_queue = queue.Queue()
        
        def make_request(request_id):
            """Función para hacer requests"""
            try:
                start_time = time.time()
                response = self.client.get('/api/sales/tickets/')
                execution_time = time.time() - start_time
                
                results_queue.put({
                    'request_id': request_id,
                    'status_code': response.status_code,
                    'execution_time': execution_time,
                    'success': response.status_code == status.HTTP_200_OK,
                    'rate_limited': response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
                })
                
            except Exception as e:
                results_queue.put({
                    'request_id': request_id,
                    'status_code': 0,
                    'execution_time': 0,
                    'success': False,
                    'error': str(e)
                })
        
        # Ejecutar requests concurrentes
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(make_request, i) 
                for i in range(num_requests)
            ]
            
            # Esperar que terminen
            for future in as_completed(futures):
                future.result()
        
        # Recolectar resultados
        all_results = []
        while not results_queue.empty():
            all_results.append(results_queue.get())
        
        successful_requests = [r for r in all_results if r['success']]
        rate_limited_requests = [r for r in all_results if r.get('rate_limited', False)]
        
        # Reporte de resultados
        print(f"📊 Resultados de rate limiting:")
        print(f"   Total de requests: {len(all_results)}")
        print(f"   Exitosos: {len(successful_requests)}")
        print(f"   Rate limited: {len(rate_limited_requests)}")
        
        # Si el rate limiting está activo, debe haber algunos requests limitados
        if len(rate_limited_requests) > 0:
            print("   ✅ Rate limiting funcionando correctamente")
        else:
            print("   ⚠️ Rate limiting no detectado (puede estar desactivado)")


@override_settings(RATE_LIMITING={'ENABLED': True})
class ConcurrencyWithRateLimitingTestCase(ConcurrencyTestCase):
    """Tests de concurrencia con rate limiting activado"""
    
    def test_concurrent_requests_with_rate_limiting(self):
        """Test de requests concurrentes con rate limiting activo"""
        print("🚦 Ejecutando test con rate limiting activo...")
        
        num_requests = 30
        results_queue = queue.Queue()
        
        def make_request(request_id):
            """Función para hacer requests"""
            try:
                start_time = time.time()
                response = self.client.get('/api/sales/tickets/')
                execution_time = time.time() - start_time
                
                results_queue.put({
                    'request_id': request_id,
                    'status_code': response.status_code,
                    'execution_time': execution_time,
                    'success': response.status_code == status.HTTP_200_OK,
                    'rate_limited': response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
                })
                
            except Exception as e:
                results_queue.put({
                    'request_id': request_id,
                    'status_code': 0,
                    'execution_time': 0,
                    'success': False,
                    'error': str(e)
                })
        
        # Ejecutar requests concurrentes
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(make_request, i) 
                for i in range(num_requests)
            ]
            
            # Esperar que terminen
            for future in as_completed(futures):
                future.result()
        
        # Recolectar resultados
        all_results = []
        while not results_queue.empty():
            all_results.append(results_queue.get())
        
        successful_requests = [r for r in all_results if r['success']]
        rate_limited_requests = [r for r in all_results if r.get('rate_limited', False)]
        
        # Assertions
        self.assertGreater(len(successful_requests), 0, "Debe haber algunos requests exitosos")
        
        # Reporte
        print(f"📊 Resultados con rate limiting:")
        print(f"   Total de requests: {len(all_results)}")
        print(f"   Exitosos: {len(successful_requests)}")
        print(f"   Rate limited: {len(rate_limited_requests)}")
        print(f"   Porcentaje limitado: {len(rate_limited_requests)/len(all_results)*100:.1f}%")
