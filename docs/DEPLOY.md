# 🚀 Guía de Despliegue - Sistema Educativo Polo

Esta guía te ayudará a desplegar la aplicación en diferentes plataformas de hosting.

## 📋 Opciones de Despliegue

### 1. 🟣 Railway (Recomendado - Más Fácil)

Railway es una plataforma muy fácil de usar con soporte nativo para Docker.

#### Pasos:

1. **Crear cuenta en Railway:**
   - Ve a https://railway.app
   - Regístrate con GitHub

2. **Conectar el repositorio:**
   - Haz clic en "New Project"
   - Selecciona "Deploy from GitHub repo"
   - Conecta tu repositorio

3. **Configurar variables de entorno:**
   - Ve a "Variables" en tu proyecto
   - Agrega:
     ```
     DEBUG=0
     SECRET_KEY=tu-secret-key-muy-seguro-aqui
     PORT=8000
     ```

4. **Agregar base de datos PostgreSQL (opcional):**
   - Haz clic en "New" → "Database" → "PostgreSQL"
   - Railway configurará automáticamente `DATABASE_URL`

5. **Desplegar:**
   - Railway detectará automáticamente el Dockerfile
   - El despliegue comenzará automáticamente

6. **Obtener URL:**
   - Railway te dará una URL como: `https://tu-app.railway.app`

#### Comandos útiles en Railway:
- Ver logs: En el dashboard de Railway
- Ejecutar comandos: Usa "Deployments" → "View Logs" → "Run Command"

---

### 2. 🔵 Render

Render es otra excelente opción gratuita.

#### Pasos:

1. **Crear cuenta en Render:**
   - Ve a https://render.com
   - Regístrate con GitHub

2. **Crear nuevo Web Service:**
   - Haz clic en "New" → "Web Service"
   - Conecta tu repositorio de GitHub

3. **Configurar el servicio:**
   - **Name:** edu-polo-app
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt && python src/manage.py collectstatic --noinput`
   - **Start Command:** `cd src && gunicorn core.wsgi:application --bind 0.0.0.0:$PORT`
   - **Root Directory:** (dejar vacío)

4. **Agregar base de datos PostgreSQL:**
   - Haz clic en "New" → "PostgreSQL"
   - Render configurará automáticamente `DATABASE_URL`

5. **Variables de entorno:**
   ```
   DEBUG=0
   SECRET_KEY=tu-secret-key-muy-seguro-aqui
   PYTHON_VERSION=3.11.4
   ```

6. **Desplegar:**
   - Haz clic en "Create Web Service"
   - Render construirá y desplegará automáticamente

---

### 3. 🟠 Heroku

Heroku es una plataforma clásica pero sigue siendo útil.

#### Pasos:

1. **Instalar Heroku CLI:**
   ```bash
   # Windows (con Chocolatey)
   choco install heroku-cli
   
   # O descarga desde: https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login en Heroku:**
   ```bash
   heroku login
   ```

3. **Crear aplicación:**
   ```bash
   heroku create tu-app-nombre
   ```

4. **Agregar PostgreSQL:**
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```

5. **Configurar variables:**
   ```bash
   heroku config:set DEBUG=0
   heroku config:set SECRET_KEY=tu-secret-key-muy-seguro
   ```

6. **Desplegar:**
   ```bash
   git push heroku main
   ```

7. **Ejecutar migraciones:**
   ```bash
   heroku run python src/manage.py migrate
   ```

8. **Crear superusuario:**
   ```bash
   heroku run python src/manage.py createsuperuser
   ```

---

### 4. 🟢 DigitalOcean App Platform

#### Pasos:

1. **Crear cuenta en DigitalOcean:**
   - Ve a https://www.digitalocean.com

2. **Crear nueva App:**
   - Ve a "Apps" → "Create App"
   - Conecta tu repositorio de GitHub

3. **Configurar:**
   - Selecciona el repositorio
   - DigitalOcean detectará automáticamente el Dockerfile
   - Agrega una base de datos PostgreSQL

4. **Variables de entorno:**
   ```
   DEBUG=0
   SECRET_KEY=tu-secret-key
   ```

5. **Desplegar:**
   - Haz clic en "Create Resources"

---

## 🔧 Configuración Pre-Despliegue

### 1. Actualizar settings.py para producción

Agrega al inicio de `src/core/settings.py`:

```python
import os
from pathlib import Path

# Detectar si estamos en producción
IS_PRODUCTION = os.environ.get('DEBUG', '1') == '0'

# Base de datos
if os.environ.get('DATABASE_URL'):
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'))
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Seguridad en producción
if IS_PRODUCTION:
    DEBUG = False
    ALLOWED_HOSTS = ['*']  # Cambia esto por tu dominio
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
else:
    DEBUG = True
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
```

### 2. Archivos estáticos

Asegúrate de que `settings.py` tenga:

```python
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'stc',
]

# Para producción con WhiteNoise
if IS_PRODUCTION:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
```

---

## 📝 Checklist Pre-Despliegue

- [ ] Actualizar `ALLOWED_HOSTS` con tu dominio
- [ ] Cambiar `SECRET_KEY` a una clave segura
- [ ] Configurar `DEBUG=0` en producción
- [ ] Configurar base de datos PostgreSQL (recomendado)
- [ ] Probar localmente con Docker
- [ ] Ejecutar `collectstatic` antes del despliegue
- [ ] Ejecutar migraciones
- [ ] Crear superusuario

---

## 🆘 Solución de Problemas

### Error: "DisallowedHost"
- Solución: Agrega tu dominio a `ALLOWED_HOSTS` en settings.py

### Error: "Static files not found"
- Solución: Ejecuta `python manage.py collectstatic --noinput`

### Error: "Database connection failed"
- Solución: Verifica que `DATABASE_URL` esté configurado correctamente

### Error: "Port already in use"
- Solución: Usa la variable de entorno `PORT` que proporciona el hosting

---

## 🔗 Enlaces Útiles

- **Railway:** https://railway.app
- **Render:** https://render.com
- **Heroku:** https://heroku.com
- **DigitalOcean:** https://www.digitalocean.com

---

## 💡 Recomendación

Para empezar rápido, usa **Railway**:
- ✅ Gratis para empezar
- ✅ Muy fácil de usar
- ✅ Soporte nativo para Docker
- ✅ Base de datos PostgreSQL incluida
- ✅ Despliegue automático desde GitHub



