## Roles y Tipos de Usuario
- Persona: entidad central con datos únicos y utilidades (edad, nombre completo) `src/apps/modulo_1/usuario/models.py:5-83`.
- Usuario (propio): credenciales locales (campo `contrasena`) y flags `activo`, permisos de imagen/voz `src/apps/modulo_1/usuario/models.py:84-97`.
- Rol: nombre/descripcion y jerarquía 1..5, con mapeo Usuario↔Rol `src/apps/modulo_1/roles/models.py:6-23`, `src/apps/modulo_1/roles/models.py:117-123`.
- Perfiles funcionales:
  - Estudiante `src/apps/modulo_1/roles/models.py:41-61`
  - Docente `src/apps/modulo_1/roles/models.py:26-38`
  - Tutor y relación Tutor-Estudiante (obligatorio para menores) `src/apps/modulo_1/roles/models.py:64-114`.
- Tipos efectivos en UI (derivados y rol explícito): Administrador (Django staff/superuser), Mesa de Entrada, Docente, Estudiante; expuestos vía context processor `src/apps/modulo_6/administracion/context_processors.py:5-52`.

## Autenticación y Seguridad
- Backend de login por DNI+contrasena del modelo Usuario; crea/actualiza espejo en `django.contrib.auth.User` `src/apps/modulo_6/seguridad/backends.py:6-44`.
- Configuración activa del backend en settings `src/core/settings.py:69-73`.
- Rutas de acceso: login personalizado, logout, password reset `src/core/urls.py:35-38`.

## Navegación y Dashboards
- Landing y rutas de dashboard general y específicos para Estudiante/Docente/Admin `src/core/urls.py:29-33`.
- Contexto de permisos en templates: `es_admin_completo`, `es_docente`, `es_estudiante`, `puede_ver_asistencias` `src/apps/modulo_6/administracion/context_processors.py:7-13, 15-52`.

## Cursos, Comisiones y Materiales
- PoloCreativo, Curso y Comision con estados, cupos y modalidad `src/apps/modulo_3/cursos/models.py:5-115`.
- Asignación de docentes a comisiones vía tabla intermedia `ComisionDocente` `src/apps/modulo_3/cursos/models.py:116-126`.
- Materiales por comisión (archivo o enlace), validaciones de consistencia `src/apps/modulo_3/cursos/models.py:128-155`.
- Vistas y rutas: lista/crear/editar/eliminar curso; cursos disponibles y mis inscripciones `src/apps/modulo_3/cursos/urls.py:7-17`.

## Inscripciones
- Modelo `Inscripcion` (estudiante↔comisión) con estados y observaciones, orden de lista de espera `src/apps/modulo_2/inscripciones/models.py:5-47`.
- Formulario de inscripción vía URL `src/apps/modulo_2/inscripciones/urls.py:7-8`.

## Asistencia y Certificación
- Registro de asistencias por inscripción/fecha y auditoría de quien registra `src/apps/modulo_4/asistencia/models.py:5-32`.
- Agregado `RegistroAsistencia` con métricas y requisito de certificado (≥60%) `src/apps/modulo_4/asistencia/models.py:34-66`.
- Señales que recalculan métricas automáticamente al crear/eliminar asistencias `src/apps/modulo_4/asistencia/signals.py:44-60`.
- Vistas de progreso/certificados y descarga (ReportLab si disponible) `src/apps/modulo_1/usuario/views_progreso.py`.

## Administración (Panel)
- Gestión integral: cursos, comisiones (crear/asignar docentes), inscripciones (panel, exportación), buscadores, polos, estadísticas, usuarios (CRUD, exportación), asistencias (panel/crear/editar/eliminar, exportaciones), docencia (mis cursos, estudiantes, materiales) `src/apps/modulo_6/administracion/urls.py:6-64`.

## API Interna
- Búsqueda de estudiante por DNI: `core/urls.py:44` y `src/apps/modulo_1/usuario/api_views.py`.

## Flujo de Usuario (Resumido)
- Público: landing, cursos por polo, registro (Estudiante por defecto) `src/apps/modulo_1/usuario/views.py:58-145`, `src/core/urls.py:29-35, 39-42`.
- Login por DNI; dashboard según rol/estado; estudiantes ven cursos y se inscriben; docentes gestionan estudiantes/materiales; administración gestiona todo.
- Asistencia alimenta progreso y condición de certificado automáticamente.

## Plan de Entrega de Documentación
### Objetivo
- Generar documentación técnica del sistema enfocada en roles, permisos, funcionalidades y flujos de navegación.

### Entregables
1. Mapa de roles y permisos efectivos (incluyendo jerarquías y derivaciones).
2. Diagrama de entidades principales (Persona/Usuario/Rol/Estudiante/Docente/Tutor/Inscripción/Comisión/Asistencia/RegistroAsistencia/Material).
3. Catálogo de funcionalidades por módulo y por rol (Admin, Mesa de Entrada, Docente, Estudiante).
4. Flujo de autenticación (DNI→Usuario→Auth.User) y recuperación de contraseña.
5. Índice de rutas/URLs por módulo con propósito.
6. Resumen de señales y efectos colaterales (asistencia→progreso/certificado).

### Método
- Navegar modelos, vistas y URLs existentes; corroborar con templates.
- Registrar referencias de código con `ruta:línea`.
- Entregar documento estructurado en secciones anteriores.

### Próximo Paso
- Confirmar este plan para producir el informe completo en la siguiente iteración sin modificar código.
