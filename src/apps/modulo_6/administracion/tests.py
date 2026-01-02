from datetime import date

from django.db import transaction
from django.test import TestCase
from django.urls import reverse

from apps.modulo_1.roles.models import Estudiante, Rol, UsuarioRol
from apps.modulo_1.usuario.models import Persona, Usuario
from apps.modulo_2.inscripciones.models import Inscripcion
from apps.modulo_3.cursos.models import Comision, Curso, PoloCreativo
from apps.modulo_4.asistencia.models import Asistencia
from apps.modulo_6.administracion.views import _normalizar_cupos_y_espera


class NormalizacionCuposTests(TestCase):
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
            cupo_maximo=1,
        )

    def _crear_estudiante(self, dni):
        persona = Persona.objects.create(
            dni=dni,
            nombre='Ana',
            apellido=dni,
            correo=f'{dni}@test.com',
        )
        usuario = Usuario.objects.create(persona=persona, contrasena='x')
        return Estudiante.objects.create(usuario=usuario, nivel_estudios='SE', institucion_actual='Colegio')

    def test_normalizar_mueve_excedente_preinscripto_a_lista_espera(self):
        e1 = self._crear_estudiante('11111111')
        e2 = self._crear_estudiante('22222222')

        i1 = Inscripcion.objects.create(estudiante=e1, comision=self.comision, estado='pre_inscripto')
        i2 = Inscripcion.objects.create(estudiante=e2, comision=self.comision, estado='pre_inscripto')

        with transaction.atomic():
            comision_locked = Comision.objects.select_for_update().get(pk=self.comision.pk)
            _normalizar_cupos_y_espera(comision_locked)

        i1.refresh_from_db()
        i2.refresh_from_db()

        self.assertIn(i1.estado, ['pre_inscripto', 'lista_espera'])
        self.assertIn(i2.estado, ['pre_inscripto', 'lista_espera'])
        self.assertNotEqual(i1.estado, i2.estado)
        moved = i1 if i1.estado == 'lista_espera' else i2
        kept = i2 if moved is i1 else i1
        self.assertEqual(moved.orden_lista_espera, 1)
        self.assertIsNone(kept.orden_lista_espera)


