# Documentación Funcional y Flujos — Edu-Polo

## Índice
- [Roles y Tipos de Usuario](#roles-y-tipos-de-usuario)
- [Autenticación y Seguridad](#autenticación-y-seguridad)
- [Navegación y Dashboards](#navegación-y-dashboards)
- [Cursos, Comisiones y Materiales](#cursos-comisiones-y-materiales)
- [Inscripciones](#inscripciones)
- [Asistencia y Certificación](#asistencia-y-certificación)
- [Administración (Panel)](#administración-panel)
- [API Interna y Rutas](#api-interna-y-rutas)
- [Flujo de Usuario](#flujo-de-usuario)
- [Entidades y Relaciones](#entidades-y-relaciones)

## Roles y Tipos de Usuario
- Persona: datos únicos, utilidades `src/apps/modulo_1/usuario/models.py:5`
- Usuario: credenciales propias (`contrasena`), flags `activo`, permisos `src/apps/modulo_1/usuario/models.py:84`
- Rol: nombre/descripcion y jerarquía 1..5 `src/apps/modulo_1/roles/models.py:6`
- UsuarioRol: relación Usuario↔Rol `src/apps/modulo_1/roles/models.py:117`
- Estudiante: perfil académico `src/apps/modulo_1/roles/models.py:41`
- Docente: especialidad/experiencia `src/apps/modulo_1/roles/models.py:26`
- Tutor: tipo de tutor y datos `src/apps/modulo_1/roles/models.py:64`
- TutorEstudiante: relación y parentesco `src/apps/modulo_1/roles/models.py:88`
- Tipos efectivos en UI: Administrador, Mesa de Entrada, Docente, Estudiante (derivados de roles y estado) `src/apps/modulo_6/administracion/context_processors.py:5`

## Autenticación y Seguridad
- Backend de login por DNI+contrasena (modelo Usuario), sincroniza `django.contrib.auth.User` `src/apps/modulo_6/seguridad/backends.py:6`
- Backends activos en settings `src/core/settings.py:69`
- Rutas de acceso: login, logout, password reset `src/core/urls.py:35-38`

## Navegación y Dashboards
- Landing y dashboards (general, estudiante, docente, admin) `src/core/urls.py:29-33`
- Contexto de permisos en todas las plantillas: `es_admin_completo`, `tipo_usuario`, `puede_ver_asistencias`, `es_docente`, `es_estudiante` `src/apps/modulo_6/administracion/context_processors.py:7-13,15-52`

## Cursos, Comisiones y Materiales
- PoloCreativo: sedes físicas `src/apps/modulo_3/cursos/models.py:5`
- Curso: estados y orden de visualización `src/apps/modulo_3/cursos/models.py:29`
- Comision: modalidad, horarios, cupos, estado y métricas de ocupación `src/apps/modulo_3/cursos/models.py:49`
- ComisionDocente: asignación de docentes a comisiones `src/apps/modulo_3/cursos/models.py:116`
- Material: archivos/enlaces vinculados a comisiones y docentes con validaciones `src/apps/modulo_3/cursos/models.py:128`
- Vistas/URLs estudiantes y CRUD admin `src/apps/modulo_3/cursos/urls.py:7-17`

## Inscripciones
- Inscripcion: estudiante↔comisión, estados, orden de lista de espera y observaciones `src/apps/modulo_2/inscripciones/models.py:5`
- Formulario de inscripción por comisión `src/apps/modulo_2/inscripciones/urls.py:7`

## Asistencia y Certificación
- Asistencia: registro por inscripción+fecha, presente/observaciones/registrado_por `src/apps/modulo_4/asistencia/models.py:5`
- RegistroAsistencia: totales, porcentaje, requisito certificado (≥60%) `src/apps/modulo_4/asistencia/models.py:34`
- Señales: recálculo automático al crear/eliminar asistencias `src/apps/modulo_4/asistencia/signals.py:44-60`

## Administración (Panel)
- Cursos: panel, crear, editar `src/apps/modulo_6/administracion/urls.py:7-11`
- Comisiones: panel, crear, asignar docente `src/apps/modulo_6/administracion/urls.py:12-16`
- Inscripciones: panel, inscribir, exportar `src/apps/modulo_6/administracion/urls.py:17-21`
- Buscadores: estudiantes y exportación `src/apps/modulo_6/administracion/urls.py:22-25`
- Polos: panel y crear `src/apps/modulo_6/administracion/urls.py:26-29`
- Estadísticas detalladas `src/apps/modulo_6/administracion/urls.py:30-31`
- Usuarios: gestión CRUD y exportación `src/apps/modulo_6/administracion/urls.py:33-39`
- API: búsqueda de estudiantes `src/apps/modulo_6/administracion/urls.py:40-42`
- Asistencias: panel, crear/editar/eliminar, exportar por curso/comisión `src/apps/modulo_6/administracion/urls.py:43-49`
- Docentes: mis cursos, estudiantes por comisión, materiales (listar/subir/eliminar) `src/apps/modulo_6/administracion/urls.py:53-61`
- Docentes y cursos (Admin/Mesa de Entrada) `src/apps/modulo_6/administracion/urls.py:62-64`

## API Interna y Rutas
- Núcleo de URLs: landing, dashboards, autenticación, módulos y API de búsqueda por DNI `src/core/urls.py:27-45`
- Usuario: registro, tutores, progreso, materiales, perfil, cambio de contraseña `src/apps/modulo_1/usuario/urls.py:11-24`
- Cursos: estudiantes y CRUD admin `src/apps/modulo_3/cursos/urls.py:7-17`
- Inscripciones: formulario `src/apps/modulo_2/inscripciones/urls.py:7-8`
- Administración: paneles y APIs `src/apps/modulo_6/administracion/urls.py:6-64`

## Flujo de Usuario
- Público: landing y cursos por polo `src/core/urls.py:29,34`
- Registro: crea Usuario (estudiante por defecto) y valida datos `src/apps/modulo_1/usuario/views.py:58-145`
- Login: DNI+contrasena, sesión como `auth.User` `src/apps/modulo_6/seguridad/backends.py:10-33`
- Estudiante: ve cursos, se inscribe, materiales, progreso, certificados
- Docente: gestiona estudiantes/materiales en sus comisiones
- Administración/Mesa de Entrada: gestión integral, paneles y exportaciones
- Asistencia: alimenta progreso y condición de certificado automáticamente `src/apps/modulo_4/asistencia/signals.py:44-60`

## Entidades y Relaciones
- Persona ↔ Usuario (1:N): `src/apps/modulo_1/usuario/models.py:84-91`
- Usuario ↔ Rol (N:M) vía UsuarioRol: `src/apps/modulo_1/roles/models.py:117-123`
- Usuario → Estudiante (1:1/N): `src/apps/modulo_1/roles/models.py:41-61`
- Persona → Docente (1:1/N): `src/apps/modulo_1/roles/models.py:26-38`
- Tutor ↔ Estudiante (N:M) vía TutorEstudiante: `src/apps/modulo_1/roles/models.py:88-114`
- Curso ↔ Comision (1:N): `src/apps/modulo_3/cursos/models.py:49-79`
- Comision ↔ Docente (N:M) vía ComisionDocente: `src/apps/modulo_3/cursos/models.py:116-126`
- Estudiante ↔ Comision (N:M) vía Inscripcion: `src/apps/modulo_2/inscripciones/models.py:5-19,31-37`
- Inscripcion ↔ Asistencia (1:N) y RegistroAsistencia (1:1): `src/apps/modulo_4/asistencia/models.py:11-22,38-43`