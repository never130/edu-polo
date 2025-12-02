# -*- coding: utf-8 -*-
"""
Script para crear el rol "Mesa de Entrada" en la base de datos
Ejecutar: python src/manage.py shell
Luego: from apps.modulo_1.roles.models import Rol; rol, created = Rol.objects.get_or_create(nombre='Mesa de Entrada', defaults={'descripcion': 'Rol para personal de mesa de entrada', 'jerarquia': 2}); print('Creado' if created else 'Ya existe')
"""
import os
import sys
import django

# Agregar el directorio src al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.modulo_1.roles.models import Rol

# Crear el rol "Mesa de Entrada"
rol, created = Rol.objects.get_or_create(
    nombre='Mesa de Entrada',
    defaults={
        'descripcion': 'Rol para personal de mesa de entrada. Puede gestionar cursos, comisiones, inscripciones y usuarios (excepto crear nuevos usuarios).',
        'jerarquia': 2
    }
)

if created:
    print('Rol "Mesa de Entrada" creado exitosamente con jerarquia 2')
else:
    print('El rol "Mesa de Entrada" ya existe')

print(f'Nombre: {rol.nombre}')
print(f'Descripcion: {rol.descripcion}')
print(f'Jerarquia: {rol.jerarquia}')
