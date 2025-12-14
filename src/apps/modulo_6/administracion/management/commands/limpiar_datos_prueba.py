from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.modulo_3.cursos.models import Curso
from django.db import transaction

class Command(BaseCommand):
    help = 'Elimina usuarios (no admin) y cursos para limpiar el entorno de pruebas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='No pedir confirmación',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('!!! ATENCIÓN: MODO LIMPIEZA DE DATOS !!!'))
        self.stdout.write(self.style.WARNING('Esta acción eliminará:'))
        self.stdout.write(self.style.WARNING('1. Todos los usuarios que NO son superusuarios (Estudiantes, Docentes, etc.)'))
        self.stdout.write(self.style.WARNING('2. Todos los Cursos (y sus comisiones, materiales, inscripciones, etc.)'))
        self.stdout.write(self.style.WARNING('-----------------------------------------------------------------------'))

        if not options['no_input']:
            confirm = input('¿Estás SEGURO de que quieres continuar? Escribe "SI" para confirmar: ')
            if confirm != 'SI':
                self.stdout.write(self.style.ERROR('Operación cancelada.'))
                return

        try:
            with transaction.atomic():
                # 1. Eliminar Cursos
                cursos_count = Curso.objects.count()
                Curso.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✓ Se eliminaron {cursos_count} Cursos (y datos relacionados).'))

                # 2. Eliminar Usuarios (No Superusers)
                # Filtramos para no borrar al admin
                users_to_delete = User.objects.filter(is_superuser=False)
                users_count = users_to_delete.count()
                users_to_delete.delete()
                self.stdout.write(self.style.SUCCESS(f'✓ Se eliminaron {users_count} Usuarios (Estudiantes/Docentes/Staff no admin).'))

                self.stdout.write(self.style.SUCCESS('-----------------------------------------------------------------------'))
                self.stdout.write(self.style.SUCCESS('LIMPIEZA COMPLETADA EXITOSAMENTE'))
                self.stdout.write(self.style.SUCCESS('El sistema está limpio y listo para nuevas pruebas.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error durante la limpieza: {str(e)}'))
