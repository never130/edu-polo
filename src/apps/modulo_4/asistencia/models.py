from datetime import date

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
        try:
            nombre = self.inscripcion.estudiante.usuario.persona.nombre_completo
        except Exception:
            nombre = f"Inscripcion#{self.inscripcion_id}"
        return f"{nombre} - {self.fecha_clase} - {estado}"

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
            dias = comision.get_dias_semana_indices() if hasattr(comision, 'get_dias_semana_indices') else set()
            if dias and self.fecha_clase and self.fecha_clase.weekday() not in dias:
                raise ValidationError({
                    'fecha_clase': "La fecha de asistencia no coincide con los días establecidos para la comisión."
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
        comision = self.inscripcion.comision

        total_programadas_hasta_hoy = comision.get_total_clases_programadas(hasta=date.today()) if hasattr(comision, 'get_total_clases_programadas') else None
        if total_programadas_hasta_hoy is not None:
            self.total_clases = total_programadas_hasta_hoy
        else:
            self.total_clases = Asistencia.objects.filter(
                inscripcion__comision=comision,
                fecha_clase__lte=date.today(),
            ).values('fecha_clase').distinct().count()

        self.clases_asistidas = Asistencia.objects.filter(
            inscripcion=self.inscripcion,
            presente=True,
            fecha_clase__lte=date.today(),
        ).count()

        if self.total_clases > 0:
            self.porcentaje_asistencia = (self.clases_asistidas / self.total_clases) * 100
        else:
            self.porcentaje_asistencia = 0

        cumple_certificado = False
        if comision.fecha_fin and comision.fecha_fin <= date.today():
            total_programadas_curso = comision.get_total_clases_programadas(hasta=comision.fecha_fin) if hasattr(comision, 'get_total_clases_programadas') else None
            if total_programadas_curso is None:
                total_programadas_curso = Asistencia.objects.filter(
                    inscripcion__comision=comision,
                    fecha_clase__lte=comision.fecha_fin,
                ).values('fecha_clase').distinct().count()

            if total_programadas_curso > 0:
                porcentaje_certificado = (self.clases_asistidas / total_programadas_curso) * 100
                cumple_certificado = 80 <= porcentaje_certificado <= 100

        self.cumple_requisito_certificado = cumple_certificado
        self.save()
        return self.porcentaje_asistencia
    
    def __str__(self):
        try:
            nombre = self.inscripcion.estudiante.usuario.persona.nombre_completo
        except Exception:
            nombre = f"Inscripcion#{self.inscripcion_id}"
        return f"{nombre} - {self.porcentaje_asistencia}%"
    