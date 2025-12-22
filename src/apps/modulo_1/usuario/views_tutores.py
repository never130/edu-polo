from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from django.utils import timezone

from apps.modulo_1.usuario.models import Persona, Usuario
from apps.modulo_1.roles.models import AutorizadoRetiro, Estudiante, Tutor, TutorEstudiante, UsuarioRol

def es_admin_o_mesa_entrada(user):
    if not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    try:
        usuario = Usuario.objects.get(persona__dni=user.username)
        roles = UsuarioRol.objects.filter(usuario_id=usuario).values_list('rol_id__nombre', flat=True)
        return 'Mesa de Entrada' in roles or 'Administrador' in roles
    except Usuario.DoesNotExist:
        return False


@login_required
def gestionar_tutores(request):
    """Vista para que el estudiante gestione sus tutores"""
    try:
        estudiante = Estudiante.objects.get(usuario__persona__dni=request.user.username)

        relaciones_tutores = TutorEstudiante.objects.filter(estudiante=estudiante).select_related('tutor__usuario__persona')
        autorizados_retiro = AutorizadoRetiro.objects.filter(estudiante=estudiante).order_by('revocado', '-confirmado', 'apellido', 'nombre')

        context = {
            'estudiante': estudiante,
            'relaciones_tutores': relaciones_tutores,
            'autorizados_retiro': autorizados_retiro,
            'tiene_tutor': relaciones_tutores.exists(),
            'es_menor': estudiante.usuario.persona.es_menor_edad,
            'edad': estudiante.usuario.persona.edad,
        }
        return render(request, 'usuario/gestionar_tutores.html', context)

    except Estudiante.DoesNotExist:
        messages.error(request, 'No tienes perfil de estudiante.')
        return redirect('dashboard')


@login_required
def agregar_tutor(request):
    """Vista para agregar un nuevo tutor"""
    try:
        estudiante = Estudiante.objects.get(usuario__persona__dni=request.user.username)
        
        if request.method == 'POST':
            with transaction.atomic():
                # Datos del tutor
                tutor_dni = request.POST.get('tutor_dni')
                tutor_nombre = request.POST.get('tutor_nombre')
                tutor_apellido = request.POST.get('tutor_apellido')
                tutor_telefono = request.POST.get('tutor_telefono')
                tutor_email = request.POST.get('tutor_email', '')
                parentesco = request.POST.get('parentesco')
                
                # Validaciones
                if not all([tutor_dni, tutor_nombre, tutor_apellido, tutor_telefono, parentesco]):
                    messages.error(request, '❌ Todos los campos obligatorios deben ser completados.')
                    return redirect('usuario:gestionar_tutores')
                
                # Crear o buscar Persona del tutor
                persona_tutor, persona_creada = Persona.objects.get_or_create(
                    dni=tutor_dni,
                    defaults={
                        'nombre': tutor_nombre,
                        'apellido': tutor_apellido,
                        'correo': tutor_email if tutor_email else f'{tutor_dni}@temp.com',
                        'telefono': tutor_telefono,
                    }
                )
                
                # Si ya existía, actualizar datos
                if not persona_creada:
                    persona_tutor.nombre = tutor_nombre
                    persona_tutor.apellido = tutor_apellido
                    persona_tutor.telefono = tutor_telefono
                    if tutor_email:
                        persona_tutor.correo = tutor_email
                    persona_tutor.save()
                
                # Crear Usuario del tutor
                usuario_tutor, _ = Usuario.objects.get_or_create(
                    persona=persona_tutor,
                    defaults={'contrasena': tutor_dni, 'activo': True}
                )
                
                # Crear perfil de Tutor
                tutor_obj, _ = Tutor.objects.get_or_create(
                    usuario=usuario_tutor,
                    defaults={
                        'tipo_tutor': 'PE',
                        'telefono_contacto': tutor_telefono,
                        'disponibilidad_horaria': 'A convenir'
                    }
                )
                
                # Verificar si ya existe la relación
                if TutorEstudiante.objects.filter(tutor=tutor_obj, estudiante=estudiante).exists():
                    messages.warning(request, '⚠️ Este tutor ya está registrado para ti.')
                    return redirect('usuario:gestionar_tutores')
                
                # Crear relación Tutor-Estudiante
                TutorEstudiante.objects.create(
                    tutor=tutor_obj,
                    estudiante=estudiante,
                    parentesco=parentesco
                )
                
                messages.success(request, f'✅ Tutor {tutor_nombre} {tutor_apellido} agregado exitosamente.')
                return redirect('usuario:gestionar_tutores')
        
        context = {
            'estudiante': estudiante,
        }
        return render(request, 'usuario/agregar_tutor.html', context)
    
    except Estudiante.DoesNotExist:
        messages.error(request, 'No tienes perfil de estudiante.')
        return redirect('dashboard')


@login_required
def eliminar_tutor(request, relacion_id):
    """Vista para eliminar un tutor"""
    try:
        estudiante = Estudiante.objects.get(usuario__persona__dni=request.user.username)
        relacion = get_object_or_404(TutorEstudiante, id=relacion_id, estudiante=estudiante)

        if estudiante.usuario.persona.es_menor_edad:
            total_tutores = TutorEstudiante.objects.filter(estudiante=estudiante).count()
            if total_tutores <= 1:
                messages.error(request, '❌ No puedes eliminar tu único tutor siendo menor de 16 años.')
                return redirect('usuario:gestionar_tutores')

        tutor_nombre = relacion.tutor.usuario.persona.nombre_completo
        relacion.delete()
        messages.success(request, f'✅ Tutor {tutor_nombre} eliminado correctamente.')

    except Estudiante.DoesNotExist:
        messages.error(request, 'No tienes perfil de estudiante.')

    return redirect('usuario:gestionar_tutores')


