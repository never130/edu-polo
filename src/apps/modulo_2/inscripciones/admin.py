from django.contrib import admin
from .models import Inscripcion

@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'comision', 'fecha_hora_inscripcion', 'estado', 'orden_lista_espera')
    list_filter = ('estado', 'comision__fk_id_curso')
    search_fields = ('estudiante__usuario__persona__nombre', 'estudiante__usuario__persona__apellido', 'comision__fk_id_curso__nombre')
    date_hierarchy = 'fecha_hora_inscripcion'
    readonly_fields = ('fecha_hora_inscripcion',)
    
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
