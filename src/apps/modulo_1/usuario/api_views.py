from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Persona


@require_http_methods(["GET"])
def buscar_estudiante_por_dni(request, dni):
    """
    API para buscar datos de un estudiante por DNI
    Retorna datos si existe, o indica que debe registrarse
    """
    try:
        persona = Persona.objects.get(dni=dni)
        
        data = {
            'existe': True,
            'dni': persona.dni,
            'nombre': persona.nombre,
            'apellido': persona.apellido,
            'correo': persona.correo,
            'telefono': persona.telefono,
            'fecha_nacimiento': persona.fecha_nacimiento.isoformat() if persona.fecha_nacimiento else None,
            'genero': persona.genero,
            'ciudad': persona.ciudad_residencia,
            'zona': persona.zona_residencia,
            'domicilio': persona.domicilio,
            'edad': persona.edad,
            'es_menor': persona.es_menor_edad,
        }
        return JsonResponse(data)
        
    except Persona.DoesNotExist:
        return JsonResponse({
            'existe': False,
            'mensaje': 'DNI no encontrado. Debe registrarse primero.'
        })
    except Exception as e:
        return JsonResponse({
            'existe': False,
            'error': str(e)
        }, status=500)





