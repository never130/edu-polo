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
    from django.db.models import Count, F, Q

    polo_seleccionado = get_object_or_404(PoloCreativo, id_polo=polo_id)

    hoy_real = date.today()

    cursos = (
        Curso.objects.filter(estado='Abierto')
        .prefetch_related('comision_set__inscripciones')
        .order_by('orden', 'id_curso')
        .filter(comision__fk_id_polo=polo_seleccionado)
        .distinct()
    )

    cursos_visibles = []

    for curso in cursos:
        curso.comisiones_abiertas = (
            curso.comision_set.filter(
                estado='Abierta',
                fk_id_polo=polo_seleccionado,
            )
            .exclude(Q(fecha_fin__isnull=False, fecha_fin__lte=hoy_real))
            .annotate(
                inscritos_count_annotated=Count(
                    'inscripciones',
                    filter=~Q(inscripciones__estado__in=['lista_espera', 'cancelada']),
                )
            )
            .filter(inscritos_count_annotated__lt=F('cupo_maximo'))
            .order_by('id_comision')
        )

        curso.comisiones_polo = list(
            curso.comision_set.filter(
                fk_id_polo=polo_seleccionado,
            )
            .exclude(estado__in=['Cerrada', 'Finalizada'])
            .exclude(Q(fecha_fin__isnull=False, fecha_fin__lte=hoy_real))
            .order_by('id_comision')
        )

        if curso.comisiones_polo:
            cursos_visibles.append(curso)

    context = {
        'polo_seleccionado': polo_seleccionado,
        'cursos': cursos_visibles,
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
        
        # Verificar si es empresa (Prioridad sobre estudiante)
        if hasattr(usuario, 'empresa') or 'Empresa' in roles:
            return redirect('dashboard_empresa')

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
    
    # Si no tiene rol específico, enviar a cursos/landing (usuario general)
    return redirect('lista_polos')


@login_required
def dashboard_empresa(request):
    from apps.modulo_1.usuario.models import Usuario
    from apps.modulo_1.roles.models import UsuarioRol
    from apps.modulo_7.empresas.models import Empresa

    try:
        usuario = Usuario.objects.get(persona__dni=request.user.username)
    except Usuario.DoesNotExist:
        return redirect('dashboard')

    roles = UsuarioRol.objects.filter(usuario_id=usuario).values_list('rol_id__nombre', flat=True)
    if not (hasattr(usuario, 'empresa') or 'Empresa' in roles):
        return redirect('dashboard')

    empresa = Empresa.objects.filter(responsable=usuario).first()
    context = {
        'persona': usuario.persona,
        'empresa': empresa,
    }
    return render(request, 'dashboard/empresa.html', context)


@login_required
def dashboard_estudiante(request):
    """Dashboard específico para estudiantes - Muestra cursos disponibles"""
    try:
        from apps.modulo_3.cursos.models import Curso
        from apps.modulo_4.asistencia.models import RegistroAsistencia
        from django.db.models import Count, Q
        
        estudiante = Estudiante.objects.get(usuario__persona__dni=request.user.username)

        inscripciones_pendientes = Inscripcion.objects.filter(
            estudiante=estudiante,
        ).exclude(
            estado__in=['confirmado', 'cancelada'],
        ).select_related('comision__fk_id_curso', 'comision__fk_id_polo')

        inscripciones_lista_espera = inscripciones_pendientes.filter(
            estado='lista_espera',
        ).order_by('orden_lista_espera', 'fecha_hora_inscripcion', 'id')

        inscripciones_preinscriptas = inscripciones_pendientes.filter(
            estado='pre_inscripto',
        ).order_by('-fecha_hora_inscripcion', '-id')

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
        hoy = date.today()

        for inscripcion in inscripciones:
            registro, _ = RegistroAsistencia.objects.get_or_create(inscripcion=inscripcion)
            registro.calcular_porcentaje()

            total_clases = registro.total_clases
            presentes = registro.clases_asistidas
            porcentaje_asistencia = int(registro.porcentaje_asistencia)

            if total_clases and total_clases > 0:
                asistencia_promedio_total += porcentaje_asistencia
                cursos_con_asistencia += 1

            comision = inscripcion.comision

            es_finalizada = (
                comision.estado == 'Finalizada'
                or (comision.fecha_fin and comision.fecha_fin < hoy)
            )
            if es_finalizada:
                continue

            if comision.fecha_inicio and comision.fecha_inicio > hoy:
                estado_ui = 'Por iniciar'
            elif comision.estado == 'En proceso':
                estado_ui = 'En curso'
            else:
                estado_ui = 'En curso'

            proxima_fecha = None
            try:
                fechas = comision.get_fechas_clase_programadas(hasta=comision.fecha_fin)
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
                'presentes': presentes,
                'estado_ui': estado_ui,
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

        inscripciones_activas_count = len(cursos_activos)
        persona = estudiante.usuario.persona
        
        context = {
            'estudiante': estudiante,
            'persona': persona,
            'es_mayor_de_edad': bool(getattr(persona, 'es_mayor_de_edad', False)),
            'inscripciones_activas': inscripciones_activas_count,
            'inscripciones_preinscripto': inscripciones_preinscriptas[:5],
            'inscripciones_lista_espera': inscripciones_lista_espera[:5],
            'preinscripto_count': inscripciones_preinscriptas.count(),
            'lista_espera_count': inscripciones_lista_espera.count(),
            'cursos_activos': cursos_activos,
            'promedio_general': promedio_general,
            'certificados': certificados_count,
            'proxima_clase': proxima_clase,
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
    from datetime import datetime
    
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
    hoy_real = hoy

    fecha_agenda = hoy_real

    Comision.objects.filter(fecha_fin__lt=hoy_real).exclude(estado='Finalizada').update(estado='Finalizada')
    
    # Estadísticas generales
    total_cursos = Curso.objects.count()
    total_estudiantes = Estudiante.objects.count()
    total_docentes = Docente.objects.count()
    total_inscripciones = Inscripcion.objects.filter(estado='confirmado').count()
    
    # Métricas de Hoy
    inscripciones_hoy_qs = Inscripcion.objects.filter(fecha_hora_inscripcion__date=hoy_real)
    inscripciones_hoy = inscripciones_hoy_qs.count()
    asistencias_hoy = Asistencia.objects.filter(fecha_clase=hoy_real, presente=True).count()
    
    # Cursos más populares (con más inscripciones)
    cursos_populares = Curso.objects.annotate(
        total_inscripciones=Count('comision__inscripciones')
    ).filter(total_inscripciones__gt=0).order_by('-total_inscripciones')[:5]
    
    # Estado de comisiones y Alertas de Cupo
    # Para el dashboard, consideramos "Finalizada" también cuando ya pasó (o llegó) la fecha_fin,
    # aunque el campo estado todavía no haya sido actualizado.
    finalizadas_q = Q(estado='Finalizada') | Q(fecha_fin__isnull=False, fecha_fin__lte=hoy_real)

    comisiones_finalizadas = Comision.objects.filter(finalizadas_q).count()
    comisiones_abiertas = Comision.objects.filter(estado='Abierta').exclude(finalizadas_q).count()
    comisiones_cerradas = Comision.objects.filter(estado='Cerrada').exclude(finalizadas_q).count()
    
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

    dia_semana = fecha_agenda.weekday()
    dia_variantes = {
        0: ['lunes', 'lun'],
        1: ['martes', 'mar'],
        2: ['miércoles', 'miercoles', 'mié', 'mie', 'mier'],
        3: ['jueves', 'jue'],
        4: ['viernes', 'vie'],
        5: ['sábado', 'sabado', 'sáb', 'sab'],
        6: ['domingo', 'dom'],
    }.get(dia_semana, [])

    filtro_dia = Q()
    for v in dia_variantes:
        filtro_dia |= Q(dias_horarios__icontains=v)

    comisiones_hoy_qs = Comision.objects.select_related('fk_id_curso', 'fk_id_polo').exclude(
        estado='Finalizada'
    ).filter(
        Q(fecha_inicio__isnull=True) | Q(fecha_inicio__lte=fecha_agenda),
        Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha_agenda),
    )

    if filtro_dia:
        comisiones_hoy_qs = comisiones_hoy_qs.filter(filtro_dia)
    else:
        comisiones_hoy_qs = Comision.objects.none()

    comisiones_hoy_qs = comisiones_hoy_qs.order_by('fk_id_curso__nombre', 'id_comision')

    if tipo_usuario == 'Mesa de Entrada':
        if ciudad_mesa_entrada:
            comisiones_hoy_qs = comisiones_hoy_qs.filter(fk_id_polo__ciudad=ciudad_mesa_entrada)
        else:
            comisiones_hoy_qs = Comision.objects.none()

    comisiones_hoy = list(comisiones_hoy_qs[:50])

    comisiones_hoy_cards = []
    comision_ids_hoy = [int(c.id_comision) for c in comisiones_hoy]

    series_por_comision = {}
    if comision_ids_hoy:
        series_raw = list(
            Asistencia.objects.filter(
                inscripcion__estado='confirmado',
                inscripcion__comision_id__in=comision_ids_hoy,
            ).values('inscripcion__comision_id', 'fecha_clase').annotate(
                total=Count('pk'),
                presentes=Count('pk', filter=Q(presente=True)),
            ).order_by('fecha_clase')
        )

        for row in series_raw:
            com_id = row.get('inscripcion__comision_id')
            fecha = row.get('fecha_clase')
            total = int(row.get('total') or 0)
            presentes = int(row.get('presentes') or 0)
            if com_id is None or fecha is None or total <= 0:
                continue
            porcentaje = round((presentes / total) * 100, 0)
            series_por_comision.setdefault(int(com_id), []).append({'fecha': fecha, 'valor': max(min(int(porcentaje), 100), 0)})

    def _sparkline_points(valores, width=120, height=24, pad=2):
        valores = [max(min(int(v), 100), 0) for v in (valores or [])]
        if not valores:
            return ''
        if len(valores) == 1:
            valores = [valores[0], valores[0]]
        inner_w = max(width - 2 * pad, 1)
        inner_h = max(height - 2 * pad, 1)
        step = inner_w / max(len(valores) - 1, 1)
        pts = []
        for i, v in enumerate(valores):
            x = pad + (step * i)
            y = pad + (inner_h * (1 - (v / 100)))
            pts.append(f"{x:.1f},{y:.1f}")
        return ' '.join(pts)

    def _parse_time_range(texto):
        import re
        t = (texto or '').lower()
        times = re.findall(r"\b([01]?\d|2[0-3])[:\.]([0-5]\d)\b", t)
        if len(times) >= 2:
            sh, sm = int(times[0][0]), int(times[0][1])
            eh, em = int(times[1][0]), int(times[1][1])
        else:
            m = re.search(r"\b([01]?\d|2[0-3])\s*(?:hs|h)?\s*(?:a|\-|–|—)\s*([01]?\d|2[0-3])(?:[:\.]([0-5]\d))?\b", t)
            if not m:
                return None
            sh = int(m.group(1))
            sm = 0
            eh = int(m.group(2))
            em = int(m.group(3) or 0)
        start_min = (sh * 60) + sm
        end_min = (eh * 60) + em
        if end_min <= start_min:
            end_min = start_min + 60
        return {
            'start_min': start_min,
            'end_min': end_min,
            'start_label': f"{sh:02d}:{sm:02d}",
            'end_label': f"{eh:02d}:{em:02d}",
        }

    palette = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4']
    agenda_row_h = 40
    agenda_start_min = 8 * 60
    agenda_end_min = 22 * 60

    agenda_timed_items = []
    agenda_untimed_items = []

    for comision in comisiones_hoy:
        com_id = int(comision.id_comision)
        serie = series_por_comision.get(com_id, [])
        serie = sorted(serie, key=lambda x: x['fecha'])
        ultimos = serie[-8:]
        valores = [int(x['valor']) for x in ultimos]
        puntos = _sparkline_points(valores)
        has_data = len(valores) > 0

        color = palette[com_id % len(palette)]
        time_range = _parse_time_range(comision.dias_horarios or '')

        card = {
            'comision': comision,
            'color': color,
            'sparkline_points': puntos,
            'sparkline_has_data': has_data,
            'sparkline_value': (valores[-1] if has_data else 0),
            'sparkline_count': len(valores),
        }
        comisiones_hoy_cards.append(card)

        if time_range:
            start_min = max(int(time_range['start_min']), agenda_start_min)
            end_min = min(int(time_range['end_min']), agenda_end_min)
            if end_min <= start_min:
                end_min = min(start_min + 60, agenda_end_min)

            top = int(round(((start_min - agenda_start_min) / 60) * agenda_row_h, 0))
            height = int(max(round(((end_min - start_min) / 60) * agenda_row_h, 0), 30))

            agenda_timed_items.append({
                **card,
                'start_min': start_min,
                'end_min': end_min,
                'start_label': time_range['start_label'],
                'end_label': time_range['end_label'],
                'top': top,
                'height': height,
            })
        else:
            agenda_untimed_items.append(card)

    agenda_timed_items.sort(key=lambda x: (int(x.get('start_min') or 0), int(x.get('end_min') or 0)))
    lane_ends = []
    for ev in agenda_timed_items:
        placed = False
        for i, end_min in enumerate(lane_ends):
            if int(ev['start_min']) >= int(end_min):
                ev['lane'] = i
                lane_ends[i] = int(ev['end_min'])
                placed = True
                break
        if not placed:
            ev['lane'] = len(lane_ends)
            lane_ends.append(int(ev['end_min']))

    total_lanes = max(len(lane_ends), 1)
    width_pct = round(100 / total_lanes, 4)
    for ev in agenda_timed_items:
        ev['width_pct'] = width_pct
        ev['left_pct'] = round(int(ev.get('lane') or 0) * width_pct, 4)

    agenda_hours = [f"{h:02d}:00" for h in range(8, 23)]
    agenda_timeline_height = max((len(agenda_hours) - 1) * agenda_row_h, 1)

    import calendar
    meses = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
        7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre',
    }
    mini_calendar_year = int(fecha_agenda.year)
    mini_calendar_month = int(fecha_agenda.month)

    cal = calendar.Calendar(firstweekday=0)
    mini_calendar_weeks = cal.monthdatescalendar(mini_calendar_year, mini_calendar_month)
    mini_calendar_month_label = f"{meses.get(mini_calendar_month, mini_calendar_month)} de {mini_calendar_year}"
    actual_today = hoy_real

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
                inscritos_total=Count('inscripciones', filter=~Q(inscripciones__estado__in=['lista_espera', 'cancelada'])),
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
        'fecha_hoy': fecha_agenda,
        'actual_today': actual_today,
        'comisiones_hoy': comisiones_hoy,
        'comisiones_hoy_cards': comisiones_hoy_cards,
        'agenda_timed_items': agenda_timed_items,
        'agenda_untimed_items': agenda_untimed_items,
        'agenda_hours': agenda_hours,
        'agenda_timeline_height': agenda_timeline_height,
        'mini_calendar_weeks': mini_calendar_weeks,
        'mini_calendar_month_label': mini_calendar_month_label,
        'mini_calendar_year': mini_calendar_year,
        'mini_calendar_month': mini_calendar_month,
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
            'condiciones_medicas': (persona.condiciones_medicas or '').strip(),
            'autorizacion_imagen': bool(persona.autorizacion_imagen),
            'autorizacion_voz': bool(persona.autorizacion_voz),
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
            inscritos_total=Count('inscripciones', filter=~Q(inscripciones__estado__in=['lista_espera', 'cancelada', 'rechazada'])),
            confirmados_total=Count('inscripciones', filter=Q(inscripciones__estado__in=['confirmado', 'aprobada'])),
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
