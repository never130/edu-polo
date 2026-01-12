from django.urls import path

from . import views

app_name = 'empresas'

urlpatterns = [
    path('', views.mi_empresa, name='mi_empresa'),
    path('equipo/', views.equipo, name='equipo'),
    path('mesa-entrada/', views.mesa_entrada_list, name='mesa_entrada_list'),
    path('mesa-entrada/<int:empresa_id>/', views.mesa_entrada_detalle, name='mesa_entrada_detalle'),
    path('gestion/', views.EmpresaListView.as_view(), name='gestion_empresas'),
]