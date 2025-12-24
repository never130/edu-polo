#!/usr/bin/env python
"""Script para probar que el servidor Django puede iniciarse"""
import os
import sys
import django

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    sys.path.insert(0, os.path.dirname(__file__))

    try:
        django.setup()
        print("✅ Django configurado correctamente")

        from django.core.management import execute_from_command_line
        print("✅ Management commands disponibles")

        print("\n🚀 Iniciando servidor...")
        print("=" * 50)
        execute_from_command_line(['manage.py', 'runserver', '127.0.0.1:8000'])
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()



