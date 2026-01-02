from datetime import date

from django.db import transaction
from django.db.utils import IntegrityError
from django.test import TestCase
from django.urls import reverse

from apps.modulo_1.roles.models import AutorizadoRetiro, Estudiante, Rol, Tutor, TutorEstudiante, UsuarioRol
from apps.modulo_1.usuario.models import Persona, Usuario


class RolesModelTests(TestCase):
    def test_rol_jerarquia_invalida_falla_por_constraint(self):
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Rol.objects.create(nombre='Rol Invalido', descripcion='x', jerarquia=0)

        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Rol.objects.create(nombre='Rol Invalido 2', descripcion='x', jerarquia=6)

    def test_rol_str_incluye_nombre_y_jerarquia(self):
        rol = Rol.objects.create(nombre='Administrador', descripcion='Admin', jerarquia=1)
        self.assertIn('Administrador', str(rol))
        self.assertIn('Jerarquia(1)', str(rol))

    def test_usuariorol_str_incluye_nombre_rol(self):
        rol = Rol.objects.create(nombre='Mesa de Entrada', descripcion='Mesa', jerarquia=2)
        persona = Persona.objects.create(dni='70000000', nombre='Ana', apellido='Test', correo='a@test.com')
        usuario = Usuario.objects.create(persona=persona, contrasena='pw')
        usuariorol = UsuarioRol.objects.create(usuario_id=usuario, rol_id=rol)
        self.assertIn('Mesa de Entrada', str(usuariorol))

    def test_tutorestudiante_es_unico_por_tutor_y_estudiante(self):
        persona_est = Persona.objects.create(dni='70100000', nombre='Ana', apellido='Est', correo='est@test.com')
        usuario_est = Usuario.objects.create(persona=persona_est, contrasena='pw')
        estudiante = Estudiante.objects.create(usuario=usuario_est, nivel_estudios='SE', institucion_actual='Colegio')

        persona_tut = Persona.objects.create(dni='70100001', nombre='Juan', apellido='Tutor', correo='t@test.com')
        usuario_tut = Usuario.objects.create(persona=persona_tut, contrasena='pw')
        tutor = Tutor.objects.create(
            usuario=usuario_tut,
            tipo_tutor='AC',
            telefono_contacto='2901000000',
            disponibilidad_horaria='Lunes 10-12',
        )

        TutorEstudiante.objects.create(tutor=tutor, estudiante=estudiante, parentesco='padre')
        with self.assertRaises(IntegrityError):
            TutorEstudiante.objects.create(tutor=tutor, estudiante=estudiante, parentesco='padre')

    def test_estudiante_y_tutor_str_incluyen_nombre(self):
        persona_est = Persona.objects.create(dni='70100002', nombre='Ana', apellido='Est', correo='est2@test.com')
        usuario_est = Usuario.objects.create(persona=persona_est, contrasena='pw')
        estudiante = Estudiante.objects.create(usuario=usuario_est, nivel_estudios='SE', institucion_actual='Colegio')
        self.assertIn('Ana', str(estudiante))

        persona_tut = Persona.objects.create(dni='70100003', nombre='Juan', apellido='Tutor', correo='t2@test.com')
        usuario_tut = Usuario.objects.create(persona=persona_tut, contrasena='pw')
        tutor = Tutor.objects.create(
            usuario=usuario_tut,
            tipo_tutor='AC',
            telefono_contacto='2901000000',
            disponibilidad_horaria='Lunes 10-12',
        )
        self.assertIn('Juan', str(tutor))


class DashboardRoleRedirectTests(TestCase):
    def setUp(self):
        self.password = 'pw'
        self.dni_admin = '71000000'
        self.admin = self._crear_usuario(self.dni_admin, self.password)
        rol_admin = Rol.objects.create(nombre='Administrador', descripcion='Admin', jerarquia=1)
        UsuarioRol.objects.create(usuario_id=self.admin, rol_id=rol_admin)

        self.dni_est = '72000000'
        self.estudiante_usuario = self._crear_usuario(self.dni_est, self.password)
        Estudiante.objects.create(usuario=self.estudiante_usuario, nivel_estudios='SE', institucion_actual='Colegio')

    def _crear_usuario(self, dni, password):
        persona = Persona.objects.create(
            dni=dni,
            nombre='Nombre',
            apellido=dni,
            correo=f'{dni}@test.com',
            fecha_nacimiento=date(2000, 1, 1),
            ciudad_residencia='Ushuaia',
        )
        return Usuario.objects.create(persona=persona, contrasena=password)

    def test_dashboard_redirige_a_admin_si_tiene_rol_admin(self):
        self.assertTrue(self.client.login(username=self.dni_admin, password=self.password))
        response = self.client.get(reverse('dashboard'), secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard_admin'))

    def test_dashboard_redirige_a_estudiante_si_tiene_perfil_estudiante(self):
        self.assertTrue(self.client.login(username=self.dni_est, password=self.password))
        response = self.client.get(reverse('dashboard'), secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard_estudiante'))


class AutorizadoRetiroModelTests(TestCase):
    def setUp(self):
        self.password = 'pw'
        persona = Persona.objects.create(
            dni='73000000',
            nombre='Ana',
            apellido='Test',
            correo='ana@test.com',
            fecha_nacimiento=date(2000, 1, 1),
            ciudad_residencia='Ushuaia',
        )
        usuario = Usuario.objects.create(persona=persona, contrasena=self.password)
        self.estudiante = Estudiante.objects.create(usuario=usuario, nivel_estudios='SE', institucion_actual='Colegio')

    def test_autorizado_retiro_es_unico_por_estudiante_y_dni(self):
        AutorizadoRetiro.objects.create(
            estudiante=self.estudiante,
            dni='12345678',
            nombre='Juan',
            apellido='Tutor',
            telefono='2901000000',
            correo='jt@test.com',
            parentesco='otro',
        )

        with self.assertRaises(IntegrityError):
            AutorizadoRetiro.objects.create(
                estudiante=self.estudiante,
                dni='12345678',
                nombre='Juan',
                apellido='Tutor',
                telefono='2901000000',
                correo='jt@test.com',
                parentesco='otro',
            )
