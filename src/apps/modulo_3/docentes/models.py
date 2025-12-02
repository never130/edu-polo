from django.db import models

# --- IMPORTANTE: Importamos los modelos del Módulo 1 ---
# Esta ruta coincide con la estructura de tu proyecto
from apps.modulo_1.usuario.models import Usuario

class Docente(models.Model):
    """
    Este es el 'Perfil' del Docente.
    Almacena la información EXTRA que solo tiene un docente.
    Se conecta 1-a-1 con el modelo Usuario (del Módulo 1).
    """
    id_docente = models.AutoField(primary_key=True)
    
    # Conexión 1 a 1 con el Usuario
    usuario = models.OneToOneField(
        Usuario, 
        on_delete=models.CASCADE,
        related_name='docente_perfil'
    )
    
    # Campos extra del 'diccionario de datos.docx'
    especialidad = models.CharField(max_length=100, blank=True, null=True, verbose_name="Especialidad")
    experiencia = models.TextField(blank=True, null=True, verbose_name="Experiencia")

    def __str__(self):
        return f"{self.usuario.persona.nombre} {self.usuario.persona.apellido}"

    @property
    def nombre_completo(self):
        return f"{self.usuario.persona.nombre} {self.usuario.persona.apellido}"

    @property
    def email(self):
        return self.usuario.persona.correo
        
    @property
    def dni(self):
        return self.usuario.persona.dni
