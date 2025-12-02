from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache


@csrf_protect
@never_cache
def custom_login(request):
    """Vista de login personalizada"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            messages.error(request, 'Por favor, ingresa tu DNI y contraseña.')
            return redirect('login')
        
        # Autenticar usando el backend personalizado
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido/a, {user.first_name}!')
            
            # Redirigir según el rol del usuario
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, '❌ DNI o contraseña incorrectos. Por favor, verifica tus datos.')
    
    # Renderizar la landing con cursos
    from apps.modulo_3.cursos.models import Curso
    
    cursos = Curso.objects.filter(estado='Abierto').prefetch_related('comision_set__inscripciones')
    
    for curso in cursos:
        curso.comisiones_abiertas = curso.comision_set.filter(estado='Abierta')
    
    context = {
        'cursos': cursos,
        'user_authenticated': False
    }
    return render(request, 'landing_cursos.html', context)
