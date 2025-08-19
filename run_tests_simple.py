#!/usr/bin/env python3
"""
Script simple para ejecutar tests de Django
"""

import os
import sys
import subprocess

def run_tests():
    """Ejecutar tests usando docker compose"""
    try:
        # Verificar que estamos en el directorio correcto
        if not os.path.exists('manage.py'):
            print("❌ Error: No se encontró manage.py")
            return False
            
        print("🚀 Ejecutando tests de Django...")
        
        # Ejecutar tests de accounts
        cmd = ['docker', 'compose', 'exec', '-T', 'web', 'python', 'manage.py', 'test', 'accounts.tests', '--verbosity=1']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Tests ejecutados exitosamente")
            print(result.stdout)
        else:
            print("❌ Error ejecutando tests:")
            print(result.stderr)
            print("STDOUT:", result.stdout)
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
