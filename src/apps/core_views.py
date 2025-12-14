from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from apps.modulo_1.roles.models import Estudiante, Docente
from apps.modulo_2.inscripciones.models import Inscripcion


def landing(request):
    """
    Vista de la landing page
    - Muestra la página de inicio con login integrado
    """
    # Si el usuario ya está autenticado, redirigir al dashboard
    # if request.user.is_authenticated:
    #     return redirect('dashboard')

    from apps.modulo_3.cursos.models import PoloCreativo
    
    # Obtener todos los polos (por si se necesitan en el futuro)
    polos = PoloCreativo.objects.filter(activo=True)
    
    context = {
        'polos': polos,
    }
    return render(request, 'landing.html', context)


def lista_polos(request):
    """
    Vista para mostrar el listado de Polos Creativos y sus cursos
    """
    from apps.modulo_3.cursos.models import PoloCreativo
    
    polos = PoloCreativo.objects.filter(activo=True)
    
    context = {
        'polos': polos,
        'user_authenticated': request.user.is_authenticated
    }
    return render(request, 'landing_cursos.html', context)


def cursos_por_polo(request, polo_id):
    """
    Vista para mostrar los cursos de un Polo específico
    """
    from apps.modulo_3.cursos.models import Curso, PoloCreativo
    from django.shortcuts import get_object_or_404
    
    polo_seleccionado = get_object_or_404(PoloCreativo, id_polo=polo_id)
    
    # Obtener cursos disponibles con comisiones abiertas en este polo
    cursos = Curso.objects.filter(estado='Abierto').prefetch_related('comision_set__inscripciones').order_by('orden', 'id_curso')
    
    # Filtrar cursos que tengan comisiones en este polo
    cursos = cursos.filter(comision__fk_id_polo=polo_seleccionado).distinct()
            
    # Agregar comisiones abiertas a cada curso para este polo
    for curso in cursos:
        curso.comisiones_abiertas = curso.comision_set.filter(estado='Abierta', fk_id_polo=polo_seleccionado)
    
    context = {
        'polo_seleccionado': polo_seleccionado,
        'cursos': cursos,
        'user_authenticated': request.user.is_authenticated
    }
    return render(request, 'cursos_por_polo.html', context)


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
    
    # Verificar si es docente (DESHABILITADO TEMPORALMENTE)
    # try:
    #     docente = Docente.objects.get(id_persona__dni=request.user.username)
    #     return redirect('dashboard_docente')
    # except Docente.DoesNotExist:
    #     pass
    
    # Si no tiene rol específico, ir a admin
    return redirect('admin:index')


@login_required
def dashboard_estudiante(request):
    """Dashboard específico para estudiantes - Muestra cursos disponibles"""
    try:
        from apps.modulo_3.cursos.models import Curso
        from apps.modulo_4.asistencia.models import Asistencia
        from django.db.models import Count, Q
        
        estudiante = Estudiante.objects.get(usuario__persona__dni=request.user.username)
        
        # Obtener inscripciones activas (confirmadas)
        inscripciones = Inscripcion.objects.filter(
            estudiante=estudiante,
            estado='confirmado'
        ).select_related('comision__fk_id_curso', 'comision__fk_id_polo')
        
        inscripciones_activas_count = inscripciones.count()
        
        # Procesar datos para el dashboard (Asistencia y Progreso)
        cursos_activos = []
        asistencia_promedio_total = 0
        cursos_con_asistencia = 0
        
        for inscripcion in inscripciones:
            # Calcular asistencia
            total_clases = Asistencia.objects.filter(inscripcion=inscripcion).count()
            presentes = Asistencia.objects.filter(inscripcion=inscripcion, presente=True).count()
            
            porcentaje_asistencia = 0
            if total_clases > 0:
                porcentaje_asistencia = int((presentes / total_clases) * 100)
                asistencia_promedio_total += porcentaje_asistencia
                cursos_con_asistencia += 1
            
            cursos_activos.append({
                'nombre': inscripcion.comision.fk_id_curso.nombre,
                'comision': inscripcion.comision.id_comision,
                'polo': inscripcion.comision.fk_id_polo.nombre if inscripcion.comision.fk_id_polo else 'Virtual',
                'horarios': inscripcion.comision.dias_horarios,
                'asistencia': porcentaje_asistencia,
                'total_clases': total_clases,
                'presentes': presentes
            })
            
        # Calcular promedio general
        promedio_general = 0
        if cursos_con_asistencia > 0:
            promedio_general = int(asistencia_promedio_total / cursos_con_asistencia)
            
        # Certificados (simulado o real si existe modelo)
        # Por ahora 0 o lógica futura
        certificados_count = 0 
        
        # Próxima clase (Simulación basada en días, requeriría lógica compleja de calendario)
        # Por ahora mostramos un mensaje genérico o el primer curso
        proxima_clase = None
        if cursos_activos:
            proxima_clase = cursos_activos[0] # Simplificación
        
        context = {
            'estudiante': estudiante,
            'inscripciones_activas': inscripciones_activas_count,
            'cursos_activos': cursos_activos,
            'promedio_general': promedio_general,
            'certificados': certificados_count,
            'proxima_clase': proxima_clase
        }
        return render(request, 'dashboard/estudiante.html', context)
    except Estudiante.DoesNotExist:
        return redirect('admin:index')


