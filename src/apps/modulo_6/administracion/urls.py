from django.urls import path
from . import views

app_name = 'administracion'

urlpatterns = [
    # Gestión de Cursos
    path('cursos/', views.panel_cursos, name='panel_cursos'),
    path('cursos/crear/', views.crear_curso, name='crear_curso'),
    path('cursos/editar/<int:curso_id>/', views.editar_curso, name='editar_curso'),
    
    # Gestión de Comisiones
    path('comisiones/', views.panel_comisiones, name='panel_comisiones'),
    path('comisiones/crear/', views.crear_comision, name='crear_comision'),
    path('comisiones/toggle-publicacion/<int:comision_id>/', views.toggle_publicacion_comision, name='toggle_publicacion_comision'),
    path('comisiones/asignar-docente/<int:comision_id>/', views.asignar_docente_comision, name='asignar_docente_comision'),
    
    # Gestión de Inscripciones
    path('inscripciones/', views.panel_inscripciones, name='panel_inscripciones'),
    path('inscripciones/inscribir/', views.inscribir_estudiante_admin, name='inscribir_estudiante'),
    path('inscripciones/exportar/', views.exportar_inscripciones, name='exportar_inscripciones'),
    
    # Buscadores
    path('estudiantes/', views.buscador_estudiantes, name='buscador_estudiantes'),
    path('estudiantes/exportar/', views.exportar_estudiantes, name='exportar_estudiantes'),
    
    # Gestión de Polos Creativos
    path('polos/', views.panel_polos, name='panel_polos'),
    path('polos/crear/', views.crear_polo, name='crear_polo'),
    
    # Estadísticas Detalladas
    path('estadisticas/', views.estadisticas_detalladas, name='estadisticas'),
    
    # Gestión de Usuarios
    path('usuarios/', views.gestion_usuarios, name='gestion_usuarios'),
    path('usuarios/crear/', views.crear_usuario_admin, name='crear_usuario'),
    path('usuarios/editar/<int:persona_id>/', views.editar_usuario_admin, name='editar_usuario'),
    path('usuarios/eliminar/<int:persona_id>/', views.eliminar_usuario_admin, name='eliminar_usuario'),
    path('usuarios/exportar-excel/', views.exportar_usuarios_excel, name='exportar_usuarios_excel'),
    
    # API
    path('api/buscar-estudiantes/', views.api_buscar_estudiantes, name='api_buscar_estudiantes'),
    path('api/detalle-estudiante/', views.api_detalle_estudiante, name='api_detalle_estudiante'),
    
    # Gestión de Asistencias
    path('asistencias/', views.panel_asistencia, name='panel_asistencia'),
    path('asistencias/crear-editar/<int:inscripcion_id>/', views.crear_editar_asistencia, name='crear_editar_asistencia'),
    path('asistencias/eliminar/<int:asistencia_id>/', views.eliminar_asistencia, name='eliminar_asistencia'),
    path('asistencias/exportar-por-curso/', views.exportar_asistencias_por_curso, name='exportar_asistencias_curso'),
    path('asistencias/exportar-por-comision/', views.exportar_asistencias_por_comision, name='exportar_asistencias_comision'),
    
    # Exportación de Estadísticas
    path('estadisticas/exportar-estudiantes-curso/', views.exportar_estadisticas_estudiantes_curso, name='exportar_estadisticas_estudiantes_curso'),
    
    # Vistas para Docentes
    path('docente/mis-cursos/', views.mis_cursos_docente, name='mis_cursos_docente'),
    path('docente/estudiantes/', views.estudiantes_docente, name='estudiantes_docente'),
    path('docente/estudiantes/<int:comision_id>/', views.estudiantes_comision, name='estudiantes_comision'),
    path('docente/materiales/', views.materiales_docente, name='materiales_docente'),
    path('docente/materiales/<int:comision_id>/', views.materiales_comision, name='materiales_comision'),
    path('docente/materiales/<int:comision_id>/subir/', views.subir_material, name='subir_material'),
    path('docente/materiales/eliminar/<int:material_id>/', views.eliminar_material, name='eliminar_material'),
    
    # Vista para ver docentes y sus cursos (Admin y Mesa de Entrada)
    path('docentes-cursos/', views.docentes_cursos, name='docentes_cursos'),
]


