# Cómo crear un superusuario en Django

## Método 1: Comando interactivo (Recomendado)

Ejecuta este comando en la terminal desde el directorio `src`:

```bash
cd src
python manage.py createsuperuser
```

El comando te pedirá:
1. **Username (leave blank to use 'usuario')**: Ingresa el nombre de usuario (ej: `admin`)
2. **Email address**: Ingresa el email (ej: `admin@edupolo.com`)
3. **Password**: Ingresa la contraseña (no se mostrará mientras escribes)
4. **Password (again)**: Confirma la contraseña

## Método 2: Comando no interactivo (con variables de entorno)

Si quieres crear el superusuario sin interacción, usa:

**En PowerShell:**
```powershell
cd src
$env:DJANGO_SUPERUSER_USERNAME="tu_usuario"
$env:DJANGO_SUPERUSER_EMAIL="tu_email@ejemplo.com"
$env:DJANGO_SUPERUSER_PASSWORD="tu_contraseña"
python manage.py createsuperuser --noinput
```

**En CMD:**
```cmd
cd src
set DJANGO_SUPERUSER_USERNAME=tu_usuario
set DJANGO_SUPERUSER_EMAIL=tu_email@ejemplo.com
set DJANGO_SUPERUSER_PASSWORD=tu_contraseña
python manage.py createsuperuser --noinput
```

**En Linux/Mac:**
```bash
cd src
DJANGO_SUPERUSER_USERNAME="tu_usuario" \
DJANGO_SUPERUSER_EMAIL="tu_email@ejemplo.com" \
DJANGO_SUPERUSER_PASSWORD="tu_contraseña" \
python manage.py createsuperuser --noinput
```

## Método 3: Script Python

También puedes usar el script `crear_superusuario.py`:

```bash
cd src
python crear_superusuario.py
```

## Nota importante

- Si el usuario ya existe, Django mostrará un error. En ese caso, usa otro nombre de usuario.
- El superusuario creado tendrá acceso completo al panel de administración de Django en `/admin/`
- Asegúrate de usar una contraseña segura en producción.


