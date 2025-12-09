import os
import sys
import django

def create_superuser():
    # Asegurarse de que estamos en el directorio correcto para importar módulos
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_dir)
    
    # Configurar Django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    try:
        django.setup()
    except Exception as e:
        print(f"Error setting up Django: {e}")
        return

    from django.contrib.auth import get_user_model
    User = get_user_model()

    username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

    if not username or not password:
        # No se proporcionaron credenciales, no hacemos nada
        return

    try:
        if User.objects.filter(username=username).exists():
            print(f"Superuser '{username}' already exists. Skipping creation.")
        else:
            print(f"Creating superuser '{username}'...")
            User.objects.create_superuser(username=username, email=email, password=password)
            print(f"Superuser '{username}' created successfully.")
    except Exception as e:
        print(f"Error creating superuser: {e}")

if __name__ == "__main__":
    create_superuser()
