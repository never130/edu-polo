from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Asistencia, RegistroAsistencia
from apps.modulo_2.inscripciones.models import Inscripcion


def actualizar_registro_asistencia(inscripcion):
    """
    Actualiza el RegistroAsistencia para una inscripción específica
    basándose en todas las asistencias registradas
    """
    # Obtener o crear el registro de asistencia
    registro, created = RegistroAsistencia.objects.get_or_create(
        inscripcion=inscripcion
    )
    
    comision = inscripcion.comision
    total_programadas = comision.get_total_clases_programadas() if hasattr(comision, 'get_total_clases_programadas') else None
    if total_programadas is not None:
        total_clases = total_programadas
    else:
        total_clases = Asistencia.objects.filter(
            inscripcion__comision=comision
        ).values('fecha_clase').distinct().count()
    
    # Contar clases asistidas por ESTE alumno (presente=True)
    clases_asistidas = Asistencia.objects.filter(
        inscripcion=inscripcion,
        presente=True
    ).count()
    
    # Actualizar los valores
    registro.total_clases = total_clases
    registro.clases_asistidas = clases_asistidas
    
    # Calcular porcentaje
    if total_clases > 0:
        registro.porcentaje_asistencia = (clases_asistidas / total_clases) * 100
        # Cumple requisito si tiene entre 80% y 100% de asistencia
        registro.cumple_requisito_certificado = 80 <= registro.porcentaje_asistencia <= 100
    else:
        registro.porcentaje_asistencia = 0
        registro.cumple_requisito_certificado = False
    
    # Guardar el registro actualizado
    registro.save()
    
    return registro


@receiver(post_save, sender=Asistencia)
def actualizar_registro_despues_guardar(sender, instance, created, **kwargs):
    """
    Señal que se ejecuta después de guardar una Asistencia.
    Si es una fecha nueva para la comisión, actualiza a TODOS los alumnos.
    Si no, solo actualiza al alumno afectado.
    """
    # Siempre actualizar al alumno actual
    actualizar_registro_asistencia(instance.inscripcion)
    
    comision = instance.inscripcion.comision
    total_programadas = comision.get_total_clases_programadas() if hasattr(comision, 'get_total_clases_programadas') else None
    if total_programadas is not None:
        return

    if created:
        # Verificar si es la primera asistencia registrada para esta fecha en la comisión
        # Count > 1 significa que ya existían registros para esta fecha (la fecha ya estaba contabilizada)
        registros_misma_fecha = Asistencia.objects.filter(
            inscripcion__comision=comision,
            fecha_clase=instance.fecha_clase
        ).count()
        
        # Si es el primer registro (count == 1), la cantidad total de clases aumentó.
        # Debemos actualizar a todos los DEMÁS alumnos de la comisión.
        if registros_misma_fecha == 1:
            otras_inscripciones = Inscripcion.objects.filter(
                comision=comision
            ).exclude(id=instance.inscripcion.id)
            
            for inscripcion in otras_inscripciones:
                actualizar_registro_asistencia(inscripcion)


@receiver(post_delete, sender=Asistencia)
def actualizar_registro_despues_eliminar(sender, instance, **kwargs):
    """
    Señal que se ejecuta después de eliminar una Asistencia.
    Si se eliminó el último registro de una fecha para la comisión, actualiza a TODOS.
    """
    try:
        inscripcion = instance.inscripcion
    except Inscripcion.DoesNotExist:
        return

    try:
        actualizar_registro_asistencia(inscripcion)
    except Inscripcion.DoesNotExist:
        return

    try:
        comision = inscripcion.comision
    except Exception:
        return

    total_programadas = comision.get_total_clases_programadas() if hasattr(comision, 'get_total_clases_programadas') else None
    if total_programadas is not None:
        return

    queda_alguien = Asistencia.objects.filter(
        inscripcion__comision=comision,
        fecha_clase=instance.fecha_clase
    ).exists()

    if not queda_alguien:
        otras_inscripciones = Inscripcion.objects.filter(
            comision=comision
        ).exclude(id=inscripcion.id)

        for inscripcion_otro in otras_inscripciones:
            actualizar_registro_asistencia(inscripcion_otro)
