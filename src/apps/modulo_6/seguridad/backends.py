from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from apps.modulo_1.usuario.models import Usuario, Persona


class DNIAuthenticationBackend(BaseBackend):
    """
    Backend de autenticación personalizado que usa solo DNI y contraseña
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        username_raw = (username or '').strip()
        username_clean = Persona.limpiar_dni(username_raw)
        try:
            # Buscar el usuario por DNI (primero crudo, luego limpio)
            try:
                usuario = Usuario.objects.get(persona__dni=username_raw)
            except Usuario.DoesNotExist:
                if username_clean and username_clean != username_raw:
                    usuario = Usuario.objects.get(persona__dni=username_clean)
                else:
                    return None
            
            # Verificar la contraseña
            if usuario.contrasena == password:
                canonical_username = username_clean or username_raw

                django_user = User.objects.filter(username=canonical_username).first()
                if django_user is None and canonical_username != username_raw:
                    django_user = User.objects.filter(username=username_raw).first()
                    if django_user is not None and not User.objects.filter(username=canonical_username).exclude(pk=django_user.pk).exists():
                        django_user.username = canonical_username
                        django_user.save(update_fields=['username'])

                if django_user is None:
                    django_user = User.objects.create_user(
                        username=canonical_username,
                        password=None,
                        first_name=usuario.persona.nombre,
                        last_name=usuario.persona.apellido,
                    )

                django_user.first_name = usuario.persona.nombre
                django_user.last_name = usuario.persona.apellido
                django_user.save(update_fields=['first_name', 'last_name'])

                return django_user
            
        except Usuario.DoesNotExist:
            return None
        
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None




from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from apps.modulo_1.usuario.models import Usuario, Persona


class DNIAuthenticationBackend(BaseBackend):
    """
    Backend de autenticación personalizado que usa solo DNI y contraseña
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        username_raw = (username or '').strip()
        username_clean = Persona.limpiar_dni(username_raw)
        try:
            # Buscar el usuario por DNI (primero crudo, luego limpio)
            try:
                usuario = Usuario.objects.get(persona__dni=username_raw)
            except Usuario.DoesNotExist:
                if username_clean and username_clean != username_raw:
                    usuario = Usuario.objects.get(persona__dni=username_clean)
                else:
                    return None
            
            # Verificar la contraseña
            if usuario.contrasena == password:
                canonical_username = username_clean or username_raw

                django_user = User.objects.filter(username=canonical_username).first()
                if django_user is None and canonical_username != username_raw:
                    django_user = User.objects.filter(username=username_raw).first()
                    if django_user is not None and not User.objects.filter(username=canonical_username).exclude(pk=django_user.pk).exists():
                        django_user.username = canonical_username
                        django_user.save(update_fields=['username'])

                if django_user is None:
                    django_user = User.objects.create_user(
                        username=canonical_username,
                        password=None,
                        first_name=usuario.persona.nombre,
                        last_name=usuario.persona.apellido,
                    )

                django_user.first_name = usuario.persona.nombre
                django_user.last_name = usuario.persona.apellido
                django_user.save(update_fields=['first_name', 'last_name'])

                return django_user
            
        except Usuario.DoesNotExist:
            return None
        
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None