from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Persona)

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('get_nombre_completo', 'get_dni', 'activo', 'creado')
    search_fields = ('persona__nombre', 'persona__apellido', 'persona__dni')
    list_filter = ('activo',)
    ordering = ('persona__apellido', 'persona__nombre')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('persona')

    @admin.display(description='Nombre', ordering='persona__nombre')
    def get_nombre_completo(self, obj):
        return f"{obj.persona.nombre} {obj.persona.apellido}"

    @admin.display(description='DNI', ordering='persona__dni')
    def get_dni(self, obj):
        return obj.persona.dni