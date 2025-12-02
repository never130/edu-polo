from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from apps.modulo_1.roles.models import Estudiante, Docente
from apps.modulo_2.inscripciones.models import Inscripcion


def landing(request):
    """
    Vista de la landing page
    - Muestra cursos disponibles públicamente con login lateral
    - Si está logueado: Puede inscribirse directamente
    """
    from apps.modulo_3.cursos.models import Curso
    
    # Obtener cursos disponibles con comisiones abiertas, ordenados por el campo 'orden'
    cursos = Curso.objects.filter(estado='Abierto').prefetch_related('comision_set__inscripciones').order_by('orden', 'id_curso')
    
    # Agregar comisiones abiertas a cada curso
    for curso in cursos:
        curso.comisiones_abiertas = curso.comision_set.filter(estado='Abierta')
    
    context = {
        'cursos': cursos,
        'user_authenticated': request.user.is_authenticated
    }
    return render(request, 'landing_cursos.html', context)


@login_required
def dashboard(request):
    """Dashboard principal que redirige según el rol del usuario"""
    from apps.modulo_1.usuario.models import Usuario
    from apps.modulo_1.roles.models import UsuarioRol
    
    # Verificar si es administrador/staff
    if request.user.is_staff or request.user.is_superuser:
        return redirect('dashboard_admin')
    
    # Verificar roles de administrador o mesa de entrada
    try:
        usuario = Usuario.objects.get(persona__dni=request.user.username)
        roles = UsuarioRol.objects.filter(usuario_id=usuario).values_list('rol_id__nombre', flat=True)
        if 'Administrador' in roles or 'Mesa de Entrada' in roles:
            return redirect('dashboard_admin')
    except Usuario.DoesNotExist:
        pass
    
    # Verificar si es estudiante
    try:
        estudiante = Estudiante.objects.get(usuario__persona__dni=request.user.username)
        return redirect('dashboard_estudiante')
    except Estudiante.DoesNotExist:
        pass
    
    # Verificar si es docente
    try:
        docente = Docente.objects.get(id_persona__dni=request.user.username)
        return redirect('dashboard_docente')
    except Docente.DoesNotExist:
        pass
    
    # Si no tiene rol específico, ir a admin
    return redirect('admin:index')


@login_required
def dashboard_estudiante(request):
    """Dashboard específico para estudiantes - Muestra cursos disponibles"""
    try:
        from apps.modulo_3.cursos.models import Curso
        
        estudiante = Estudiante.objects.get(usuario__persona__dni=request.user.username)
        inscripciones_activas = Inscripcion.objects.filter(
            estudiante=estudiante,
            estado='confirmado'
        ).count()
        
        # Obtener cursos disponibles con comisiones abiertas
        cursos = Curso.objects.filter(estado='Abierto')
        for curso in cursos:
            curso.comisiones_abiertas = curso.comision_set.filter(estado='Abierta')
        
        context = {
            'estudiante': estudiante,
            'inscripciones_activas': inscripciones_activas,
            'cursos_disponibles': cursos.count(),
            'cursos': cursos[:6],  # Mostrar solo los primeros 6 cursos en el dashboard
        }
        return render(request, 'dashboard/estudiante.html', context)
    except Estudiante.DoesNotExist:
        return redirect('admin:index')


@login_required
def dashboard_docente(request):
    """Dashboard específico para docentes"""
    try:
        from apps.modulo_1.usuario.models import Usuario
        from apps.modulo_3.cursos.models import ComisionDocente
        
        docente = Docente.objects.get(id_persona__dni=request.user.username)
        
        # Obtener el usuario asociado al docente
        try:
            usuario = Usuario.objects.get(persona=docente.id_persona)
            # Verificar si tiene comisiones asignadas
            comisiones_asignadas = ComisionDocente.objects.filter(fk_id_docente=usuario).count()
            tiene_cursos = comisiones_asignadas > 0
        except Usuario.DoesNotExist:
            tiene_cursos = False
        
        context = {
            'docente': docente,
            'tiene_cursos': tiene_cursos,
            'comisiones_asignadas': comisiones_asignadas if 'comisiones_asignadas' in locals() else 0,
        }
        return render(request, 'dashboard/docente.html', context)
    except Docente.DoesNotExist:
        return redirect('admin:index')


@login_required
def dashboard_admin(request):
    """Dashboard específico para administradores y mesa de entrada con estadísticas"""
    from apps.modulo_1.usuario.models import Usuario
    from apps.modulo_1.roles.models import UsuarioRol
    
    # Verificar si es staff o superuser (administrador Django)
    es_admin_django = request.user.is_staff or request.user.is_superuser
    
    # Verificar si tiene rol de Administrador o Mesa de Entrada
    es_admin_rol = False
    try:
        usuario = Usuario.objects.get(persona__dni=request.user.username)
        roles = UsuarioRol.objects.filter(usuario_id=usuario).values_list('rol_id__nombre', flat=True)
        es_admin_rol = 'Administrador' in roles or 'Mesa de Entrada' in roles
    except Usuario.DoesNotExist:
        pass
    
    if not (es_admin_django or es_admin_rol):
        return redirect('dashboard')
    
    from apps.modulo_3.cursos.models import Curso, Comision
    from django.db.models import Count
    
    # Estadísticas generales
    total_cursos = Curso.objects.count()
    total_estudiantes = Estudiante.objects.count()
    total_docentes = Docente.objects.count()
    total_inscripciones = Inscripcion.objects.filter(estado='confirmado').count()
    
    # Cursos más populares (con más inscripciones)
    cursos_populares = Curso.objects.annotate(
        total_inscripciones=Count('comision__inscripciones')
    ).filter(total_inscripciones__gt=0).order_by('-total_inscripciones')[:5]
    
    # Estado de comisiones
    comisiones_abiertas = Comision.objects.filter(estado='Abierta').count()
    comisiones_cerradas = Comision.objects.filter(estado='Cerrada').count()
    comisiones_finalizadas = Comision.objects.filter(estado='Finalizada').count()
    
    # Determinar el tipo de usuario para el template
    tipo_usuario = 'Administrador'
    puede_crear_usuarios = es_admin_django
    es_admin_completo = es_admin_django
    if not es_admin_django:
        try:
            usuario = Usuario.objects.get(persona__dni=request.user.username)
            roles = UsuarioRol.objects.filter(usuario_id=usuario).values_list('rol_id__nombre', flat=True)
            if 'Mesa de Entrada' in roles:
                tipo_usuario = 'Mesa de Entrada'
                es_admin_completo = False
            elif 'Administrador' in roles:
                tipo_usuario = 'Administrador'
                puede_crear_usuarios = True
                es_admin_completo = True
        except Usuario.DoesNotExist:
            pass
    
    context = {
        'total_cursos': total_cursos,
        'total_estudiantes': total_estudiantes,
        'total_docentes': total_docentes,
        'total_inscripciones': total_inscripciones,
        'cursos_populares': cursos_populares,
        'comisiones_abiertas': comisiones_abiertas,
        'comisiones_cerradas': comisiones_cerradas,
        'comisiones_finalizadas': comisiones_finalizadas,
        'tipo_usuario': tipo_usuario,
        'puede_crear_usuarios': puede_crear_usuarios,
        'es_admin_completo': es_admin_completo,
    }
    return render(request, 'dashboard/admin.html', context)

