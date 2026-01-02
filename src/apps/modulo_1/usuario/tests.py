from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.modulo_1.roles.models import Estudiante
from apps.modulo_1.usuario.models import Persona, Usuario
from apps.modulo_2.inscripciones.models import Inscripcion
from apps.modulo_3.cursos.models import Comision, Curso, PoloCreativo
from apps.modulo_4.asistencia.models import Asistencia, RegistroAsistencia


class ProgresoEstudianteTests(TestCase):
    def setUp(self):
        self.polo = PoloCreativo.objects.create(
            nombre='Polo Test',
            ciudad='Ushuaia',
            direccion='Test 123',
            activo=True,
        )
        self.curso = Curso.objects.create(nombre='Curso Test', estado='Abierto', orden=1)

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
        self.auth_user = User.objects.create_user(username=self.persona.dni, password='x')
        self.client.force_login(self.auth_user)

    def test_mi_progreso_sin_asistencias_calcula_0_sobre_total_programado(self):
        comision = Comision.objects.create(
            fk_id_curso=self.curso,
            fk_id_polo=self.polo,
            dias_horarios='Miércoles 10:00 - 12:00',
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 1, 1),
            estado='Finalizada',
        )
        Inscripcion.objects.create(estudiante=self.estudiante, comision=comision, estado='confirmado')

        response = self.client.get(reverse('usuario:mi_progreso'), secure=True)
        self.assertEqual(response.status_code, 200)

        inscripciones = list(response.context['inscripciones'])
        self.assertEqual(len(inscripciones), 1)
        self.assertEqual(inscripciones[0].progreso, 0)
        self.assertEqual(inscripciones[0].total_clases, 1)
        self.assertEqual(inscripciones[0].asistencias_count, 0)
        self.assertFalse(inscripciones[0].cumple_certificado)

    def test_mi_progreso_con_asistencia_calcula_100_y_habilita_certificado(self):
        comision = Comision.objects.create(
            fk_id_curso=self.curso,
            fk_id_polo=self.polo,
            dias_horarios='Miércoles 10:00 - 12:00',
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 1, 1),
            estado='Finalizada',
        )
        inscripcion = Inscripcion.objects.create(estudiante=self.estudiante, comision=comision, estado='confirmado')
        Asistencia.objects.create(
            inscripcion=inscripcion,
            fecha_clase=date(2025, 1, 1),
            presente=True,
        )

        response = self.client.get(reverse('usuario:mi_progreso'), secure=True)
        self.assertEqual(response.status_code, 200)

        inscripciones = list(response.context['inscripciones'])
        self.assertEqual(len(inscripciones), 1)
        self.assertEqual(inscripciones[0].progreso, 100)
        self.assertEqual(inscripciones[0].total_clases, 1)
        self.assertEqual(inscripciones[0].asistencias_count, 1)
        self.assertTrue(inscripciones[0].cumple_certificado)

        registro = RegistroAsistencia.objects.get(inscripcion=inscripcion)
        self.assertEqual(registro.total_clases, 1)
        self.assertEqual(registro.clases_asistidas, 1)

    def test_mi_progreso_parcial_calcula_porcentaje_en_base_a_clases_programadas(self):
        comision = Comision.objects.create(
            fk_id_curso=self.curso,
            fk_id_polo=self.polo,
            dias_horarios='Lunes y Miércoles 10:00 - 12:00',
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 1, 6),
            estado='Finalizada',
        )
        inscripcion = Inscripcion.objects.create(estudiante=self.estudiante, comision=comision, estado='confirmado')
        Asistencia.objects.create(
            inscripcion=inscripcion,
            fecha_clase=date(2025, 1, 1),
            presente=True,
        )

        response = self.client.get(reverse('usuario:mi_progreso'), secure=True)
        self.assertEqual(response.status_code, 200)

        inscripciones = list(response.context['inscripciones'])
        self.assertEqual(len(inscripciones), 1)
        self.assertEqual(inscripciones[0].progreso, 50)
        self.assertFalse(inscripciones[0].cumple_certificado)