class InscribirEstudianteAdminTests(TestCase):
    def setUp(self):
        self.polo_ushuaia = PoloCreativo.objects.create(
            nombre='Polo Ushuaia',
            ciudad='Ushuaia',
            direccion='Test 123',
            activo=True,
        )
        self.polo_rg = PoloCreativo.objects.create(
            nombre='Polo Rio Grande',
            ciudad='Rio Grande',
            direccion='Test 456',
            activo=True,
        )
        self.curso = Curso.objects.create(nombre='Curso Test', estado='Abierto', orden=1)
        self.comision_ushuaia = Comision.objects.create(
            fk_id_curso=self.curso,
            fk_id_polo=self.polo_ushuaia,
            dias_horarios='Miércoles 10:00 - 12:00',
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 1, 1),
            estado='Abierta',
            cupo_maximo=1,
        )
        self.comision_rg = Comision.objects.create(
            fk_id_curso=self.curso,
            fk_id_polo=self.polo_rg,
            dias_horarios='Miércoles 10:00 - 12:00',
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 1, 1),
            estado='Abierta',
            cupo_maximo=1,
        )
        self.url_inscribir = reverse('administracion:inscribir_estudiante')
        self.url_panel = reverse('administracion:panel_inscripciones')

        self.admin_password = 'adminpass'
        self.admin_usuario = self._crear_usuario(dni='90000000', password=self.admin_password, ciudad='Ushuaia')
        self._asignar_rol(self.admin_usuario, nombre_rol='Administrador', jerarquia=1)
        self.assertTrue(self.client.login(username='90000000', password=self.admin_password))

    def _crear_usuario(self, dni, password, ciudad):
        persona = Persona.objects.create(
            dni=dni,
            nombre='Nombre',
            apellido=dni,
            correo=f'{dni}@test.com',
            ciudad_residencia=ciudad,
            fecha_nacimiento=date(2000, 1, 1),
        )
        return Usuario.objects.create(persona=persona, contrasena=password)

    def _crear_estudiante(self, dni, ciudad='Ushuaia'):
        usuario = self._crear_usuario(dni=dni, password='pw', ciudad=ciudad)
        return Estudiante.objects.create(usuario=usuario, nivel_estudios='SE', institucion_actual='Colegio')

    def _asignar_rol(self, usuario, nombre_rol, jerarquia):
        rol, _ = Rol.objects.get_or_create(
            nombre=nombre_rol,
            defaults={'descripcion': nombre_rol, 'jerarquia': jerarquia},
        )
        UsuarioRol.objects.get_or_create(usuario_id=usuario, rol_id=rol)

    def test_confirmar_preinscripto_cuando_hay_cupo(self):
        estudiante = self._crear_estudiante('11111111')
        inscripcion = Inscripcion.objects.create(estudiante=estudiante, comision=self.comision_ushuaia, estado='pre_inscripto')

        response = self.client.post(
            self.url_inscribir,
            data={
                'estudiante_id': estudiante.id,
                'comision_id': self.comision_ushuaia.id_comision,
                'next': 'administracion:panel_inscripciones',
            },
            secure=True,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.url_panel)

        inscripcion.refresh_from_db()
        self.assertEqual(inscripcion.estado, 'confirmado')
        self.assertIsNone(inscripcion.orden_lista_espera)

    def test_preinscripto_no_se_confirma_si_cupo_ya_lleno(self):
        estudiante_confirmado = self._crear_estudiante('22222222')
        Inscripcion.objects.create(estudiante=estudiante_confirmado, comision=self.comision_ushuaia, estado='confirmado')

        estudiante = self._crear_estudiante('33333333')
        inscripcion = Inscripcion.objects.create(estudiante=estudiante, comision=self.comision_ushuaia, estado='pre_inscripto')

        response = self.client.post(
            self.url_inscribir,
            data={
                'estudiante_id': estudiante.id,
                'comision_id': self.comision_ushuaia.id_comision,
                'next': 'administracion:panel_inscripciones',
            },
            secure=True,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.url_panel)

        inscripcion.refresh_from_db()
        self.assertEqual(inscripcion.estado, 'lista_espera')
        self.assertEqual(inscripcion.orden_lista_espera, 1)

    def test_confirmar_lista_espera_cuando_hay_cupo(self):
        estudiante = self._crear_estudiante('44444444')
        inscripcion = Inscripcion.objects.create(
            estudiante=estudiante,
            comision=self.comision_ushuaia,
            estado='lista_espera',
            orden_lista_espera=1,
        )

        response = self.client.post(
            self.url_inscribir,
            data={
                'estudiante_id': estudiante.id,
                'comision_id': self.comision_ushuaia.id_comision,
                'next': 'administracion:panel_inscripciones',
            },
            secure=True,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.url_panel)

        inscripcion.refresh_from_db()
        self.assertEqual(inscripcion.estado, 'confirmado')
        self.assertIsNone(inscripcion.orden_lista_espera)

    def test_si_ya_esta_confirmado_no_modifica_estado(self):
        estudiante = self._crear_estudiante('55555555')
        inscripcion = Inscripcion.objects.create(estudiante=estudiante, comision=self.comision_ushuaia, estado='confirmado')

        response = self.client.post(
            self.url_inscribir,
            data={
                'estudiante_id': estudiante.id,
                'comision_id': self.comision_ushuaia.id_comision,
                'next': 'administracion:panel_inscripciones',
            },
            secure=True,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.url_panel)

        inscripcion.refresh_from_db()
        self.assertEqual(inscripcion.estado, 'confirmado')

    def test_mesa_entrada_no_puede_inscribir_en_otra_ciudad(self):
        self.client.logout()
        mesa_password = 'mesapass'
        mesa_usuario = self._crear_usuario(dni='91000000', password=mesa_password, ciudad='Ushuaia')
        self._asignar_rol(mesa_usuario, nombre_rol='Mesa de Entrada', jerarquia=2)
        self.assertTrue(self.client.login(username='91000000', password=mesa_password))

        estudiante = self._crear_estudiante('66666666', ciudad='Ushuaia')
        Inscripcion.objects.create(estudiante=estudiante, comision=self.comision_rg, estado='pre_inscripto')

        response = self.client.post(
            self.url_inscribir,
            data={
                'estudiante_id': estudiante.id,
                'comision_id': self.comision_rg.id_comision,
                'next': 'administracion:panel_inscripciones',
            },
            secure=True,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.url_panel)

        self.assertFalse(
            Inscripcion.objects.filter(estudiante=estudiante, comision=self.comision_rg, estado='confirmado').exists()
        )

    def test_usuario_sin_roles_no_puede_usar_inscribir(self):
        self.client.logout()
        user_password = 'userpass'
        self._crear_usuario(dni='92000000', password=user_password, ciudad='Ushuaia')
        self.assertTrue(self.client.login(username='92000000', password=user_password))

        estudiante = self._crear_estudiante('77777777')
        Inscripcion.objects.create(estudiante=estudiante, comision=self.comision_ushuaia, estado='pre_inscripto')

        response = self.client.post(
            self.url_inscribir,
            data={
                'estudiante_id': estudiante.id,
                'comision_id': self.comision_ushuaia.id_comision,
                'next': 'administracion:panel_inscripciones',
            },
            secure=True,
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

    def test_admin_puede_ver_panel_cursos(self):
        response = self.client.get(reverse('administracion:panel_cursos'), secure=True)
        self.assertEqual(response.status_code, 200)

    def test_mesa_entrada_no_puede_ver_panel_cursos(self):
        self.client.logout()
        mesa_password = 'mesapass'
        mesa_usuario = self._crear_usuario(dni='93000000', password=mesa_password, ciudad='Ushuaia')
        self._asignar_rol(mesa_usuario, nombre_rol='Mesa de Entrada', jerarquia=2)
        self.assertTrue(self.client.login(username='93000000', password=mesa_password))

        response = self.client.get(reverse('administracion:panel_cursos'), secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

    def test_mesa_entrada_no_puede_ver_gestion_usuarios(self):
        self.client.logout()
        mesa_password = 'mesapass'
        mesa_usuario = self._crear_usuario(dni='94000000', password=mesa_password, ciudad='Ushuaia')
        self._asignar_rol(mesa_usuario, nombre_rol='Mesa de Entrada', jerarquia=2)
        self.assertTrue(self.client.login(username='94000000', password=mesa_password))

        response = self.client.get(reverse('administracion:gestion_usuarios'), secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

    def test_mesa_entrada_puede_ver_panel_inscripciones(self):
        self.client.logout()
        mesa_password = 'mesapass'
        mesa_usuario = self._crear_usuario(dni='95000000', password=mesa_password, ciudad='Ushuaia')
        self._asignar_rol(mesa_usuario, nombre_rol='Mesa de Entrada', jerarquia=2)
        self.assertTrue(self.client.login(username='95000000', password=mesa_password))

        response = self.client.get(reverse('administracion:panel_inscripciones'), secure=True)
        self.assertEqual(response.status_code, 200)

    def test_exportar_inscripciones_csv_filtra_por_ciudad_mesa_entrada(self):
        self.client.logout()
        mesa_password = 'mesapass'
        mesa_usuario = self._crear_usuario(dni='96000000', password=mesa_password, ciudad='Ushuaia')
        self._asignar_rol(mesa_usuario, nombre_rol='Mesa de Entrada', jerarquia=2)
        self.assertTrue(self.client.login(username='96000000', password=mesa_password))

        estudiante_ush = self._crear_estudiante('10101010', ciudad='Ushuaia')
        estudiante_rg = self._crear_estudiante('20202020', ciudad='Rio Grande')
        Inscripcion.objects.create(estudiante=estudiante_ush, comision=self.comision_ushuaia, estado='pre_inscripto')
        Inscripcion.objects.create(estudiante=estudiante_rg, comision=self.comision_rg, estado='pre_inscripto')

        response = self.client.get(reverse('administracion:exportar_inscripciones'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')

        csv_text = response.content.decode('utf-8')
        self.assertIn('10101010', csv_text)
        self.assertNotIn('20202020', csv_text)

    def test_exportar_usuarios_excel_requiere_admin_completo(self):
        response = self.client.get(reverse('administracion:exportar_usuarios_excel'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', response['Content-Type'])
        self.assertTrue(response.content.startswith(b'PK'))

        self.client.logout()
        mesa_password = 'mesapass'
        mesa_usuario = self._crear_usuario(dni='97000000', password=mesa_password, ciudad='Ushuaia')
        self._asignar_rol(mesa_usuario, nombre_rol='Mesa de Entrada', jerarquia=2)
        self.assertTrue(self.client.login(username='97000000', password=mesa_password))

        response = self.client.get(reverse('administracion:exportar_usuarios_excel'), secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

    def test_exportar_asistencias_por_curso_xlsx(self):
        estudiante = self._crear_estudiante('30303030')
        inscripcion = Inscripcion.objects.create(estudiante=estudiante, comision=self.comision_ushuaia, estado='confirmado')
        Asistencia.objects.create(
            inscripcion=inscripcion,
            fecha_clase=date(2025, 1, 1),
            presente=True,
            registrado_por='Admin',
        )

        url = reverse('administracion:exportar_asistencias_curso') + f'?curso_id={self.curso.id_curso}'
        response = self.client.get(url, secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', response['Content-Type'])
        self.assertTrue(response.content.startswith(b'PK'))

    def test_exportar_asistencias_por_comision_xlsx(self):
        estudiante = self._crear_estudiante('40404040')
        inscripcion = Inscripcion.objects.create(estudiante=estudiante, comision=self.comision_ushuaia, estado='confirmado')
        Asistencia.objects.create(
            inscripcion=inscripcion,
            fecha_clase=date(2025, 1, 1),
            presente=False,
            registrado_por='Admin',
        )

        url = reverse('administracion:exportar_asistencias_comision') + f'?comision_id={self.comision_ushuaia.id_comision}'
        response = self.client.get(url, secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', response['Content-Type'])
        self.assertTrue(response.content.startswith(b'PK'))
