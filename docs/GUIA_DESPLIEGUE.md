# 🚀 Guía de Despliegue en Producción (Ubuntu/Debian)

Esta guía detalla paso a paso cómo desplegar el proyecto **Edu-Polo** en un servidor privado virtual (VPS) utilizando **Nginx**, **Gunicorn** y **PostgreSQL**.

---

## 1. Preparación del Servidor

Conéctate a tu servidor vía SSH y asegúrate de que el sistema esté actualizado.

```bash
# Actualizar lista de paquetes y sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias necesarias (Python, PostgreSQL, Nginx, Git, etc.)
sudo apt install python3-venv python3-dev libpq-dev postgresql postgresql-contrib nginx curl git -y
```

---

## 2. Configuración de Base de Datos (PostgreSQL)

Configura la base de datos y el usuario que utilizará la aplicación.

```bash
# Cambiar al usuario postgres
sudo -u postgres psql

# Dentro de la consola SQL:
CREATE DATABASE edupolo_db;
CREATE USER edupolo_user WITH PASSWORD 'tu_password_segura';

# Configuración recomendada para Django
ALTER ROLE edupolo_user SET client_encoding TO 'utf8';
ALTER ROLE edupolo_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE edupolo_user SET timezone TO 'UTC';

# Dar privilegios
GRANT ALL PRIVILEGES ON DATABASE edupolo_db TO edupolo_user;

# Salir
\q
```

---

## 3. Configuración del Proyecto

### Clonar el repositorio y preparar el entorno

```bash
# Navegar a un directorio (por ejemplo, /var/www/)
cd /var/www

# Clonar repositorio (reemplaza la URL con la tuya)
sudo git clone https://github.com/tu-usuario/edu-polo.git
cd edu-polo

# Crear entorno virtual
python3 -m venv venv

# Activar entorno
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### Configurar Variables de Entorno

Crea el archivo `.env` con la configuración de producción.

```bash
# Copiar el ejemplo
cp .env.example .env

# Editar el archivo
nano .env
```

**Valores importantes a configurar en `.env`:**

```ini
DEBUG=0
SECRET_KEY=generar_una_clave_larga_y_aleatoria
ALLOWED_HOSTS=midominio.com,www.midominio.com,ip_del_servidor
DATABASE_URL=postgres://edupolo_user:tu_password_segura@localhost:5432/edupolo_db
```

### Comandos Finales de Django

```bash
# Aplicar migraciones a la base de datos PostgreSQL
python src/manage.py migrate

# Recopilar archivos estáticos (CSS, JS, Imágenes)
python src/manage.py collectstatic --noinput

# Crear superusuario (opcional, para entrar al admin)
python src/manage.py createsuperuser
```

---

## 4. Configuración de Gunicorn (Systemd)

Para que la aplicación se ejecute en segundo plano y se reinicie automáticamente, creamos un servicio de systemd.

```bash
sudo nano /etc/systemd/system/edupolo.service
```

Pega el siguiente contenido (ajusta las rutas y usuario según corresponda):

```ini
[Unit]
Description=Gunicorn daemon para Edu-Polo
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/edu-polo
ExecStart=/var/www/edu-polo/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/var/www/edu-polo/edupolo.sock core.wsgi:application

[Install]
WantedBy=multi-user.target
```
*Nota: Se recomienda usar un usuario no-root para `User`, pero para simplificar esta guía usamos root/www-data. Lo ideal es crear un usuario dedicado.*

**Iniciar y habilitar el servicio:**

```bash
sudo systemctl start edupolo
sudo systemctl enable edupolo
sudo systemctl status edupolo  # Verificar que esté activo (verde)
```

---

## 5. Configuración de Nginx (Proxy Inverso)

Nginx recibirá las peticiones web y las pasará a Gunicorn.

Crear archivo de configuración:
```bash
sudo nano /etc/nginx/sites-available/edupolo
```

Contenido:

```nginx
server {
    listen 80;
    server_name midominio.com www.midominio.com ip_del_servidor;

    # Ignorar favicon.ico
    location = /favicon.ico { access_log off; log_not_found off; }

    # Archivos estáticos (CSS, JS, Imágenes del sistema)
    location /static/ {
        root /var/www/edu-polo/staticfiles; # Asegúrate que esta ruta coincida con STATIC_ROOT en settings.py
    }

    # Archivos media (Subidos por usuarios)
    location /media/ {
        root /var/www/edu-polo/media; # Asegúrate que esta ruta coincida con MEDIA_ROOT en settings.py
    }

    # Proxy hacia Gunicorn
    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/edu-polo/edupolo.sock;
    }
}
```

**Activar el sitio y reiniciar Nginx:**

```bash
# Crear enlace simbólico
sudo ln -s /etc/nginx/sites-available/edupolo /etc/nginx/sites-enabled

# Verificar sintaxis
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
```

Si tienes un firewall activo (UFW), permite el tráfico:
```bash
sudo ufw allow 'Nginx Full'
```

---

## 6. HTTPS (Certificado SSL Seguro)

Usaremos Certbot (Let's Encrypt) para activar HTTPS gratis y automático.

```bash
# Instalar Certbot y plugin de Nginx
sudo apt install certbot python3-certbot-nginx -y

# Obtener certificado (sigue las instrucciones en pantalla)
sudo certbot --nginx -d midominio.com -d www.midominio.com
```

¡Listo! Tu aplicación debería estar corriendo de forma segura en `https://midominio.com`.

---

## 🛠 Comandos Útiles de Mantenimiento

**Ver logs de errores de la aplicación:**
```bash
sudo journalctl -u edupolo -f
```

**Ver logs de Nginx:**
```bash
sudo tail -f /var/log/nginx/error.log
```

**Reiniciar aplicación después de cambios en el código:**
```bash
# 1. Bajar cambios
git pull
# 2. Reiniciar servicio
sudo systemctl restart edupolo
```
