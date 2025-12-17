from datetime import date

from django.test import TestCase

from apps.modulo_1.usuario.models import Persona, Usuario
from apps.modulo_1.roles.models import Estudiante
from apps.modulo_2.inscripciones.models import Inscripcion
from apps.modulo_3.cursos.models import Curso, Comision, PoloCreativo
from apps.modulo_4.asistencia.models import Asistencia, RegistroAsistencia


class AsistenciaProgramacionTests(TestCase):
    def setUp(self):
        self.polo = PoloCreativo.objects.create(
            nombre='Polo Test',
            ciudad='Ushuaia',
            direccion='Test 123',
            activo=True,
        )
        self.curso = Curso.objects.create(nombre='Curso Test')
        self.comision = Comision.objects.create(
            fk_id_curso=self.curso,
            fk_id_polo=self.polo,
            dias_horarios='Lunes y Miércoles 18:00 - 21:00',
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 1, 8),
        )

        self.persona = Persona.objects.create(
            dni='12345678',
            nombre='Ana',
            apellido='Test',
            correo='ana@test.com',
        )
        self.usuario = Usuario.objects.create(persona=self.persona, contrasena='x')
        self.estudiante = Estudiante.objects.create(
            usuario=self.usuario,
            nivel_estudios='SE',
            institucion_actual='Colegio',
        )
        self.inscripcion = Inscripcion.objects.create(estudiante=self.estudiante, comision=self.comision)

    def test_total_clases_programadas(self):
        self.assertEqual(self.comision.get_total_clases_programadas(), 3)

    def test_asistencia_valida_dia(self):
        asistencia = Asistencia.objects.create(
            inscripcion=self.inscripcion,
            fecha_clase=date(2025, 1, 1),
            presente=True,
        )
        self.assertIsNotNone(asistencia.id_asistencia)

    def test_asistencia_invalida_dia(self):
        with self.assertRaises(Exception):
            Asistencia.objects.create(
                inscripcion=self.inscripcion,
                fecha_clase=date(2025, 1, 2),
                presente=True,
            )

    def test_registro_asistencia_usa_programacion(self):
        Asistencia.objects.create(inscripcion=self.inscripcion, fecha_clase=date(2025, 1, 1), presente=True)
        registro, _ = RegistroAsistencia.objects.get_or_create(inscripcion=self.inscripcion)
        registro.calcular_porcentaje()
        self.assertEqual(registro.total_clases, 3)
        self.assertEqual(registro.clases_asistidas, 1)
