from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from apps.modulo_1.usuario.models import Usuario


class DNIAuthenticationBackend(BaseBackend):
    """
    Backend de autenticación personalizado que usa solo DNI y contraseña
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Buscar el usuario por DNI
            usuario = Usuario.objects.get(persona__dni=username)
            
            # Verificar la contraseña
            if usuario.contrasena == password:
                # Obtener o crear el usuario de Django Auth
                django_user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': usuario.persona.nombre,
                        'last_name': usuario.persona.apellido,
                    }
                )
                
                # Actualizar nombre si cambió
                if not created:
                    django_user.first_name = usuario.persona.nombre
                    django_user.last_name = usuario.persona.apellido
                    django_user.save()
                
                return django_user
            
        except Usuario.DoesNotExist:
            return None
        
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None




