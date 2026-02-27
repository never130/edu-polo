# Implementación de envío de emails por AIF (reemplazo de SMTP)

Este documento describe, de principio a fin, cómo se integró el envío de correos vía API de Notificaciones AIF en este proyecto Django, reemplazando el uso de SMTP.

## 1) Objetivo

- Reemplazar el envío por SMTP por el envío vía AIF para todas las llamadas estándar de Django (`send_mail`, `EmailMessage`, `EmailMultiAlternatives`).
- Mantener compatibilidad con el flujo de **recupero de contraseña** (password reset).
- Permitir configuración por variables de entorno en desarrollo y producción (Portainer/Docker).

## 2) Archivos involucrados

- Backend AIF: [src/core/aif_email_backend.py]
- Settings: [src/core/settings.py]
- Password reset: [src/apps/modulo_6/seguridad/views_password_reset.py]
- URLs del recovery: [src/core/urls.py]

## 3) Variables de entorno

### 3.1 Variables mínimas para AIF

- `AIF_EMAIL_BASE_URL` (ej: `https://api-notificaciones.aif.gob.ar`)
- `AIF_EMAIL_CLIENT_ID` (provisto por AIF)
- `AIF_EMAIL_CLIENT_SECRET` (provisto por AIF)

### 3.2 Variables recomendadas en producción

- `PUBLIC_BASE_URL` (ej: `https://polos.aif.gob.ar`)
  - Se usa para generar enlaces correctos en emails (ej. recupero de contraseña) sin depender del `Host` detectado en el request.

## 4) Implementación técnica

### 4.1 Backend de Email: `AIFEmailBackend`

Archivo: `src/core/aif_email_backend.py`

Funciones clave:

1. Construcción de URLs:
   - Parte de `AIF_EMAIL_BASE_URL`.
   - Concatena rutas:
     - Token: `/api/email/auth/client-token/`
     - Send: `/api/email/client/email/send/`
   - Limpia comillas/backticks por si se copiaron valores con caracteres extra.

2. Obtención de token (client credentials):
   - POST JSON con `client_id` y `client_secret` al endpoint de token.
   - Cache del token (evita pedir token por cada email).

3. Envío:
   - POST JSON al endpoint de envío.
   - Header: `Authorization: Bearer <token>`.
   - `to` / `cc` / `bcc` se envían como lista de objetos `{email, name}`.

4. Contenido:
   - Si el mensaje contiene alternativa HTML (`EmailMultiAlternatives` con `text/html`), envía `is_html=True`.
   - Si no, envía texto plano.

5. Adjuntos:
   - Convierte adjuntos a base64 en el payload, si se incluyen.

6. Robustez:
   - User-Agent configurado para minimizar bloqueos WAF.
   - Mensajes de error más claros cuando el token es bloqueado o el servicio devuelve HTML de WAF.

### 4.2 Activación en settings (`EMAIL_BACKEND`)

Archivo: `src/core/settings.py`

Regla aplicada:

- Si existen `AIF_EMAIL_CLIENT_ID` y `AIF_EMAIL_CLIENT_SECRET` ⇒ se fuerza:
  - `EMAIL_BACKEND = 'core.aif_email_backend.AIFEmailBackend'`
- Si no ⇒ se respeta `EMAIL_BACKEND` si viene por entorno; caso contrario se usa backend de consola.

Nota:
- `EMAIL_HOST`, `EMAIL_PORT`, etc. pueden quedar en settings o `.env`, pero no se usan si el `EMAIL_BACKEND` activo es AIF.

### 4.3 Enlaces correctos en emails (`PUBLIC_BASE_URL`)

Archivo: `src/core/settings.py`

- Se agrega `PUBLIC_BASE_URL` (sanitizado para evitar backticks/comillas).
- En producción, si no se setea, se intenta inferir un host público a partir de `ALLOWED_HOSTS`.
- Recomendación: setearlo explícitamente en Portainer.

### 4.4 Recupero de contraseña (password reset)

Archivo: `src/apps/modulo_6/seguridad/views_password_reset.py`

Flujo:

