from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Max
from datetime import date

from .models import Inscripcion
from apps.modulo_3.cursos.models import Comision
from apps.modulo_1.usuario.models import Persona, Usuario
from apps.modulo_1.roles.models import Estudiante, Tutor, TutorEstudiante


@login_required
def formulario_inscripcion(request, comision_id):
    """
    Formulario completo de inscripción con:
    - Datos personales completos
    - Tutores (si es menor de 16)
    - Observaciones de salud
    - Políticas de uso de datos
    """
    comision = get_object_or_404(Comision, id_comision=comision_id)
    
    # Verificar cupo disponible
    if comision.cupo_lleno:
        messages.warning(request, f'⚠️ Esta comisión tiene el cupo lleno. Si completas la inscripción, quedarás en LISTA DE ESPERA.')
        # No redirigimos, permitimos continuar para inscribirse en lista de espera
    
    # Verificar si ya está inscrito (para evitar mostrar el formulario si ya lo está)
    try:
        # Asumiendo que el username es el DNI
        estudiante_check = Estudiante.objects.filter(usuario__persona__dni=request.user.username).first()
        if estudiante_check:
            # Verificar inscripción en la misma comisión
            if Inscripcion.objects.filter(estudiante=estudiante_check, comision=comision).exists():
                messages.warning(request, '⚠️ Ya estás inscrito en esta comisión.')
                return redirect('landing')
            
            # Verificar inscripción en otra comisión del mismo curso
            curso = comision.fk_id_curso
            if Inscripcion.objects.filter(estudiante=estudiante_check, comision__fk_id_curso=curso).exists():
                messages.warning(request, f'⚠️ Ya estás inscrito en el curso "{curso.nombre}" (en esta u otra comisión). No se permiten inscripciones múltiples al mismo curso.')
                return redirect('landing')
            
            # Verificar rango etario (validación previa)
            persona = estudiante_check.usuario.persona
            edad_check = persona.edad
            if edad_check is not None:
                if curso.edad_minima and edad_check < curso.edad_minima:
                     messages.error(request, f'⛔ No cumples con la edad mínima requerida ({curso.edad_minima} años). Tienes {edad_check} años.')
                     return redirect('landing')
                if curso.edad_maxima and edad_check > curso.edad_maxima:
                     messages.error(request, f'⛔ Superas la edad máxima permitida ({curso.edad_maxima} años). Tienes {edad_check} años.')
                     return redirect('landing')
    except Exception:
        pass # Si hay error al verificar, dejamos que continúe (el POST manejará validaciones estrictas)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 1. Obtener DNI (usar el del usuario logueado para seguridad)
                # Aunque el form envíe DNI, priorizamos el del usuario autenticado
                dni = request.user.username  # Asumiendo que username es DNI
                
                # 2. Buscar persona existente (debe estar registrada)
                try:
                    persona = Persona.objects.get(dni=dni)
                except Persona.DoesNotExist:
                    messages.error(request, '❌ DNI no encontrado. Debes registrarte primero en el sistema.')
                    return redirect('usuario:registro')
                
                # 3. Actualizar autorizaciones
                persona.autorizacion_imagen = request.POST.get('autorizacion_imagen') == 'on'
                persona.autorizacion_voz = request.POST.get('autorizacion_voz') == 'on'
                persona.save()
                
                # 4. Obtener usuario y estudiante
                usuario = Usuario.objects.get(persona=persona)
                estudiante = Estudiante.objects.get(usuario=usuario)
                
                # 5. Calcular edad y Validar Rango Etario
                edad_real = persona.edad
                curso = comision.fk_id_curso

                if edad_real is None:
                    # Si no tiene edad registrada y el curso tiene restricciones, exigir fecha de nacimiento
                    if curso.edad_minima or curso.edad_maxima:
                        messages.error(request, '⚠️ Para inscribirte a este curso, necesitamos conocer tu fecha de nacimiento. Por favor actualiza tu perfil.')
                        return redirect('landing')
                    # Si no tiene restricciones, asumimos 18 para lógica de tutores
                    edad = 18
                else:
                    # Validar límites de edad
                    if curso.edad_minima and edad_real < curso.edad_minima:
                        messages.error(request, f'⛔ No cumples con la edad mínima requerida para este curso ({curso.edad_minima} años). Tienes {edad_real} años.')
                        return redirect('landing')
                    
                    if curso.edad_maxima and edad_real > curso.edad_maxima:
                        messages.error(request, f'⛔ Superas la edad máxima permitida para este curso ({curso.edad_maxima} años). Tienes {edad_real} años.')
                        return redirect('landing')
                    
                    edad = edad_real
                
                # 6. Si es menor de 16, procesar tutores
                if edad < 16:
                    # Buscar cuántos tutores se enviaron
                    tutor_index = 0
                    while f'tutor_dni_{tutor_index}' in request.POST:
                        tutor_dni = request.POST.get(f'tutor_dni_{tutor_index}')
                        tutor_nombre = request.POST.get(f'tutor_nombre_{tutor_index}')
                        tutor_apellido = request.POST.get(f'tutor_apellido_{tutor_index}')
                        tutor_telefono = request.POST.get(f'tutor_telefono_{tutor_index}')
                        tutor_email = request.POST.get(f'tutor_email_{tutor_index}', '')
                        parentesco = request.POST.get(f'tutor_parentesco_{tutor_index}')
                        
                        # Crear o buscar Persona del tutor
                        persona_tutor, _ = Persona.objects.get_or_create(
                            dni=tutor_dni,
                            defaults={
                                'nombre': tutor_nombre,
                                'apellido': tutor_apellido,
                                'correo': tutor_email if tutor_email else f'{tutor_dni}@temp.com',
                                'telefono': tutor_telefono,
                            }
                        )
                        
                        # Crear Usuario del tutor
                        usuario_tutor, _ = Usuario.objects.get_or_create(
                            persona=persona_tutor,
                            defaults={'contrasena': tutor_dni, 'activo': True}
                        )
                        
                        # Crear perfil de Tutor
                        tutor_obj, _ = Tutor.objects.get_or_create(
                            usuario=usuario_tutor,
                            defaults={
                                'tipo_tutor': 'PE',  # Personal
                                'telefono_contacto': tutor_telefono,
                                'disponibilidad_horaria': 'A convenir'
                            }
                        )
                        
                        # Crear relación Tutor-Estudiante
                        TutorEstudiante.objects.get_or_create(
                            tutor=tutor_obj,
                            estudiante=estudiante,
                            defaults={'parentesco': parentesco}
                        )
                        
                        tutor_index += 1
                    
                    if tutor_index == 0:
                        messages.error(request, '❌ Como eres menor de 16 años, debes registrar al menos un tutor.')
                        return render(request, 'inscripciones/formulario_inscripcion.html', {'comision': comision})
                
                # 6. Verificar nuevamente cupo disponible (por si alguien se inscribió mientras llenaba el form)
                if comision.cupo_lleno:
                    messages.error(request, '🚫 Lo sentimos, el cupo se completó mientras completabas el formulario.')
                    return redirect('landing')
                
                # 7. Verificar si ya está inscrito en la comisión o en otra comisión del mismo curso
                # Verificar inscripción en la misma comisión
                if Inscripcion.objects.filter(estudiante=estudiante, comision=comision).exists():
                    messages.warning(request, '⚠️ Ya estás inscrito en esta comisión.')
                    return redirect('landing')

                # Verificar inscripción en otra comisión del mismo curso
                curso = comision.fk_id_curso
                if Inscripcion.objects.filter(estudiante=estudiante, comision__fk_id_curso=curso).exists():
                    messages.warning(request, f'⚠️ Ya estás inscrito en el curso "{curso.nombre}" (en esta u otra comisión). No se permiten inscripciones múltiples al mismo curso.')
                    return redirect('landing')
                
                # 8. Crear inscripción con observaciones
                # Determinar estado y orden
                estado_inscripcion = 'pre_inscripto'
                orden = None
                
                # Re-verificar cupo en el momento de guardar (dentro de transacción)
                comision.refresh_from_db()
                
                if comision.cupo_lleno:
                    estado_inscripcion = 'lista_espera'
                    ultimo_orden = Inscripcion.objects.filter(comision=comision, estado='lista_espera').aggregate(Max('orden_lista_espera'))['orden_lista_espera__max']
                    orden = (ultimo_orden or 0) + 1
                
                Inscripcion.objects.create(
                    estudiante=estudiante,
                    comision=comision,
                    estado=estado_inscripcion,
                    orden_lista_espera=orden,
                    observaciones_discapacidad=request.POST.get('observaciones_discapacidad', ''),
                    observaciones_salud=request.POST.get('observaciones_salud', ''),
                    observaciones_generales=request.POST.get('observaciones_generales', ''),
                )
                
                # 7. Mensaje de éxito personalizado
                curso_nombre = comision.fk_id_curso.nombre
                
                if estado_inscripcion == 'lista_espera':
                    mensaje = f'📝 Te has inscrito en LISTA DE ESPERA para el curso "{curso_nombre}". Tu posición es: {orden}.'
                    messages.warning(request, mensaje)
                else:
                    cupos_restantes = comision.cupos_disponibles - 1
                    
                    if cupos_restantes == 0:
                        mensaje = f'🎉 ¡PRE-INSCRIPCIÓN EXITOSA! Te has pre-inscrito al curso "{curso_nombre}". ¡Has tomado el ÚLTIMO CUPO disponible! Tu inscripción está pendiente de confirmación.'
                    elif cupos_restantes <= 3:
                        mensaje = f'✅ ¡PRE-INSCRIPCIÓN EXITOSA! Te has pre-inscrito al curso "{curso_nombre}". ⚠️ Solo quedan {cupos_restantes} cupos. Tu inscripción está pendiente de confirmación.'
                    else:
                        mensaje = f'✅ ¡PRE-INSCRIPCIÓN EXITOSA! Te has pre-inscrito al curso "{curso_nombre}". Tu inscripción está pendiente de confirmación.'
                    
                    messages.success(request, mensaje)
                
                # Redirección inteligente: Si está logueado va a mis inscripciones, sino al landing
                if request.user.is_authenticated:
                    return redirect('cursos:mis_inscripciones')
                else:
                    return redirect('landing')
                
        except Exception as e:
            messages.error(request, f'❌ Error al procesar la inscripción: {str(e)}')
            return render(request, 'inscripciones/formulario_inscripcion.html', {'comision': comision})
    
    # GET - Mostrar formulario
    tutores_existentes = []
    if request.user.is_authenticated:
        try:
            estudiante = Estudiante.objects.get(usuario__persona__dni=request.user.username)
            # Obtener relaciones de tutor
            relaciones = TutorEstudiante.objects.filter(estudiante=estudiante).select_related('tutor__usuario__persona')
            for rel in relaciones:
                tutor_persona = rel.tutor.usuario.persona
                tutores_existentes.append({
                    'dni': tutor_persona.dni,
                    'nombre': tutor_persona.nombre,
                    'apellido': tutor_persona.apellido,
                    'telefono': tutor_persona.telefono,
                    'email': tutor_persona.correo,
                    'parentesco': rel.parentesco
                })
        except Estudiante.DoesNotExist:
            pass

    context = {
        'comision': comision,
        'tutores_existentes': tutores_existentes
    }
    
    # Pre-cargar datos de persona si existe
    try:
        if request.user.is_authenticated:
            persona = Persona.objects.get(dni=request.user.username)
            context['persona'] = persona
    except Persona.DoesNotExist:
        pass
        
    return render(request, 'inscripciones/formulario_inscripcion.html', context)
