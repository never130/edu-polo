#!/bin/bash
set -e

# Función para logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Esperar a que la base de datos esté lista (si se usa PostgreSQL)
if [ "$DATABASE" = "postgres" ] || [ -n "$DATABASE_URL" ]; then
    log "Esperando a PostgreSQL..."
    # Extraer host y puerto de DATABASE_URL si está disponible
    if [ -n "$DATABASE_URL" ]; then
        DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
        DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    fi
    if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
        while ! nc -z ${DB_HOST} ${DB_PORT}; do
            sleep 0.1
        done
        log "PostgreSQL está listo"
    fi
fi

# Ejecutar migraciones
log "Ejecutando migraciones..."
python manage.py migrate --noinput || {
    log "ADVERTENCIA: Fallo al ejecutar migraciones, intentando continuar..."
    # No salir con error aquí, puede ser que las tablas ya existan
}

# Crear superusuario si las variables de entorno están definidas
log "Verificando creación de superusuario..."
python create_superuser.py || {
    log "ADVERTENCIA: Fallo al intentar crear superusuario, continuando..."
}

# Recopilar archivos estáticos
log "Recopilando archivos estáticos..."
python manage.py collectstatic --noinput || {
    log "ADVERTENCIA: Fallo al recopilar archivos estáticos, continuando..."
}

# Verificar configuración
log "Verificando configuración de Django..."
python manage.py check --deploy || {
    log "ADVERTENCIA: Hay problemas con la configuración de despliegue"
}

log "Iniciando aplicación..."
# Ejecutar el comando proporcionado
exec "$@"
