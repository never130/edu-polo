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
        'es_empresa': False,
    }
    
    if request.user.is_authenticated:
        es_admin_django = request.user.is_staff or request.user.is_superuser
        if es_admin_django:
            context['es_admin_completo'] = True
            context['tipo_usuario'] = 'Administrador'
            context['puede_ver_asistencias'] = True
        try:
            usuario = Usuario.objects.get(persona__dni=request.user.username)
        except Usuario.DoesNotExist:
            usuario = None

        if usuario is not None:
            roles = UsuarioRol.objects.filter(usuario_id=usuario).values_list('rol_id__nombre', flat=True)

            if 'Empresa' in roles or hasattr(usuario, 'empresa'):
                context['es_empresa'] = True

            if Estudiante.objects.filter(usuario=usuario).exists():
                context['es_estudiante'] = True
                if not context['tipo_usuario']:
                    context['tipo_usuario'] = 'Estudiante'

            if Docente.objects.filter(id_persona=usuario.persona).exists():
                context['es_docente'] = True
                from apps.modulo_3.cursos.models import ComisionDocente
                tiene_comisiones = ComisionDocente.objects.filter(fk_id_docente=usuario).exists()
                if tiene_comisiones and not es_admin_django:
                    context['tipo_usuario'] = 'Docente'
                    context['puede_ver_asistencias'] = True

            if context['es_empresa'] and not context['tipo_usuario']:
                context['tipo_usuario'] = 'Empresa'

            if not es_admin_django:
                if 'Mesa de Entrada' in roles:
                    context['tipo_usuario'] = 'Mesa de Entrada'
                    context['es_admin_completo'] = False
                    context['puede_ver_asistencias'] = True
                elif 'Administrador' in roles:
                    context['tipo_usuario'] = 'Administrador'
                    context['es_admin_completo'] = True
                    context['puede_ver_asistencias'] = True
    
    return context
