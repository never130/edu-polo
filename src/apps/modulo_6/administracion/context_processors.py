from apps.modulo_1.usuario.models import Usuario
from apps.modulo_1.roles.models import UsuarioRol, Docente, Estudiante


def admin_context(request):
    """Context processor para agregar variables de administración a todos los templates"""
    context = {
        'es_admin_completo': False,
        'tipo_usuario': None,
        'puede_ver_asistencias': False,
        'es_docente': False,
        'es_estudiante': False,
    }
    
    if request.user.is_authenticated:
        # Verificar si es staff o superuser (administrador Django)
        if request.user.is_staff or request.user.is_superuser:
            context['es_admin_completo'] = True
            context['tipo_usuario'] = 'Administrador'
            context['puede_ver_asistencias'] = True
        else:
            # Verificar roles
            try:
                usuario = Usuario.objects.get(persona__dni=request.user.username)
                roles = UsuarioRol.objects.filter(usuario_id=usuario).values_list('rol_id__nombre', flat=True)
                
                # Verificar si es estudiante
                if Estudiante.objects.filter(usuario=usuario).exists():
                    context['es_estudiante'] = True
                    context['tipo_usuario'] = 'Estudiante'
                
                # Verificar si es docente
                if Docente.objects.filter(id_persona=usuario.persona).exists():
                    context['es_docente'] = True
                    from apps.modulo_3.cursos.models import ComisionDocente
                    tiene_comisiones = ComisionDocente.objects.filter(fk_id_docente=usuario).exists()
                    if tiene_comisiones:
                        context['tipo_usuario'] = 'Docente'
                        context['puede_ver_asistencias'] = True
                
                if 'Mesa de Entrada' in roles:
                    context['tipo_usuario'] = 'Mesa de Entrada'
                    context['es_admin_completo'] = False
                    context['puede_ver_asistencias'] = True
                elif 'Administrador' in roles:
                    context['tipo_usuario'] = 'Administrador'
                    context['es_admin_completo'] = True
                    context['puede_ver_asistencias'] = True
            except Usuario.DoesNotExist:
                pass
    
    return context

