# 🔧 Solución de Error 500 (Internal Server Error) en Render

## Pasos para Solucionar el Error

### 1. Verificar Variables de Entorno en Render

Ve a tu servicio en Render → **Environment** y asegúrate de tener estas variables:

```
DEBUG=0
SECRET_KEY=<tu-secret-key-generado>
DATABASE_URL=<url-de-la-base-de-datos>
ALLOWED_HOSTS=tu-app.onrender.com
CSRF_TRUSTED_ORIGINS=https://tu-app.onrender.com
```

**Importante:** Reemplaza `tu-app.onrender.com` con la URL real que Render te dio.

### 2. Verificar que la Base de Datos esté Conectada

1. Ve a **Dashboard** en Render
2. Verifica que la base de datos PostgreSQL esté creada y conectada
3. Copia la **Internal Database URL** y pégala en la variable `DATABASE_URL`

### 3. Ejecutar Migraciones Manualmente

Si las migraciones no se ejecutaron automáticamente:

1. Ve a tu servicio en Render
2. Haz clic en **Shell** (terminal)
3. Ejecuta:
```bash
cd src
python manage.py migrate
```

### 4. Verificar los Logs

1. Ve a tu servicio en Render
2. Haz clic en **Logs**
3. Busca errores específicos como:
   - `ModuleNotFoundError`
   - `Database connection failed`
   - `TemplateDoesNotExist`
   - `CSRF verification failed`

### 5. Crear Superusuario (si es necesario)

En la Shell de Render:
```bash
cd src
python manage.py createsuperuser
```

### 6. Verificar Archivos Estáticos

Si hay errores con archivos estáticos, en la Shell:
```bash
cd src
python manage.py collectstatic --noinput
```

## Errores Comunes y Soluciones

### Error: "DisallowedHost"
**Solución:** Agrega tu dominio a `ALLOWED_HOSTS`:
```
ALLOWED_HOSTS=tu-app.onrender.com
```

### Error: "CSRF verification failed"
**Solución:** Agrega tu dominio a `CSRF_TRUSTED_ORIGINS`:
```
CSRF_TRUSTED_ORIGINS=https://tu-app.onrender.com
```

### Error: "Database connection failed"
**Solución:** 
1. Verifica que `DATABASE_URL` esté configurada correctamente
2. Asegúrate de que la base de datos esté activa en Render

### Error: "ModuleNotFoundError"
**Solución:** Verifica que `requirements.txt` tenga todas las dependencias

## Verificar que Todo Funcione

1. Accede a tu URL: `https://tu-app.onrender.com`
2. Deberías ver la página de inicio o login
3. Si aún hay error 500, revisa los logs en Render

## Contacto

Si el problema persiste, comparte los logs de Render para diagnosticar mejor.

