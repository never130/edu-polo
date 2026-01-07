from django.apps import apps as django_apps
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Inscripcion


@receiver(post_save, sender=Inscripcion)
def asegurar_registro_asistencia(sender, instance, **kwargs):
    if instance.estado != 'confirmado':
        return

    RegistroAsistencia = django_apps.get_model('asistencia', 'RegistroAsistencia')
    RegistroAsistencia.objects.get_or_create(inscripcion=instance)

