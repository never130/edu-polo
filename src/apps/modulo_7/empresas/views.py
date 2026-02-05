from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView

from apps.modulo_1.usuario.models import Usuario
from apps.modulo_1.roles.models import Estudiante
from apps.modulo_6.administracion.views import es_admin_completo, es_admin_o_mesa

from .forms import AgregarMiembroForm, ActualizarLogoEmpresaForm, EmpresaForm, RechazarEmpresaForm
from .models import Empresa, MiembroEmpresa, PlanHorarioEmpresa, TurnoEmpresa

import calendar
from datetime import date, datetime, timedelta


def _obtener_usuario_app(request):
    try:
        return Usuario.objects.get(persona__dni=request.user.username)
    except Usuario.DoesNotExist:
        return None


def _es_mayor_de_edad(usuario):
    if not usuario or not usuario.persona:
        return False
    edad = usuario.persona.edad
    return edad is not None and edad >= 18


def _parse_periodo_ym(periodo_raw, default_date):
    if periodo_raw:
        try:
            anio_str, mes_str = str(periodo_raw).split('-', 1)
            anio = int(anio_str)
            mes = int(mes_str)
            if 1 <= mes <= 12 and 1900 <= anio <= 2100:
                return anio, mes, f'{anio:04d}-{mes:02d}'
        except (TypeError, ValueError):
            pass
    anio = int(default_date.year)
    mes = int(default_date.month)
    return anio, mes, f'{anio:04d}-{mes:02d}'


@login_required
def mi_empresa(request):
    usuario = _obtener_usuario_app(request)
    if not usuario:
        messages.error(request, 'No se encontró tu perfil de usuario.')
        return redirect('dashboard')

    if Estudiante.objects.filter(usuario=usuario).exists() and not hasattr(usuario, 'empresa'):
        messages.error(request, 'Esta sección no está disponible para estudiantes.')
        return redirect('dashboard')

    if not _es_mayor_de_edad(usuario):
        messages.error(request, 'Esta sección está disponible solo para mayores de 18 años.')
        return redirect('dashboard')

    empresa = Empresa.objects.filter(responsable=usuario).first()
    if empresa and empresa.estado == 'aprobada':
        return redirect('empresas:equipo')

    puede_editar = (empresa is None) or (empresa.estado == 'rechazada')

    if request.method == 'POST':
        if empresa and empresa.estado == 'aprobada':
            messages.error(request, 'Tu empresa ya fue aprobada.')
            return redirect('empresas:mi_empresa')

        if empresa and empresa.estado == 'pendiente':
            messages.error(request, 'Tu solicitud está en revisión. No podés editarla hasta que sea rechazada.')
            return redirect('empresas:mi_empresa')

        form = EmpresaForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.responsable = usuario
            if empresa and empresa.estado == 'rechazada':
                obj.estado = 'pendiente'
                obj.motivo_rechazo = None
                obj.rechazado_por = None
                obj.rechazado_en = None
            elif not empresa:
                obj.estado = 'pendiente'
            obj.save()
            messages.success(request, 'Solicitud enviada. Estado: Pendiente.')
            return redirect('empresas:mi_empresa')
    else:
        form = EmpresaForm(instance=empresa)

    if not puede_editar:
        for field in form.fields.values():
            field.disabled = True

    context = {
        'persona': usuario.persona,
        'empresa': empresa,
        'form': form,
        'puede_editar': puede_editar,
    }
    return render(request, 'empresas/mi_empresa.html', context)


@login_required
def equipo(request):
    usuario = _obtener_usuario_app(request)
    if not usuario:
        messages.error(request, 'No se encontró tu perfil de usuario.')
        return redirect('dashboard')

    if not _es_mayor_de_edad(usuario):
        messages.error(request, 'Esta sección está disponible solo para mayores de 18 años.')
        return redirect('dashboard')

    empresa = Empresa.objects.filter(responsable=usuario).first()
    if not empresa:
        messages.error(request, 'Primero debés crear tu solicitud de empresa.')
        return redirect('empresas:mi_empresa')

    if empresa.estado != 'aprobada':
        messages.error(request, 'La gestión de equipo se habilita cuando la empresa está aprobada.')
        return redirect('empresas:mi_empresa')

    if request.method == 'POST':
        accion = (request.POST.get('accion') or '').strip().lower()

        if accion == 'logo':
            logo_form = ActualizarLogoEmpresaForm(request.POST, request.FILES, instance=empresa)
            form = AgregarMiembroForm()
            if logo_form.is_valid():
                logo_form.save()
                messages.success(request, 'Logo actualizado.')
                return redirect('empresas:equipo')

        else:
            form = AgregarMiembroForm(request.POST)
            logo_form = ActualizarLogoEmpresaForm(instance=empresa)
            if form.is_valid():
                usuario_obj = form.cleaned_data['dni_usuario']
                rol = (form.cleaned_data.get('rol') or '').strip() or None
                es_socio = bool(form.cleaned_data.get('es_socio'))
                MiembroEmpresa.objects.update_or_create(
                    empresa=empresa,
                    usuario=usuario_obj,
                    defaults={'rol': rol, 'es_socio': es_socio},
                )
                messages.success(request, 'Miembro agregado/actualizado.')
                return redirect('empresas:equipo')

    else:
        form = AgregarMiembroForm()
        logo_form = ActualizarLogoEmpresaForm(instance=empresa)

    miembros = MiembroEmpresa.objects.filter(empresa=empresa).select_related('usuario__persona')
    context = {
        'persona': usuario.persona,
        'empresa': empresa,
        'miembros': miembros,
        'form': form,
        'logo_form': logo_form,
    }
    return render(request, 'empresas/equipo.html', context)


