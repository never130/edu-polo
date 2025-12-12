from django.db import models
from apps.modulo_1.usuario.models import Usuario, Persona


# Create your models here.
class Rol(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255)
    jerarquia = models.PositiveSmallIntegerField()


    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(jerarquia__gte=1) & models.Q(jerarquia__lte=5),
                name="rol_jerarquia_entre_1_y_5"
            )
        ]
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
   
    def __str__(self):
        return f"{self.nombre} - Jerarquia({self.jerarquia})"


class Docente(models.Model):
    especialidad = models.CharField(max_length=100)
    experiencia = models.TextField()
    id_persona = models.ForeignKey(Persona, on_delete=models.CASCADE)


    class Meta:
        verbose_name = "Docente"
        verbose_name_plural = "Docentes"


    def __str__(self):
        return f"{self.id_persona.nombre} - Especialidad {self.especialidad}"


class Estudiante(models.Model):
    grado = [
        ('PI', 'Primaria Incompleto'),
        ('PR', 'Primaria Completo'),
        ('SI', 'Secundaria Incompleto'),
        ('SE', 'Secundaria Completo'),
        ('UI', 'Universidad Incompleto'),
        ('UN', 'Universidad Completo'),
        ('OT', 'Otro'),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    nivel_estudios = models.CharField(max_length=2, choices=grado)
    institucion_actual = models.CharField(max_length=255)
    experiencia_laboral = models.TextField(blank=True, null=True)


    class Meta:
        verbose_name = "Estudiante"
        verbose_name_plural = "Estudiantes"


    def __str__(self):
        return f"Estudiante: {self.usuario.persona.nombre} {self.usuario.persona.apellido}"


class Tutor(models.Model):
    tipo = [
        ('AC', 'Academico'),
        ('PE', 'Personal'),
        ('LA', 'Laboral'),
        ('OT', 'Otro'),
    ]


    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    tipo_tutor = models.CharField(max_length=2, choices=tipo)
    telefono_contacto = models.CharField(max_length=15)
    disponibilidad_horaria = models.CharField(max_length=100)


    class Meta:
        verbose_name = "Tutor"
        verbose_name_plural = "Tutores"


    def __str__(self):
        return f"Tutor: {self.usuario.persona.nombre} {self.usuario.persona.apellido}"


class TutorEstudiante(models.Model):
    """
    Tabla intermedia que relaciona un Estudiante con su Tutor.
    Obligatorio para menores de 16 años.
    """
    PARENTESCOS = [
        ('padre', 'Padre'),
        ('madre', 'Madre'),
        ('tutor_legal', 'Tutor Legal'),
        ('abuelo', 'Abuelo/a'),
        ('hermano', 'Hermano/a'),
        ('otro', 'Otro'),
    ]
    
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name='estudiantes_a_cargo', verbose_name="Tutor")
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='tutores', verbose_name="Estudiante")
    parentesco = models.CharField(max_length=20, choices=PARENTESCOS, blank=True, null=True, verbose_name="Parentesco")
    fecha_asignacion = models.DateField(auto_now_add=True, verbose_name="Fecha de Asignación")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    
    class Meta:
        verbose_name = "Relación Tutor-Estudiante"
        verbose_name_plural = "Relaciones Tutor-Estudiante"
        unique_together = ('tutor', 'estudiante')

    def __str__(self):
        return f"Tutor: {self.tutor.usuario.persona.nombre_completo} - Estudiante: {self.estudiante.usuario.persona.nombre_completo}"


class UsuarioRol(models.Model):
    usuario_id = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    rol_id = models.ForeignKey(Rol, on_delete=models.CASCADE)


    def __str__(self):
        return f"Usuario {self.usuario_id} - Rol {self.rol_id.nombre}"