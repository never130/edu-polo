from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Rol)
admin.site.register(Docente)

@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ('get_nombre_completo', 'get_dni', 'nivel_estudios', 'institucion_actual')
    search_fields = ('usuario__persona__nombre', 'usuario__persona__apellido', 'usuario__persona__dni', 'usuario__persona__correo')
    list_filter = ('nivel_estudios',)
    ordering = ('usuario__persona__apellido', 'usuario__persona__nombre')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('usuario__persona')

    @admin.display(description='Nombre Completo', ordering='usuario__persona__nombre')
    def get_nombre_completo(self, obj):
        return f"{obj.usuario.persona.nombre} {obj.usuario.persona.apellido}"

    @admin.display(description='DNI', ordering='usuario__persona__dni')
    def get_dni(self, obj):
        return obj.usuario.persona.dni

admin.site.register(Tutor)
admin.site.register(TutorEstudiante)