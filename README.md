# 🎓 Edu-Polo - Sistema Educativo

Sistema de gestión educativa desarrollado con Django para la administración de cursos, estudiantes, docentes y materiales.

## 🚀 Despliegue Rápido

### Opción 1: Render (Recomendado - Gratis)

**Render se conecta automáticamente con GitHub y despliega tu app cuando haces push.**

1. **Ve a [Render.com](https://render.com)** y crea una cuenta (gratis)
2. **Conecta tu repositorio de GitHub:**
   - Haz clic en "New +" → "Web Service"
   - Selecciona tu repositorio: `bogapunk/edu-polo`
   - Render detectará automáticamente el archivo `render.yaml`
3. **Agrega una base de datos PostgreSQL:**
   - Haz clic en "New +" → "PostgreSQL"
   - Plan: Free
4. **¡Listo!** Render te dará una URL como: `https://edu-polo-app.onrender.com`

**Ventajas:**
- ✅ Despliegue automático cuando haces `git push`
- ✅ Gratis para empezar
- ✅ Base de datos PostgreSQL incluida
- ✅ HTTPS automático

### Opción 2: Railway (Alternativa)

1. **Ve a [Railway.app](https://railway.app)** y crea una cuenta
2. **Conecta tu repositorio de GitHub:**
   - "New Project" → "Deploy from GitHub repo"
   - Selecciona `bogapunk/edu-polo`
3. **Agrega PostgreSQL:**
   - "New" → "Database" → "PostgreSQL"
4. **Railway detectará el Dockerfile y desplegará automáticamente**

**URL resultante:** `https://tu-app.railway.app`

---

## 📋 Después del Despliegue

Una vez desplegado, ejecuta estos comandos en la terminal del servicio:

```bash
# 1. Ejecutar migraciones
cd src && python manage.py migrate

# 2. Crear superusuario
cd src && python manage.py createsuperuser
```

---

## 🔗 Compartir tu Proyecto

Una vez desplegado, tendrás una URL pública que puedes compartir:

- **Render:** `https://edu-polo-app.onrender.com`
- **Railway:** `https://tu-app.railway.app`

Esta URL es pública y cualquiera puede acceder a tu aplicación.

---

## 🛠️ Desarrollo Local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar migraciones
cd src
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver
```

---

## 📝 Nota Importante

**GitHub Pages NO funciona para aplicaciones Django** porque:
- GitHub Pages solo sirve sitios estáticos (HTML, CSS, JS)
- Django necesita un servidor Python y base de datos
- Por eso usamos servicios como Render o Railway

**Pero la buena noticia es que estos servicios:**
- Se conectan automáticamente con GitHub
- Despliegan automáticamente cuando haces `git push`
- Son gratuitos para empezar
- Te dan una URL pública para compartir

---

## 🔧 Tecnologías

- **Backend:** Django 5.2.7
- **Base de Datos:** PostgreSQL (producción) / SQLite (desarrollo)
- **Servidor:** Gunicorn
- **Archivos Estáticos:** WhiteNoise

---

## 📞 Soporte

Para más información sobre despliegue, consulta el archivo `DEPLOY.md`

