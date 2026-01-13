import base64
import os
import shutil
import tempfile
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.modulo_1.roles.models import Rol, UsuarioRol
from apps.modulo_1.usuario.models import Persona, Usuario
from apps.modulo_7.empresas.models import Empresa, MiembroEmpresa


_TEMP_MEDIA_ROOT = tempfile.mkdtemp(prefix="test_media_empresas_")


def _png_1x1_bytes():
    return base64.b64decode(
        b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
    )


@override_settings(MEDIA_ROOT=_TEMP_MEDIA_ROOT, MEDIA_URL="/media/")
class FlujoEmpresaTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(_TEMP_MEDIA_ROOT, ignore_errors=True)

    def _asignar_rol(self, usuario_app, nombre_rol, jerarquia):
        rol, _ = Rol.objects.get_or_create(
            nombre=nombre_rol,
            defaults={"descripcion": nombre_rol, "jerarquia": jerarquia},
        )
        UsuarioRol.objects.get_or_create(usuario_id=usuario_app, rol_id=rol)

    def _crear_usuario_app(self, dni, password, *, nombre="Ana", apellido="Test", edad=25):
        fecha_nac = date.today() - timedelta(days=365 * edad)
        persona = Persona.objects.create(
            dni=dni,
            nombre=nombre,
            apellido=apellido,
            correo=f"{dni}@example.com",
            telefono="2901000000",
            fecha_nacimiento=fecha_nac,
        )
        UserModel = get_user_model()
        UserModel.objects.create_user(username=dni, password=password, email=persona.correo)
        usuario_app = Usuario.objects.create(persona=persona, contrasena=password, activo=True)
        return usuario_app

    def _crear_empresa_pendiente(self, *, dni="30000000", password="pw", nombre_empresa="Empresa Test"):
        usuario = self._crear_usuario_app(dni=dni, password=password, nombre="Laura", apellido="Empresa", edad=25)
        self._asignar_rol(usuario, nombre_rol="Empresa", jerarquia=3)
        empresa = Empresa.objects.create(
            responsable=usuario,
            nombre=nombre_empresa,
            condicion_fiscal="en_formacion",
            cuit="",
            cantidad_miembros=2,
            rubro="Desarrollo de software",
            descripcion="Empresa de software",
            acepto_terminos=True,
            estado="pendiente",
        )
        return empresa, usuario

    def _crear_staff_user(self, username="99000000", password="staffpw"):
        UserModel = get_user_model()
        return UserModel.objects.create_user(
            username=username,
            password=password,
            email=f"{username}@example.com",
            is_staff=True,
        )

    def test_registro_empresa_crea_solicitud_pendiente_con_adjuntos(self):
        dni = "31000000"
        password = "pw123456"
        fecha_nac = (date.today() - timedelta(days=365 * 25)).isoformat()

        dni_file = SimpleUploadedFile(
            "dni.pdf",
            b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n",
            content_type="application/pdf",
        )
        nomina_file = SimpleUploadedFile(
            "nomina.pdf",
            b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n",
            content_type="application/pdf",
        )
        logo_file = SimpleUploadedFile(
            "logo.png",
            _png_1x1_bytes(),
            content_type="image/png",
        )

        payload = {
            "tipo_usuario": "empresa",
            "dni": dni,
            "nombre": "Laura",
            "apellido": "Startup",
            "correo": f"{dni}@example.com",
            "telefono": "2901999999",
            "fecha_nacimiento": fecha_nac,
            "password": password,
            "password_confirm": password,
            "politica_datos": "on",
            "datos_veridicos": "on",
            "empresa_nombre": "Startup Test",
            "condicion_fiscal": "en_formacion",
            "cuit": "",
            "cantidad_miembros": "3",
            "nomina_socios_link": "",
            "empresa_rubro": "Software",
            "empresa_descripcion": "Hacemos software",
            "empresa_acepto_terminos": "on",
            "dni_responsable_archivo": dni_file,
            "nomina_socios_archivo": nomina_file,
            "logo": logo_file,
        }

        response = self.client.post(reverse("usuario:registro"), data=payload, secure=True)
        if response.status_code != 302:
            msgs = [str(m) for m in get_messages(response.wsgi_request)]
            raise AssertionError(f"Registro no redirigió. Status={response.status_code}. Messages={msgs}")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login"))

        empresa = Empresa.objects.get(responsable__persona__dni=dni)
        self.assertEqual(empresa.estado, "pendiente")
        self.assertTrue(bool(empresa.dni_responsable_archivo))
        self.assertTrue(bool(empresa.nomina_socios_archivo))
        self.assertTrue(bool(empresa.logo))

        self.assertTrue(os.path.exists(empresa.dni_responsable_archivo.path))
        self.assertTrue(os.path.exists(empresa.nomina_socios_archivo.path))
        self.assertTrue(os.path.exists(empresa.logo.path))

        self.assertTrue(empresa.dni_responsable_archivo.name.startswith("empresas/documentos/dni/"))
        self.assertTrue(empresa.nomina_socios_archivo.name.startswith("empresas/documentos/nomina/"))
        self.assertTrue(empresa.logo.name.startswith("empresas/logos/"))

    def test_mesa_entrada_list_muestra_solo_pendientes(self):
        empresa_pendiente, _ = self._crear_empresa_pendiente(dni="32000000", nombre_empresa="Pendiente SA")
        empresa_aprobada, _ = self._crear_empresa_pendiente(dni="33000000", nombre_empresa="Aprobada SRL")
        empresa_aprobada.estado = "aprobada"
        empresa_aprobada.save()

        staff = self._crear_staff_user(username="99100000", password="staffpw")
        self.assertTrue(self.client.login(username=staff.username, password="staffpw"))

        response = self.client.get(reverse("empresas:mesa_entrada_list"), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, empresa_pendiente.nombre)
        self.assertNotContains(response, empresa_aprobada.nombre)

    def test_rechazar_empresa_setea_motivo_y_habilita_reenvio(self):
        empresa, responsable = self._crear_empresa_pendiente(dni="34000000", nombre_empresa="Flujo Rechazo", password="pw")
        staff = self._crear_staff_user(username="99200000", password="staffpw")
        self.assertTrue(self.client.login(username=staff.username, password="staffpw"))

        motivo = "Rubro fuera de Software/Tecnología"
        response = self.client.post(
            reverse("empresas:mesa_entrada_detalle", args=[empresa.id]),
            data={"accion": "rechazar", "motivo_rechazo": motivo},
            secure=True,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("empresas:mesa_entrada_list"))

        empresa.refresh_from_db()
        self.assertEqual(empresa.estado, "rechazada")
        self.assertEqual(empresa.motivo_rechazo, motivo)
        self.assertEqual(empresa.rechazado_por_id, staff.id)
        self.assertIsNotNone(empresa.rechazado_en)

        self.client.logout()
        self.assertTrue(self.client.login(username=responsable.persona.dni, password="pw"))
        response = self.client.get(reverse("empresas:mi_empresa"), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reenviar solicitud")
        self.assertContains(response, motivo)

    def test_aprobar_empresa_actualiza_estado_y_crea_miembro_responsable(self):
        empresa, responsable = self._crear_empresa_pendiente(dni="35000000", nombre_empresa="Flujo Aprobar", password="pw")
        staff = self._crear_staff_user(username="99300000", password="staffpw")
        self.assertTrue(self.client.login(username=staff.username, password="staffpw"))

        response = self.client.post(
            reverse("empresas:mesa_entrada_detalle", args=[empresa.id]),
            data={"accion": "aprobar"},
            secure=True,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("empresas:mesa_entrada_list"))

        empresa.refresh_from_db()
        self.assertEqual(empresa.estado, "aprobada")
        self.assertEqual(empresa.aprobado_por_id, staff.id)
        self.assertIsNotNone(empresa.aprobado_en)

        self.assertTrue(
            MiembroEmpresa.objects.filter(
                empresa=empresa,
                usuario=responsable,
                rol="Responsable",
                es_socio=True,
            ).exists()
        )

        self.client.logout()
        self.assertTrue(self.client.login(username=responsable.persona.dni, password="pw"))
        response = self.client.get(reverse("empresas:mi_empresa"), secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("empresas:equipo"))

    def test_gestion_empresas_requiere_admin_o_mesa(self):
        empresa, responsable = self._crear_empresa_pendiente(dni="36000000", nombre_empresa="Acceso Gestión", password="pw")
        self.assertTrue(self.client.login(username=responsable.persona.dni, password="pw"))
        response = self.client.get(reverse("empresas:gestion_empresas"), secure=True)
        self.assertEqual(response.status_code, 403)

        self.client.logout()
        staff = self._crear_staff_user(username="99400000", password="staffpw")
        self.assertTrue(self.client.login(username=staff.username, password="staffpw"))
        response = self.client.get(reverse("empresas:gestion_empresas"), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, empresa.nombre)
