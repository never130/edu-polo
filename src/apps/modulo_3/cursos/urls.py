from django.urls import path
from . import views
from .views_cursos_estudiante import ver_cursos_disponibles

app_name = 'cursos'

urlpatterns = [
    # Vistas para estudiantes (requieren login)
    path('disponibles/', ver_cursos_disponibles, name='ver_disponibles'),
    path('mis-inscripciones/', views.mis_inscripciones, name='mis_inscripciones'),
    
    # Vistas CRUD para admin
    path('', views.CursoListView.as_view(), name='lista'),
    path('crear/', views.CursoCreateView.as_view(), name='crear'),
    path('<int:pk>/actualizar/', views.CursoUpdateView.as_view(), name='actualizar'),
    path('<int:pk>/eliminar/', views.CursoDeleteView.as_view(), name='eliminar'),
]
