from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Asistencia, RegistroAsistencia


def actualizar_registro_asistencia(inscripcion):
    """
    Actualiza el RegistroAsistencia para una inscripción específica
    basándose en todas las asistencias registradas
    """
    # Obtener o crear el registro de asistencia
    registro, created = RegistroAsistencia.objects.get_or_create(
        inscripcion=inscripcion
    )
    
    # Contar total de clases (todas las asistencias registradas)
    total_clases = Asistencia.objects.filter(inscripcion=inscripcion).count()
    
    # Contar clases asistidas (presente=True)
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
        # Cumple requisito si tiene entre 60% y 100% de asistencia
        registro.cumple_requisito_certificado = 60 <= registro.porcentaje_asistencia <= 100
    else:
        registro.porcentaje_asistencia = 0
        registro.cumple_requisito_certificado = False
    
    # Guardar el registro actualizado
    registro.save()
    
    return registro


@receiver(post_save, sender=Asistencia)
def actualizar_registro_despues_guardar(sender, instance, created, **kwargs):
    """
    Señal que se ejecuta después de guardar una Asistencia
    Actualiza automáticamente el RegistroAsistencia correspondiente
    """
    actualizar_registro_asistencia(instance.inscripcion)


@receiver(post_delete, sender=Asistencia)
def actualizar_registro_despues_eliminar(sender, instance, **kwargs):
    """
    Señal que se ejecuta después de eliminar una Asistencia
    Actualiza automáticamente el RegistroAsistencia correspondiente
    """
    actualizar_registro_asistencia(instance.inscripcion)



