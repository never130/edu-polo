from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Max
from .models import Curso, Comision
from apps.modulo_1.roles.models import Estudiante
from apps.modulo_2.inscripciones.models import Inscripcion


class CursoListView(ListView):
    """Vista pública de cursos disponibles"""
    model = Curso
    template_name = 'cursos/lista.html'
    context_object_name = 'cursos'
    
    def get_queryset(self):
        return Curso.objects.filter(estado='Abierto')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Agregar comisiones abiertas para cada curso
        for curso in context['cursos']:
            curso.comisiones_abiertas = curso.comision_set.filter(estado='Abierta')
        return context


# -----------------------------------------------------------------------------
# TODO: Vistas deprecadas - Gestión movida a apps.modulo_6.administracion
# -----------------------------------------------------------------------------
# class CursoCreateView(LoginRequiredMixin, CreateView):
#     model = Curso
#     template_name = 'cursos/crear.html'
#     fields = ['nombre', 'descripcion', 'edad_minima', 'edad_maxima', 'requisitos', 'contenido_multimedia']
#     success_url = reverse_lazy('cursos:lista')
#     
#     def form_valid(self, form):
#         messages.success(self.request, 'Curso creado exitosamente.')
#         return super().form_valid(form)
# 
# 
# class CursoUpdateView(LoginRequiredMixin, UpdateView):
#     model = Curso
#     template_name = 'cursos/actualizar.html'
#     fields = ['nombre', 'descripcion', 'edad_minima', 'edad_maxima', 'requisitos', 'contenido_multimedia', 'estado']
#     success_url = reverse_lazy('cursos:lista')
#     
#     def form_valid(self, form):
#         messages.success(self.request, 'Curso actualizado exitosamente.')
#         return super().form_valid(form)
# 
# 
# class CursoDeleteView(LoginRequiredMixin, DeleteView):
#     model = Curso
#     template_name = 'cursos/eliminar.html'
#     success_url = reverse_lazy('cursos:lista')
#     
#     def delete(self, request, *args, **kwargs):
#         messages.success(request, 'Curso eliminado exitosamente.')
#         return super().delete(request, *args, **kwargs)
# 
# 
# def inscribirse_comision(request, comision_id):
#     """
#     DEPRECADO: Usar apps.modulo_2.inscripciones.views.formulario_inscripcion
#     """
#     if not request.user.is_authenticated:
#         messages.warning(request, '🔒 Debes iniciar sesión para inscribirte a un curso.')
#         return redirect('landing')
#     
#     comision = get_object_or_404(Comision, id_comision=comision_id)
#     
#     try:
#         # Buscar si el usuario tiene perfil de estudiante
#         estudiante = Estudiante.objects.get(usuario__persona__dni=request.user.username)
#         
#         # Verificar si ya está inscrito en la comisión
#         if Inscripcion.objects.filter(estudiante=estudiante, comision=comision).exists():
#             messages.warning(request, '⚠️ Ya estás inscrito en esta comisión.')
#             return redirect('landing')
#
#         # ... (código original omitido por ser obsoleto)
#     except Exception as e:
#         messages.error(request, f'❌ Error al inscribirse: {str(e)}')
#     
#     return redirect('landing')


def mis_inscripciones(request):
    """Vista para ver las inscripciones del usuario"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        estudiante = Estudiante.objects.get(usuario__persona__dni=request.user.username)
        # Mostrar solo inscripciones activas (confirmadas o pendientes)
        inscripciones = Inscripcion.objects.filter(
            estudiante=estudiante
        ).exclude(
            estado__in=['cancelada', 'rechazada']
        ).select_related('comision__fk_id_curso', 'comision__fk_id_polo').order_by('-fecha_hora_inscripcion')
        
        return render(request, 'cursos/mis_inscripciones.html', {'inscripciones': inscripciones})
    except Estudiante.DoesNotExist:
        messages.error(request, 'No tienes perfil de estudiante.')
        return redirect('home')
