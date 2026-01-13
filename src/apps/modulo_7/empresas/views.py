from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import ListView

from apps.modulo_1.usuario.models import Usuario
from apps.modulo_1.roles.models import Estudiante
from apps.modulo_6.administracion.views import es_admin_completo

from .forms import AgregarMiembroForm, ActualizarLogoEmpresaForm, EmpresaForm, RechazarEmpresaForm
from .models import Empresa, MiembroEmpresa


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
@user_passes_test(es_admin_completo)
def mesa_entrada_list(request):
    pendientes = Empresa.objects.filter(estado='pendiente').select_related('responsable__persona').order_by('-actualizado')
    context = {
        'pendientes': pendientes,
    }
    return render(request, 'empresas/mesa_entrada_list.html', context)


@login_required
@user_passes_test(es_admin_completo)
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
