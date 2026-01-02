from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.modulo_1.roles.models import Estudiante
from apps.modulo_1.usuario.models import Persona, Usuario
from apps.modulo_2.inscripciones.models import Inscripcion
from apps.modulo_3.cursos.models import Comision, Curso, Material, PoloCreativo


class SeguimientoProgresoTests(TestCase):
    def setUp(self):
        self.password = 'pw'
        self.dni = '83000000'
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

    def test_mi_progreso_renderiza_y_muestra_curso(self):
        response = self.client.get(reverse('usuario:mi_progreso'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.curso.nombre)

    def test_materiales_estudiante_muestra_material_de_comision(self):
        Material.objects.create(
            fk_id_comision=self.comision,
            fk_id_docente=None,
            nombre_archivo='Material 1',
            descripcion='Desc',
            tipo='enlace',
            enlace='https://example.com',
        )
        response = self.client.get(reverse('usuario:materiales_estudiante'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Material 1')

    def test_materiales_estudiante_no_muestra_material_de_otra_comision(self):
        otro_polo = PoloCreativo.objects.create(nombre='Otro Polo', ciudad='Ushuaia', direccion='Otro', activo=True)
        otro_curso = Curso.objects.create(nombre='Otro Curso', estado='Abierto', orden=2)
        otra_comision = Comision.objects.create(
            fk_id_curso=otro_curso,
            fk_id_polo=otro_polo,
            dias_horarios='Miércoles 10:00 - 12:00',
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 1, 1),
            estado='Finalizada',
            cupo_maximo=10,
        )
        Material.objects.create(
            fk_id_comision=otra_comision,
            fk_id_docente=None,
            nombre_archivo='Material Oculto',
            descripcion='Desc',
            tipo='enlace',
            enlace='https://example.com/oculto',
        )
        response = self.client.get(reverse('usuario:materiales_estudiante'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Material Oculto')
