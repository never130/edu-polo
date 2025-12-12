from django.db import models
from apps.modulo_1.roles.models import Estudiante
from apps.modulo_3.cursos.models import Comision

class Inscripcion(models.Model):
    """
    Conecta un Estudiante con una Comisión específica.
    Gestiona cupos y lista de espera automáticamente.
    """
    ESTADOS = [
        ('pre_inscripto', 'Pre-Inscripto'),
        ('confirmado', 'Confirmado'),
        ('lista_espera', 'En Lista de Espera'),
        ('cancelada', 'Cancelada'),
    ]
    
    # Relaciones
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='inscripciones', verbose_name="Estudiante")
    comision = models.ForeignKey(Comision, on_delete=models.CASCADE, related_name='inscripciones', verbose_name="Comisión")
    
    # Datos de la inscripción
    fecha_hora_inscripcion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora de Inscripción")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='confirmado', verbose_name="Estado")
    orden_lista_espera = models.IntegerField(blank=True, null=True, verbose_name="Orden en Lista de Espera")
    
    # Observaciones especiales
    observaciones_discapacidad = models.TextField(blank=True, null=True, verbose_name="Observaciones de Discapacidad")
    observaciones_salud = models.TextField(blank=True, null=True, verbose_name="Observaciones de Salud (celíaco, alergias, etc.)")
    observaciones_generales = models.TextField(blank=True, null=True, verbose_name="Observaciones Generales")
    
    class Meta:
        unique_together = ('estudiante', 'comision')
        verbose_name = "Inscripción"
        verbose_name_plural = "Inscripciones"
        ordering = ['orden_lista_espera', '-fecha_hora_inscripcion']
    
    def __str__(self):
        return f"{self.estudiante.usuario.persona.nombre_completo} - {self.comision.fk_id_curso.nombre}"
    
    @property
    def esta_en_lista_espera(self):
        """Verifica si está en lista de espera"""
        return self.estado == 'lista_espera'
    
    @property
    def esta_confirmado(self):
        """Verifica si la inscripción está confirmada"""
        return self.estado == 'confirmado'
