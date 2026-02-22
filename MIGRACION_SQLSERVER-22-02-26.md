# Migración a SQL Server (Producción) - edu-polo

## Fecha
- 2026-02-22

## Contexto y entorno
- Servidor: ush-inf-edu-polo-QA
- IP: Solicitado por el equipo de infraestructura
- Stack Portainer: edu-polo
- Contenedores:
  - edu-polo-web-1 (Django)
  - edu-polo-db-1 (Postgres 15 - respaldo)
- Imagen Docker: edu-polo:latest

## Paso 0 — Backup obligatorio (Postgres actual)
```bash
docker exec -t edu-polo-db-1 pg_dump -U postgres -d edu_polo > /home/eloza/edu_polo_backup.sql
```

## Paso 1 — Preparar el contenedor para MSSQL
### 1.1 Dockerfile
Se agregó soporte ODBC para SQL Server:
- unixODBC
- msodbcsql18
- ca-certificates / curl / gnupg

### 1.2 requirements.txt
Se agregaron dependencias:
- mssql-django
- pyodbc

## Paso 2 — Subir cambios al repositorio
```bash
git add Dockerfile requirements.txt
git commit -m "Add SQL Server dependencies"
git push origin version-final
```

## Paso 3 — Actualizar servidor y construir imagen
```bash
cd /home/eloza/edu-polo
git fetch gobierno
git reset --hard gobierno/version-final
docker build -t edu-polo:latest .
```

## Paso 4 — Update Stack en Portainer
- Stack: edu-polo
- Re-pull image: desactivado

## Paso 5 — Cambiar variables a SQL Server en Portainer
En el servicio web se eliminaron variables de Postgres:
```
DATABASE=postgres
DB_HOST=db
DB_PORT=5432
DB_NAME=edu_polo
DB_USER=postgres
DB_PASSWORD=postgres
```

Se agregaron variables MSSQL:
```
DB_ENGINE=mssql
DB_NAME=db_edu_polo_prd
DB_USER=edu_polo_user
DB_PASSWORD=********
DB_HOST=ush-sis-dbsistemas
DB_PORT=1433
```

## Paso 6 — Migraciones (estructura en SQL Server)
```bash
docker exec -it edu-polo-web-1 python manage.py migrate
```

## Paso 7 — Migración de datos (Postgres → SQL Server)
### 7.1 Dump desde Postgres
```bash
docker exec \
  -e DATABASE=postgres \
  -e DB_HOST=db \
  -e DB_PORT=5432 \
  -e DB_NAME=edu_polo \
  -e DB_USER=postgres \
  -e DB_PASSWORD=xxxxxx \
  edu-polo-web-1 \
  python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.permission --indent 2 \
  > /home/eloza/edu_polo_data.json
```

### 7.2 Cargar en SQL Server
```bash
docker cp /home/eloza/edu_polo_data.json edu-polo-web-1:/tmp/edu_polo_data.json
docker exec -it edu-polo-web-1 python manage.py loaddata /tmp/edu_polo_data.json
```

## Paso 8 — Validación
- Se verificaron datos en la web
- La app quedó conectada a SQL Server

## Post-migración (recomendado)
- Mantener Postgres activo algunos días como respaldo
- Solicitar backup diario de db_edu_polo_prd
- Retirar Postgres del stack solo cuando esté confirmado

## Backups y archivos
- /home/eloza/edu_polo_backup.sql
- /home/eloza/edu_polo_data.json