@login_required
def asistencia_empresas(request):
    usuario = _obtener_usuario_app(request)
    if not usuario:
        messages.error(request, 'No se encontró tu perfil de usuario.')
        return redirect('dashboard')

    if Estudiante.objects.filter(usuario=usuario).exists() and not hasattr(usuario, 'empresa'):
        messages.error(request, 'Esta sección no está disponible para estudiantes.')
        return redirect('dashboard')

    if not _es_mayor_de_edad(usuario):
        messages.error(request, 'Esta sección está disponible solo para mayores de 18 años.')
        return redirect('dashboard')

    empresa = Empresa.objects.filter(responsable=usuario).first()
    hoy = timezone.localdate()

    turnos = []
    resumen_mes = None
    if empresa:
        inicio = hoy - timedelta(days=30)
        fin = hoy + timedelta(days=30)
        turnos = list(
            TurnoEmpresa.objects.filter(empresa=empresa, fecha__range=(inicio, fin))
            .order_by('fecha', 'hora_desde')
        )

        anio, mes, periodo = _parse_periodo_ym(request.GET.get('periodo'), hoy)
        desde_mes = date(anio, mes, 1)
        hasta_mes = date(anio, mes, calendar.monthrange(anio, mes)[1])
        qs_mes = TurnoEmpresa.objects.filter(empresa=empresa, fecha__range=(desde_mes, hasta_mes))
        resumen_mes = {
            'anio': anio,
            'mes': mes,
            'periodo': periodo,
            'total': qs_mes.count(),
            'presente': qs_mes.filter(estado_asistencia='presente').count(),
            'ausente': qs_mes.filter(estado_asistencia='ausente').count(),
            'sin_marcar': qs_mes.filter(estado_asistencia__isnull=True).count(),
        }
    context = {
        'persona': usuario.persona,
        'empresa': empresa,
        'turnos': turnos,
        'resumen_mes': resumen_mes,
        'hoy': hoy,
    }
    return render(request, 'empresas/asistencia_empresas.html', context)


def _parse_dias_semana(raw_list):
    dias = []
    for v in raw_list:
        try:
            n = int(str(v).strip())
        except (TypeError, ValueError):
            continue
        if 0 <= n <= 6:
            dias.append(n)
    dias = sorted(set(dias))
    return dias


def _iter_fechas(inicio, fin):
    actual = inicio
    while actual <= fin:
        yield actual
        actual += timedelta(days=1)


