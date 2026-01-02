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
