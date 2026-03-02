# Migración de SQLite a SQL Server en Django con Docker

**Proyecto:** edu-polo  
**Fecha:** 2026-03-01  
**Resultado:** ✅ 28,655 registros migrados exitosamente

---

## Contexto del problema

Al migrar una base de datos Django de producción de **SQLite a SQL Server**, el comando `loaddata` fallaba repetidamente por tres causas:

1. **Truncamiento de datos:** campos `CharField` con `max_length=30` contenían valores más largos (SQLite lo permite, SQL Server no).
2. **Violación de UNIQUE KEY:** registros duplicados en `asistencia.RegistroAsistencia` que SQLite toleraba pero SQL Server rechaza.
3. **Signals de Django** que se disparaban durante la carga e intentaban acceder a registros que aún no habían sido insertados.

---

## Prerequisitos

- Acceso SSH al servidor de producción (PuTTY + WireGuard)
- Contenedor Docker corriendo: `edu-polo-web-1`
- Stack gestionado con Portainer
- Editor `nano` disponible en el servidor

---

## FASE 1 — Preparación y backup (apuntando a SQLite)

### Paso 1.1 — Ajustar modelos para evitar truncamiento

En `usuario/models.py`, aumentar `max_length` del campo `telefono`:

```python
telefono = models.CharField(max_length=50, blank=True, null=True, verbose_name="Teléfono")
```

En `roles/models.py`, aumentar `max_length` del campo `telefono_contacto`:

```python
telefono_contacto = models.CharField(max_length=50)
```

### Paso 1.2 — Backup físico del archivo SQLite

```bash
docker cp edu-polo-web-1:/app/src/db.sqlite3 ./db.sqlite3.backup
```

> ⚠️ **Este archivo es tu red de seguridad absoluta.** Si algo sale mal, restaurá con:
> ```bash
> docker cp ./db.sqlite3.backup edu-polo-web-1:/app/src/db.sqlite3
> ```

### Paso 1.3 — Generar dump de datos desde SQLite

```bash
docker exec -e DB_ENGINE=sqlite edu-polo-web-1 python manage.py dumpdata \
  --natural-foreign --natural-primary \
  -e contenttypes -e auth.permission \
  --indent 2 --output /tmp/edu_polo_dirty.json
```

Verificar que el archivo se generó correctamente:

```bash
docker exec edu-polo-web-1 ls -lh /tmp/edu_polo_dirty.json
```

> El archivo debe pesar varios MB (en este caso: 8.5MB). Si pesa 0KB, el dumpdata falló.

---

## FASE 2 — Limpieza de datos

### Paso 2.1 — Crear el script de limpieza

Crear el archivo en el servidor con `nano`:

```bash
nano /home/tu_usuario/tu_proyecto/clean_dump.py
```

Pegar el siguiente contenido y guardar con `Ctrl+O`, `Enter`, `Ctrl+X`:

