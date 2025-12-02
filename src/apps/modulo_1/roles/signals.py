from django.db.models.signals import post_migrate
from django.contrib.auth.models import Group, Permission
from django.dispatch import receiver


@receiver(post_migrate)
def crear_roles_y_permisos(sender, **kwargs):
    #Preparado, falta tener el resto de tablas funcionales para agregar los permisos
    roles = {
        "Administrador": [],
        "Coordinador": [],
        "MesaEntrada": [],
        "Docente": [],
        "Estudiante": [],
        "PuntoMedio": [],
    }


    for nombre, permisos in roles.items():
            grupo, _ = Group.objects.get_or_create(name=nombre)
            for codename in permisos:
                try:
                    permiso = Permission.objects.get(codename=codename)
                    grupo.permissions.add(permiso)
                except Permission.DoesNotExist:
                    print(f"El permiso {codename} no existe.")