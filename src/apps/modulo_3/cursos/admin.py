from django.contrib import admin
from django.db.models import Count, Q
from .models import Curso, Comision, ComisionDocente, Material, PoloCreativo

# Inline para poder asignar docentes directamente desde la Comision
class ComisionDocenteInline(admin.TabularInline):
    model = ComisionDocente
    extra = 1
    autocomplete_fields = ['fk_id_docente']

class ComisionAdmin(admin.ModelAdmin):
    list_display = ('id_comision', 'fk_id_curso', 'lugar', 'fecha_inicio', 'publicada', 'get_cupos_info', 'estado')
    list_filter = ('publicada', 'estado', 'lugar', 'fk_id_curso')
    search_fields = ('fk_id_curso__nombre',)
    ordering = ('fk_id_curso__nombre', 'id_comision')
    inlines = [ComisionDocenteInline]
    readonly_fields = ('get_inscritos', 'get_cupos_disponibles', 'get_porcentaje_ocupacion')
    autocomplete_fields = ['fk_id_curso']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('fk_id_curso')
        # Optimizacion N+1: Anotar conteo de inscritos directamente en la query
        qs = qs.annotate(
            inscritos_count_annotated=Count(
                'inscripciones',
                filter=~Q(inscripciones__estado__in=['lista_espera', 'cancelada'])
            )
        )
        return qs
    
    @admin.display(description='Cupos (Disponibles/Total)')
    def get_cupos_info(self, obj):
        # Usar valor anotado si existe, sino fallback a property (que hace query)
        inscritos = getattr(obj, 'inscritos_count_annotated', obj.inscritos_count)
        disponibles = obj.cupo_maximo - inscritos
        
        total = obj.cupo_maximo
        if disponibles <= 0:
            return f"🚫 LLENO (0/{total})"
        elif disponibles <= 5:
            return f"⚠️ {disponibles}/{total}"
        else:
            return f"✅ {disponibles}/{total}"
    
    @admin.display(description='Estudiantes Inscritos')
    def get_inscritos(self, obj):
        return getattr(obj, 'inscritos_count_annotated', obj.inscritos_count)
    
    @admin.display(description='Cupos Disponibles')
    def get_cupos_disponibles(self, obj):
        inscritos = getattr(obj, 'inscritos_count_annotated', obj.inscritos_count)
        return obj.cupo_maximo - inscritos
    
    @admin.display(description='% Ocupación')
    def get_porcentaje_ocupacion(self, obj):
        if obj.cupo_maximo == 0:
            return "0%"
        inscritos = getattr(obj, 'inscritos_count_annotated', obj.inscritos_count)
        porcentaje = int((inscritos / obj.cupo_maximo) * 100)
        return f"{porcentaje}%"

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
