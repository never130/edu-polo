from django.apps import AppConfig


class RolesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.modulo_1.roles'

    def ready(self):
        import apps.modulo_1.roles.signals