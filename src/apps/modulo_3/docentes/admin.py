from django.contrib import admin
from .models import Docente

@admin.register(Docente)
class DocenteAdmin(admin.ModelAdmin):
    """
    Personalización del Admin para nuestro modelo 'Docente'.
    """
    list_display = ('id_docente', 'get_nombre_completo', 'get_dni', 'especialidad', 'get_email')
    search_fields = (
        'usuario__persona__nombre', 
        'usuario__persona__apellido', 
        'usuario__persona__dni'
    )
    
    @admin.display(description='Nombre Completo')
    def get_nombre_completo(self, obj):
        return obj.nombre_completo

    @admin.display(description='DNI')
    def get_dni(self, obj):
        return obj.dni

    @admin.display(description='Email')
    def get_email(self, obj):
        return obj.email
