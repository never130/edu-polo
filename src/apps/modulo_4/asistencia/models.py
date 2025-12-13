from django.db import models
from django.core.exceptions import ValidationError
from apps.modulo_2.inscripciones.models import Inscripcion


class Asistencia(models.Model):
    """
    Registra la concurrencia de un estudiante a cada clase.
    Permite calcular porcentaje de asistencia para certificados.
    """
    id_asistencia = models.AutoField(primary_key=True)
    inscripcion = models.ForeignKey(
        Inscripcion, 
        on_delete=models.CASCADE, 
        related_name='asistencias',
        verbose_name="Inscripción"
    )
    fecha_clase = models.DateField(verbose_name="Fecha de la Clase")
    presente = models.BooleanField(default=False, verbose_name="Presente")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    registrado_por = models.CharField(max_length=100, blank=True, null=True, verbose_name="Registrado por")
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")
    
    class Meta:
        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"
        unique_together = ('inscripcion', 'fecha_clase')
        ordering = ['-fecha_clase']
    
    def __str__(self):
        estado = "✅ Presente" if self.presente else "❌ Ausente"
        return f"{self.inscripcion.estudiante.usuario.persona.nombre_completo} - {self.fecha_clase} - {estado}"

    def clean(self):
        super().clean()
        if self.inscripcion_id and self.inscripcion.comision:
            comision = self.inscripcion.comision
            if comision.fecha_inicio and self.fecha_clase < comision.fecha_inicio:
                raise ValidationError({
                    'fecha_clase': f"La fecha de asistencia no puede ser anterior al inicio del curso ({comision.fecha_inicio})"
                })
            if comision.fecha_fin and self.fecha_clase > comision.fecha_fin:
                raise ValidationError({
                    'fecha_clase': f"La fecha de asistencia no puede ser posterior al fin del curso ({comision.fecha_fin})"
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class RegistroAsistencia(models.Model):
    """
    Clase helper para calcular estadísticas de asistencia por inscripción
    """
    inscripcion = models.OneToOneField(
        Inscripcion,
        on_delete=models.CASCADE,
        related_name='registro_asistencia',
        verbose_name="Inscripción"
    )
    total_clases = models.IntegerField(default=0, verbose_name="Total de Clases")
    clases_asistidas = models.IntegerField(default=0, verbose_name="Clases Asistidas")
    porcentaje_asistencia = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="% de Asistencia")
    cumple_requisito_certificado = models.BooleanField(default=False, verbose_name="Cumple Requisito para Certificado")
    
    class Meta:
        verbose_name = "Registro de Asistencia"
        verbose_name_plural = "Registros de Asistencia"
    
    def calcular_porcentaje(self):
        """Calcula el porcentaje de asistencia"""
        # Recalcular total_clases basado en la comisión (todas las fechas únicas)
        self.total_clases = Asistencia.objects.filter(
            inscripcion__comision=self.inscripcion.comision
        ).values('fecha_clase').distinct().count()
        
        # Recalcular clases asistidas por este alumno
        self.clases_asistidas = Asistencia.objects.filter(
            inscripcion=self.inscripcion,
            presente=True
        ).count()
        
        if self.total_clases > 0:
            self.porcentaje_asistencia = (self.clases_asistidas / self.total_clases) * 100
            # Cumple requisito si tiene entre 80% y 100% de asistencia
            self.cumple_requisito_certificado = 80 <= self.porcentaje_asistencia <= 100
        else:
            self.porcentaje_asistencia = 0
            self.cumple_requisito_certificado = False
        self.save()
        return self.porcentaje_asistencia
    
    def __str__(self):
        return f"{self.inscripcion.estudiante.usuario.persona.nombre_completo} - {self.porcentaje_asistencia}%"
