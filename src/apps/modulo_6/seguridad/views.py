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
            return redirect('landing')
        
        # Autenticar usando el backend personalizado
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            remember_me = request.POST.get('remember_me') == 'on'

            login(request, user)
            if remember_me:
                request.session.set_expiry(60 * 60 * 24 * 30)
            else:
                request.session.set_expiry(0)

            messages.success(request, f'¡Bienvenido/a, {user.first_name}!')

            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, '❌ DNI o contraseña incorrectos. Por favor, verifica tus datos.')
            return redirect('landing')
    
    # Si es GET, redirigir a la landing
    return redirect('landing')
