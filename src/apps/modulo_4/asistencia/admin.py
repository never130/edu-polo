from django.contrib import admin
from .models import Asistencia, RegistroAsistencia


@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('get_estudiante', 'get_curso', 'fecha_clase', 'presente', 'registrado_por')
    list_filter = ('presente', 'fecha_clase', 'inscripcion__comision__fk_id_curso')
    search_fields = ('inscripcion__estudiante__usuario__persona__nombre', 'inscripcion__estudiante__usuario__persona__apellido')
    date_hierarchy = 'fecha_clase'
    readonly_fields = ('fecha_registro',)
    
    @admin.display(description='Estudiante')
    def get_estudiante(self, obj):
        return obj.inscripcion.estudiante.usuario.persona.nombre_completo
    
    @admin.display(description='Curso')
    def get_curso(self, obj):
        return obj.inscripcion.comision.fk_id_curso.nombre
    
    fieldsets = (
        ('Información de Asistencia', {
            'fields': ('inscripcion', 'fecha_clase', 'presente')
        }),
        ('Registro', {
            'fields': ('registrado_por', 'observaciones', 'fecha_registro')
        }),
    )


@admin.register(RegistroAsistencia)
class RegistroAsistenciaAdmin(admin.ModelAdmin):
    list_display = ('get_estudiante', 'get_curso', 'total_clases', 'clases_asistidas', 'porcentaje_asistencia', 'cumple_requisito_certificado')
    list_filter = ('cumple_requisito_certificado', 'inscripcion__comision__fk_id_curso')
    search_fields = ('inscripcion__estudiante__usuario__persona__nombre', 'inscripcion__estudiante__usuario__persona__apellido')
    readonly_fields = ('porcentaje_asistencia', 'cumple_requisito_certificado')
    
    @admin.display(description='Estudiante')
    def get_estudiante(self, obj):
        return obj.inscripcion.estudiante.usuario.persona.nombre_completo
    
    @admin.display(description='Curso')
    def get_curso(self, obj):
        return obj.inscripcion.comision.fk_id_curso.nombre
    
    actions = ['recalcular_porcentajes']
    
    @admin.action(description='Recalcular porcentajes de asistencia')
    def recalcular_porcentajes(self, request, queryset):
        for registro in queryset:
            registro.calcular_porcentaje()
        self.message_user(request, f'Se recalcularon {queryset.count()} registros.')