1. Se valida DNI y email.
2. Se genera token con `TimestampSigner`.
3. Se arma el enlace:
   - `confirm_path = reverse('password_reset_confirm')`
   - Si `PUBLIC_BASE_URL` está definido: `reset_link = f"{PUBLIC_BASE_URL}{confirm_path}?token=..."`
   - Si no: fallback con `request.build_absolute_uri(...)`
4. Se envía email por `send_mail()`:
   - Como el `EMAIL_BACKEND` es AIF, termina saliendo por AIF.

Decisión importante:
- El mensaje se manda en **texto plano** para que el enlace sea visible incluso si se filtra HTML.

Protección adicional:
- En producción, si `EMAIL_BACKEND` es `console` o `locmem`, el endpoint muestra error en vez de “éxito falso”.

## 5) Verificación local (Windows)

Desde la raíz del repo:

```powershell
cd C:\Users\x\x\Documentos\VSCode\x\x\edu-polo
py .\src\manage.py shell -c "from django.conf import settings; print('EMAIL_BACKEND=', settings.EMAIL_BACKEND)"
```

Probar token:

```powershell
py .\src\manage.py shell -c "from core.aif_email_backend import AIFEmailBackend; print(AIFEmailBackend()._get_access_token()[:20])"
```

Probar envío:

```powershell
py .\src\manage.py shell -c "from django.core.mail import send_mail; from django.conf import settings; print(send_mail('Prueba AIF', 'Hola', settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL], fail_silently=False))"
```

## 6) Verificación en producción (Portainer / Docker)

### 6.1 Verificar variables y backend dentro del contenedor

Portainer → Containers → `<tu-contenedor-web>` → Console → `/bin/bash`:

```bash
cd /app/src
python manage.py shell -c "import os; from django.conf import settings; print('EMAIL_BACKEND=', settings.EMAIL_BACKEND); print('AIF_ID_SET=', bool(os.environ.get('AIF_EMAIL_CLIENT_ID'))); print('AIF_SECRET_SET=', bool(os.environ.get('AIF_EMAIL_CLIENT_SECRET'))); print('PUBLIC_BASE_URL=', getattr(settings,'PUBLIC_BASE_URL',''))"
```

Resultado esperado:
- `EMAIL_BACKEND= core.aif_email_backend.AIFEmailBackend`
- `AIF_ID_SET= True`
- `AIF_SECRET_SET= True`
- `PUBLIC_BASE_URL= https://polos.aif.gob.ar`

### 6.2 Definir variables en Portainer

#### Si se usa Stack (docker-compose)

Portainer → Stacks → `<tu-stack>` → Editor → servicio `web`:

```yaml
environment:
  - AIF_EMAIL_BASE_URL=https://api-notificaciones.aif.gob.ar
  - AIF_EMAIL_CLIENT_ID=...
  - AIF_EMAIL_CLIENT_SECRET=...
  - PUBLIC_BASE_URL=https://polos.aif.gob.ar
```

Luego: **Update the stack / Deploy** (recrea contenedores con esas variables).

#### Si usás Container suelto

Portainer → Containers → `<tu-contenedor>` → Duplicate/Edit → Environment variables:

- `AIF_EMAIL_BASE_URL`
- `AIF_EMAIL_CLIENT_ID`
- `AIF_EMAIL_CLIENT_SECRET`
- `PUBLIC_BASE_URL`

Luego: Deploy/Recreate.

## 7) Problemas comunes y diagnóstico

### 7.1 “Dice enviado pero no llega”

En producción, si el backend es `console`, Django puede devolver “éxito” sin enviar nada real.

Diagnóstico (dentro del contenedor):
- Si `EMAIL_BACKEND= django.core.mail.backends.console.EmailBackend` y `AIF_*_SET=False` ⇒ faltan variables AIF en el contenedor.

Solución:
- Definir variables en Portainer y redeploy/recreate el servicio.

### 7.2 `PUBLIC_BASE_URL` con backticks/comillas

Si se pega el valor con comillas/backticks, el enlace puede salir mal.

Solución:
- Quitar caracteres extra en Portainer (recomendado).
- El código además sanitiza `PUBLIC_BASE_URL`.

## 8) Seguridad

- No versionar ni compartir `AIF_EMAIL_CLIENT_SECRET`.
- Si un secreto se expuso, rotarlo con AIF y actualizar Portainer.

Agradecimientos al equipo de infraestructura por facilitarnos este sistema.