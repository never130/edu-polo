from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.db import transaction
from apps.modulo_1.usuario.models import Persona, Usuario
from apps.modulo_1.roles.models import Estudiante, Docente, UsuarioRol, Rol
from datetime import date


@login_required
def mi_perfil(request):
    """Vista del perfil del usuario con opción de edición"""
    try:
        # Obtener la persona asociada al usuario logueado
        usuario = Usuario.objects.get(persona__dni=request.user.username)
        persona = usuario.persona
        
        # Determinar el tipo de usuario
        es_estudiante = Estudiante.objects.filter(usuario=usuario).exists()
        es_docente = Docente.objects.filter(id_persona=persona).exists()
        
        # Verificar roles
        roles = UsuarioRol.objects.filter(usuario_id=usuario).values_list('rol_id__nombre', flat=True)
        es_admin = 'Administrador' in roles or request.user.is_staff
        es_mesa_entrada = 'Mesa de Entrada' in roles
        
        # Obtener información adicional según el tipo
        perfil_adicional = None
        if es_estudiante:
            perfil_adicional = Estudiante.objects.get(usuario=usuario)
            tipo_usuario = 'Estudiante'
        elif es_docente:
            perfil_adicional = Docente.objects.get(id_persona=persona)
            tipo_usuario = 'Docente'
        elif es_admin:
            tipo_usuario = 'Administrador'
        elif es_mesa_entrada:
            tipo_usuario = 'Mesa de Entrada'
        else:
            tipo_usuario = 'Usuario'
        
        context = {
            'persona': persona,
            'usuario': usuario,
            'perfil_adicional': perfil_adicional,
            'tipo_usuario': tipo_usuario,
            'es_estudiante': es_estudiante,
            'es_docente': es_docente,
            'es_admin': es_admin,
            'es_mesa_entrada': es_mesa_entrada,
            'puede_crear_usuarios': es_admin,  # Solo administradores pueden crear usuarios
        }
        return render(request, 'usuario/mi_perfil.html', context)
    except Usuario.DoesNotExist:
        # Si es superuser y no tiene perfil, crearlo automáticamente
        if request.user.is_superuser:
            try:
                with transaction.atomic():
                    # Preparar correo único
                    base_email = request.user.email or f'admin_{request.user.username}@example.com'
                    email = base_email
                    
                    # Verificar si el correo ya existe en otra persona
                    if Persona.objects.filter(correo=email).exclude(dni=request.user.username).exists():
                        import time
                        email = f"{int(time.time())}_{base_email}"

                    # Crear o recuperar Persona (usando username como DNI si es posible)
                    persona, created = Persona.objects.get_or_create(
                        dni=request.user.username,
                        defaults={
                            'nombre': request.user.first_name or 'Administrador',
                            'apellido': request.user.last_name or 'Sistema',
                            'correo': email,
                        }
                    )
                    
                    # Si la persona ya existía pero no tenía correo, actualizarlo si es necesario
                    if not created and not persona.correo:
                         persona.correo = email
                         persona.save()
                    
                    # Crear Usuario
                    usuario, created = Usuario.objects.get_or_create(
                        persona=persona,
                        defaults={
                            'contrasena': 'admin_managed_via_django',
                            'activo': True
                        }
                    )
                    
                    # Asignar Rol Administrador
                    rol_admin, _ = Rol.objects.get_or_create(
                        nombre='Administrador', 
                        defaults={'descripcion': 'Administrador del sistema', 'jerarquia': 1}
                    )
                    
                    UsuarioRol.objects.get_or_create(usuario_id=usuario, rol_id=rol_admin)
                    
                    messages.success(request, 'Perfil de administrador generado automáticamente.')
                    return redirect('usuario:mi_perfil')
            except Exception as e:
                messages.error(request, f'Error al generar perfil de administrador: {str(e)}')
                return redirect('dashboard')

        messages.error(request, 'No se encontró tu perfil de usuario.')
        return redirect('dashboard')


