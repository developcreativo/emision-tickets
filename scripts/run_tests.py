#!/usr/bin/env python3
"""
Script para ejecutar tests del sistema de emisión de tickets
Incluye tests unitarios, de integración y de rendimiento
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


def run_command(command, description, exit_on_error=True):
    """Ejecutar comando y mostrar resultado"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    print(f"Comando: {command}")
    print("-" * 60)
    
    start_time = time.time()
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    end_time = time.time()
    
    execution_time = end_time - start_time
    
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    print(f"\n⏱️  Tiempo de ejecución: {execution_time:.2f} segundos")
    
    if result.returncode != 0:
        print(f"❌ Error en: {description}")
        if exit_on_error:
            sys.exit(result.returncode)
        return False
    else:
        print(f"✅ Completado: {description}")
        return True


def run_django_tests(test_type="all", coverage=True, parallel=False):
    """Ejecutar tests de Django"""
    
    if test_type == "unit":
        test_paths = ["accounts", "catalog", "sales"]
        test_files = []
    elif test_type == "integration":
        test_paths = []
        test_files = ["tests_integration.py"]
    elif test_type == "advanced":
        test_paths = []
        test_files = ["sales/tests_advanced.py"]
    else:  # all
        test_paths = ["accounts", "catalog", "sales"]
        test_files = ["tests_integration.py", "sales/tests_advanced.py"]
    
    # Construir comando de test
    cmd_parts = ["python", "manage.py", "test"]
    
    if coverage:
        cmd_parts.extend(["--with-coverage", "--cover-package=accounts,catalog,sales"])
    
    if parallel:
        cmd_parts.extend(["--parallel"])
    
    cmd_parts.extend(test_paths + test_files)
    
    command = " ".join(cmd_parts)
    return run_command(command, f"Tests de Django - {test_type}", exit_on_error=False)


def run_pytest_tests(test_type="all", coverage=True, parallel=False, html_report=False):
    """Ejecutar tests con pytest"""
    
    cmd_parts = ["pytest"]
    
    if test_type == "unit":
        cmd_parts.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd_parts.extend(["-m", "integration"])
    elif test_type == "performance":
        cmd_parts.extend(["-m", "performance"])
    elif test_type == "security":
        cmd_parts.extend(["-m", "security"])
    
    if coverage:
        cmd_parts.extend(["--cov=accounts", "--cov=catalog", "--cov=sales"])
        cmd_parts.extend(["--cov-report=term-missing"])
        if html_report:
            cmd_parts.extend(["--cov-report=html"])
    
    if parallel:
        cmd_parts.extend(["-n", "auto"])
    
    if html_report:
        cmd_parts.extend(["--html=test_reports/report.html", "--self-contained-html"])
    
    cmd_parts.extend(["--tb=short", "--durations=10"])
    
    command = " ".join(cmd_parts)
    return run_command(command, f"Tests con pytest - {test_type}", exit_on_error=False)


def run_code_quality_checks():
    """Ejecutar verificaciones de calidad de código"""
    
    # Flake8 (linting)
    run_command("flake8 accounts catalog sales --max-line-length=79 --exclude=__pycache__,migrations", 
                "Verificación de estilo con Flake8", exit_on_error=False)
    
    # Black (formateo)
    run_command("black --check accounts catalog sales", 
                "Verificación de formato con Black", exit_on_error=False)
    
    # Isort (imports)
    run_command("isort --check-only accounts catalog sales", 
                "Verificación de orden de imports con isort", exit_on_error=False)
    
    # Security checks
    run_command("bandit -r accounts catalog sales", 
                "Verificación de seguridad con Bandit", exit_on_error=False)
    
    # Safety (dependencias)
    run_command("safety check", 
                "Verificación de dependencias con Safety", exit_on_error=False)


def run_performance_tests():
    """Ejecutar tests de rendimiento"""
    
    # Test de carga básico con Locust
    if os.path.exists("locustfile.py"):
        run_command("locust --headless --users 10 --spawn-rate 2 --run-time 30s", 
                    "Test de carga con Locust", exit_on_error=False)
    else:
        print("⚠️  No se encontró locustfile.py para tests de rendimiento")


def generate_test_report():
    """Generar reporte de tests"""
    
    # Crear directorio de reportes si no existe
    report_dir = Path("test_reports")
    report_dir.mkdir(exist_ok=True)
    
    # Generar reporte de cobertura HTML
    if os.path.exists(".coverage"):
        run_command("coverage html --directory=test_reports/coverage", 
                    "Generar reporte de cobertura HTML", exit_on_error=False)
    
    # Generar badge de cobertura
    try:
        run_command("coverage-badge -o test_reports/coverage-badge.svg", 
                    "Generar badge de cobertura", exit_on_error=False)
    except:
        print("⚠️  No se pudo generar badge de cobertura")


def main():
    parser = argparse.ArgumentParser(description="Ejecutar tests del sistema de tickets")
    parser.add_argument("--type", choices=["all", "unit", "integration", "advanced", "performance"], 
                       default="all", help="Tipo de tests a ejecutar")
    parser.add_argument("--framework", choices=["django", "pytest", "both"], 
                       default="both", help="Framework de testing a usar")
    parser.add_argument("--no-coverage", action="store_true", 
                       help="No ejecutar cobertura de código")
    parser.add_argument("--parallel", action="store_true", 
                       help="Ejecutar tests en paralelo")
    parser.add_argument("--html-report", action="store_true", 
                       help="Generar reporte HTML")
    parser.add_argument("--quality", action="store_true", 
                       help="Ejecutar verificaciones de calidad de código")
    parser.add_argument("--performance", action="store_true", 
                       help="Ejecutar tests de rendimiento")
    
    args = parser.parse_args()
    
    print("🚀 Iniciando suite de tests del sistema de emisión de tickets")
    print(f"📅 {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("manage.py"):
        print("❌ Error: No se encontró manage.py. Ejecuta desde el directorio raíz del proyecto.")
        sys.exit(1)
    
    # Crear directorio de reportes
    os.makedirs("test_reports", exist_ok=True)
    
    # Ejecutar tests según el framework seleccionado
    if args.framework in ["django", "both"]:
        run_django_tests(args.type, not args.no_coverage, args.parallel)
    
    if args.framework in ["pytest", "both"]:
        run_pytest_tests(args.type, not args.no_coverage, args.parallel, args.html_report)
    
    # Verificaciones adicionales
    if args.quality:
        run_code_quality_checks()
    
    if args.performance:
        run_performance_tests()
    
    # Generar reportes
    if not args.no_coverage:
        generate_test_report()
    
    print("\n" + "="*60)
    print("🎉 Suite de tests completada")
    print("📊 Los reportes están disponibles en: test_reports/")
    print("="*60)


if __name__ == "__main__":
    main()
