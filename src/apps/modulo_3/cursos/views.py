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


class CursoCreateView(LoginRequiredMixin, CreateView):
    model = Curso
    template_name = 'cursos/crear.html'
    fields = ['nombre', 'descripcion', 'edad_minima', 'edad_maxima', 'requisitos', 'contenido_multimedia']
    success_url = reverse_lazy('cursos:lista')
    
    def form_valid(self, form):
        messages.success(self.request, 'Curso creado exitosamente.')
        return super().form_valid(form)


class CursoUpdateView(LoginRequiredMixin, UpdateView):
    model = Curso
    template_name = 'cursos/actualizar.html'
    fields = ['nombre', 'descripcion', 'edad_minima', 'edad_maxima', 'requisitos', 'contenido_multimedia', 'estado']
    success_url = reverse_lazy('cursos:lista')
    
    def form_valid(self, form):
        messages.success(self.request, 'Curso actualizado exitosamente.')
        return super().form_valid(form)


class CursoDeleteView(LoginRequiredMixin, DeleteView):
    model = Curso
    template_name = 'cursos/eliminar.html'
    success_url = reverse_lazy('cursos:lista')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Curso eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)


def inscribirse_comision(request, comision_id):
    """
    Vista para inscribirse a una comisión
    Sistema automático de gestión de cupos:
    - Cada inscripción descuenta 1 cupo
    - Cuando llega a 0 muestra "Cupo Lleno"
    - Bloquea inscripciones cuando está completo
    """
    if not request.user.is_authenticated:
        messages.warning(request, '🔒 Debes iniciar sesión para inscribirte a un curso.')
        return redirect('landing')
    
    comision = get_object_or_404(Comision, id_comision=comision_id)
    
    try:
        # Buscar si el usuario tiene perfil de estudiante
        estudiante = Estudiante.objects.get(usuario__persona__dni=request.user.username)
        
        # Verificar si ya está inscrito en la comisión
        if Inscripcion.objects.filter(estudiante=estudiante, comision=comision).exists():
            messages.warning(request, '⚠️ Ya estás inscrito en esta comisión.')
            return redirect('landing')

        # Verificar inscripción en otra comisión del mismo curso
        curso = comision.fk_id_curso
        if Inscripcion.objects.filter(estudiante=estudiante, comision__fk_id_curso=curso).exists():
            messages.warning(request, f'⚠️ Ya estás inscrito en el curso "{curso.nombre}" (en esta u otra comisión). No se permiten inscripciones múltiples al mismo curso.')
            return redirect('landing')
            
        # Validar rango etario
        persona = estudiante.usuario.persona
        edad_alumno = persona.edad
        
        if edad_alumno is None:
            # Si el curso tiene restricciones de edad, requerimos que el usuario tenga fecha de nacimiento
            if curso.edad_minima or curso.edad_maxima:
                messages.warning(request, '⚠️ Para inscribirte a este curso, necesitamos conocer tu edad. Por favor, actualiza tu fecha de nacimiento en tu perfil.')
                return redirect('landing')
        else:
            if curso.edad_minima and edad_alumno < curso.edad_minima:
                messages.error(request, f'⛔ No cumples con la edad mínima requerida para este curso ({curso.edad_minima} años). Tienes {edad_alumno} años.')
                return redirect('landing')
            
            if curso.edad_maxima and edad_alumno > curso.edad_maxima:
                messages.error(request, f'⛔ Superas la edad máxima permitida para este curso ({curso.edad_maxima} años). Tienes {edad_alumno} años.')
                return redirect('landing')
        
        # Determinar estado y orden
        estado_inscripcion = 'confirmado'
        orden = None
        
        # Verificar cupo disponible usando la propiedad del modelo
        if comision.cupo_lleno:
            estado_inscripcion = 'lista_espera'
            ultimo_orden = Inscripcion.objects.filter(comision=comision, estado='lista_espera').aggregate(Max('orden_lista_espera'))['orden_lista_espera__max']
            orden = (ultimo_orden or 0) + 1
        
        # Obtener cupos antes de inscribir (solo relevante si es confirmado)
        cupos_antes = comision.cupos_disponibles
        
        # Crear inscripción
        Inscripcion.objects.create(
            estudiante=estudiante,
            comision=comision,
            estado=estado_inscripcion,
            orden_lista_espera=orden
        )
        
        curso_nombre = comision.fk_id_curso.nombre
        
        if estado_inscripcion == 'lista_espera':
             mensaje = f'📝 Te has inscrito en LISTA DE ESPERA para el curso "{curso_nombre}". Tu posición es: {orden}.'
             messages.warning(request, mensaje)
        else:
            # Calcular cupos restantes después de la inscripción
            cupos_restantes = cupos_antes - 1
            
            # Mensaje personalizado según cupos restantes
            if cupos_restantes == 0:
                messages.success(request, f'🎉 ¡Felicitaciones! Te has inscrito al curso "{curso_nombre}". ¡Has tomado el ÚLTIMO CUPO disponible!')
            elif cupos_restantes <= 3:
                messages.success(request, f'✅ ¡Inscripción exitosa al curso "{curso_nombre}"! ⚠️ Solo quedan {cupos_restantes} cupos disponibles.')
            elif cupos_restantes <= 10:
                messages.success(request, f'✅ ¡Inscripción exitosa al curso "{curso_nombre}"! Quedan {cupos_restantes} cupos.')
            else:
                messages.success(request, f'✅ ¡Inscripción exitosa al curso "{curso_nombre}"!')
        
    except Estudiante.DoesNotExist:
        messages.error(request, '❌ Debes ser un estudiante para inscribirte a cursos. Por favor, regístrate como estudiante.')
        return redirect('usuario:registro')
    except Exception as e:
        messages.error(request, f'❌ Error al inscribirse: {str(e)}')
    
    return redirect('landing')


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
        ).select_related('comision__fk_id_curso').order_by('-fecha_hora_inscripcion')
        
        return render(request, 'cursos/mis_inscripciones.html', {'inscripciones': inscripciones})
    except Estudiante.DoesNotExist:
        messages.error(request, 'No tienes perfil de estudiante.')
        return redirect('home')
