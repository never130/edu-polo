from django.contrib import admin
from .models import Inscripcion
from apps.modulo_4.asistencia.models import RegistroAsistencia

class RegistroAsistenciaInline(admin.StackedInline):
    model = RegistroAsistencia
    can_delete = False
    verbose_name_plural = 'Registro de Asistencia'
    readonly_fields = ('total_clases', 'clases_asistidas', 'porcentaje_asistencia', 'cumple_requisito_certificado')

@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'comision', 'fecha_hora_inscripcion', 'estado', 'orden_lista_espera')
    list_filter = ('estado', 'comision__fk_id_curso')
    search_fields = ('estudiante__usuario__persona__nombre', 'estudiante__usuario__persona__apellido', 'comision__fk_id_curso__nombre')
    date_hierarchy = 'fecha_hora_inscripcion'
    readonly_fields = ('fecha_hora_inscripcion',)
    inlines = [RegistroAsistenciaInline]
    
    fieldsets = (
        ('Información de Inscripción', {
            'fields': ('estudiante', 'comision', 'estado', 'orden_lista_espera')
        }),
        ('Observaciones Especiales', {
            'fields': ('observaciones_discapacidad', 'observaciones_salud', 'observaciones_generales')
        }),
        ('Metadata', {
            'fields': ('fecha_hora_inscripcion',)
        }),
    )
