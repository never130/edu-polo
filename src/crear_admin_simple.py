#!/usr/bin/env python
"""Script simple para crear un superusuario de Django"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# ============================================
# CONFIGURA AQUÍ TUS DATOS
# ============================================
USERNAME = 'superadmin'  # Cambia esto por el nombre que quieras
EMAIL = 'superadmin@edupolo.com'  # Cambia esto por tu email
PASSWORD = 'admin123456'  # Cambia esto por tu contraseña
# ============================================

def crear_superusuario():
    """Crea un superusuario"""
    try:
        # Verificar si el usuario ya existe
        if User.objects.filter(username=USERNAME).exists():
            print(f"❌ El usuario '{USERNAME}' ya existe.")
            print("💡 Edita este script y cambia el USERNAME o elimina el usuario existente.")
            return
        
        # Crear el superusuario
        User.objects.create_superuser(
            username=USERNAME,
            email=EMAIL,
            password=PASSWORD
        )
        
        print("=" * 50)
        print("✅ Superusuario creado exitosamente!")
        print("=" * 50)
        print(f"👤 Username: {USERNAME}")
        print(f"📧 Email: {EMAIL}")
        print(f"🔑 Password: {PASSWORD}")
        print("=" * 50)
        print(f"\n💡 Ahora puedes iniciar sesión en:")
        print(f"   http://127.0.0.1:8000/admin/")
        print(f"\n⚠️  IMPORTANTE: Cambia la contraseña después del primer inicio de sesión.")
        
    except Exception as e:
        print(f"❌ Error al crear el superusuario: {str(e)}")

if __name__ == '__main__':
    crear_superusuario()