@login_required
def dashboard_docente(request):
    """Dashboard específico para docentes"""
    # DESHABILITADO TEMPORALMENTE
    from django.contrib import messages
    messages.warning(request, 'El panel de docentes no está habilitado por el momento.')
    return redirect('dashboard')

    # try:
    #     from apps.modulo_1.usuario.models import Usuario
    """
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
    """


@login_required
def dashboard_admin(request):
    """Dashboard específico para administradores y mesa de entrada con estadísticas"""
    from apps.modulo_1.usuario.models import Usuario
    from apps.modulo_1.roles.models import UsuarioRol
    from django.utils import timezone
    
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
    from apps.modulo_4.asistencia.models import Asistencia
    from django.db.models import Count, F
    
    # Estadísticas generales
    total_cursos = Curso.objects.count()
    total_estudiantes = Estudiante.objects.count()
    total_docentes = Docente.objects.count()
    total_inscripciones = Inscripcion.objects.filter(estado='confirmado').count()
    
    # Métricas de Hoy
    hoy = timezone.now().date()
    inscripciones_hoy = Inscripcion.objects.filter(fecha_hora_inscripcion__date=hoy).count()
    asistencias_hoy = Asistencia.objects.filter(fecha_clase=hoy, presente=True).count()
    
    # Cursos más populares (con más inscripciones)
    cursos_populares = Curso.objects.annotate(
        total_inscripciones=Count('comision__inscripciones')
    ).filter(total_inscripciones__gt=0).order_by('-total_inscripciones')[:5]
    
    # Estado de comisiones y Alertas de Cupo
    comisiones_abiertas = Comision.objects.filter(estado='Abierta').count()
    comisiones_cerradas = Comision.objects.filter(estado='Cerrada').count()
    comisiones_finalizadas = Comision.objects.filter(estado='Finalizada').count()
    
    # Alertas de Cupo (Comisiones abiertas con 5 o menos lugares)
    alertas_cupo = []
    comisiones_activas = Comision.objects.filter(estado='Abierta').prefetch_related('inscripciones')
    
    for comision in comisiones_activas:
        if comision.cupos_disponibles <= 5 and comision.cupos_disponibles > 0:
            alertas_cupo.append({
                'nombre': f"{comision.fk_id_curso.nombre} (Com #{comision.id_comision})",
                'cupos_restantes': comision.cupos_disponibles,
                'total': comision.cupo_maximo,
                'porcentaje': comision.porcentaje_ocupacion
            })
    
    # Nuevas preinscripciones para el modal
    nuevas_preinscripciones = Inscripcion.objects.filter(
        estado='pre_inscripto'
    ).select_related(
        'estudiante__usuario__persona',
        'comision__fk_id_curso'
    ).order_by('-fecha_hora_inscripcion')
    
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
        'inscripciones_hoy': inscripciones_hoy,
        'asistencias_hoy': asistencias_hoy,
        'cursos_populares': cursos_populares,
        'comisiones_abiertas': comisiones_abiertas,
        'comisiones_cerradas': comisiones_cerradas,
        'comisiones_finalizadas': comisiones_finalizadas,
        'alertas_cupo': alertas_cupo,
        'tipo_usuario': tipo_usuario,
        'puede_crear_usuarios': puede_crear_usuarios,
        'es_admin_completo': es_admin_completo,
        'nuevas_preinscripciones': nuevas_preinscripciones,
    }
    return render(request, 'dashboard/admin.html', context)