@login_required
def agregar_autorizado_retiro(request):
    try:
        estudiante = Estudiante.objects.get(usuario__persona__dni=request.user.username)

        if request.method != 'POST':
            return redirect('usuario:gestionar_tutores')

        if not TutorEstudiante.objects.filter(estudiante=estudiante).exists():
            messages.error(request, '❌ Para agregar autorizados, primero debes registrar al menos un tutor.')
            return redirect('usuario:gestionar_tutores')

        dni_raw = (request.POST.get('dni') or '').strip()
        dni = ''.join(ch for ch in dni_raw if ch.isdigit())
        nombre = (request.POST.get('nombre') or '').strip()
        apellido = (request.POST.get('apellido') or '').strip()
        telefono_raw = (request.POST.get('telefono') or '').strip()
        telefono = ''.join(ch for ch in telefono_raw if ch.isdigit())
        correo = (request.POST.get('correo') or '').strip()
        parentesco = (request.POST.get('parentesco') or '').strip()

        if not all([dni, nombre, apellido, telefono, parentesco]):
            messages.error(request, '❌ Completá todos los campos obligatorios para agregar un autorizado.')
            return redirect('usuario:gestionar_tutores')

        parentescos_validos = {k for k, _ in AutorizadoRetiro.PARENTESCOS}
        if parentesco not in parentescos_validos:
            messages.error(request, '❌ Parentesco inválido.')
            return redirect('usuario:gestionar_tutores')

        if AutorizadoRetiro.objects.filter(estudiante=estudiante, dni=dni).exists():
            messages.warning(request, '⚠️ Ya existe un autorizado con ese DNI.')
            return redirect('usuario:gestionar_tutores')

        AutorizadoRetiro.objects.create(
            estudiante=estudiante,
            dni=dni,
            nombre=nombre,
            apellido=apellido,
            telefono=telefono,
            correo=correo or None,
            parentesco=parentesco,
            confirmado=False,
            revocado=False,
        )

        messages.success(request, f'✅ Autorizado {nombre} {apellido} agregado. Ahora falta confirmar la autorización.')
        return redirect('usuario:gestionar_tutores')

    except Estudiante.DoesNotExist:
        messages.error(request, 'No tienes perfil de estudiante.')
        return redirect('dashboard')


@login_required
def confirmar_autorizado_retiro(request, autorizado_id):
    try:
        estudiante = Estudiante.objects.get(usuario__persona__dni=request.user.username)
        autorizado = get_object_or_404(AutorizadoRetiro, id=autorizado_id, estudiante=estudiante)

        if request.method != 'POST':
            return redirect('usuario:gestionar_tutores')

        if autorizado.revocado:
            messages.error(request, '❌ No podés confirmar un autorizado revocado. Reactivalo primero.')
            return redirect('usuario:gestionar_tutores')

        if not autorizado.confirmado:
            autorizado.confirmado = True
            autorizado.confirmado_en = timezone.now()
            autorizado.save(update_fields=['confirmado', 'confirmado_en', 'actualizado_en'])

        messages.success(request, '✅ Autorización confirmada.')
        return redirect('usuario:gestionar_tutores')

    except Estudiante.DoesNotExist:
        messages.error(request, 'No tienes perfil de estudiante.')
        return redirect('dashboard')


@login_required
def revocar_autorizado_retiro(request, autorizado_id):
    try:
        estudiante = Estudiante.objects.get(usuario__persona__dni=request.user.username)
        autorizado = get_object_or_404(AutorizadoRetiro, id=autorizado_id, estudiante=estudiante)

        if request.method != 'POST':
            return redirect('usuario:gestionar_tutores')

        if autorizado.revocado:
            autorizado.revocado = False
            autorizado.revocado_en = None
            autorizado.save(update_fields=['revocado', 'revocado_en', 'actualizado_en'])
            messages.success(request, '✅ Autorizado reactivado.')
        else:
            autorizado.revocado = True
            autorizado.revocado_en = timezone.now()
            autorizado.save(update_fields=['revocado', 'revocado_en', 'actualizado_en'])
            messages.success(request, '✅ Autorización revocada.')

        return redirect('usuario:gestionar_tutores')

    except Estudiante.DoesNotExist:
        messages.error(request, 'No tienes perfil de estudiante.')
        return redirect('dashboard')


@login_required
def eliminar_autorizado_retiro(request, autorizado_id):
    try:
        estudiante = Estudiante.objects.get(usuario__persona__dni=request.user.username)
        autorizado = get_object_or_404(AutorizadoRetiro, id=autorizado_id, estudiante=estudiante)

        if request.method != 'POST':
            return redirect('usuario:gestionar_tutores')

        autorizado.delete()
        messages.success(request, '✅ Autorizado eliminado.')
        return redirect('usuario:gestionar_tutores')

    except Estudiante.DoesNotExist:
        messages.error(request, 'No tienes perfil de estudiante.')
        return redirect('dashboard')



