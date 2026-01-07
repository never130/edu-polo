from django.core.management.base import BaseCommand

from apps.modulo_2.inscripciones.models import Inscripcion


class Command(BaseCommand):
    help = 'Crea RegistroAsistencia faltantes para inscripciones confirmadas'

    def handle(self, *args, **options):
        RegistroAsistencia = self._get_model_registro()

        qs = Inscripcion.objects.filter(estado='confirmado')
        creados = 0
        existentes = 0

        for inscripcion in qs.iterator():
            _, created = RegistroAsistencia.objects.get_or_create(inscripcion=inscripcion)
            if created:
                creados += 1
            else:
                existentes += 1

        self.stdout.write(f'Registros creados: {creados}')
        self.stdout.write(f'Registros existentes: {existentes}')

    def _get_model_registro(self):
        from django.apps import apps as django_apps

        return django_apps.get_model('asistencia', 'RegistroAsistencia')

