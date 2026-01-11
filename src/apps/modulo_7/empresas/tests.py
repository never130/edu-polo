from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.modulo_1.roles.models import Estudiante, Rol, UsuarioRol
from apps.modulo_1.usuario.models import Persona, Usuario

from .models import Empresa, MiembroEmpresa


class SidebarEmpresasLinksTests(TestCase):
    def _crear_usuario(self, dni, password, fecha_nacimiento):
        persona = Persona.objects.create(
            dni=dni,
            nombre='Ana',
            apellido='Test',
            correo=f'{dni}@test.com',
            fecha_nacimiento=fecha_nacimiento,
        )
        usuario = Usuario.objects.create(persona=persona, contrasena=password)
        return usuario

    def test_dashboard_estudiante_muestra_link_empresas_si_es_mayor(self):
        password = 'pw'
        dni = '80000000'
        usuario = self._crear_usuario(dni, password, date(2000, 1, 1))
        Estudiante.objects.create(usuario=usuario, nivel_estudios='SE', institucion_actual='Colegio')

        self.assertTrue(self.client.login(username=dni, password=password))
        response = self.client.get(reverse('dashboard_estudiante'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('empresas:mi_empresa'))
        self.assertContains(response, 'Mi Empresa / Startup')

    def test_dashboard_estudiante_no_muestra_link_empresas_si_es_menor(self):
        password = 'pw'
        dni = '80000001'
        usuario = self._crear_usuario(dni, password, date(2012, 1, 1))
        Estudiante.objects.create(usuario=usuario, nivel_estudios='SE', institucion_actual='Colegio')

        self.assertTrue(self.client.login(username=dni, password=password))
        response = self.client.get(reverse('dashboard_estudiante'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse('empresas:mi_empresa'))
        self.assertNotContains(response, 'Mi Empresa / Startup')

    def test_mi_perfil_muestra_link_empresas_si_es_mayor(self):
        password = 'pw'
        dni = '80000002'
        usuario = self._crear_usuario(dni, password, date(1999, 6, 1))

        self.assertTrue(self.client.login(username=dni, password=password))
        response = self.client.get(reverse('usuario:mi_perfil'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('empresas:mi_empresa'))

    def test_mi_perfil_no_muestra_link_empresas_si_es_menor(self):
        password = 'pw'
        dni = '80000003'
        self._crear_usuario(dni, password, date(2014, 6, 1))

        self.assertTrue(self.client.login(username=dni, password=password))
        response = self.client.get(reverse('usuario:mi_perfil'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse('empresas:mi_empresa'))

    def test_dashboard_admin_muestra_link_solicitudes_empresas(self):
        password = 'pw'
        dni = '80000004'
        usuario = self._crear_usuario(dni, password, date(1990, 1, 1))
        rol_mesa = Rol.objects.create(nombre='Mesa de Entrada', descripcion='Mesa', jerarquia=2)
        UsuarioRol.objects.create(usuario_id=usuario, rol_id=rol_mesa)

        self.assertTrue(self.client.login(username=dni, password=password))
        response = self.client.get(reverse('dashboard_admin'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('empresas:mesa_entrada_list'))


class EmpresaFlowTests(TestCase):
    def _crear_usuario(self, dni, password, fecha_nacimiento, ciudad_residencia='Ushuaia'):
        persona = Persona.objects.create(
            dni=dni,
            nombre='Ana',
            apellido='Test',
            correo=f'{dni}@test.com',
            fecha_nacimiento=fecha_nacimiento,
            ciudad_residencia=ciudad_residencia,
        )
        return Usuario.objects.create(persona=persona, contrasena=password)

    def _crear_mesa_entrada(self, dni='90000000', password='pw', ciudad_residencia='Ushuaia'):
        usuario = self._crear_usuario(dni, password, date(1990, 1, 1), ciudad_residencia=ciudad_residencia)
        rol_mesa, _ = Rol.objects.get_or_create(
            nombre='Mesa de Entrada',
            defaults={'descripcion': 'Mesa', 'jerarquia': 2},
        )
        UsuarioRol.objects.create(usuario_id=usuario, rol_id=rol_mesa)
        return usuario

    def test_flujo_empresa_desde_solicitud_hasta_gestion(self):
        password = 'pw'
        dni_responsable = '80001000'
        self._crear_usuario(dni_responsable, password, date(1990, 1, 1), ciudad_residencia='Ushuaia')

        self.assertTrue(self.client.login(username=dni_responsable, password=password))
        response = self.client.get(reverse('empresas:mi_empresa'), secure=True)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse('empresas:mi_empresa'),
            data={
                'nombre': 'Ever',
                'rubro': 'Software',
                'descripcion': 'Empresa de prueba',
                'acepto_terminos': 'on',
            },
            secure=True,
        )
        self.assertEqual(response.status_code, 302)

        empresa = Empresa.objects.get(responsable__persona__dni=dni_responsable)
        self.assertEqual(empresa.estado, 'pendiente')

        self.client.logout()
        mesa_password = 'pw'
        dni_mesa = '90001000'
        self._crear_mesa_entrada(dni=dni_mesa, password=mesa_password, ciudad_residencia='Rio Grande')
        self.assertTrue(self.client.login(username=dni_mesa, password=mesa_password))

        response = self.client.get(reverse('empresas:mesa_entrada_list'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ever')

        response = self.client.get(reverse('empresas:mesa_entrada_detalle', args=[empresa.id]), secure=True)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse('empresas:mesa_entrada_detalle', args=[empresa.id]),
            data={'accion': 'aprobar'},
            secure=True,
        )
        self.assertEqual(response.status_code, 302)

        empresa.refresh_from_db()
        self.assertEqual(empresa.estado, 'aprobada')

        self.assertTrue(
            MiembroEmpresa.objects.filter(
                empresa=empresa,
                usuario=empresa.responsable,
                rol='Responsable',
            ).exists()
        )

        self.client.logout()
        self.assertTrue(self.client.login(username=dni_responsable, password=password))
        response = self.client.get(reverse('empresas:mi_empresa'), secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('empresas:equipo'), response.url)

        response = self.client.get(reverse('empresas:equipo'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ever')

        self.client.logout()
        self.assertTrue(self.client.login(username=dni_mesa, password=mesa_password))

        usuario_pendiente = self._crear_usuario('80001001', password, date(1990, 1, 1), ciudad_residencia='Tolhuin')
        empresa_pendiente = Empresa.objects.create(
            responsable=usuario_pendiente,
            nombre='Pendiente SA',
            rubro='Tecnología',
            descripcion='Pendiente',
            acepto_terminos=True,
            estado='pendiente',
        )

        response = self.client.get(reverse('empresas:gestion_empresas'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ciudad')
        self.assertContains(response, 'Ushuaia')
        self.assertContains(response, "openEmpresaMiembrosModal('")
        self.assertContains(response, reverse('empresas:mesa_entrada_detalle', args=[empresa_pendiente.id]))

    def test_flujo_rechazo_empresa(self):
        password = 'pw'
        dni_responsable = '80002000'
        self._crear_usuario(dni_responsable, password, date(1990, 1, 1))

        empresa = Empresa.objects.create(
            responsable=Usuario.objects.get(persona__dni=dni_responsable),
            nombre='Rechazame',
            rubro='Software',
            descripcion='Solicitud',
            acepto_terminos=True,
            estado='pendiente',
        )

        mesa_password = 'pw'
        dni_mesa = '90002000'
        self._crear_mesa_entrada(dni=dni_mesa, password=mesa_password)

        self.assertTrue(self.client.login(username=dni_mesa, password=mesa_password))
        response = self.client.post(
            reverse('empresas:mesa_entrada_detalle', args=[empresa.id]),
            data={'accion': 'rechazar', 'motivo_rechazo': 'No cumple requisitos'},
            secure=True,
        )
        self.assertEqual(response.status_code, 302)

        empresa.refresh_from_db()
        self.assertEqual(empresa.estado, 'rechazada')
        self.assertEqual(empresa.motivo_rechazo, 'No cumple requisitos')
