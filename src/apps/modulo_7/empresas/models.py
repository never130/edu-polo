from django.conf import settings
from django.db import models

from apps.modulo_1.usuario.models import Usuario


class Empresa(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]

    CONDICIONES_FISCALES = [
        ('monotributo', 'Monotributo'),
        ('responsable_inscripto', 'Responsable Inscripto (Unipersonal)'),
        ('sas', 'S.A.S. (Sociedad por Acciones Simplificada)'),
        ('srl', 'S.R.L. (Sociedad de Responsabilidad Limitada)'),
        ('sa', 'S.A. (Sociedad Anónima)'),
        ('cooperativa', 'Cooperativa'),
        ('en_formacion', 'En formación / No constituida aún'),
    ]

    responsable = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='empresa')
    nombre = models.CharField(max_length=150)
    condicion_fiscal = models.CharField(max_length=40, choices=CONDICIONES_FISCALES, blank=True, default='')
    cuit = models.CharField(max_length=15, blank=True, default='')
    cantidad_miembros = models.PositiveSmallIntegerField(blank=True, null=True)
    dni_responsable_archivo = models.FileField(upload_to='empresas/documentos/dni/', blank=True, null=True)
    nomina_socios_archivo = models.FileField(upload_to='empresas/documentos/nomina/', blank=True, null=True)
    nomina_socios_link = models.URLField(blank=True, default='')
    logo = models.ImageField(upload_to='empresas/logos/', blank=True, null=True)
    rubro = models.CharField(max_length=120, default="")
    descripcion = models.TextField(default="")
    acepto_terminos = models.BooleanField(default=False)

    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    motivo_rechazo = models.TextField(blank=True, null=True)

    aprobado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='empresas_aprobadas',
    )
    aprobado_en = models.DateTimeField(blank=True, null=True)
    rechazado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='empresas_rechazadas',
    )
    rechazado_en = models.DateTimeField(blank=True, null=True)

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['-actualizado', '-creado']

    def __str__(self):
        return self.nombre


class MiembroEmpresa(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='miembros')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='membresias_empresa')
    rol = models.CharField(max_length=80, blank=True, null=True)
    es_socio = models.BooleanField(default=False)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Miembro de Empresa'
        verbose_name_plural = 'Miembros de Empresa'
        unique_together = ('empresa', 'usuario')
        ordering = ['-creado']

    def __str__(self):
        return f'{self.empresa} - {self.usuario}'
