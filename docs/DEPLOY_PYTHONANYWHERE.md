# Guía de Despliegue en PythonAnywhere

Esta guía detalla los pasos para desplegar la aplicación "Edu-Polo" en PythonAnywhere.

## Prerrequisitos
- Una cuenta en [PythonAnywhere](https://www.pythonanywhere.com/).
- El código de tu proyecto subido a un repositorio (GitHub, GitLab, etc.) o listo para subir.

## Paso 1: Configuración Inicial en PythonAnywhere

1. **Iniciar Sesión**: Entra a tu cuenta de PythonAnywhere.
2. **Consola Bash**: Abre una nueva consola "Bash" desde el Dashboard.

## Paso 2: Obtener el Código

En la consola Bash, clona tu repositorio:
```bash
git clone https://github.com/tu-usuario/edu-polo.git
cd edu-polo
```
*(Reemplaza la URL con la de tu repositorio)*.

## Paso 3: Crear Entorno Virtual

Crea y activa un entorno virtual para aislar las dependencias:
```bash
mkvirtualenv --python=/usr/bin/python3.10 edu-polo-env
```
*(Puedes cambiar la versión de Python si es necesario)*.

## Paso 4: Instalar Dependencias

Instala los requerimientos del proyecto:
```bash
pip install -r requirements.txt
```
*Asegúrate de tener un archivo `requirements.txt` en la raíz de tu proyecto.*

## Paso 5: Configuración de Variables de Entorno

1. Crea un archivo `.env` en la carpeta raíz del proyecto (donde está `manage.py`):
```bash
nano .env
```
2. Agrega las variables necesarias (ajusta según tu configuración):
```
DEBUG=False
SECRET_KEY=tu_clave_secreta_segura
ALLOWED_HOSTS=.pythonanywhere.com
DATABASE_URL=sqlite:///db.sqlite3
```
3. Guarda con `Ctrl+O`, `Enter` y sal con `Ctrl+X`.

## Paso 6: Configuración de Base de Datos y Archivos Estáticos

Ejecuta las migraciones y recolecta archivos estáticos:
```bash
python manage.py migrate
python manage.py collectstatic
```

## Paso 7: Configuración de Web App

1. Ve a la pestaña **Web** en el Dashboard de PythonAnywhere.
2. Haz clic en **Add a new web app**.
3. Selecciona **Manual configuration** (ya creamos el entorno virtual).
4. Elige la versión de Python que usaste (ej. 3.10).

### Configurar Rutas
En la sección **Code**:
- **Source code**: `/home/tu_usuario/edu-polo/src` (o la ruta donde esté `manage.py`).
- **Working directory**: `/home/tu_usuario/edu-polo/src`.

### Configurar Entorno Virtual
En la sección **Virtualenv**:
- Ingresa la ruta: `/home/tu_usuario/.virtualenvs/edu-polo-env`.

### Configurar Archivos Estáticos
En la sección **Static files**:
- **URL**: `/static/`
- **Directory**: `/home/tu_usuario/edu-polo/src/staticfiles` (o la ruta definida en `STATIC_ROOT`).

## Paso 8: Configurar WSGI

1. En la pestaña **Web**, haz clic en el enlace del archivo **WSGI configuration file**.
2. Borra el contenido por defecto y configura para Django:

```python
import os
import sys

# Ruta al proyecto
path = '/home/tu_usuario/edu-polo/src'
if path not in sys.path:
    sys.path.append(path)

# Configuración de entorno
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'

# Iniciar aplicación WSGI
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```
*(Asegúrate de reemplazar `tu_usuario` y `core.settings` si tu carpeta de configuración se llama diferente)*.

## Paso 9: Finalizar

1. Vuelve a la pestaña **Web**.
2. Haz clic en el botón verde **Reload**.
3. Visita tu URL (ej. `tu_usuario.pythonanywhere.com`) para ver la aplicación funcionando.

## Solución de Problemas

- Si ves errores, revisa los **Error log** en la pestaña Web.
- Asegúrate de que `ALLOWED_HOSTS` incluya tu dominio de PythonAnywhere.
