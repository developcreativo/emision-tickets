#!/usr/bin/env python3
"""
Script principal para ejecutar todos los tests de rendimiento
Integra benchmarks de base de datos, tests de memoria, concurrencia y carga
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Agregar el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()


class PerformanceTestRunner:
    """Runner principal para tests de rendimiento"""
    
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
        self.reports_dir = Path("performance-reports")
        self.reports_dir.mkdir(exist_ok=True)
    
    def run_database_benchmarks(self):
        """Ejecutar benchmarks de base de datos"""
        print("🗄️ Ejecutando benchmarks de base de datos...")
        
        try:
            result = subprocess.run(
                [sys.executable, "scripts/db_benchmarks.py"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print("✅ Benchmarks de base de datos completados")
                self.results['database_benchmarks'] = {
                    'status': 'success',
                    'output': result.stdout,
                    'error': result.stderr
                }
            else:
                print(f"❌ Error en benchmarks de base de datos: {result.stderr}")
                self.results['database_benchmarks'] = {
                    'status': 'error',
                    'output': result.stdout,
                    'error': result.stderr
                }
                
        except subprocess.TimeoutExpired:
            print("⏰ Timeout en benchmarks de base de datos")
            self.results['database_benchmarks'] = {
                'status': 'timeout',
                'error': 'Execution timeout'
            }
        except Exception as e:
            print(f"❌ Error ejecutando benchmarks: {e}")
            self.results['database_benchmarks'] = {
                'status': 'error',
                'error': str(e)
            }
    
    def run_memory_stress_tests(self):
        """Ejecutar tests de stress de memoria"""
        print("🧠 Ejecutando tests de stress de memoria...")
        
        try:
            result = subprocess.run(
                [sys.executable, "scripts/memory_stress_test.py"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print("✅ Tests de memoria completados")
                self.results['memory_stress_tests'] = {
                    'status': 'success',
                    'output': result.stdout,
                    'error': result.stderr
                }
            else:
                print(f"❌ Error en tests de memoria: {result.stderr}")
                self.results['memory_stress_tests'] = {
                    'status': 'error',
                    'output': result.stdout,
                    'error': result.stderr
                }
                
        except subprocess.TimeoutExpired:
            print("⏰ Timeout en tests de memoria")
            self.results['memory_stress_tests'] = {
                'status': 'timeout',
                'error': 'Execution timeout'
            }
        except Exception as e:
            print(f"❌ Error ejecutando tests de memoria: {e}")
            self.results['memory_stress_tests'] = {
                'status': 'error',
                'error': str(e)
            }
    
    def run_concurrency_tests(self):
        """Ejecutar tests de concurrencia"""
        print("⚡ Ejecutando tests de concurrencia...")
        
        try:
            result = subprocess.run(
                [sys.executable, "manage.py", "test", "sales.tests_concurrency", "--verbosity=2"],
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                print("✅ Tests de concurrencia completados")
                self.results['concurrency_tests'] = {
                    'status': 'success',
                    'output': result.stdout,
                    'error': result.stderr
                }
            else:
                print(f"❌ Error en tests de concurrencia: {result.stderr}")
                self.results['concurrency_tests'] = {
                    'status': 'error',
                    'output': result.stdout,
                    'error': result.stderr
                }
                
        except subprocess.TimeoutExpired:
            print("⏰ Timeout en tests de concurrencia")
            self.results['concurrency_tests'] = {
                'status': 'timeout',
                'error': 'Execution timeout'
            }
        except Exception as e:
            print(f"❌ Error ejecutando tests de concurrencia: {e}")
            self.results['concurrency_tests'] = {
                'status': 'error',
                'error': str(e)
            }
    
    def run_load_tests(self):
        """Ejecutar tests de carga con Locust"""
        print("🚀 Ejecutando tests de carga...")
        
        try:
            # Verificar si Locust está instalado
            result = subprocess.run(
                ["locust", "--version"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print("⚠️ Locust no está instalado, saltando tests de carga")
                self.results['load_tests'] = {
                    'status': 'skipped',
                    'error': 'Locust not installed'
                }
                return
            
            # Ejecutar Locust en modo headless
            result = subprocess.run([
                "locust",
                "-f", "locustfile.py",
                "--headless",
                "--users", "10",
                "--spawn-rate", "2",
                "--run-time", "60s",
                "--host", "http://localhost:8000"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✅ Tests de carga completados")
                self.results['load_tests'] = {
                    'status': 'success',
                    'output': result.stdout,
                    'error': result.stderr
                }
            else:
                print(f"❌ Error en tests de carga: {result.stderr}")
                self.results['load_tests'] = {
                    'status': 'error',
                    'output': result.stdout,
                    'error': result.stderr
                }
                
        except subprocess.TimeoutExpired:
            print("⏰ Timeout en tests de carga")
            self.results['load_tests'] = {
                'status': 'timeout',
                'error': 'Execution timeout'
            }
        except Exception as e:
            print(f"❌ Error ejecutando tests de carga: {e}")
            self.results['load_tests'] = {
                'status': 'error',
                'error': str(e)
            }
    
    def collect_reports(self):
        """Recolectar reportes generados"""
        print("📊 Recolectando reportes...")
        
        # Buscar archivos de reporte
        report_files = []
        
        # Buscar archivos JSON
        for json_file in Path(".").glob("*.json"):
            if "benchmark" in json_file.name or "stress" in json_file.name or "report" in json_file.name:
                report_files.append(str(json_file))
        
        # Buscar archivos HTML
        for html_file in Path(".").glob("*.html"):
            if "locust" in html_file.name or "report" in html_file.name:
                report_files.append(str(html_file))
        
        # Mover archivos al directorio de reportes
        for file_path in report_files:
            try:
                source = Path(file_path)
                destination = self.reports_dir / source.name
                source.rename(destination)
                print(f"📁 Movido: {source.name}")
            except Exception as e:
                print(f"⚠️ Error moviendo {file_path}: {e}")
        
        self.results['reports_collected'] = {
            'status': 'success',
            'files': report_files,
            'count': len(report_files)
        }
    
    def generate_summary_report(self):
        """Generar reporte resumen"""
        print("📋 Generando reporte resumen...")
        
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        summary = {
            'test_run': {
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration.total_seconds(),
                'total_tests': len(self.results)
            },
            'results': self.results,
            'summary': {
                'successful': len([r for r in self.results.values() if r.get('status') == 'success']),
                'failed': len([r for r in self.results.values() if r.get('status') == 'error']),
                'timeout': len([r for r in self.results.values() if r.get('status') == 'timeout']),
                'skipped': len([r for r in self.results.values() if r.get('status') == 'skipped'])
            }
        }
        
        # Guardar reporte resumen
        summary_file = self.reports_dir / f"performance_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"💾 Reporte resumen guardado: {summary_file}")
        
        return summary
    
    def print_results(self, summary):
        """Imprimir resultados en consola"""
        print("\n" + "="*60)
        print("🚀 REPORTE FINAL DE TESTS DE RENDIMIENTO")
        print("="*60)
        
        print(f"⏱️ Duración total: {summary['test_run']['duration_seconds']:.1f} segundos")
        print(f"📊 Tests ejecutados: {summary['summary']['total_tests']}")
        print(f"✅ Exitosos: {summary['summary']['successful']}")
        print(f"❌ Fallidos: {summary['summary']['failed']}")
        print(f"⏰ Timeouts: {summary['summary']['timeout']}")
        print(f"⏭️ Saltados: {summary['summary']['skipped']}")
        
        print("\n🔍 DETALLES POR TEST:")
        for test_name, result in self.results.items():
            status_emoji = {
                'success': '✅',
                'error': '❌',
                'timeout': '⏰',
                'skipped': '⏭️'
            }.get(result.get('status'), '❓')
            
            print(f"  {status_emoji} {test_name}: {result.get('status', 'unknown')}")
        
        print(f"\n📁 Reportes guardados en: {self.reports_dir}")
        
        # Listar archivos de reporte
        if self.reports_dir.exists():
            report_files = list(self.reports_dir.glob("*"))
            if report_files:
                print("📄 Archivos de reporte:")
                for file in report_files:
                    print(f"  - {file.name}")
    
    def run_all_tests(self):
        """Ejecutar todos los tests de rendimiento"""
        print("🚀 Iniciando suite completa de tests de rendimiento...")
        print(f"📁 Reportes se guardarán en: {self.reports_dir}")
        
        # Ejecutar tests en secuencia
        self.run_database_benchmarks()
        self.run_memory_stress_tests()
        self.run_concurrency_tests()
        self.run_load_tests()
        
        # Recolectar reportes
        self.collect_reports()
        
        # Generar resumen
        summary = self.generate_summary_report()
        
        # Mostrar resultados
        self.print_results(summary)
        
        return summary


def main():
    """Función principal"""
    runner = PerformanceTestRunner()
    
    try:
        summary = runner.run_all_tests()
        
        # Retornar código de salida basado en resultados
        if summary['summary']['failed'] > 0:
            print("\n❌ Algunos tests fallaron")
            sys.exit(1)
        elif summary['summary']['successful'] == 0:
            print("\n⚠️ Ningún test se ejecutó exitosamente")
            sys.exit(2)
        else:
            print("\n✅ Todos los tests completados exitosamente")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrumpidos por el usuario")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Error inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
