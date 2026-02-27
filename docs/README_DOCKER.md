# Dockerización del Sistema Educativo Polo

## 📦 Archivos creados

1. **Dockerfile**: Configuración para crear la imagen Docker de la aplicación
2. **docker-compose.yml**: Orquestación de servicios (aplicación + base de datos PostgreSQL)
3. **.dockerignore**: Archivos que se excluyen del contexto de Docker
4. **docker-entrypoint.sh**: Script de inicio que ejecuta migraciones y recopila archivos estáticos

## 🔧 Requisitos

- Docker instalado (versión 20.10 o superior)
- Docker Compose instalado (versión 2.0 o superior)

## 🚀 Uso Rápido

### Opción 1: Usar Docker Compose (Recomendado)

1. **Construir y ejecutar los contenedores:**
   ```bash
   docker-compose up --build
   ```

2. **En otra terminal, ejecutar migraciones:**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

3. **Crear superusuario (opcional):**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

4. **Acceder a la aplicación:**
   - 🌐 Aplicación: http://localhost:8000
   - 🗄️ Base de datos PostgreSQL: localhost:5432

### Opción 2: Usar solo Docker

1. **Construir la imagen:**
   ```bash
   docker build -t edu-polo .
   ```

2. **Ejecutar el contenedor:**
   ```bash
   docker run -p 8000:8000 -v $(pwd)/src:/app/src edu-polo
   ```

## 📋 Comandos Útiles

- **Ver logs en tiempo real:**
  ```bash
  docker-compose logs -f web
  ```

- **Detener contenedores:**
  ```bash
  docker-compose down
  ```

- **Detener y eliminar volúmenes (⚠️ elimina datos):**
  ```bash
  docker-compose down -v
  ```

- **Ejecutar comandos Django:**
  ```bash
  docker-compose exec web python manage.py <comando>
  ```

- **Acceder al shell del contenedor:**
  ```bash
  docker-compose exec web bash
  ```

- **Reconstruir sin caché:**
  ```bash
  docker-compose build --no-cache
  ```

## 🗄️ Configuración de Base de Datos

Por defecto, el proyecto usa **SQLite** (archivo `db.sqlite3`).

Para usar **PostgreSQL** en producción:

1. Descomenta las variables de entorno de PostgreSQL en `docker-compose.yml`
2. Actualiza `src/core/settings.py` para detectar y usar PostgreSQL cuando esté disponible

## 🔐 Variables de Entorno

Puedes crear un archivo `.env` en la raíz del proyecto:

```env
DEBUG=1
SECRET_KEY=tu-secret-key-seguro-aqui
DATABASE=sqlite
# Para PostgreSQL:
# DATABASE=postgres
# DB_HOST=db
# DB_PORT=5432
# DB_NAME=edu_polo
# DB_USER=postgres
# DB_PASSWORD=postgres
```

## 📝 Notas Importantes

- ✅ Los archivos estáticos se recopilan automáticamente al iniciar el contenedor
- ✅ Las migraciones se ejecutan automáticamente al iniciar el contenedor
- ✅ Los cambios en el código se reflejan automáticamente gracias al volumen montado
- ✅ La base de datos SQLite se guarda en `src/db.sqlite3` (persistente)
- ✅ Para producción, cambia el comando en `docker-compose.yml` a `gunicorn`

## 🐛 Solución de Problemas

- **Error de permisos:** Asegúrate de que `docker-entrypoint.sh` tenga permisos de ejecución
- **Puerto ocupado:** Cambia el puerto en `docker-compose.yml` (ej: "8001:8000")
- **Base de datos no conecta:** Verifica que el servicio `db` esté corriendo: `docker-compose ps`

