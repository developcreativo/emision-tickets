#!/usr/bin/env python3
"""
Test simple para verificar que Django funcione
"""

import os
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Test simple
from accounts.models import User

def test_simple():
    """Test simple para verificar que Django funcione"""
    try:
        # Crear un usuario simple
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='SELLER'
        )
        print(f"✅ Usuario creado exitosamente: {user.username}")
        
        # Verificar que se puede acceder al usuario
        user.refresh_from_db()
        print(f"✅ Usuario accesible: {user.username} - {user.role}")
        
        # Limpiar
        user.delete()
        print("✅ Usuario eliminado exitosamente")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Ejecutando test simple...")
    success = test_simple()
    if success:
        print("🎉 Test simple completado exitosamente")
    else:
        print("💥 Test simple falló")