```python
import os
import sys
import json
from collections import defaultdict

sys.path.append('/app/src')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()
from django.apps import apps

INPUT_FILE = '/tmp/edu_polo_dirty.json'
OUTPUT_FILE = '/tmp/edu_polo_clean.json'

with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

by_model = defaultdict(list)
for obj in data:
    by_model[obj['model']].append(obj)

model_map = {}
unique_fields_map = {}
relation_map = defaultdict(list)

for model in apps.get_models():
    label = f"{model._meta.app_label}.{model._meta.model_name}"
    model_map[label] = model
    unique_fields = []
    for field in model._meta.fields:
        if field.primary_key:
            continue
        if field.unique or field.one_to_one:
            unique_fields.append(field.name)
    unique_fields_map[label] = unique_fields
    for field in model._meta.fields:
        if field.is_relation and (field.many_to_one or field.one_to_one):
            target = field.related_model
            target_label = f"{target._meta.app_label}.{target._meta.model_name}"
            relation_map[target_label].append((label, field.name, False))
    for field in model._meta.many_to_many:
        target = field.related_model
        target_label = f"{target._meta.app_label}.{target._meta.model_name}"
        relation_map[target_label].append((label, field.name, True))

def truncate_phone_fields(obj):
    fields = obj['fields']
    for key in ('telefono', 'telefono_contacto'):
        val = fields.get(key)
        if isinstance(val, str) and len(val) > 50:
            fields[key] = val[:50]

removed_counts = defaultdict(int)
remap = {}

# Procesar personas con DNI duplicado
persona_label = 'usuario.persona'
if persona_label in by_model:
    seen_dni = {}
    kept = []
    for r in sorted(by_model[persona_label], key=lambda x: x.get('pk', 0)):
        truncate_phone_fields(r)
        dni = (r['fields'].get('dni') or '').strip()
        r['fields']['dni'] = dni
        if dni and dni in seen_dni:
            remap[r.get('pk')] = seen_dni[dni]
            removed_counts[persona_label] += 1
        else:
            if dni:
                seen_dni[dni] = r.get('pk')
            kept.append(r)
    by_model[persona_label] = kept

# Reasignar FKs de registros eliminados
for model_label, records in by_model.items():
    if model_label == persona_label:
        continue
    for r in records:
        truncate_phone_fields(r)
        for k, v in r['fields'].items():
            if isinstance(v, int) and v in remap:
                r['fields'][k] = remap[v]

# Procesar duplicados UNIQUE en registroasistencia
ra_label = 'asistencia.registroasistencia'
if ra_label in by_model:
    seen_inscripcion = {}
    kept = []
    for r in sorted(by_model[ra_label], key=lambda x: x.get('pk', 0)):
        inscripcion = r['fields'].get('inscripcion')
        if inscripcion and inscripcion in seen_inscripcion:
            removed_counts[ra_label] += 1
        else:
            if inscripcion:
                seen_inscripcion[inscripcion] = r.get('pk')
            kept.append(r)
    by_model[ra_label] = kept

final_data = [obj for records in by_model.values() for obj in records]

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(final_data, f, ensure_ascii=False, indent=2)

print("RESUMEN_ELIMINADOS")
for label, count in removed_counts.items():
    print(f"  {label}: {count}")
print("LIMPIEZA_COMPLETADA")
```

### Paso 2.2 — Copiar el script al contenedor y ejecutarlo

```bash
docker cp /home/tu_usuario/tu_proyecto/clean_dump.py edu-polo-web-1:/tmp/clean_dump.py
docker exec edu-polo-web-1 python /tmp/clean_dump.py
```

El output debe terminar con `LIMPIEZA_COMPLETADA`.

### Paso 2.3 — Eliminar logs de admin con user_id NULL

```bash
docker exec edu-polo-web-1 python -c "
import json
with open('/tmp/edu_polo_clean.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
antes = len(data)
data = [obj for obj in data if obj['model'] != 'admin.logentry']
despues = len(data)
with open('/tmp/edu_polo_final.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f'Eliminados {antes - despues} registros de admin.logentry')
print('Archivo guardado en /tmp/edu_polo_final.json')
"
```

### Paso 2.4 — Validar que no quedan duplicados reales

```bash
docker exec edu-polo-web-1 python -c "
import json
from collections import defaultdict

with open('/tmp/edu_polo_final.json', 'r') as f:
    data = json.load(f)

unique_constraints = {
    'usuario.persona': ['dni'],
    'asistencia.registroasistencia': ['inscripcion'],
    'auth.user': ['username'],
    'roles.usuariorol': ['usuario'],
}

by_model = defaultdict(list)
for obj in data:
    by_model[obj['model']].append(obj)

found = False
for model, fields in unique_constraints.items():
    records = by_model.get(model, [])
    for field in fields:
        values = [r['fields'].get(field) for r in records if r['fields'].get(field) is not None]
        dupes = [v for v in values if values.count(v) > 1]
        if dupes:
            print(f'DUPLICADO REAL -> modelo: {model}, campo: {field}, valores: {set(dupes)}')
            found = True

if not found:
    print('Todo limpio. Listo para Fase 3.')
"
```

> ✅ El output debe ser únicamente: `Todo limpio. Listo para Fase 3.`  
> Si aparece algún `DUPLICADO REAL`, corregir el `clean_dump.py` antes de continuar.

### Paso 2.5 — Guardar el archivo final en el servidor (antes de reiniciar)

> ⚠️ El directorio `/tmp` del contenedor se borra al reiniciar. Guardarlo en una ruta persistente:

```bash
docker cp edu-polo-web-1:/tmp/edu_polo_final.json /home/tu_usuario/tu_proyecto/edu_polo_final.json
```

---

## FASE 3 — Migración final a SQL Server

### Paso 3.1 — Cambiar variables en Portainer

En el stack de Portainer, actualizar las variables de entorno para apuntar a SQL Server en lugar de SQLite y hacer **redeploy** del stack.

### Paso 3.2 — Aplicar migraciones en SQL Server

