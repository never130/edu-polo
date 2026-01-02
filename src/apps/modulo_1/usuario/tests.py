from datetime import date

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from apps.modulo_1.roles.models import AutorizadoRetiro, Estudiante, Tutor, TutorEstudiante
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


class TutoresYAutorizadosFlowTests(TestCase):
    def setUp(self):
        self.dni = '87654321'
        self.password = 'pw'
        persona = Persona.objects.create(
            dni=self.dni,
            nombre='Ana',
            apellido='Estudiante',
            correo='ana2@test.com',
            fecha_nacimiento=date(2000, 1, 1),
            ciudad_residencia='Ushuaia',
        )
        self.usuario = Usuario.objects.create(persona=persona, contrasena=self.password)
        self.estudiante = Estudiante.objects.create(usuario=self.usuario, nivel_estudios='SE', institucion_actual='Colegio')
        self.auth_user = User.objects.create_user(username=self.dni, password=self.password)
        self.client.force_login(self.auth_user)

    def test_agregar_autorizado_retiro_sin_tutor_rechaza(self):
        response = self.client.post(
            reverse('usuario:agregar_autorizado_retiro'),
            data={
                'dni': '11222333',
                'nombre': 'Juan',
                'apellido': 'Autorizado',
                'telefono': '2901000000',
                'correo': 'juan@test.com',
                'parentesco': 'otro',
            },
            follow=True,
            secure=True,
        )
        self.assertEqual(response.status_code, 200)
        mensajes = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn('❌ Para agregar autorizados, primero debes registrar al menos un tutor.', mensajes)
        self.assertFalse(AutorizadoRetiro.objects.exists())

    def test_agregar_tutor_y_autorizado_confirmar_y_revocar(self):
        response = self.client.post(
            reverse('usuario:agregar_tutor'),
            data={
                'tutor_dni': '99888777',
                'tutor_nombre': 'Maria',
                'tutor_apellido': 'Tutor',
                'tutor_telefono': '2901999999',
                'tutor_email': 'maria@test.com',
                'parentesco': 'madre',
            },
            follow=True,
            secure=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(TutorEstudiante.objects.filter(estudiante=self.estudiante).exists())

        response = self.client.post(
            reverse('usuario:agregar_autorizado_retiro'),
            data={
                'dni': '11222333',
                'nombre': 'Juan',
                'apellido': 'Autorizado',
                'telefono': '2901000000',
                'correo': 'juan@test.com',
                'parentesco': 'otro',
            },
            follow=True,
            secure=True,
        )
        self.assertEqual(response.status_code, 200)
        autorizado = AutorizadoRetiro.objects.get(estudiante=self.estudiante, dni='11222333')
        self.assertFalse(autorizado.confirmado)
        self.assertFalse(autorizado.revocado)

        response = self.client.post(
            reverse('usuario:confirmar_autorizado_retiro', args=[autorizado.id]),
            follow=True,
            secure=True,
        )
        self.assertEqual(response.status_code, 200)
        autorizado.refresh_from_db()
        self.assertTrue(autorizado.confirmado)
        self.assertIsNotNone(autorizado.confirmado_en)

        response = self.client.post(
            reverse('usuario:revocar_autorizado_retiro', args=[autorizado.id]),
            follow=True,
            secure=True,
        )
        self.assertEqual(response.status_code, 200)
        autorizado.refresh_from_db()
        self.assertTrue(autorizado.revocado)
        self.assertIsNotNone(autorizado.revocado_en)

        response = self.client.post(
            reverse('usuario:confirmar_autorizado_retiro', args=[autorizado.id]),
            follow=True,
            secure=True,
        )
        self.assertEqual(response.status_code, 200)
        mensajes = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn('❌ No podés confirmar un autorizado revocado. Reactivalo primero.', mensajes)

        response = self.client.post(
            reverse('usuario:revocar_autorizado_retiro', args=[autorizado.id]),
            follow=True,
            secure=True,
        )
        self.assertEqual(response.status_code, 200)
        autorizado.refresh_from_db()
        self.assertFalse(autorizado.revocado)
        self.assertIsNone(autorizado.revocado_en)

    def test_menor_no_puede_eliminar_unico_tutor(self):
        self.estudiante.usuario.persona.fecha_nacimiento = date(2015, 1, 1)
        self.estudiante.usuario.persona.save(update_fields=['fecha_nacimiento'])

        tutor_persona = Persona.objects.create(
            dni='55667788',
            nombre='Tito',
            apellido='Tutor',
            correo='tutor@test.com',
            telefono='2901123456',
        )
        tutor_usuario = Usuario.objects.create(persona=tutor_persona, contrasena='x')
        tutor = Tutor.objects.create(
            usuario=tutor_usuario,
            tipo_tutor='PE',
            telefono_contacto='2901123456',
            disponibilidad_horaria='A convenir',
        )
        relacion = TutorEstudiante.objects.create(tutor=tutor, estudiante=self.estudiante, parentesco='tutor_legal')

        response = self.client.post(
            reverse('usuario:eliminar_tutor', args=[relacion.id]),
            follow=True,
            secure=True,
        )
        self.assertEqual(response.status_code, 200)
        mensajes = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn('❌ No puedes eliminar tu único tutor siendo menor de 16 años.', mensajes)
        self.assertTrue(TutorEstudiante.objects.filter(id=relacion.id).exists())
