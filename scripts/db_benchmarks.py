#!/usr/bin/env python3
"""
Script para benchmarks de base de datos
Mide el rendimiento de queries complejas y operaciones críticas
"""

import json
import os
import queue
import statistics
import sys
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

# Agregar el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
from django.db import connection, reset_queries

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db.models import Avg, Count, Sum
from django.utils import timezone

from sales.models import Ticket


class DatabaseBenchmark:
    """Clase para ejecutar benchmarks de base de datos"""
    
    def __init__(self):
        self.results = {}
        self.query_count = 0
        self.total_time = 0
    
    def measure_query(self, name: str, func, *args, **kwargs) -> Dict[str, Any]:
        """Mide el tiempo de ejecución de una query"""
        reset_queries()
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Contar queries ejecutadas
            queries = len(connection.queries)
            
            benchmark_result = {
                'name': name,
                'execution_time': execution_time,
                'query_count': queries,
                'success': True,
                'result_size': len(result) if hasattr(result, '__len__') else 1,
                'timestamp': datetime.now().isoformat()
            }
            
            self.results[name] = benchmark_result
            return benchmark_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            benchmark_result = {
                'name': name,
                'execution_time': execution_time,
                'query_count': len(connection.queries),
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.results[name] = benchmark_result
            return benchmark_result
    
    def benchmark_ticket_queries(self):
        """Benchmarks para queries relacionadas con tickets"""
        print("🔍 Ejecutando benchmarks de tickets...")
        
        # 1. Query simple: contar tickets
        self.measure_query(
            "count_tickets",
            lambda: Ticket.objects.count()
        )
        
        # 2. Query con filtros: tickets por zona
        self.measure_query(
            "tickets_by_zone",
            lambda: list(Ticket.objects.filter(zone_id=1).select_related('zone'))
        )
        
        # 3. Query con agregaciones: total de piezas por zona
        self.measure_query(
            "total_pieces_by_zone",
            lambda: list(Ticket.objects.values('zone__name').annotate(
                total_pieces=Sum('total_pieces'),
                ticket_count=Count('id')
            ))
        )
        
        # 4. Query compleja: reporte de ventas con múltiples joins
        self.measure_query(
            "complex_sales_report",
            lambda: list(Ticket.objects.select_related('zone', 'draw_type', 'user')
                        .prefetch_related('items')
                        .filter(created_at__gte=timezone.now() - timedelta(days=30))
                        .values('zone__name', 'draw_type__name')
                        .annotate(
                            total_tickets=Count('id'),
                            total_pieces=Sum('total_pieces'),
                            avg_pieces=Avg('total_pieces')
                        ))
        )
        
        # 5. Query con subconsultas: tickets con más items
        self.measure_query(
            "tickets_with_most_items",
            lambda: list(Ticket.objects.annotate(
                item_count=Count('items')
            ).filter(item_count__gt=5).order_by('-item_count')[:10])
        )
    
    def benchmark_report_queries(self):
        """Benchmarks para queries de reportes"""
        print("📊 Ejecutando benchmarks de reportes...")
        
        # 1. Reporte de resumen diario
        self.measure_query(
            "daily_summary_report",
            lambda: list(Ticket.objects.filter(
                created_at__date=timezone.now().date()
            ).values('zone__name').annotate(
                total_tickets=Count('id'),
                total_pieces=Sum('total_pieces')
            ))
        )
        
        # 2. Reporte por rangos de fechas
        start_date = timezone.now() - timedelta(days=7)
        end_date = timezone.now()
        
        self.measure_query(
            "date_range_report",
            lambda: list(Ticket.objects.filter(
                created_at__range=(start_date, end_date)
            ).values('created_at__date').annotate(
                daily_tickets=Count('id'),
                daily_pieces=Sum('total_pieces')
            ).order_by('created_at__date'))
        )
        
        # 3. Reporte con múltiples filtros
        self.measure_query(
            "filtered_report",
            lambda: list(Ticket.objects.filter(
                zone_id__in=[1, 2, 3],
                draw_type_id__in=[1, 2],
                created_at__gte=timezone.now() - timedelta(days=30)
            ).select_related('zone', 'draw_type')
            .values('zone__name', 'draw_type__name')
            .annotate(
                total_tickets=Count('id'),
                total_pieces=Sum('total_pieces')
            ))
        )
    
    def benchmark_concurrent_queries(self):
        """Benchmarks para queries concurrentes"""
        print("⚡ Ejecutando benchmarks de concurrencia...")
        
        results_queue = queue.Queue()
        
        def concurrent_query(query_id):
            """Query individual para concurrencia"""
            try:
                start_time = time.time()
                # Query que simula carga
                result = list(Ticket.objects.filter(
                    created_at__gte=timezone.now() - timedelta(days=7)
                ).select_related('zone').values('zone__name').annotate(
                    count=Count('id')
                ))
                execution_time = time.time() - start_time
                
                results_queue.put({
                    'query_id': query_id,
                    'execution_time': execution_time,
                    'success': True,
                    'result_count': len(result)
                })
            except Exception as e:
                results_queue.put({
                    'query_id': query_id,
                    'execution_time': 0,
                    'success': False,
                    'error': str(e)
                })
        
        # Ejecutar 10 queries concurrentes
        threads = []
        for i in range(10):
            thread = threading.Thread(target=concurrent_query, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Esperar que terminen
        for thread in threads:
            thread.join()
        
        # Recolectar resultados
        concurrent_results = []
        while not results_queue.empty():
            concurrent_results.append(results_queue.get())
        
        # Calcular estadísticas
        successful_times = [
            r['execution_time'] for r in concurrent_results 
            if r['success']
        ]
        
        if successful_times:
            self.results['concurrent_queries'] = {
                'name': 'concurrent_queries',
                'execution_time': statistics.mean(successful_times),
                'min_time': min(successful_times),
                'max_time': max(successful_times),
                'std_dev': statistics.stdev(successful_times) if len(successful_times) > 1 else 0,
                'success_count': len(successful_times),
                'total_queries': len(concurrent_results),
                'success': True,
                'timestamp': datetime.now().isoformat()
            }
    
    def benchmark_index_performance(self):
        """Benchmarks para verificar rendimiento de índices"""
        print("📈 Ejecutando benchmarks de índices...")
        
        # Query sin usar índices específicos
        self.measure_query(
            "query_without_index_optimization",
            lambda: list(Ticket.objects.filter(
                total_pieces__gt=10,
                created_at__year=2024
            ))
        )
        
        # Query optimizada con índices
        self.measure_query(
            "query_with_index_optimization",
            lambda: list(Ticket.objects.filter(
                total_pieces__gt=10,
                created_at__year=2024
            ).select_related('zone', 'draw_type'))
        )
    
    def generate_report(self) -> Dict[str, Any]:
        """Genera reporte de benchmarks"""
        successful_results = [
            r for r in self.results.values() 
            if r.get('success', False)
        ]
        
        if not successful_results:
            return {'error': 'No hay resultados exitosos'}
        
        execution_times = [r['execution_time'] for r in successful_results]
        
        report = {
            'summary': {
                'total_benchmarks': len(self.results),
                'successful_benchmarks': len(successful_results),
                'failed_benchmarks': len(self.results) - len(successful_results),
                'average_execution_time': statistics.mean(execution_times),
                'min_execution_time': min(execution_times),
                'max_execution_time': max(execution_times),
                'total_execution_time': sum(execution_times)
            },
            'benchmarks': self.results,
            'recommendations': self._generate_recommendations(),
            'timestamp': datetime.now().isoformat()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Genera recomendaciones basadas en los resultados"""
        recommendations = []
        
        # Analizar tiempos de ejecución
        slow_queries = [
            name for name, result in self.results.items()
            if result.get('success') and result.get('execution_time', 0) > 1.0
        ]
        
        if slow_queries:
            recommendations.append(
                f"⚠️ Queries lentas detectadas: {', '.join(slow_queries)}"
            )
        
        # Analizar número de queries
        high_query_count = [
            name for name, result in self.results.items()
            if result.get('success') and result.get('query_count', 0) > 10
        ]
        
        if high_query_count:
            recommendations.append(
                f"🔍 Queries con muchas consultas: {', '.join(high_query_count)}"
            )
        
        # Recomendaciones generales
        recommendations.extend([
            "✅ Considerar agregar índices en campos frecuentemente consultados",
            "✅ Usar select_related() y prefetch_related() para optimizar joins",
            "✅ Implementar cache para reportes complejos",
            "✅ Monitorear regularmente el rendimiento de queries críticas"
        ])
        
        return recommendations


def main():
    """Función principal para ejecutar benchmarks"""
    print("🚀 Iniciando benchmarks de base de datos...")
    
    benchmark = DatabaseBenchmark()
    
    # Ejecutar todos los benchmarks
    benchmark.benchmark_ticket_queries()
    benchmark.benchmark_report_queries()
    benchmark.benchmark_concurrent_queries()
    benchmark.benchmark_index_performance()
    
    # Generar reporte
    report = benchmark.generate_report()
    
    # Mostrar resultados
    print("\n" + "="*60)
    print("📊 REPORTE DE BENCHMARKS DE BASE DE DATOS")
    print("="*60)
    
    if 'summary' in report:
        summary = report['summary']
        print(f"✅ Benchmarks exitosos: {summary['successful_benchmarks']}/{summary['total_benchmarks']}")
        print(f"⏱️ Tiempo promedio: {summary['average_execution_time']:.3f}s")
        print(f"⚡ Tiempo mínimo: {summary['min_execution_time']:.3f}s")
        print(f"🐌 Tiempo máximo: {summary['max_execution_time']:.3f}s")
        print(f"📈 Tiempo total: {summary['total_execution_time']:.3f}s")
    
    print("\n🔍 DETALLES POR BENCHMARK:")
    for name, result in benchmark.results.items():
        status = "✅" if result.get('success') else "❌"
        time_str = f"{result.get('execution_time', 0):.3f}s"
        queries = result.get('query_count', 0)
        print(f"  {status} {name}: {time_str} ({queries} queries)")
    
    print("\n💡 RECOMENDACIONES:")
    for rec in report.get('recommendations', []):
        print(f"  {rec}")
    
    # Guardar reporte en archivo
    report_file = f"db_benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n💾 Reporte guardado en: {report_file}")


if __name__ == "__main__":
    main()
