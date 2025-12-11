from django.contrib import admin
from .models import Curso, Comision, ComisionDocente, Material, PoloCreativo

# Inline para poder asignar docentes directamente desde la Comision
class ComisionDocenteInline(admin.TabularInline):
    model = ComisionDocente
    extra = 1  # Cuántos campos vacíos mostrar

class ComisionAdmin(admin.ModelAdmin):
    list_display = ('id_comision', 'fk_id_curso', 'lugar', 'fecha_inicio', 'get_cupos_info', 'estado')
    list_filter = ('estado', 'lugar', 'fk_id_curso')
    search_fields = ('fk_id_curso__nombre',)
    inlines = [ComisionDocenteInline]
    readonly_fields = ('get_inscritos', 'get_cupos_disponibles', 'get_porcentaje_ocupacion')
    
    @admin.display(description='Cupos (Disponibles/Total)')
    def get_cupos_info(self, obj):
        disponibles = obj.cupos_disponibles
        total = obj.cupo_maximo
        if disponibles <= 0:
            return f"🚫 LLENO (0/{total})"
        elif disponibles <= 5:
            return f"⚠️ {disponibles}/{total}"
        else:
            return f"✅ {disponibles}/{total}"
    
    @admin.display(description='Estudiantes Inscritos')
    def get_inscritos(self, obj):
        return obj.inscritos_count
    
    @admin.display(description='Cupos Disponibles')
    def get_cupos_disponibles(self, obj):
        return obj.cupos_disponibles
    
    @admin.display(description='% Ocupación')
    def get_porcentaje_ocupacion(self, obj):
        return f"{obj.porcentaje_ocupacion}%"

class CursoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'estado', 'edad_minima', 'edad_maxima')
    search_fields = ('nombre',)
    list_filter = ('estado',)

class MaterialAdmin(admin.ModelAdmin):
    list_display = ('nombre_archivo', 'fk_id_comision', 'fk_id_docente', 'fecha_subida')
    list_filter = ('fk_id_comision',)
    search_fields = ('nombre_archivo', 'fk_id_comision__fk_id_curso__nombre')

class PoloCreativoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ciudad', 'direccion', 'activo')
    list_filter = ('ciudad', 'activo')
    search_fields = ('nombre', 'ciudad', 'direccion')

# Registramos los modelos en el sitio de administración
admin.site.register(Curso, CursoAdmin)
admin.site.register(Comision, ComisionAdmin)
admin.site.register(Material, MaterialAdmin)
admin.site.register(PoloCreativo, PoloCreativoAdmin)
