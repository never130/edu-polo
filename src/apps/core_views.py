from datetime import date

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
    from django.db.models import Case, IntegerField, When
    
    polos = PoloCreativo.objects.filter(activo=True).order_by(
        Case(
            When(id_polo=1, then=0),
            When(id_polo=2, then=1),
            When(id_polo=3, then=2),
            When(id_polo=4, then=3),
            default=99,
            output_field=IntegerField(),
        ),
        'id_polo',
    )
    
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
        from apps.modulo_4.asistencia.models import RegistroAsistencia
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
            registro, _ = RegistroAsistencia.objects.get_or_create(inscripcion=inscripcion)
            registro.calcular_porcentaje()

            total_clases = registro.total_clases
            presentes = registro.clases_asistidas
            porcentaje_asistencia = int(registro.porcentaje_asistencia)

            if total_clases > 0:
                asistencia_promedio_total += porcentaje_asistencia
                cursos_con_asistencia += 1
            
            comision = inscripcion.comision
            proxima_fecha = None
            try:
                fechas = comision.get_fechas_clase_programadas(hasta=comision.fecha_fin)
                hoy = date.today()
                for f in fechas:
                    if f >= hoy:
                        proxima_fecha = f
                        break
            except Exception:
                proxima_fecha = None

            cursos_activos.append({
                'nombre': comision.fk_id_curso.nombre,
                'comision': comision.id_comision,
                'polo': comision.fk_id_polo.nombre if comision.fk_id_polo else 'Virtual',
                'horarios': comision.dias_horarios,
                'proxima_fecha': proxima_fecha,
                'asistencia': porcentaje_asistencia,
                'total_clases': total_clases,
                'presentes': presentes
            })
            
        # Calcular promedio general
        promedio_general = 0
        if cursos_con_asistencia > 0:
            promedio_general = int(asistencia_promedio_total / cursos_con_asistencia)
            
        certificados_count = RegistroAsistencia.objects.filter(
            inscripcion__estudiante=estudiante,
            cumple_requisito_certificado=True,
        ).count()
        
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
    from django.db.models import Count, F, Q

    hoy = timezone.now().date()
    Comision.objects.filter(fecha_fin__lt=hoy).exclude(estado='Finalizada').update(estado='Finalizada')
    
    # Estadísticas generales
    total_cursos = Curso.objects.count()
    total_estudiantes = Estudiante.objects.count()
    total_docentes = Docente.objects.count()
    total_inscripciones = Inscripcion.objects.filter(estado='confirmado').count()
    
    # Métricas de Hoy
    inscripciones_hoy_qs = Inscripcion.objects.filter(fecha_hora_inscripcion__date=hoy)
    inscripciones_hoy = inscripciones_hoy_qs.count()
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
        'comision__fk_id_curso',
        'comision__fk_id_polo'
    ).order_by('-fecha_hora_inscripcion')
    
    # Determinar el tipo de usuario para el template
    tipo_usuario = 'Administrador'
    puede_crear_usuarios = es_admin_django
    es_admin_completo = es_admin_django
    ciudad_mesa_entrada = None
    if not es_admin_django:
        try:
            usuario = Usuario.objects.get(persona__dni=request.user.username)
            roles = UsuarioRol.objects.filter(usuario_id=usuario).values_list('rol_id__nombre', flat=True)
            if 'Mesa de Entrada' in roles:
                tipo_usuario = 'Mesa de Entrada'
                es_admin_completo = False
                ciudad_mesa_entrada = usuario.persona.ciudad_residencia
            elif 'Administrador' in roles:
                tipo_usuario = 'Administrador'
                puede_crear_usuarios = True
                es_admin_completo = True
        except Usuario.DoesNotExist:
            pass

    if tipo_usuario == 'Mesa de Entrada':
        if ciudad_mesa_entrada:
            nuevas_preinscripciones = nuevas_preinscripciones.filter(
                comision__fk_id_polo__ciudad=ciudad_mesa_entrada
            )
            inscripciones_hoy = inscripciones_hoy_qs.filter(
                comision__fk_id_polo__ciudad=ciudad_mesa_entrada
            ).count()
        else:
            nuevas_preinscripciones = Inscripcion.objects.none()
            inscripciones_hoy = 0

    inscripciones_confirmadas_qs = Inscripcion.objects.filter(estado='confirmado')
    if tipo_usuario == 'Mesa de Entrada':
        if ciudad_mesa_entrada:
            inscripciones_confirmadas_qs = inscripciones_confirmadas_qs.filter(comision__fk_id_polo__ciudad=ciudad_mesa_entrada)
        else:
            inscripciones_confirmadas_qs = Inscripcion.objects.none()

    estudiantes_por_curso = list(
        inscripciones_confirmadas_qs.values(
            'comision__fk_id_curso_id',
            'comision__fk_id_curso__nombre',
        )
        .annotate(total_estudiantes=Count('estudiante', distinct=True))
        .order_by('comision__fk_id_curso__nombre')
    )

    curso_ids = sorted({c.get('comision__fk_id_curso_id') for c in estudiantes_por_curso if c.get('comision__fk_id_curso_id')})
    comisiones_por_curso = {}
    if curso_ids:
        comisiones_qs = Comision.objects.filter(fk_id_curso_id__in=curso_ids).select_related('fk_id_polo')
        if tipo_usuario == 'Mesa de Entrada':
            if ciudad_mesa_entrada:
                comisiones_qs = comisiones_qs.filter(fk_id_polo__ciudad=ciudad_mesa_entrada)
            else:
                comisiones_qs = Comision.objects.none()

        comisiones_data = list(
            comisiones_qs.annotate(
                inscritos_total=Count('inscripciones', filter=Q(inscripciones__estado__in=['confirmado', 'pre_inscripto'])),
                confirmados_total=Count('inscripciones', filter=Q(inscripciones__estado='confirmado')),
            ).values(
                'id_comision',
                'fk_id_curso_id',
                'cupo_maximo',
                'inscritos_total',
                'confirmados_total',
                'fk_id_polo__nombre',
            )
        )

        for com in comisiones_data:
            curso_id = com.get('fk_id_curso_id')
            cupo_maximo = int(com.get('cupo_maximo') or 0)
            inscritos_total = int(com.get('inscritos_total') or 0)
            com['cupos_disponibles'] = max(cupo_maximo - inscritos_total, 0)
            comisiones_por_curso.setdefault(curso_id, []).append(com)

        for curso_id, coms in comisiones_por_curso.items():
            coms.sort(key=lambda x: int(x.get('id_comision') or 0))

    for c in estudiantes_por_curso:
        cid = c.get('comision__fk_id_curso_id')
        c['comisiones'] = comisiones_por_curso.get(cid, [])

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
        'ciudad_mesa_entrada': ciudad_mesa_entrada,
        'estudiantes_por_curso': estudiantes_por_curso,
    }
    return render(request, 'dashboard/admin.html', context)


