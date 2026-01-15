from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.modulo_1.roles.models import Estudiante
from apps.modulo_1.usuario.models import Persona, Usuario
from apps.modulo_2.inscripciones.models import Inscripcion
from apps.modulo_3.cursos.models import Comision, Curso, PoloCreativo


class InscripcionesFlowTests(TestCase):
    def setUp(self):
        self.polo = PoloCreativo.objects.create(
            nombre='Polo Test',
            ciudad='Ushuaia',
            direccion='Test 123',
            activo=True,
        )
        self.curso = Curso.objects.create(nombre='Curso Test', estado='Abierto', orden=1)
        self.comision = Comision.objects.create(
            fk_id_curso=self.curso,
            fk_id_polo=self.polo,
            dias_horarios='Miércoles 10:00 - 12:00',
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 1, 1),
            estado='Abierta',
            cupo_maximo=2,
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
        self.auth_user = User.objects.create_user(username=self.persona.dni, password='x')
        self.client.force_login(self.auth_user)

    def test_formulario_crea_preinscripcion_cuando_hay_cupo(self):
        response = self.client.post(
            reverse('inscripciones:formulario', args=[self.comision.id_comision]),
            data={},
            secure=True,
        )
        self.assertEqual(response.status_code, 302)

        inscripcion = Inscripcion.objects.get(estudiante=self.estudiante, comision=self.comision)
        self.assertEqual(inscripcion.estado, 'pre_inscripto')
        self.assertIsNone(inscripcion.orden_lista_espera)

    def test_formulario_crea_lista_espera_con_orden_cuando_no_hay_cupo(self):
        self.comision.cupo_maximo = 0
        self.comision.save(update_fields=['cupo_maximo'])

        response = self.client.post(
            reverse('inscripciones:formulario', args=[self.comision.id_comision]),
            data={},
            secure=True,
        )
        self.assertEqual(response.status_code, 302)

        inscripcion = Inscripcion.objects.get(estudiante=self.estudiante, comision=self.comision)
        self.assertEqual(inscripcion.estado, 'lista_espera')
        self.assertEqual(inscripcion.orden_lista_espera, 1)

    def test_cancelar_inscripcion_cambia_estado_a_cancelada(self):
        inscripcion = Inscripcion.objects.create(estudiante=self.estudiante, comision=self.comision, estado='confirmado')

        response = self.client.post(
            reverse('inscripciones:cancelar', args=[inscripcion.id]),
            secure=True,
        )
        self.assertEqual(response.status_code, 302)

        inscripcion.refresh_from_db()
        self.assertEqual(inscripcion.estado, 'cancelada')

    def test_confirmado_en_comision_finalizada_puede_inscribirse_a_nueva_comision_mismo_curso(self):
        comision_pasada = Comision.objects.create(
            fk_id_curso=self.curso,
            fk_id_polo=self.polo,
            dias_horarios='Miércoles 10:00 - 12:00',
            fecha_inicio=date(2020, 1, 5),
            fecha_fin=date(2020, 1, 16),
            estado='En proceso',
            cupo_maximo=2,
        )
        comision_nueva = Comision.objects.create(
            fk_id_curso=self.curso,
            fk_id_polo=self.polo,
            dias_horarios='Miércoles 10:00 - 12:00',
            fecha_inicio=date(2026, 1, 19),
            fecha_fin=date(2026, 1, 30),
            estado='Abierta',
            cupo_maximo=2,
        )
        Inscripcion.objects.create(estudiante=self.estudiante, comision=comision_pasada, estado='confirmado')

        response = self.client.post(
            reverse('inscripciones:formulario', args=[comision_nueva.id_comision]),
            data={},
            secure=True,
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('cursos:mis_inscripciones'))
        self.assertTrue(Inscripcion.objects.filter(estudiante=self.estudiante, comision=comision_nueva).exists())

    def test_confirmado_en_comision_vigente_puede_inscribirse_a_nueva_comision_mismo_curso_si_no_se_solapa(self):
        comision_vigente = Comision.objects.create(
            fk_id_curso=self.curso,
            fk_id_polo=self.polo,
            dias_horarios='Miércoles 10:00 - 12:00',
            fecha_inicio=date(2099, 1, 5),
            fecha_fin=date(2099, 1, 16),
            estado='Abierta',
            cupo_maximo=2,
        )
        comision_nueva = Comision.objects.create(
            fk_id_curso=self.curso,
            fk_id_polo=self.polo,
            dias_horarios='Miércoles 10:00 - 12:00',
            fecha_inicio=date(2099, 1, 19),
            fecha_fin=date(2099, 1, 30),
            estado='Abierta',
            cupo_maximo=2,
        )
        Inscripcion.objects.create(estudiante=self.estudiante, comision=comision_vigente, estado='confirmado')

        response = self.client.post(
            reverse('inscripciones:formulario', args=[comision_nueva.id_comision]),
            data={},
            secure=True,
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('cursos:mis_inscripciones'))
        self.assertTrue(Inscripcion.objects.filter(estudiante=self.estudiante, comision=comision_nueva).exists())

    def test_confirmado_en_comision_sin_fechas_puede_inscribirse_a_otra_mismo_curso(self):
        comision_sin_fechas = Comision.objects.create(
            fk_id_curso=self.curso,
            fk_id_polo=self.polo,
            dias_horarios='Miércoles 10:00 - 12:00',
            estado='En proceso',
            cupo_maximo=2,
        )
        comision_nueva = Comision.objects.create(
            fk_id_curso=self.curso,
            fk_id_polo=self.polo,
            dias_horarios='Miércoles 10:00 - 12:00',
            fecha_inicio=date(2099, 1, 19),
            fecha_fin=date(2099, 1, 30),
            estado='Abierta',
            cupo_maximo=2,
        )
        Inscripcion.objects.create(estudiante=self.estudiante, comision=comision_sin_fechas, estado='confirmado')

        response = self.client.post(
            reverse('inscripciones:formulario', args=[comision_nueva.id_comision]),
            data={},
            secure=True,
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('cursos:mis_inscripciones'))
        self.assertTrue(Inscripcion.objects.filter(estudiante=self.estudiante, comision=comision_nueva).exists())

    def test_confirmado_en_comision_que_se_solapa_no_puede_inscribirse_a_otra_mismo_curso(self):
        comision_a = Comision.objects.create(
            fk_id_curso=self.curso,
            fk_id_polo=self.polo,
            dias_horarios='Miércoles 10:00 - 12:00',
            fecha_inicio=date(2099, 1, 5),
            fecha_fin=date(2099, 1, 16),
            estado='Abierta',
            cupo_maximo=2,
        )
        comision_b = Comision.objects.create(
            fk_id_curso=self.curso,
            fk_id_polo=self.polo,
            dias_horarios='Miércoles 10:00 - 12:00',
            fecha_inicio=date(2099, 1, 10),
            fecha_fin=date(2099, 1, 30),
            estado='Abierta',
            cupo_maximo=2,
        )
        Inscripcion.objects.create(estudiante=self.estudiante, comision=comision_a, estado='confirmado')

        response = self.client.post(
            reverse('inscripciones:formulario', args=[comision_b.id_comision]),
            data={},
            secure=True,
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('landing'))
        self.assertFalse(Inscripcion.objects.filter(estudiante=self.estudiante, comision=comision_b).exists())
