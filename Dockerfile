# Usar imagen base de Python
FROM python:3.11-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
# Suprimir warning de pip como root (común en contenedores Docker)
ENV PIP_ROOT_USER_ACTION=ignore

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias de Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY src/ /app/src/

# Crear directorio para archivos estáticos
RUN mkdir -p /app/src/staticfiles

# Establecer el directorio de trabajo en src
WORKDIR /app/src

# Exponer el puerto 8000
EXPOSE 8000

# Script de inicio
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Comando por defecto
# En producción, usar gunicorn si PORT está definido, sino runserver
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD sh -c "if [ -n \"\$PORT\" ]; then gunicorn core.wsgi:application --bind 0.0.0.0:\$PORT --workers 3 --timeout 120; else python manage.py runserver 0.0.0.0:8000; fi"
