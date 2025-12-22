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
        ('vecino', 'Vecino/a'),
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


class AutorizadoRetiro(models.Model):
    PARENTESCOS = TutorEstudiante.PARENTESCOS + [
        ('otro', 'Otro'),
    ]

    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='autorizados_retiro')

    dni = models.CharField(max_length=12)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15)
    correo = models.EmailField(blank=True, null=True)
    parentesco = models.CharField(max_length=20, choices=PARENTESCOS)

    confirmado = models.BooleanField(default=False)
    confirmado_en = models.DateTimeField(blank=True, null=True)

    revocado = models.BooleanField(default=False)
    revocado_en = models.DateTimeField(blank=True, null=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Autorizado para Retirar"
        verbose_name_plural = "Autorizados para Retirar"
        unique_together = ('estudiante', 'dni')

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.dni})"


class UsuarioRol(models.Model):
    usuario_id = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    rol_id = models.ForeignKey(Rol, on_delete=models.CASCADE)


    def __str__(self):
        return f"Usuario {self.usuario_id} - Rol {self.rol_id.nombre}"