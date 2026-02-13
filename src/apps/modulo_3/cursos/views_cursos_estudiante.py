from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Prefetch, Q

from apps.modulo_1.roles.models import Estudiante
from apps.modulo_1.usuario.models import Persona
from .models import Curso, Comision


@login_required
def ver_cursos_disponibles(request):
    """Vista de cursos disponibles para estudiantes (su ciudad + virtual global)."""
    try:
        estudiante = Estudiante.objects.select_related('usuario__persona').get(
            usuario__persona__dni=request.user.username
        )
    except Estudiante.DoesNotExist:
        messages.error(request, 'No tienes perfil de estudiante.')
        return render(request, 'cursos/cursos_disponibles.html', {'cursos': Curso.objects.none()})

    ciudad = Persona.normalizar_ciudad(estudiante.usuario.persona.ciudad_residencia)
    if not ciudad:
        messages.warning(
            request,
            '⚠️ No tenés ciudad cargada en tu perfil. Completala en "Mi Perfil" para ver cursos disponibles en tu ciudad.'
        )
        return render(request, 'cursos/cursos_disponibles.html', {'cursos': Curso.objects.none()})

    virtual_global_q = Q(modalidad='Virtual', fk_id_polo__isnull=True)

    comisiones_ciudad_qs = Comision.objects.filter(
        Q(fk_id_polo__ciudad=ciudad) | virtual_global_q,
        publicada=True,
    ).select_related('fk_id_polo').prefetch_related('inscripciones').order_by('id_comision')

    cursos_scope_q = Q(comision__fk_id_polo__ciudad=ciudad) | Q(
        comision__modalidad='Virtual',
        comision__fk_id_polo__isnull=True,
    )

    cursos = (
        Curso.objects.filter(
            estado='Abierto',
            comision__publicada=True,
        )
        .filter(cursos_scope_q)
        .distinct()
        .prefetch_related(
            Prefetch('comision_set', queryset=comisiones_ciudad_qs, to_attr='comisiones_ciudad')
        )
    )

    return render(request, 'cursos/cursos_disponibles.html', {'cursos': cursos})





