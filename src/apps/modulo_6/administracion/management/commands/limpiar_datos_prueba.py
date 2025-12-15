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
                # Importar modelos primero
                from apps.modulo_1.roles.models import Estudiante, Docente, Tutor, TutorEstudiante, UsuarioRol
                from apps.modulo_1.usuario.models import Usuario, Persona
                from apps.modulo_3.docentes.models import Docente as DocentePerfil
                from apps.modulo_3.cursos.models import ComisionDocente, Comision, Material, Curso
                from apps.modulo_2.inscripciones.models import Inscripcion
                from apps.modulo_4.asistencia.models import Asistencia, RegistroAsistencia
                from django.contrib.admin.models import LogEntry
                
                # 1. Limpieza de Módulo Académico (De abajo hacia arriba para evitar FK constraints)
                self.stdout.write('Eliminando Asistencias...')
                # Borrado masivo para evitar signals que intenten actualizar registros de inscripciones que se están borrando
                Asistencia.objects.all().delete()
                
                self.stdout.write('Eliminando Registros de Asistencia...')
                RegistroAsistencia.objects.all().delete()
                
                self.stdout.write('Eliminando Inscripciones...')
                Inscripcion.objects.all().delete()
                
                self.stdout.write('Eliminando Materiales...')
                Material.objects.all().delete()
                
                self.stdout.write('Eliminando Asignaciones Docentes...')
                ComisionDocente.objects.all().delete()
                
                self.stdout.write('Eliminando Comisiones...')
                Comision.objects.all().delete()
                
                self.stdout.write('Eliminando Cursos...')
                cursos_count = Curso.objects.count()
                Curso.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✓ Se eliminaron {cursos_count} Cursos (y datos relacionados).'))

                # 2. Eliminar Usuarios (No Superusers)
                # Filtramos para no borrar al admin
                users_to_delete = User.objects.filter(is_superuser=False)
                
                # Obtener los DNIs de los usuarios a borrar para limpiar las tablas personalizadas
                dnis_to_delete = list(users_to_delete.values_list('username', flat=True))
                
                # 3. Eliminar relaciones Tutor-Estudiante
                TutorEstudiante.objects.all().delete()
                
                # 4. Eliminar Tutores, Estudiantes, Docentes
                # Filtramos por usuarios que vamos a borrar
                usuarios_app = Usuario.objects.filter(persona__dni__in=dnis_to_delete)

                # Eliminar LogEntry asociados a los usuarios de Django
                LogEntry.objects.filter(user__in=users_to_delete).delete()

                # Eliminar Perfiles de Docente (Módulo 3) que apuntan a Usuario
                DocentePerfil.objects.filter(usuario__in=usuarios_app).delete()
                
                # Eliminar solo los roles (Estudiante/Tutor) y Usuario de App
                
                # Eliminar Estudiantes (el rol de estudiante y sus datos académicos)
                Estudiante.objects.filter(usuario__in=usuarios_app).delete()
                
                # Eliminar Tutores y relaciones
                Tutor.objects.filter(usuario__in=usuarios_app).delete()
                
                # Eliminar vinculación de roles en tabla intermedia
                UsuarioRol.objects.filter(usuario_id__in=usuarios_app).delete()
                
                # 5. Eliminar Usuarios de la App y Usuarios de Django (Login)
                # MANTENIENDO LA PERSONA FÍSICA
                usuarios_app.delete()
                
                # 6. Eliminar Personas huérfanas (que no tienen Usuario asociado)
                # OJO: No borrar Personas que estén vinculadas a Superusuarios
                
                # Obtener DNIs de superusuarios
                superusers_dnis = User.objects.filter(is_superuser=True).values_list('username', flat=True)
                
                # Borrar Personas que NO son de superusuarios
                # Como ya borramos los Usuarios de App de los no-superusers, estas personas ya no tienen usuario_app asociado
                # Pero filtramos por si acaso para no borrar la persona del admin
                
                personas_borradas = Persona.objects.exclude(dni__in=superusers_dnis).delete()
                self.stdout.write(self.style.SUCCESS(f'✓ Se eliminaron Personas huérfanas: {personas_borradas}'))
                
                # 7. Eliminar usuarios de Django (auth_user)
                users_to_delete.delete()
                self.stdout.write(self.style.SUCCESS(f'✓ Se eliminaron usuarios de sistema.'))

                # 8. Reiniciar secuencias de IDs (Autoincrement) en SQLite
                self.stdout.write('Reiniciando contadores de IDs...')
                from django.db import connection
                with connection.cursor() as cursor:
                    # Lista de tablas a reiniciar
                    tablas = [
                        'cursos_comision',
                        'cursos_curso',
                        'inscripciones_inscripcion',
                        'roles_estudiante',
                        'roles_tutor',
                        'roles_tutorestudiante',
                        'usuario_usuario',
                        'usuario_persona',
                        'asistencia_asistencia',
                        'asistencia_registroasistencia',
                        'cursos_material',
                        'cursos_comisiondocente',
                        'docentes_docente',
                        'roles_usuariorol'
                    ]
                    for tabla in tablas:
                        try:
                            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{tabla}';")
                        except Exception:
                            pass # Ignorar si la tabla no está en sqlite_sequence
                self.stdout.write(self.style.SUCCESS(f'✓ Se reiniciaron los contadores de IDs.'))

                self.stdout.write(self.style.SUCCESS('-----------------------------------------------------------------------'))
                self.stdout.write(self.style.SUCCESS('LIMPIEZA COMPLETADA EXITOSAMENTE'))
                self.stdout.write(self.style.SUCCESS('El sistema está limpio y listo para nuevas pruebas.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error durante la limpieza: {str(e)}'))