@login_required
def api_estudiantes_por_curso(request):
    from django.http import JsonResponse
    from apps.modulo_1.usuario.models import Usuario
    from apps.modulo_1.roles.models import UsuarioRol
    from apps.modulo_3.cursos.models import Curso

    if not (request.user.is_staff or request.user.is_superuser):
        try:
            usuario = Usuario.objects.get(persona__dni=request.user.username)
            roles = UsuarioRol.objects.filter(usuario_id=usuario).values_list('rol_id__nombre', flat=True)
            if 'Administrador' not in roles and 'Mesa de Entrada' not in roles:
                return JsonResponse({'error': 'No autorizado.'}, status=403)
        except Usuario.DoesNotExist:
            return JsonResponse({'error': 'No autorizado.'}, status=403)

    curso_id = (request.GET.get('curso_id') or '').strip()
    if not curso_id:
        return JsonResponse({'error': 'curso_id requerido.'}, status=400)

    try:
        curso = Curso.objects.get(id_curso=curso_id)
    except Curso.DoesNotExist:
        return JsonResponse({'error': 'Curso no encontrado.'}, status=404)

    tipo_usuario = 'Administrador'
    ciudad_mesa_entrada = None

    if not (request.user.is_staff or request.user.is_superuser):
        try:
            usuario = Usuario.objects.get(persona__dni=request.user.username)
            roles = UsuarioRol.objects.filter(usuario_id=usuario).values_list('rol_id__nombre', flat=True)
            if 'Mesa de Entrada' in roles and 'Administrador' not in roles:
                tipo_usuario = 'Mesa de Entrada'
                ciudad_mesa_entrada = usuario.persona.ciudad_residencia
        except Usuario.DoesNotExist:
            pass

    qs = Inscripcion.objects.filter(
        estado='confirmado',
        comision__fk_id_curso_id=curso.id_curso,
    ).select_related('estudiante__usuario__persona', 'comision', 'comision__fk_id_polo')

    if tipo_usuario == 'Mesa de Entrada':
        if ciudad_mesa_entrada:
            qs = qs.filter(comision__fk_id_polo__ciudad=ciudad_mesa_entrada)
        else:
            qs = Inscripcion.objects.none()

    data_estudiantes = []
    seen_dni = set()
    for ins in qs.order_by(
        'estudiante__usuario__persona__apellido',
        'estudiante__usuario__persona__nombre',
        'comision_id',
    ):
        persona = ins.estudiante.usuario.persona
        dni = (persona.dni or '').strip()
        if dni in seen_dni:
            continue
        seen_dni.add(dni)

        nombre = (persona.nombre or '').strip()
        apellido = (persona.apellido or '').strip()
        data_estudiantes.append({
            'dni': dni,
            'nombre_completo': f"{nombre} {apellido}".strip(),
            'correo': (persona.correo or '').strip(),
            'telefono': (persona.telefono or '').strip(),
            'ciudad_residencia': (persona.ciudad_residencia or '').strip(),
            'comision_id': getattr(ins.comision, 'id_comision', None),
        })

    from apps.modulo_3.cursos.models import Comision
    from django.db.models import Count, Q

    comisiones_qs = Comision.objects.filter(fk_id_curso_id=curso.id_curso).select_related('fk_id_polo')
    if tipo_usuario == 'Mesa de Entrada':
        if ciudad_mesa_entrada:
            comisiones_qs = comisiones_qs.filter(fk_id_polo__ciudad=ciudad_mesa_entrada)
        else:
            comisiones_qs = Comision.objects.none()

    comisiones_data = list(
        comisiones_qs.annotate(
            inscritos_total=Count('inscripciones', filter=Q(inscripciones__estado__in=['confirmado', 'pre_inscripto'])),
            confirmados_total=Count('inscripciones', filter=Q(inscripciones__estado='confirmado')),
        ).values(
            'id_comision',
            'cupo_maximo',
            'inscritos_total',
            'confirmados_total',
            'fk_id_polo__nombre',
        )
    )
    for com in comisiones_data:
        cupo_maximo = int(com.get('cupo_maximo') or 0)
        inscritos_total = int(com.get('inscritos_total') or 0)
        com['cupos_disponibles'] = max(cupo_maximo - inscritos_total, 0)

    return JsonResponse({
        'curso_id': curso.id_curso,
        'curso_nombre': curso.nombre,
        'ciudad_mesa_entrada': ciudad_mesa_entrada,
        'total_estudiantes': len(data_estudiantes),
        'comisiones': comisiones_data,
        'estudiantes': data_estudiantes,
    })
