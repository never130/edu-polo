import re
from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.modulo_1.roles.models import Estudiante
from apps.modulo_1.usuario.models import Persona, Usuario
from apps.modulo_2.inscripciones.models import Inscripcion
from apps.modulo_3.cursos.models import Comision, Curso, PoloCreativo


class CursosViewsTests(TestCase):
    def setUp(self):
        self.polo = PoloCreativo.objects.create(
            nombre='Polo Test',
            ciudad='Ushuaia',
            direccion='Test 123',
            activo=True,
        )
        self.curso_abierto = Curso.objects.create(nombre='Curso Abierto', estado='Abierto', orden=1)
        self.curso_cerrado = Curso.objects.create(nombre='Curso Cerrado', estado='Cerrado', orden=2)

        self.comision_1 = Comision.objects.create(
            fk_id_curso=self.curso_abierto,
            fk_id_polo=self.polo,
            dias_horarios='Lunes y Miércoles 18:00 - 21:00',
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 1, 8),
            estado='Abierta',
        )
        self.comision_2 = Comision.objects.create(
            fk_id_curso=self.curso_abierto,
            fk_id_polo=self.polo,
            dias_horarios='Lunes y Miércoles 18:00 - 21:00',
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 1, 8),
            estado='Cerrada',
        )

        self.persona = Persona.objects.create(
            dni='12345678',
            nombre='Ana',
            apellido='Test',
            correo='ana@test.com',
            ciudad_residencia='Ushuaia',
        )
        self.usuario = Usuario.objects.create(persona=self.persona, contrasena='x')
        self.estudiante = Estudiante.objects.create(
            usuario=self.usuario,
            nivel_estudios='SE',
            institucion_actual='Colegio',
        )
        self.auth_user = User.objects.create_user(username=self.persona.dni, password='x')
        self.client.force_login(self.auth_user)

    def test_curso_list_view_filtra_abiertos_y_agrega_comisiones_abiertas(self):
        url = reverse('cursos:lista')
        response = self.client.get(url, secure=True)
        self.assertEqual(response.status_code, 200)

        cursos = list(response.context['cursos'])
        self.assertEqual([c.nombre for c in cursos], ['Curso Abierto'])

        curso = cursos[0]
        comisiones_abiertas = list(curso.comisiones_abiertas)
        self.assertEqual([c.id_comision for c in comisiones_abiertas], [self.comision_1.id_comision])

    def test_mis_inscripciones_muestra_confirmadas_y_oculta_canceladas(self):
        Inscripcion.objects.create(estudiante=self.estudiante, comision=self.comision_1, estado='confirmado')
        Inscripcion.objects.create(
            estudiante=self.estudiante,
            comision=Comision.objects.create(
                fk_id_curso=self.curso_abierto,
                fk_id_polo=self.polo,
                dias_horarios='Lunes y Miércoles 18:00 - 21:00',
                fecha_inicio=date(2025, 1, 1),
                fecha_fin=date(2025, 1, 8),
                estado='Abierta',
            ),
            estado='cancelada',
        )

        url = reverse('cursos:mis_inscripciones')
        response = self.client.get(url, secure=True)
        self.assertEqual(response.status_code, 200)
        inscripciones = list(response.context['inscripciones'])
        self.assertEqual(len(inscripciones), 1)
        self.assertEqual(inscripciones[0].estado, 'confirmado')

    def test_cursos_por_polo_comisiones_abiertas_excluye_cupo_lleno(self):
        curso_lleno = Curso.objects.create(nombre='Curso Cupo Lleno', estado='Abierto', orden=3)
        comision_llena = Comision.objects.create(
            fk_id_curso=curso_lleno,
            fk_id_polo=self.polo,
            dias_horarios='Martes 10:00 - 12:00',
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 1, 8),
            estado='Abierta',
            cupo_maximo=1,
        )
        Inscripcion.objects.create(estudiante=self.estudiante, comision=comision_llena, estado='confirmado')

        url = reverse('cursos_por_polo', args=[self.polo.id_polo])
        response = self.client.get(url, secure=True)
        self.assertEqual(response.status_code, 200)

        cursos = list(response.context['cursos'])
        curso_ctx = next(c for c in cursos if c.nombre == 'Curso Cupo Lleno')
        self.assertEqual(list(curso_ctx.comisiones_abiertas), [])

        html = response.content.decode('utf-8')
        pattern = r"Curso Cupo Lleno[\s\S]*?Abiertas:\s*0"
        self.assertRegex(html, pattern)

        pattern = rf"#{comision_llena.id_comision}[\s\S]*?>Cerrada<"
        self.assertRegex(html, pattern)

    def test_ver_cursos_disponibles_html_badges_y_botones(self):
        curso = Curso.objects.create(nombre='Curso UI', estado='Abierto', orden=10)
        comision_llena = Comision.objects.create(
            fk_id_curso=curso,
            fk_id_polo=self.polo,
            dias_horarios='Martes 10:00 - 12:00',
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 1, 8),
            estado='Abierta',
            cupo_maximo=1,
        )
        Inscripcion.objects.create(estudiante=self.estudiante, comision=comision_llena, estado='confirmado')

        comision_ok = Comision.objects.create(
            fk_id_curso=curso,
            fk_id_polo=self.polo,
            dias_horarios='Jueves 10:00 - 12:00',
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 1, 8),
            estado='Abierta',
            cupo_maximo=1,
        )

        response = self.client.get(reverse('cursos:ver_disponibles'), secure=True)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')

        pattern = rf"#{comision_llena.id_comision}\s*-\s*[\s\S]*?Cerrada[\s\S]*?Disponibles:\s*0/1[\s\S]*?Cupo lleno"
        self.assertRegex(html, pattern)

        pattern = rf"#{comision_ok.id_comision}\s*-\s*[\s\S]*?Abierta[\s\S]*?Disponibles:\s*1/1[\s\S]*?Inscribirme"
        self.assertRegex(html, pattern)
