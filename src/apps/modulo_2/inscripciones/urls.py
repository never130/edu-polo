from django.urls import path
from . import views

app_name = 'inscripciones'

urlpatterns = [
    path('formulario/<int:comision_id>/', views.formulario_inscripcion, name='formulario'),
]





