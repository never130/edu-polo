from django.apps import AppConfig


class InscripcionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.modulo_2.inscripciones'

    def ready(self):
        import apps.modulo_2.inscripciones.signals
