from django.contrib import admin

from .models import Empresa, MiembroEmpresa


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'estado', 'responsable', 'actualizado')
    list_filter = ('estado',)
    search_fields = ('nombre', 'responsable__persona__dni', 'responsable__persona__nombre', 'responsable__persona__apellido')


@admin.register(MiembroEmpresa)
class MiembroEmpresaAdmin(admin.ModelAdmin):
    list_display = ('id', 'empresa', 'usuario', 'rol', 'es_socio', 'creado')
    list_filter = ('es_socio',)
    search_fields = ('empresa__nombre', 'usuario__persona__dni', 'usuario__persona__nombre', 'usuario__persona__apellido')

