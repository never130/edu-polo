from django.apps import AppConfig


class AsistenciaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.modulo_4.asistencia'
    
    def ready(self):
        """Importa las señales cuando la aplicación está lista"""
        import apps.modulo_4.asistencia.signals