from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Curso


@login_required
def ver_cursos_disponibles(request):
    """
    Vista de cursos disponibles SOLO para usuarios logueados.
    Muestra todos los cursos con sus comisiones y cupos en tiempo real.
    """
    # Obtener cursos disponibles con comisiones abiertas
    cursos = Curso.objects.filter(estado='Abierto').prefetch_related('comision_set__inscripciones')
    
    # Agregar comisiones abiertas a cada curso
    for curso in cursos:
        curso.comisiones_abiertas = curso.comision_set.filter(estado='Abierta')
    
    context = {
        'cursos': cursos,
    }
    return render(request, 'cursos/cursos_disponibles.html', context)





