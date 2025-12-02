from django.urls import path
from . import views

# Nombre del namespace para esta app
app_name = 'docentes'

urlpatterns = [
    # Ruta para la lista de docentes
    path('', views.DocenteListView.as_view(), name='docente_list'),
    
    # Ruta para crear un nuevo docente
    path('nuevo/', views.DocenteCreateView.as_view(), name='docente_create'),
    
    # Ruta para editar un docente (pasa el 'pk' del Docente)
    path('<int:pk>/editar/', views.DocenteUpdateView.as_view(), name='docente_update'),
    
    # Ruta para eliminar un docente
    path('<int:pk>/eliminar/', views.DocenteDeleteView.as_view(), name='docente_delete'),
]
