from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from datetime import date

from .models import Inscripcion
from apps.modulo_3.cursos.models import Comision
from apps.modulo_1.usuario.models import Persona, Usuario
from apps.modulo_1.roles.models import Estudiante, Tutor, TutorEstudiante


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
        messages.error(request, f'🚫 Lo sentimos, esta comisión ya no tiene cupos disponibles. CUPO LLENO!')
        return redirect('landing')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 1. Obtener DNI
                dni = request.POST.get('dni')
                
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
                
                # 5. Calcular edad
                edad = persona.edad if persona.edad else 18
                
                # 5. Si es menor de 16, procesar tutores
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
                
                # 7. Verificar si ya está inscrito
                if Inscripcion.objects.filter(estudiante=estudiante, comision=comision).exists():
                    messages.warning(request, '⚠️ Ya estás inscrito en esta comisión.')
                    return redirect('landing')
                
                # 8. Crear inscripción con observaciones
                Inscripcion.objects.create(
                    estudiante=estudiante,
                    comision=comision,
                    estado='confirmado',
                    observaciones_discapacidad=request.POST.get('observaciones_discapacidad', ''),
                    observaciones_salud=request.POST.get('observaciones_salud', ''),
                    observaciones_generales=request.POST.get('observaciones_generales', ''),
                )
                
                # 7. Mensaje de éxito personalizado
                cupos_restantes = comision.cupos_disponibles - 1
                curso_nombre = comision.fk_id_curso.nombre
                
                if cupos_restantes == 0:
                    mensaje = f'🎉 ¡INSCRIPCIÓN EXITOSA! Te has inscrito al curso "{curso_nombre}". ¡Has tomado el ÚLTIMO CUPO disponible!'
                elif cupos_restantes <= 3:
                    mensaje = f'✅ ¡INSCRIPCIÓN EXITOSA! Te has inscrito al curso "{curso_nombre}". ⚠️ Solo quedan {cupos_restantes} cupos.'
                else:
                    mensaje = f'✅ ¡INSCRIPCIÓN EXITOSA! Te has inscrito al curso "{curso_nombre}".'
                
                messages.success(request, mensaje)
                return redirect('cursos:mis_inscripciones')
                
        except Exception as e:
            messages.error(request, f'❌ Error al procesar la inscripción: {str(e)}')
            return render(request, 'inscripciones/formulario_inscripcion.html', {'comision': comision})
    
    # GET - Mostrar formulario
    context = {
        'comision': comision
    }
    return render(request, 'inscripciones/formulario_inscripcion.html', context)
