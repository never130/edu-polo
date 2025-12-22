from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Prefetch

from apps.modulo_1.roles.models import Estudiante
from .models import Curso, Comision


@login_required
def ver_cursos_disponibles(request):
    """Vista de cursos disponibles para estudiantes (solo su ciudad)."""
    try:
        estudiante = Estudiante.objects.select_related('usuario__persona').get(
            usuario__persona__dni=request.user.username
        )
    except Estudiante.DoesNotExist:
        messages.error(request, 'No tienes perfil de estudiante.')
        return render(request, 'cursos/cursos_disponibles.html', {'cursos': Curso.objects.none()})

    ciudad = estudiante.usuario.persona.ciudad_residencia
    if not ciudad:
        messages.warning(
            request,
            '⚠️ No tenés ciudad cargada en tu perfil. Completala en "Mi Perfil" para ver cursos disponibles en tu ciudad.'
        )
        return render(request, 'cursos/cursos_disponibles.html', {'cursos': Curso.objects.none()})

    comisiones_abiertas_qs = Comision.objects.filter(
        estado='Abierta',
        fk_id_polo__ciudad=ciudad,
    ).select_related('fk_id_polo').prefetch_related('inscripciones')

    cursos = (
        Curso.objects.filter(
            estado='Abierto',
            comision__estado='Abierta',
            comision__fk_id_polo__ciudad=ciudad,
        )
        .distinct()
        .prefetch_related(
            Prefetch('comision_set', queryset=comisiones_abiertas_qs, to_attr='comisiones_abiertas')
        )
    )

    return render(request, 'cursos/cursos_disponibles.html', {'cursos': cursos})





