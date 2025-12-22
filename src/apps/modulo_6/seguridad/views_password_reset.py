from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta
from apps.modulo_1.usuario.models import Usuario, Persona

User = get_user_model()


def password_reset_request(request):
    """Vista para solicitar el reseteo de contraseña"""
    if request.method == 'POST':
        dni = request.POST.get('dni', '').strip()
        
        if not dni:
            messages.error(request, '❌ Por favor, ingresa tu DNI.')
            return render(request, 'registration/password_reset_request.html')
        
        email_confirm = request.POST.get('email', '').strip()
        if not email_confirm:
            messages.error(request, '❌ Por favor, confirma tu correo electrónico.')
            return render(request, 'registration/password_reset_request.html')
        
        try:
            # Buscar el usuario por DNI
            usuario = Usuario.objects.get(persona__dni=dni)
            persona = usuario.persona
            
            # Verificar si tiene email registrado
            if not persona.correo:
                messages.error(request, '❌ Tu cuenta no tiene un email registrado. Por favor, contacta al administrador.')
                return render(request, 'registration/password_reset_request.html')
                
            # Verificar que el email coincida (case insensitive)
            if persona.correo.strip().lower() != email_confirm.strip().lower():
                 messages.error(request, '❌ El correo electrónico no coincide con el registrado para este DNI.')
                 return render(request, 'registration/password_reset_request.html')
            
            # Generar token único
            token = get_random_string(length=32)
            
            # Guardar el token en la sesión (en producción, usar base de datos)
            request.session[f'password_reset_token_{dni}'] = {
                'token': token,
                'timestamp': timezone.now().isoformat(),
                'dni': dni
            }
            
            # Crear el enlace de reseteo
            reset_link = request.build_absolute_uri(
                f'/accounts/password-reset-confirm/?dni={dni}&token={token}'
            )
            
            # Enviar email
            subject = 'Recuperación de Contraseña - Edu-Polo'
            html_message = render_to_string('registration/password_reset_email.html', {
                'nombre': persona.nombre,
                'reset_link': reset_link,
                'dni': dni,
            })
            plain_message = strip_tags(html_message)
            
            try:
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [persona.correo],
                    html_message=html_message,
                    fail_silently=False,
                )
                messages.success(request, f'✅ Se ha enviado un email a {persona.correo} con las instrucciones para recuperar tu contraseña.')
                return redirect('login')
            except Exception as e:
                messages.error(request, f'❌ Error al enviar el email: {str(e)}. Por favor, contacta al administrador.')
                
        except Usuario.DoesNotExist:
            messages.error(request, '❌ No se encontró un usuario con ese DNI.')
        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
    
    return render(request, 'registration/password_reset_request.html')


def password_reset_confirm(request):
    """Vista para confirmar y cambiar la contraseña"""
    dni = request.GET.get('dni', '')
    token = request.GET.get('token', '')
    
    if not dni or not token:
        messages.error(request, '❌ Enlace inválido o expirado.')
        return redirect('password_reset_request')
    
    # Verificar el token en la sesión
    session_key = f'password_reset_token_{dni}'
    token_data = request.session.get(session_key)
    
    if not token_data or token_data.get('token') != token:
        messages.error(request, '❌ Token inválido o expirado.')
        return redirect('password_reset_request')
    
    # Verificar que el token no haya expirado (24 horas)
    try:
        timestamp = timezone.datetime.fromisoformat(token_data['timestamp'])
        if timezone.now() - timestamp > timedelta(hours=24):
            messages.error(request, '❌ El enlace ha expirado. Por favor, solicita uno nuevo.')
            del request.session[session_key]
            return redirect('password_reset_request')
    except:
        messages.error(request, '❌ Error al verificar el token.')
        return redirect('password_reset_request')
    
    if request.method == 'POST':
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        
        if not password or not password_confirm:
            messages.error(request, '❌ Por favor, completa todos los campos.')
            return render(request, 'registration/password_reset_confirm.html', {'dni': dni, 'token': token})
        
        if password != password_confirm:
            messages.error(request, '❌ Las contraseñas no coinciden.')
            return render(request, 'registration/password_reset_confirm.html', {'dni': dni, 'token': token})
        
        if len(password) < 6:
            messages.error(request, '❌ La contraseña debe tener al menos 6 caracteres.')
            return render(request, 'registration/password_reset_confirm.html', {'dni': dni, 'token': token})
        
        try:
            usuario = Usuario.objects.get(persona__dni=dni)
            usuario.contrasena = password
            usuario.save()

            django_user, _ = User.objects.get_or_create(
                username=dni,
                defaults={
                    'email': usuario.persona.correo or '',
                    'first_name': usuario.persona.nombre,
                    'last_name': usuario.persona.apellido,
                }
            )
            django_user.email = usuario.persona.correo or django_user.email
            django_user.first_name = usuario.persona.nombre
            django_user.last_name = usuario.persona.apellido
            django_user.set_password(password)
            django_user.save()
            
            # Eliminar el token de la sesión
            del request.session[session_key]
            
            messages.success(request, '✅ Tu contraseña ha sido actualizada exitosamente. Ahora puedes iniciar sesión.')
            return redirect('login')
        except Usuario.DoesNotExist:
            messages.error(request, '❌ Usuario no encontrado.')
        except Exception as e:
            messages.error(request, f'❌ Error al actualizar la contraseña: {str(e)}')
    
    return render(request, 'registration/password_reset_confirm.html', {'dni': dni, 'token': token})

