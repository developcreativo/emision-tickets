#!/usr/bin/env python3
"""
Script para tests de stress de memoria
Mide el uso de memoria bajo diferentes cargas de trabajo
"""

import gc
import os
import queue
import sys
import threading
from datetime import datetime
from typing import Any, Dict, List

import psutil

# Agregar el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.utils import timezone

from sales.models import Ticket


class MemoryStressTest:
    """Clase para ejecutar tests de stress de memoria"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.results = {}
        self.memory_snapshots = []
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Obtiene información detallada del uso de memoria"""
        memory_info = self.process.memory_info()
        memory_percent = self.process.memory_percent()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
            'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
            'percent': memory_percent,
            'timestamp': datetime.now().isoformat()
        }
    
    def take_memory_snapshot(self, test_name: str):
        """Toma una instantánea del uso de memoria"""
        snapshot = {
            'test_name': test_name,
            'memory': self.get_memory_usage(),
            'gc_stats': gc.get_stats() if hasattr(gc, 'get_stats') else {}
        }
        self.memory_snapshots.append(snapshot)
        return snapshot
    
    def test_memory_leak_creation(self):
        """Test para detectar memory leaks en creación de objetos"""
        print("🧪 Ejecutando test de memory leak en creación...")
        
        initial_memory = self.get_memory_usage()
        self.take_memory_snapshot("before_creation")
        
        # Crear muchos objetos
        objects_created = []
        for i in range(1000):
            # Simular creación de tickets en memoria
            ticket_data = {
                'id': i,
                'zone_id': 1,
                'draw_type_id': 1,
                'total_pieces': 10,
                'created_at': timezone.now(),
                'items': [{'number': '01', 'pieces': 5} for _ in range(3)]
            }
            objects_created.append(ticket_data)
        
        after_creation = self.get_memory_usage()
        self.take_memory_snapshot("after_creation")
        
        # Limpiar objetos
        del objects_created
        gc.collect()
        
        after_cleanup = self.get_memory_usage()
        self.take_memory_snapshot("after_cleanup")
        
        # Calcular diferencias
        creation_increase = (
            after_creation['rss_mb'] - initial_memory['rss_mb']
        )
        cleanup_decrease = (
            after_creation['rss_mb'] - after_cleanup['rss_mb']
        )
        
        self.results['memory_leak_creation'] = {
            'initial_memory_mb': initial_memory['rss_mb'],
            'after_creation_mb': after_creation['rss_mb'],
            'after_cleanup_mb': after_cleanup['rss_mb'],
            'creation_increase_mb': creation_increase,
            'cleanup_decrease_mb': cleanup_decrease,
            'memory_leak_mb': creation_increase - cleanup_decrease,
            'objects_created': 1000,
            'success': True
        }
    
    def test_database_query_memory(self):
        """Test de uso de memoria en queries de base de datos"""
        print("🗄️ Ejecutando test de memoria en queries...")
        
        initial_memory = self.get_memory_usage()
        self.take_memory_snapshot("before_queries")
        
        # Ejecutar queries que cargan muchos datos
        large_datasets = []
        for i in range(10):
            # Query que carga muchos tickets
            tickets = list(Ticket.objects.all()[:1000])
            large_datasets.append(tickets)
            
            # Simular procesamiento
            processed_data = []
            for ticket in tickets:
                processed_data.append({
                    'id': ticket.id,
                    'total_pieces': ticket.total_pieces,
                    'zone_name': ticket.zone.name if ticket.zone else None
                })
            
            large_datasets.append(processed_data)
        
        after_queries = self.get_memory_usage()
        self.take_memory_snapshot("after_queries")
        
        # Limpiar
        del large_datasets
        gc.collect()
        
        after_cleanup = self.get_memory_usage()
        self.take_memory_snapshot("after_queries_cleanup")
        
        self.results['database_query_memory'] = {
            'initial_memory_mb': initial_memory['rss_mb'],
            'after_queries_mb': after_queries['rss_mb'],
            'after_cleanup_mb': after_cleanup['rss_mb'],
            'query_increase_mb': after_queries['rss_mb'] - initial_memory['rss_mb'],
            'cleanup_decrease_mb': after_queries['rss_mb'] - after_cleanup['rss_mb'],
            'memory_leak_mb': (after_queries['rss_mb'] - initial_memory['rss_mb']) - 
                             (after_queries['rss_mb'] - after_cleanup['rss_mb']),
            'queries_executed': 10,
            'success': True
        }
    
    def test_concurrent_memory_usage(self):
        """Test de uso de memoria bajo concurrencia"""
        print("⚡ Ejecutando test de memoria concurrente...")
        
        initial_memory = self.get_memory_usage()
        self.take_memory_snapshot("before_concurrency")
        
        results_queue = queue.Queue()
        
        def concurrent_worker(worker_id):
            """Worker que ejecuta operaciones concurrentes"""
            try:
                # Simular trabajo intensivo
                worker_data = []
                for i in range(100):
                    worker_data.append({
                        'worker_id': worker_id,
                        'iteration': i,
                        'data': f"data_{worker_id}_{i}" * 100  # Datos grandes
                    })
                
                # Simular procesamiento
                processed_data = []
                for item in worker_data:
                    processed_data.append({
                        'processed': item['data'].upper(),
                        'length': len(item['data'])
                    })
                
                results_queue.put({
                    'worker_id': worker_id,
                    'success': True,
                    'data_size': len(worker_data)
                })
                
            except Exception as e:
                results_queue.put({
                    'worker_id': worker_id,
                    'success': False,
                    'error': str(e)
                })
        
        # Ejecutar workers concurrentes
        threads = []
        for i in range(5):
            thread = threading.Thread(target=concurrent_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Esperar que terminen
        for thread in threads:
            thread.join()
        
        peak_memory = self.get_memory_usage()
        self.take_memory_snapshot("peak_concurrency")
        
        # Limpiar
        gc.collect()
        
        final_memory = self.get_memory_usage()
        self.take_memory_snapshot("after_concurrency")
        
        # Recolectar resultados
        worker_results = []
        while not results_queue.empty():
            worker_results.append(results_queue.get())
        
        self.results['concurrent_memory'] = {
            'initial_memory_mb': initial_memory['rss_mb'],
            'peak_memory_mb': peak_memory['rss_mb'],
            'final_memory_mb': final_memory['rss_mb'],
            'peak_increase_mb': peak_memory['rss_mb'] - initial_memory['rss_mb'],
            'final_increase_mb': final_memory['rss_mb'] - initial_memory['rss_mb'],
            'workers_executed': len(worker_results),
            'successful_workers': len([r for r in worker_results if r['success']]),
            'success': True
        }
    
    def test_cache_memory_usage(self):
        """Test de uso de memoria en cache"""
        print("💾 Ejecutando test de memoria en cache...")
        
        from django.core.cache import cache
        
        initial_memory = self.get_memory_usage()
        self.take_memory_snapshot("before_cache")
        
        # Llenar cache con datos
        cache_data = {}
        for i in range(1000):
            key = f"test_key_{i}"
            value = {
                'id': i,
                'data': f"large_data_string_{i}" * 50,
                'timestamp': datetime.now().isoformat(),
                'nested': {
                    'level1': {'level2': {'level3': f"deep_data_{i}"}}
                }
            }
            cache.set(key, value, timeout=300)
            cache_data[key] = value
        
        after_cache_fill = self.get_memory_usage()
        self.take_memory_snapshot("after_cache_fill")
        
        # Limpiar cache
        for key in cache_data.keys():
            cache.delete(key)
        
        after_cache_clear = self.get_memory_usage()
        self.take_memory_snapshot("after_cache_clear")
        
        self.results['cache_memory'] = {
            'initial_memory_mb': initial_memory['rss_mb'],
            'after_fill_mb': after_cache_fill['rss_mb'],
            'after_clear_mb': after_cache_clear['rss_mb'],
            'cache_increase_mb': after_cache_fill['rss_mb'] - initial_memory['rss_mb'],
            'cache_cleanup_mb': after_cache_fill['rss_mb'] - after_cache_clear['rss_mb'],
            'cache_entries': len(cache_data),
            'success': True
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """Genera reporte de tests de memoria"""
        report = {
            'summary': {
                'total_tests': len(self.results),
                'successful_tests': len([r for r in self.results.values() if r.get('success')]),
                'memory_snapshots': len(self.memory_snapshots),
                'peak_memory_mb': max(
                    [snapshot['memory']['rss_mb'] for snapshot in self.memory_snapshots]
                ) if self.memory_snapshots else 0,
                'final_memory_mb': self.memory_snapshots[-1]['memory']['rss_mb'] if self.memory_snapshots else 0
            },
            'tests': self.results,
            'snapshots': self.memory_snapshots,
            'recommendations': self._generate_recommendations(),
            'timestamp': datetime.now().isoformat()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Genera recomendaciones basadas en los resultados"""
        recommendations = []
        
        # Analizar memory leaks
        memory_leaks = []
        for test_name, result in self.results.items():
            if result.get('success') and result.get('memory_leak_mb', 0) > 10:
                memory_leaks.append(test_name)
        
        if memory_leaks:
            recommendations.append(
                f"⚠️ Memory leaks detectados en: {', '.join(memory_leaks)}"
            )
        
        # Analizar uso de memoria
        peak_memory = max(
            [snapshot['memory']['rss_mb'] for snapshot in self.memory_snapshots]
        ) if self.memory_snapshots else 0
        
        if peak_memory > 500:  # Más de 500MB
            recommendations.append(
                f"⚠️ Uso de memoria alto detectado: {peak_memory:.1f}MB"
            )
        
        # Recomendaciones generales
        recommendations.extend([
            "✅ Revisar objetos que no se liberan correctamente",
            "✅ Usar context managers para recursos",
            "✅ Implementar límites en queries de base de datos",
            "✅ Monitorear uso de memoria en producción",
            "✅ Considerar usar streaming para datasets grandes"
        ])
        
        return recommendations


def main():
    """Función principal para ejecutar tests de memoria"""
    print("🧠 Iniciando tests de stress de memoria...")
    
    stress_test = MemoryStressTest()
    
    # Ejecutar todos los tests
    stress_test.test_memory_leak_creation()
    stress_test.test_database_query_memory()
    stress_test.test_concurrent_memory_usage()
    stress_test.test_cache_memory_usage()
    
    # Generar reporte
    report = stress_test.generate_report()
    
    # Mostrar resultados
    print("\n" + "="*60)
    print("🧠 REPORTE DE TESTS DE STRESS DE MEMORIA")
    print("="*60)
    
    if 'summary' in report:
        summary = report['summary']
        print(f"✅ Tests exitosos: {summary['successful_tests']}/{summary['total_tests']}")
        print(f"📊 Memoria pico: {summary['peak_memory_mb']:.1f}MB")
        print(f"📊 Memoria final: {summary['final_memory_mb']:.1f}MB")
        print(f"📸 Snapshots tomados: {summary['memory_snapshots']}")
    
    print("\n🔍 DETALLES POR TEST:")
    for name, result in stress_test.results.items():
        status = "✅" if result.get('success') else "❌"
        memory_leak = result.get('memory_leak_mb', 0)
        print(f"  {status} {name}: {memory_leak:.1f}MB leak")
    
    print("\n💡 RECOMENDACIONES:")
    for rec in report.get('recommendations', []):
        print(f"  {rec}")
    
    # Guardar reporte
    import json
    report_file = f"memory_stress_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n💾 Reporte guardado en: {report_file}")


if __name__ == "__main__":
    main()
