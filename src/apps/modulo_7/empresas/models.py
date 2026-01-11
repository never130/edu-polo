from django.conf import settings
from django.db import models

from apps.modulo_1.usuario.models import Usuario


class Empresa(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]

    responsable = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='empresa')
    nombre = models.CharField(max_length=150)
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

