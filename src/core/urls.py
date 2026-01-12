"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from apps import core_views
from apps.modulo_1.usuario.api_views import buscar_estudiante_por_dni
from apps.modulo_6.seguridad.views import custom_login
from apps.modulo_6.seguridad.views_password_reset import password_reset_request, password_reset_confirm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', core_views.landing, name='landing'),
    path('polos/', core_views.lista_polos, name='lista_polos'),
    path('dashboard/', core_views.dashboard, name='dashboard'),
    path('dashboard/estudiante/', core_views.dashboard_estudiante, name='dashboard_estudiante'),
    path('dashboard/empresa/', core_views.dashboard_empresa, name='dashboard_empresa'),
    path('dashboard/docente/', core_views.dashboard_docente, name='dashboard_docente'),
    path('dashboard/admin/', core_views.dashboard_admin, name='dashboard_admin'),
    path('polo/<int:polo_id>/cursos/', core_views.cursos_por_polo, name='cursos_por_polo'),
    path('accounts/login/', custom_login, name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='landing'), name='logout'),
    path('accounts/password-reset/', password_reset_request, name='password_reset_request'),
    path('accounts/password-reset-confirm/', password_reset_confirm, name='password_reset_confirm'),
    path('accounts/registro/', include('apps.modulo_1.usuario.urls')),
    path('cursos/', include('apps.modulo_3.cursos.urls')),
    path('inscripciones/', include('apps.modulo_2.inscripciones.urls')),
    path('panel/', include('apps.modulo_6.administracion.urls')),
    path('empresas/', include('apps.modulo_7.empresas.urls')),
    # API
    path('api/buscar-estudiante/<str:dni>/', buscar_estudiante_por_dni, name='api_buscar_estudiante'),
    path('api/estudiantes-por-curso/', core_views.api_estudiantes_por_curso, name='api_estudiantes_por_curso'),
]

# Servir archivos media y estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
