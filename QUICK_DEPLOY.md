# 🚀 Despliegue Rápido - Sistema Educativo Polo

## ⚡ Opción Más Rápida: Railway

### Paso 1: Preparar el código
1. Asegúrate de que todos los cambios estén en GitHub
2. Haz commit y push de todos los archivos

### Paso 2: Desplegar en Railway (5 minutos)

1. **Ve a Railway:**
   - Abre https://railway.app
   - Haz clic en "Login" y conéctate con GitHub

2. **Crear nuevo proyecto:**
   - Haz clic en "New Project"
   - Selecciona "Deploy from GitHub repo"
   - Elige tu repositorio

3. **Railway detectará automáticamente:**
   - ✅ Dockerfile
   - ✅ Configuración de Python
   - ✅ Puerto 8000

4. **Agregar base de datos PostgreSQL:**
   - En tu proyecto, haz clic en "New"
   - Selecciona "Database" → "PostgreSQL"
   - Railway configurará automáticamente `DATABASE_URL`

5. **Configurar variables de entorno:**
   - Ve a "Variables" en tu proyecto
   - Agrega estas variables:
     ```
     DEBUG=0
     SECRET_KEY=genera-una-clave-secreta-muy-larga-y-aleatoria-aqui
     ```
   - Para generar SECRET_KEY, puedes usar:
     ```python
     python -c "import secrets; print(secrets.token_urlsafe(50))"
     ```

6. **¡Listo!**
   - Railway desplegará automáticamente
   - Obtendrás una URL como: `https://tu-app.up.railway.app`
   - La aplicación estará online en 2-3 minutos

### Paso 3: Configurar la aplicación

1. **Ejecutar migraciones:**
   - En Railway, ve a tu servicio web
   - Haz clic en "Deployments" → "View Logs"
   - O ejecuta manualmente:
     ```bash
     railway run python manage.py migrate
     ```

2. **Crear superusuario:**
   ```bash
   railway run python manage.py createsuperuser
   ```

3. **Acceder a la aplicación:**
   - Visita la URL que Railway te proporcionó
   - Inicia sesión con el superusuario creado

---

## 🔧 Alternativa: Render (También Gratis)

### Pasos Rápidos:

1. **Ve a Render:** https://render.com
2. **Nuevo Web Service:**
   - Conecta tu repositorio de GitHub
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `cd src && gunicorn core.wsgi:application --bind 0.0.0.0:$PORT`
3. **Agregar PostgreSQL:**
   - "New" → "PostgreSQL" (plan gratuito)
4. **Variables de entorno:**
   ```
   DEBUG=0
   SECRET_KEY=tu-clave-secreta
   ```
5. **¡Desplegar!**

---

## 📝 Checklist Pre-Despliegue

- [x] ✅ Dockerfile creado
- [x] ✅ settings.py actualizado para producción
- [x] ✅ requirements.txt incluye todas las dependencias
- [ ] ⚠️ Cambiar SECRET_KEY en producción
- [ ] ⚠️ Configurar ALLOWED_HOSTS con tu dominio
- [ ] ⚠️ Ejecutar migraciones
- [ ] ⚠️ Crear superusuario

---

## 🎯 URLs Importantes

Después del despliegue, tendrás acceso a:
- **Aplicación principal:** `https://tu-app.up.railway.app`
- **Admin Django:** `https://tu-app.up.railway.app/admin/`
- **Panel Admin:** `https://tu-app.up.railway.app/dashboard/admin/`

---

## 💡 Tips

1. **Railway es gratis** para empezar (500 horas/mes)
2. **Render también es gratis** (plan free tier)
3. **Ambos** configuran PostgreSQL automáticamente
4. **Despliegue automático** desde GitHub en cada push

---

## 🆘 Problemas Comunes

### "DisallowedHost"
- Solución: Agrega tu dominio a `ALLOWED_HOSTS` en Railway variables

### "Static files not found"
- Solución: Ya está configurado con WhiteNoise, debería funcionar automáticamente

### "Database connection failed"
- Solución: Verifica que PostgreSQL esté agregado y `DATABASE_URL` esté configurado

---

## 🎉 ¡Listo!

Tu aplicación estará online en menos de 10 minutos siguiendo estos pasos.