@login_required
@user_passes_test(es_admin_completo)
def turnos_admin(request):
    empresas_aprobadas = list(
        Empresa.objects.filter(estado='aprobada').order_by('nombre')
    )

    hoy = timezone.localdate()
    planes = list(
        PlanHorarioEmpresa.objects.select_related('empresa')
        .filter(empresa__estado='aprobada')
        .order_by('-actualizado')
    )
    dias_label = {
        0: 'Lun',
        1: 'Mar',
        2: 'Mié',
        3: 'Jue',
        4: 'Vie',
        5: 'Sáb',
        6: 'Dom',
    }
    for p in planes:
        raw = (p.dias_semana or '').strip()
        dias = []
        if raw:
            for token in raw.split(','):
                token = (token or '').strip()
                if not token:
                    continue
                try:
                    n = int(token)
                except (TypeError, ValueError):
                    continue
                if 0 <= n <= 6:
                    dias.append(n)
        dias = sorted(set(dias))
        p.dias_semana_labels = [dias_label[d] for d in dias] if dias else []
        p.dias_semana_display = ', '.join(p.dias_semana_labels) if p.dias_semana_labels else '-'

    anio_rep, mes_rep, periodo_rep = _parse_periodo_ym(request.GET.get('periodo'), hoy)
    desde_rep = date(anio_rep, mes_rep, 1)
    hasta_rep = date(anio_rep, mes_rep, calendar.monthrange(anio_rep, mes_rep)[1])

    reporte_rows = list(
        TurnoEmpresa.objects.filter(
            empresa__estado='aprobada',
            fecha__range=(desde_rep, hasta_rep),
        )
        .values('empresa_id', 'empresa__nombre')
        .annotate(
            total=Count('id'),
            presente=Count('id', filter=Q(estado_asistencia='presente')),
            ausente=Count('id', filter=Q(estado_asistencia='ausente')),
            sin_marcar=Count('id', filter=Q(estado_asistencia__isnull=True)),
        )
        .order_by('empresa__nombre')
    )
    for row in reporte_rows:
        presentes = int(row.get('presente') or 0)
        ausentes = int(row.get('ausente') or 0)
        denom = presentes + ausentes
        row['cumplimiento'] = round((presentes / denom * 100), 2) if denom > 0 else None

    totales = {
        'total': sum(int(r.get('total') or 0) for r in reporte_rows),
        'presente': sum(int(r.get('presente') or 0) for r in reporte_rows),
        'ausente': sum(int(r.get('ausente') or 0) for r in reporte_rows),
        'sin_marcar': sum(int(r.get('sin_marcar') or 0) for r in reporte_rows),
    }
    denom_total = int(totales.get('presente') or 0) + int(totales.get('ausente') or 0)
    totales['cumplimiento'] = round((totales['presente'] / denom_total * 100), 2) if denom_total > 0 else None

    reporte_mensual = {
        'anio': anio_rep,
        'mes': mes_rep,
        'periodo': periodo_rep,
        'desde': desde_rep,
        'hasta': hasta_rep,
        'rows': reporte_rows,
        'totales': totales,
    }

    if request.method == 'POST':
        accion = (request.POST.get('accion') or '').strip().lower()

        if accion == 'crear_plan':
            empresa_id = request.POST.get('empresa_id')
            fecha_inicio_raw = request.POST.get('fecha_inicio')
            fecha_fin_raw = request.POST.get('fecha_fin')
            hora_desde_raw = request.POST.get('hora_desde')
            hora_hasta_raw = request.POST.get('hora_hasta')
            dias_raw = request.POST.getlist('dias_semana')

            empresa = Empresa.objects.filter(id=empresa_id, estado='aprobada').first()
            if not empresa:
                messages.error(request, 'La empresa debe existir y estar aprobada.')
                return redirect('empresas:turnos_admin')

            try:
                fecha_inicio = datetime.strptime(fecha_inicio_raw, '%Y-%m-%d').date()
                fecha_fin = datetime.strptime(fecha_fin_raw, '%Y-%m-%d').date()
            except (TypeError, ValueError):
                messages.error(request, 'Fechas inválidas.')
                return redirect('empresas:turnos_admin')

            try:
                hora_desde = datetime.strptime(hora_desde_raw, '%H:%M').time()
                hora_hasta = datetime.strptime(hora_hasta_raw, '%H:%M').time()
            except (TypeError, ValueError):
                messages.error(request, 'Horarios inválidos.')
                return redirect('empresas:turnos_admin')

            if fecha_inicio > fecha_fin:
                messages.error(request, 'La fecha de inicio no puede ser mayor a la fecha fin.')
                return redirect('empresas:turnos_admin')

            if hora_desde >= hora_hasta:
                messages.error(request, 'El horario "desde" debe ser menor al "hasta".')
                return redirect('empresas:turnos_admin')

            es_un_solo_dia = fecha_inicio == fecha_fin
            if es_un_solo_dia:
                dias = [fecha_inicio.weekday()]
            else:
                dias = _parse_dias_semana(dias_raw)
                if not dias:
                    messages.error(request, 'Seleccioná al menos un día de la semana.')
                    return redirect('empresas:turnos_admin')

            with transaction.atomic():
                plan = PlanHorarioEmpresa.objects.create(
                    empresa=empresa,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    hora_desde=hora_desde,
                    hora_hasta=hora_hasta,
                    dias_semana=','.join(str(d) for d in dias),
                    activo=True,
                    creado_por=request.user,
                )

                turnos_a_crear = []
                for f in _iter_fechas(fecha_inicio, fecha_fin):
                    if f.weekday() not in dias:
                        continue
                    turnos_a_crear.append(
                        TurnoEmpresa(
                            empresa=empresa,
                            plan=plan,
                            fecha=f,
                            hora_desde=hora_desde,
                            hora_hasta=hora_hasta,
                            estado_asistencia=None,
                        )
                    )

                if turnos_a_crear:
                    TurnoEmpresa.objects.bulk_create(turnos_a_crear, ignore_conflicts=True)

            messages.success(request, 'Plan creado y turnos generados.')
            return redirect('empresas:turnos_admin')

        if accion == 'toggle_plan':
            plan_id = request.POST.get('plan_id')
            plan = PlanHorarioEmpresa.objects.select_related('empresa').filter(id=plan_id).first()
            if not plan:
                messages.error(request, 'No se encontró el plan.')
                return redirect('empresas:turnos_admin')
            plan.activo = not plan.activo
            plan.save(update_fields=['activo', 'actualizado'])
            messages.success(request, 'Plan actualizado.')
            return redirect('empresas:turnos_admin')


    context = {
        'empresas_aprobadas': empresas_aprobadas,
        'planes': planes,
        'hoy': hoy,
        'reporte_mensual': reporte_mensual,
    }
    return render(request, 'empresas/turnos_admin.html', context)


