"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from pathlib import Path

from django.core.asgi import get_asgi_application

try:
    from dotenv import load_dotenv
    repo_root_env = Path(__file__).resolve().parent.parent.parent / ".env"
    src_env = Path(__file__).resolve().parent.parent / ".env"
    if repo_root_env.exists():
        load_dotenv(dotenv_path=repo_root_env)
    if src_env.exists():
        load_dotenv(dotenv_path=src_env, override=False)
except ImportError:
    pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_asgi_application()