@login_required
def editar_perfil(request):
    """Vista para editar los datos personales del usuario"""
    try:
        usuario = Usuario.objects.get(persona__dni=request.user.username)
        persona = usuario.persona
        
        # Determinar el tipo de usuario
        es_estudiante = Estudiante.objects.filter(usuario=usuario).exists()
        es_docente = Docente.objects.filter(id_persona=persona).exists()
        
        # Verificar roles
        roles = UsuarioRol.objects.filter(usuario_id=usuario).values_list('rol_id__nombre', flat=True)
        es_admin = 'Administrador' in roles or request.user.is_staff
        es_mesa_entrada = 'Mesa de Entrada' in roles
        
        perfil_adicional = None
        if es_estudiante:
            perfil_adicional = Estudiante.objects.get(usuario=usuario)
        elif es_docente:
            perfil_adicional = Docente.objects.get(id_persona=persona)
        
        if request.method == 'POST':
            try:
                with transaction.atomic():
                    # Actualizar datos personales básicos
                    persona.nombre = request.POST.get('nombre', persona.nombre)
                    persona.apellido = request.POST.get('apellido', persona.apellido)
                    persona.telefono = request.POST.get('telefono', persona.telefono)
                    persona.correo = request.POST.get('correo', persona.correo)
                    
                    # Fecha de nacimiento
                    fecha_nac = request.POST.get('fecha_nacimiento')
                    if fecha_nac:
                        try:
                            fecha_nac_date = date.fromisoformat(fecha_nac)
                        except ValueError:
                            messages.error(request, '❌ La fecha de nacimiento no es válida.')
                            return redirect('usuario:editar_perfil')

                        if fecha_nac_date > date.today():
                            messages.error(request, '❌ La fecha de nacimiento no puede ser futura.')
                            return redirect('usuario:editar_perfil')

                        persona.fecha_nacimiento = fecha_nac_date
                    
                    # Género
                    persona.genero = request.POST.get('genero', persona.genero)
                    
                    # Dirección
                    persona.ciudad_residencia = request.POST.get('ciudad_residencia', persona.ciudad_residencia)
                    persona.zona_residencia = request.POST.get('zona_residencia', persona.zona_residencia)
                    persona.domicilio = request.POST.get('domicilio', persona.domicilio)
                    
                    # Condiciones médicas
                    persona.condiciones_medicas = request.POST.get('condiciones_medicas', persona.condiciones_medicas)
                    
                    # Autorizaciones
                    persona.autorizacion_imagen = request.POST.get('autorizacion_imagen') == 'on'
                    persona.autorizacion_voz = request.POST.get('autorizacion_voz') == 'on'
                    
                    persona.save()
                    
                    # Actualizar datos adicionales según el tipo de usuario
                    if es_estudiante and perfil_adicional:
                        perfil_adicional.nivel_estudios = request.POST.get('nivel_estudios', perfil_adicional.nivel_estudios)
                        perfil_adicional.institucion_actual = request.POST.get('institucion_actual', perfil_adicional.institucion_actual)
                        perfil_adicional.save()
                    
                    elif es_docente and perfil_adicional:
                        perfil_adicional.especialidad = request.POST.get('especialidad', perfil_adicional.especialidad)
                        perfil_adicional.experiencia_anios = request.POST.get('experiencia_anios', perfil_adicional.experiencia_anios)
                        perfil_adicional.save()
                    
                    messages.success(request, '✅ ¡Perfil actualizado exitosamente!')
                    return redirect('usuario:mi_perfil')
                    
            except Exception as e:
                messages.error(request, f'❌ Error al actualizar el perfil: {str(e)}')
        
        # Determinar tipo de usuario para el template
        if es_estudiante:
            tipo_usuario = 'Estudiante'
        elif es_docente:
            tipo_usuario = 'Docente'
        elif es_admin:
            tipo_usuario = 'Administrador'
        elif es_mesa_entrada:
            tipo_usuario = 'Mesa de Entrada'
        else:
            tipo_usuario = 'Usuario'
        
        context = {
            'persona': persona,
            'usuario': usuario,
            'perfil_adicional': perfil_adicional,
            'es_estudiante': es_estudiante,
            'es_docente': es_docente,
            'es_admin': es_admin,
            'es_mesa_entrada': es_mesa_entrada,
            'tipo_usuario': tipo_usuario,
        }
        return render(request, 'usuario/editar_perfil.html', context)
        
    except Usuario.DoesNotExist:
        if request.user.is_superuser:
            return redirect('usuario:mi_perfil')
        messages.error(request, 'No se encontró tu perfil de usuario.')
        return redirect('dashboard')


