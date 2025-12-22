from django.urls import path
from . import views
from .views_tutores import (
    gestionar_tutores,
    agregar_tutor,
    eliminar_tutor,
    agregar_autorizado_retiro,
    confirmar_autorizado_retiro,
    revocar_autorizado_retiro,
    eliminar_autorizado_retiro,
)
from . import views_progreso
from .views_progreso import mi_progreso, mis_certificados, materiales_estudiante, materiales_comision_estudiante
from .views_perfil import mi_perfil, editar_perfil, cambiar_contrasena
from .api_views import buscar_estudiante_por_dni

app_name = 'usuario'

urlpatterns = [
    path('', views.RegistroView.as_view(), name='registro'),
    path('tutores/', gestionar_tutores, name='gestionar_tutores'),
    path('tutores/agregar/', agregar_tutor, name='agregar_tutor'),
    path('tutores/eliminar/<int:relacion_id>/', eliminar_tutor, name='eliminar_tutor'),

    path('tutores/autorizados/agregar/', agregar_autorizado_retiro, name='agregar_autorizado_retiro'),
    path('tutores/autorizados/confirmar/<int:autorizado_id>/', confirmar_autorizado_retiro, name='confirmar_autorizado_retiro'),
    path('tutores/autorizados/revocar/<int:autorizado_id>/', revocar_autorizado_retiro, name='revocar_autorizado_retiro'),
    path('tutores/autorizados/eliminar/<int:autorizado_id>/', eliminar_autorizado_retiro, name='eliminar_autorizado_retiro'),

    path('progreso/', mi_progreso, name='mi_progreso'),
    # path('certificados/', mis_certificados, name='mis_certificados'),
    path('certificados/descargar/<int:inscripcion_id>/', views_progreso.descargar_certificado, name='descargar_certificado'),
    path('materiales/', materiales_estudiante, name='materiales_estudiante'),
    path('materiales/comision/<int:comision_id>/', materiales_comision_estudiante, name='materiales_comision_estudiante'),
    path('perfil/', mi_perfil, name='mi_perfil'),
    path('perfil/editar/', editar_perfil, name='editar_perfil'),
    path('perfil/cambiar-contrasena/', cambiar_contrasena, name='cambiar_contrasena'),
]

# API endpoints
api_urlpatterns = [
    path('api/buscar-estudiante/<str:dni>/', buscar_estudiante_por_dni, name='api_buscar_estudiante'),
]

urlpatterns += api_urlpatterns