```bash
docker exec -it edu-polo-web-1 python manage.py makemigrations
docker exec -it edu-polo-web-1 python manage.py migrate
```

Verificar que las migraciones de `max_length=50` se aplicaron:
- `roles.0006_alter_tutor_telefono_contacto`
- `usuario.0004_alter_persona_telefono`

### Paso 3.3 — Restaurar el archivo en el contenedor

```bash
docker cp /home/tu_usuario/tu_proyecto/edu_polo_final.json edu-polo-web-1:/tmp/edu_polo_final.json
```

### Paso 3.4 — Limpiar SQL Server y cargar datos

```bash
docker exec -it edu-polo-web-1 python manage.py flush --noinput
```

Cargar los datos **desconectando los signals** para evitar que se disparen durante la carga:

```bash
docker exec -it edu-polo-web-1 python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db.models.signals import post_save, post_delete
from django.core.management import call_command
from apps.modulo_4.asistencia.models import Asistencia
from apps.modulo_4.asistencia.signals import actualizar_registro_despues_guardar, actualizar_registro_despues_eliminar

post_save.disconnect(actualizar_registro_despues_guardar, sender=Asistencia)
post_delete.disconnect(actualizar_registro_despues_eliminar, sender=Asistencia)

print('Signals desconectados. Iniciando carga...')
call_command('loaddata', '/tmp/edu_polo_final.json', verbosity=1)
print('CARGA COMPLETADA.')
"
```

> ⚠️ Este proceso puede tardar entre 2 y 10 minutos. **No interrumpir con Ctrl+C.**

---

## FASE 4 — Verificación final

### Paso 4.1 — Verificar integridad del sistema

```bash
docker exec -it edu-polo-web-1 python manage.py check
```

Output esperado: `System check identified no issues (0 silenced).`

### Paso 4.2 — Crear superusuario si es necesario

```bash
docker exec -it edu-polo-web-1 python manage.py createsuperuser
```

### Paso 4.3 — Guardar backup definitivo post-migración

```bash
cp /home/tu_usuario/tu_proyecto/edu_polo_final.json \
   /home/tu_usuario/tu_proyecto/edu_polo_MIGRADO_$(date +%Y%m%d).json
```

---

## Errores conocidos y soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| `Violation of UNIQUE KEY constraint` | Datos duplicados en SQLite | Script `clean_dump.py` elimina duplicados |
| `String truncated` | `max_length` insuficiente en modelos | Aumentar a `max_length=50` en modelos afectados |
| `Cannot insert NULL into column 'user_id'` | Logs de admin con usuario eliminado | Eliminar registros `admin.logentry` del JSON |
| `Inscripcion matching query does not exist` | Signal disparado antes de que FK exista | Desconectar signals antes del `loaddata` |
| `PermissionError` al escribir en `/tmp` | Archivo creado por root | Escribir en archivo nuevo (`edu_polo_final.json`) |
| `KeyboardInterrupt` + `Communication link failure` | Se interrumpió la carga con Ctrl+C | Ejecutar `flush` y repetir la carga sin interrumpir |

---

## Archivos generados durante el proceso

| Archivo | Ubicación | Descripción |
|---------|-----------|-------------|
| `db.sqlite3.backup` | Servidor local | Backup físico de SQLite (red de seguridad) |
| `edu_polo_dirty.json` | `/tmp/` del contenedor | Dump crudo sin limpiar |
| `clean_dump.py` | Servidor + contenedor | Script de limpieza de datos |
| `edu_polo_clean.json` | `/tmp/` del contenedor | Datos limpios sin `admin.logentry` |
| `edu_polo_final.json` | Servidor + contenedor | Archivo final listo para cargar |
| `edu_polo_MIGRADO_YYYYMMDD.json` | Servidor local | Backup definitivo post-migración |

---

## Notas importantes

- **SQLite es permisivo, SQL Server es estricto.** Datos que SQLite acepta sin problemas (textos largos, duplicados en campos únicos) serán rechazados por SQL Server.
- **Los signals de Django** que recalculan datos derivados deben desconectarse durante el `loaddata` para evitar errores de FK no encontradas. Reconectarlos no es necesario ya que el contenedor reiniciado los carga de cero.
- **El directorio `/tmp` del contenedor es volátil.** Siempre guardar los archivos importantes en el servidor antes de cualquier reinicio.
- **No interrumpir el `loaddata`** . Si se interrumpe, ejecutar `flush --noinput` antes de reintentar.