@login_required
def cambiar_contrasena(request):
    """Vista para cambiar la contraseña del usuario"""
    try:
        usuario = Usuario.objects.get(persona__dni=request.user.username)
        persona = usuario.persona
        
        # Verificar roles para el template
        es_estudiante = Estudiante.objects.filter(usuario=usuario).exists()
        es_docente = Docente.objects.filter(id_persona=persona).exists()
        roles = UsuarioRol.objects.filter(usuario_id=usuario).values_list('rol_id__nombre', flat=True)
        es_admin = 'Administrador' in roles or request.user.is_staff
        es_mesa_entrada = 'Mesa de Entrada' in roles
        
        # Determinar tipo de usuario
        if es_estudiante:
            tipo_usuario = 'Estudiante'
        elif es_docente:
            tipo_usuario = 'Docente'
        elif es_admin:
            tipo_usuario = 'Administrador'
        elif es_mesa_entrada:
            tipo_usuario = 'Mesa de Entrada'
        else:
            tipo_usuario = 'Usuario'
        
        if request.method == 'POST':
            contrasena_actual = request.POST.get('contrasena_actual')
            contrasena_nueva = request.POST.get('contrasena_nueva')
            contrasena_confirmar = request.POST.get('contrasena_confirmar')
            
            # Validar contraseña actual
            if usuario.contrasena != contrasena_actual:
                messages.error(request, '❌ La contraseña actual es incorrecta.')
                context = {
                    'persona': persona,
                    'tipo_usuario': tipo_usuario,
                    'es_admin': es_admin,
                    'es_mesa_entrada': es_mesa_entrada,
                    'es_docente': es_docente,
                    'es_estudiante': es_estudiante,
                }
                return render(request, 'usuario/cambiar_contrasena.html', context)
            
            # Validar que las contraseñas nuevas coincidan
            if contrasena_nueva != contrasena_confirmar:
                messages.error(request, '❌ Las contraseñas nuevas no coinciden.')
                context = {
                    'persona': persona,
                    'tipo_usuario': tipo_usuario,
                    'es_admin': es_admin,
                    'es_mesa_entrada': es_mesa_entrada,
                    'es_docente': es_docente,
                    'es_estudiante': es_estudiante,
                }
                return render(request, 'usuario/cambiar_contrasena.html', context)
            
            # Validar longitud mínima
            if len(contrasena_nueva) < 6:
                messages.error(request, '❌ La contraseña debe tener al menos 6 caracteres.')
                context = {
                    'persona': persona,
                    'tipo_usuario': tipo_usuario,
                    'es_admin': es_admin,
                    'es_mesa_entrada': es_mesa_entrada,
                    'es_docente': es_docente,
                    'es_estudiante': es_estudiante,
                }
                return render(request, 'usuario/cambiar_contrasena.html', context)
            
            # Actualizar contraseña
            usuario.contrasena = contrasena_nueva
            usuario.save()

            request.user.set_password(contrasena_nueva)
            request.user.save()
            update_session_auth_hash(request, request.user)
            
            messages.success(request, '✅ ¡Contraseña actualizada exitosamente!')
            return redirect('usuario:mi_perfil')
        
        context = {
            'persona': persona,
            'tipo_usuario': tipo_usuario,
            'es_admin': es_admin,
            'es_mesa_entrada': es_mesa_entrada,
            'es_docente': es_docente,
            'es_estudiante': es_estudiante,
        }
        return render(request, 'usuario/cambiar_contrasena.html', context)
        
    except Usuario.DoesNotExist:
        if request.user.is_superuser:
            return redirect('usuario:mi_perfil')
        messages.error(request, 'No se encontró tu perfil de usuario.')
        return redirect('dashboard')

