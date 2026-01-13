from django.contrib import admin
from django.utils.html import format_html

from .models import Empresa, MiembroEmpresa


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'nombre',
        'condicion_fiscal',
        'cuit',
        'cantidad_miembros',
        'estado',
        'responsable',
        'dni_responsable_adjunto',
        'nomina_socios_adjunto',
        'logo_preview',
        'actualizado',
    )
    list_filter = ('estado',)
    search_fields = ('nombre', 'responsable__persona__dni', 'responsable__persona__nombre', 'responsable__persona__apellido')

    def dni_responsable_adjunto(self, obj):
        if not obj.dni_responsable_archivo:
            return '-'
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">Ver</a>',
            obj.dni_responsable_archivo.url,
        )

    dni_responsable_adjunto.short_description = 'DNI'

    def nomina_socios_adjunto(self, obj):
        if not obj.nomina_socios_archivo:
            return '-'
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">Ver</a>',
            obj.nomina_socios_archivo.url,
        )

    nomina_socios_adjunto.short_description = 'Nómina'

    def logo_preview(self, obj):
        if not obj.logo:
            return '-'
        return format_html(
            '<a href="{}" target="_blank" rel="noopener"><img src="{}" alt="Logo" style="height: 32px; width: auto; object-fit: contain;"></a>',
            obj.logo.url,
            obj.logo.url,
        )

    logo_preview.short_description = 'Logo'


@admin.register(MiembroEmpresa)
class MiembroEmpresaAdmin(admin.ModelAdmin):
    list_display = ('id', 'empresa', 'usuario', 'rol', 'es_socio', 'creado')
    list_filter = ('es_socio',)
    search_fields = ('empresa__nombre', 'usuario__persona__dni', 'usuario__persona__nombre', 'usuario__persona__apellido')
