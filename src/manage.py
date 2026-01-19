#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def main():
    """Run administrative tasks."""
    # Cargar variables de entorno desde .env si existe
    try:
        from dotenv import load_dotenv
        repo_root_env = Path(__file__).resolve().parent.parent / ".env"
        src_env = Path(__file__).resolve().parent / ".env"
        if repo_root_env.exists():
            load_dotenv(dotenv_path=repo_root_env)
        if src_env.exists():
            load_dotenv(dotenv_path=src_env, override=False)
    except ImportError:
        pass

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