@login_required
@user_passes_test(es_admin_o_mesa)
def turnos_hoy(request):
    hoy = timezone.localdate()
    fecha_raw = (request.GET.get('fecha') or request.POST.get('fecha') or '').strip()
    if fecha_raw:
        try:
            fecha_seleccionada = datetime.strptime(fecha_raw, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            fecha_seleccionada = hoy
    else:
        fecha_seleccionada = hoy

    empresa_id = (request.GET.get('empresa_id') or request.POST.get('empresa_id') or '').strip()
    turnos = list(
        TurnoEmpresa.objects.select_related('empresa')
        .filter(fecha=fecha_seleccionada, empresa__estado='aprobada')
        .order_by('hora_desde', 'empresa__nombre')
    )
    if empresa_id:
        turnos = [t for t in turnos if str(t.empresa_id) == empresa_id]
    empresas = list(
        Empresa.objects.filter(estado='aprobada').order_by('nombre').values('id', 'nombre')
    )

    resumen_dia = {
        'total': len(turnos),
        'presente': sum(1 for t in turnos if t.estado_asistencia == 'presente'),
        'ausente': sum(1 for t in turnos if t.estado_asistencia == 'ausente'),
        'sin_marcar': sum(1 for t in turnos if not t.estado_asistencia),
    }

    if request.method == 'POST':
        accion = (request.POST.get('accion') or '').strip().lower()
        if accion == 'marcar':
            turno_id = request.POST.get('turno_id')
            estado = (request.POST.get('estado') or '').strip().lower()
            if estado not in {'presente', 'ausente'}:
                messages.error(request, 'Estado inválido.')
                return redirect(f"{reverse('empresas:turnos_hoy')}?fecha={fecha_seleccionada.isoformat()}&empresa_id={empresa_id}")
            turno = TurnoEmpresa.objects.select_related('empresa').filter(id=turno_id, fecha=fecha_seleccionada).first()
            if not turno:
                messages.error(request, 'No se encontró el turno.')
                return redirect(f"{reverse('empresas:turnos_hoy')}?fecha={fecha_seleccionada.isoformat()}&empresa_id={empresa_id}")
            turno.estado_asistencia = estado
            turno.marcado_por = request.user
            turno.marcado_en = timezone.now()
            turno.save(update_fields=['estado_asistencia', 'marcado_por', 'marcado_en', 'actualizado'])
            messages.success(request, 'Asistencia actualizada.')
            return redirect(f"{reverse('empresas:turnos_hoy')}?fecha={fecha_seleccionada.isoformat()}&empresa_id={empresa_id}")

        if accion == 'marcar_todos':
            estado = (request.POST.get('estado') or '').strip().lower()
            if estado not in {'presente', 'ausente'}:
                messages.error(request, 'Estado inválido.')
                return redirect(f"{reverse('empresas:turnos_hoy')}?fecha={fecha_seleccionada.isoformat()}&empresa_id={empresa_id}")

            qs = TurnoEmpresa.objects.filter(
                fecha=fecha_seleccionada,
                empresa__estado='aprobada',
                estado_asistencia__isnull=True,
            )
            if empresa_id:
                qs = qs.filter(empresa_id=empresa_id)

            ahora = timezone.now()
            cantidad = qs.update(
                estado_asistencia=estado,
                marcado_por=request.user,
                marcado_en=ahora,
                actualizado=ahora,
            )
            messages.success(request, f'Asistencia actualizada (solo sin marcar). Turnos: {cantidad}.')
            return redirect(f"{reverse('empresas:turnos_hoy')}?fecha={fecha_seleccionada.isoformat()}&empresa_id={empresa_id}")

    context = {
        'hoy': hoy,
        'fecha': fecha_seleccionada,
        'empresa_id': empresa_id,
        'empresas': empresas,
        'turnos': turnos,
        'resumen_dia': resumen_dia,
    }
    return render(request, 'empresas/turnos_hoy.html', context)


@login_required
@user_passes_test(es_admin_o_mesa)
def turnos_cerrar_dia(request):
    if request.method != 'POST':
        return redirect('empresas:turnos_hoy')

    hoy = timezone.localdate()
    fecha_raw = (request.POST.get('fecha') or '').strip()
    if fecha_raw:
        try:
            fecha_obj = datetime.strptime(fecha_raw, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            fecha_obj = hoy
    else:
        fecha_obj = hoy

    empresa_id = (request.POST.get('empresa_id') or '').strip()
    ahora = timezone.now()
    qs = TurnoEmpresa.objects.filter(
        fecha=fecha_obj,
        empresa__estado='aprobada',
        estado_asistencia__isnull=True,
    )
    if empresa_id:
        qs = qs.filter(empresa_id=empresa_id)

    cantidad = qs.update(
        estado_asistencia='ausente',
        marcado_por=request.user,
        marcado_en=ahora,
        actualizado=ahora,
    )
    messages.success(request, f'Día cerrado. Ausentes marcados: {cantidad}.')
    return redirect(f"{reverse('empresas:turnos_hoy')}?fecha={fecha_obj.isoformat()}&empresa_id={empresa_id}")


class EmpresaListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Empresa
    template_name = 'empresas/gestion_empresas.html'
    context_object_name = 'empresas'

    def test_func(self):
        return es_admin_completo(self.request.user)

    def get_queryset(self):
        queryset = Empresa.objects.select_related(
            'responsable__persona',
            'aprobado_por',
            'rechazado_por',
        ).prefetch_related(
            'miembros__usuario__persona',
        ).order_by('-actualizado')

        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(nombre__icontains=search_query) |
                Q(responsable__persona__dni__icontains=search_query) |
                Q(responsable__persona__nombre__icontains=search_query) |
                Q(responsable__persona__apellido__icontains=search_query)
            )
        return queryset


@login_required
@user_passes_test(es_admin_o_mesa)
def mesa_entrada_list(request):
    pendientes = Empresa.objects.filter(estado='pendiente').select_related('responsable__persona').order_by('-actualizado')
    context = {
        'pendientes': pendientes,
    }
    return render(request, 'empresas/mesa_entrada_list.html', context)


@login_required
@user_passes_test(es_admin_o_mesa)
def mesa_entrada_detalle(request, empresa_id):
    empresa = get_object_or_404(Empresa.objects.select_related('responsable__persona'), pk=empresa_id)

    if request.method == 'POST':
        accion = (request.POST.get('accion') or '').strip().lower()
        if accion == 'aprobar':
            empresa.estado = 'aprobada'
            empresa.motivo_rechazo = None
            empresa.aprobado_por = request.user
            empresa.aprobado_en = timezone.now()
            empresa.rechazado_por = None
            empresa.rechazado_en = None
            empresa.save()
            MiembroEmpresa.objects.get_or_create(
                empresa=empresa,
                usuario=empresa.responsable,
                defaults={'rol': 'Responsable', 'es_socio': True},
            )
            messages.success(request, 'Empresa aprobada.')
            return redirect('empresas:mesa_entrada_list')

        if accion == 'rechazar':
            form_rechazo = RechazarEmpresaForm(request.POST)
            if form_rechazo.is_valid():
                empresa.estado = 'rechazada'
                empresa.motivo_rechazo = form_rechazo.cleaned_data['motivo_rechazo']
                empresa.rechazado_por = request.user
                empresa.rechazado_en = timezone.now()
                empresa.aprobado_por = None
                empresa.aprobado_en = None
                empresa.save()
                messages.success(request, 'Empresa rechazada.')
                return redirect('empresas:mesa_entrada_list')
        else:
            form_rechazo = RechazarEmpresaForm()
    else:
        form_rechazo = RechazarEmpresaForm(initial={'motivo_rechazo': empresa.motivo_rechazo})

    context = {
        'empresa': empresa,
        'responsable': empresa.responsable,
        'persona_responsable': empresa.responsable.persona,
        'form_rechazo': form_rechazo,
    }
    return render(request, 'empresas/mesa_entrada_detalle.html', context)
