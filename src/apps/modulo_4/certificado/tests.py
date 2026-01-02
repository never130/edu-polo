from datetime import date
from unittest.mock import patch

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from apps.modulo_1.roles.models import Estudiante
from apps.modulo_1.usuario.models import Persona, Usuario
from apps.modulo_2.inscripciones.models import Inscripcion
from apps.modulo_3.cursos.models import Comision, Curso, PoloCreativo
from apps.modulo_4.asistencia.models import Asistencia, RegistroAsistencia


class CertificadosTests(TestCase):
    def setUp(self):
        self.password = 'pw'
        self.dni = '82000000'
        persona = Persona.objects.create(
            dni=self.dni,
            nombre='Ana',
            apellido='Test',
            correo='ana@test.com',
            fecha_nacimiento=date(2000, 1, 1),
            ciudad_residencia='Ushuaia',
        )
        self.usuario = Usuario.objects.create(persona=persona, contrasena=self.password)
        self.estudiante = Estudiante.objects.create(usuario=self.usuario, nivel_estudios='SE', institucion_actual='Colegio')

        self.polo = PoloCreativo.objects.create(nombre='Polo', ciudad='Ushuaia', direccion='Test', activo=True)
        self.curso = Curso.objects.create(nombre='Curso', estado='Abierto', orden=1)
        self.comision = Comision.objects.create(
            fk_id_curso=self.curso,
            fk_id_polo=self.polo,
            dias_horarios='Lunes y Miércoles 18:00 - 21:00',
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 1, 8),
            estado='Finalizada',
            cupo_maximo=10,
        )
        self.inscripcion = Inscripcion.objects.create(estudiante=self.estudiante, comision=self.comision, estado='confirmado')

        self.assertTrue(self.client.login(username=self.dni, password=self.password))

    def test_url_mis_certificados_existe(self):
        self.assertTrue(reverse('usuario:mis_certificados'))

    def test_descargar_certificado_sin_reportlab_redirige_a_mis_certificados(self):
        with patch('apps.modulo_1.usuario.views_progreso.REPORTLAB_AVAILABLE', False):
            response = self.client.get(
                reverse('usuario:descargar_certificado', args=[self.inscripcion.id]),
                follow=True,
                secure=True,
            )
        self.assertEqual(response.status_code, 200)
        mensajes = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn('❌ La funcionalidad de certificados PDF no está disponible. Por favor, contacta al administrador.', mensajes)

    def test_mis_certificados_no_muestra_registros_si_no_cumple(self):
        response = self.client.get(reverse('usuario:mis_certificados'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Aún no tienes certificados disponibles')

    def test_mis_certificados_muestra_curso_si_cumple_requisito(self):
        Asistencia.objects.create(inscripcion=self.inscripcion, fecha_clase=date(2025, 1, 1), presente=True)
        registro, _ = RegistroAsistencia.objects.get_or_create(inscripcion=self.inscripcion)
        registro.calcular_porcentaje()

        response = self.client.get(reverse('usuario:mis_certificados'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.curso.nombre)

    def test_descargar_certificado_rechaza_si_no_cumple_y_comision_no_finalizo(self):
        comision_futura = Comision.objects.create(
            fk_id_curso=self.curso,
            fk_id_polo=self.polo,
            dias_horarios='Miércoles 10:00 - 12:00',
            fecha_inicio=date(2099, 1, 1),
            fecha_fin=date(2099, 1, 1),
            estado='En proceso',
            cupo_maximo=10,
        )
        inscripcion_futura = Inscripcion.objects.create(estudiante=self.estudiante, comision=comision_futura, estado='confirmado')

        with patch('apps.modulo_1.usuario.views_progreso.REPORTLAB_AVAILABLE', True):
            response = self.client.get(
                reverse('usuario:descargar_certificado', args=[inscripcion_futura.id]),
                follow=True,
                secure=True,
            )
        self.assertEqual(response.status_code, 200)
        mensajes = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn('❌ El certificado se habilita al finalizar la comisión.', mensajes)

    def test_descargar_certificado_rechaza_si_no_cumple_y_comision_finalizo(self):
        with patch('apps.modulo_1.usuario.views_progreso.REPORTLAB_AVAILABLE', True):
            response = self.client.get(
                reverse('usuario:descargar_certificado', args=[self.inscripcion.id]),
                follow=True,
                secure=True,
            )
        self.assertEqual(response.status_code, 200)
        mensajes = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn('❌ No cumples con el requisito mínimo de 80% de asistencia para obtener el certificado.', mensajes)
