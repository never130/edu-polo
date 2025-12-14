from django.db import models
from datetime import date

# Create your models here.
class Persona(models.Model):
    """
    Entidad central que almacena datos únicos de cada individuo.
    Una persona puede tener múltiples roles (Estudiante, Docente, Tutor, etc.)
    """
    GENEROS = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
        ('P', 'Prefiero no decirlo'),
    ]
    
    CIUDADES = [
        ('Ushuaia', 'Ushuaia'),
        ('Rio Grande', 'Río Grande'),
        ('Tolhuin', 'Tolhuin'),
    ]

    # Datos personales básicos
    dni = models.CharField(max_length=12, unique=True, verbose_name="DNI")
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    apellido = models.CharField(max_length=100, verbose_name="Apellido")
    correo = models.EmailField(verbose_name="Correo Electrónico")
    telefono = models.CharField(max_length=15, blank=True, null=True, verbose_name="Teléfono")
    fecha_nacimiento = models.DateField(blank=True, null=True, verbose_name="Fecha de Nacimiento")
    genero = models.CharField(max_length=1, choices=GENEROS, blank=True, null=True, verbose_name="Género")
    
    # Ubicación
    ciudad_residencia = models.CharField(max_length=50, choices=CIUDADES, blank=True, null=True, verbose_name="Ciudad de Residencia")
    zona_residencia = models.CharField(max_length=100, blank=True, null=True, verbose_name="Zona/Barrio")
    domicilio = models.CharField(max_length=255, blank=True, null=True, verbose_name="Domicilio Completo")
    
    # Información médica y permisos
    condiciones_medicas = models.TextField(blank=True, null=True, verbose_name="Condiciones Médicas/Alergias")
    autorizacion_imagen = models.BooleanField(default=False, verbose_name="Autorización Uso de Imagen")
    autorizacion_voz = models.BooleanField(default=False, verbose_name="Autorización Uso de Voz")

    @property
    def edad(self):
        """Calcula edad automáticamente desde fecha de nacimiento"""
        if not self.fecha_nacimiento:
            return None
        today = date.today()
        return (
            today.year
            - self.fecha_nacimiento.year
            - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
        )
    
    @property
    def es_menor_edad(self):
        """Verifica si es menor de 16 años (requiere tutor)"""
        if self.edad:
            return self.edad < 16
        return False
    
    @property
    def nombre_completo(self):
        """Retorna nombre completo"""
        return f"{self.nombre} {self.apellido}"

    def __str__(self):
        return self.nombre_completo

    @staticmethod
    def limpiar_dni(dni_raw: str) -> str:
        """Limpia DNI dejando solo números"""
        return ''.join(ch for ch in dni_raw if ch.isdigit())
    
    @staticmethod
    def validar_gmail(email: str) -> bool:
        """Valida que el correo sea de Gmail"""
        return email.lower().endswith('@gmail.com')
    
    class Meta:
        verbose_name = "Persona"
        verbose_name_plural = "Personas"
        ordering = ['apellido', 'nombre']

class Usuario(models.Model):
    contrasena = models.CharField(max_length=128)
    permiso_imagen = models.BooleanField(default=False)
    permiso_voz = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.persona.nombre} {self.persona.apellido}"