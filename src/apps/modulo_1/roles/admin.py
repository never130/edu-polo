from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Rol)
admin.site.register(Docente)
admin.site.register(Estudiante)
admin.site.register(Tutor)
admin.site.register(TutorEstudiante)