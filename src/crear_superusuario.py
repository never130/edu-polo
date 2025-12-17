#!/usr/bin/env python
"""Script para crear un superusuario de Django"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def crear_superusuario():
    """Crea un superusuario si no existe"""
    username = input("Ingresa el nombre de usuario (o presiona Enter para usar 'admin'): ").strip()
    if not username:
        username = 'admin'
    
    # Verificar si el usuario ya existe
    if User.objects.filter(username=username).exists():
        print(f"❌ El usuario '{username}' ya existe.")
        respuesta = input("¿Quieres crear otro usuario? (s/n): ").strip().lower()
        if respuesta != 's':
            print("Operación cancelada.")
            return
        username = input("Ingresa un nuevo nombre de usuario: ").strip()
        if not username:
            print("❌ El nombre de usuario no puede estar vacío.")
            return
    
    email = input("Ingresa el email (o presiona Enter para omitir): ").strip()
    
    password = input("Ingresa la contraseña: ").strip()
    if not password:
        print("❌ La contraseña no puede estar vacía.")
        return
    
    password_confirm = input("Confirma la contraseña: ").strip()
    if password != password_confirm:
        print("❌ Las contraseñas no coinciden.")
        return
    
    try:
        # Crear el superusuario
        User.objects.create_superuser(
            username=username,
            email=email if email else f"{username}@example.com",
            password=password
        )
        print(f"✅ Superusuario '{username}' creado exitosamente!")
        print(f"   Username: {username}")
        print(f"   Email: {email if email else f'{username}@example.com'}")
        print(f"\n💡 Ahora puedes iniciar sesión en /admin/ con estas credenciales.")
    except Exception as e:
        print(f"❌ Error al crear el superusuario: {str(e)}")

if __name__ == '__main__':
    crear_superusuario()


