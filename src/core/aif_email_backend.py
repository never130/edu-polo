import base64
import json
import os
import time
from email.utils import parseaddr
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import EmailMultiAlternatives


def _join_url(base: str, path: str) -> str:
    return base.rstrip("/") + "/" + path.lstrip("/")


def _clean_url(value: str) -> str:
    cleaned = (value or "").strip()
    cleaned = cleaned.strip("`\"'")
    return cleaned


def _clean_env_value(value: str) -> str:
    cleaned = (value or "").strip()
    cleaned = cleaned.strip("`\"'")
    return cleaned


_TOKEN_CACHE: dict[str, Any] = {"access": None, "expires_at": 0.0}


class AIFEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently: bool = False, **kwargs: Any):
        super().__init__(fail_silently=fail_silently)

        base_url = os.environ.get("AIF_EMAIL_BASE_URL") or "https://api-notificaciones.aif.gob.ar"
        self.base_url = _clean_url(base_url).rstrip("/")

        token_url = os.environ.get("AIF_EMAIL_TOKEN_URL") or _join_url(self.base_url, "/api/email/auth/client-token/")
        send_url = os.environ.get("AIF_EMAIL_SEND_URL") or _join_url(self.base_url, "/api/email/client/email/send/")
        self.token_url = _clean_url(token_url)
        self.send_url = _clean_url(send_url)

        self.client_id = _clean_env_value(os.environ.get("AIF_EMAIL_CLIENT_ID") or "")
        self.client_secret = _clean_env_value(os.environ.get("AIF_EMAIL_CLIENT_SECRET") or "")
        self.secret_id = _clean_env_value(os.environ.get("AIF_EMAIL_SECRET_ID") or "")

        self.profile = (os.environ.get("AIF_EMAIL_PROFILE") or "").strip()
        self.user_agent = (
            os.environ.get("AIF_EMAIL_USER_AGENT")
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ).strip()
        self.timeout = float(os.environ.get("AIF_EMAIL_TIMEOUT") or "15")
        self.token_ttl_seconds = int(os.environ.get("AIF_EMAIL_TOKEN_TTL_SECONDS") or str(8 * 60 * 60))

    def _http_json(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        body = json.dumps(payload).encode("utf-8")
        req_headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.user_agent:
            req_headers["User-Agent"] = self.user_agent
        if headers:
            req_headers.update(headers)

        req = Request(url=url, data=body, headers=req_headers, method="POST")

        try:
            with urlopen(req, timeout=self.timeout) as resp:
                status = int(getattr(resp, "status", 200))
                raw = resp.read().decode("utf-8", errors="replace").strip()
                data = json.loads(raw) if raw else {}
                return status, data
        except HTTPError as e:
            raw = ""
            try:
                raw = e.read().decode("utf-8", errors="replace").strip()
            except Exception:
                raw = ""
            try:
                data = json.loads(raw) if raw else {}
            except Exception:
                data = {"detail": raw or str(e)}
            return int(getattr(e, "code", 500) or 500), data
        except URLError as e:
            raise RuntimeError(f"Error de red al llamar API de AIF: {e}") from e

    def _get_access_token(self) -> str:
        now = time.time()
        access = _TOKEN_CACHE.get("access")
        expires_at = float(_TOKEN_CACHE.get("expires_at") or 0)

        if access and now < expires_at:
            return str(access)

        if not self.client_id or not self.client_secret:
            raise RuntimeError("Faltan credenciales AIF_EMAIL_CLIENT_ID / AIF_EMAIL_CLIENT_SECRET.")

        token_payload: dict[str, Any] = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        if self.secret_id:
            token_payload["secret_id"] = self.secret_id

        status, data = self._http_json(self.token_url, token_payload)

        if status < 200 or status >= 300:
            detail = data.get("detail") if isinstance(data, dict) else None
            if isinstance(detail, str) and "<html" in detail.lower():
                lowered = detail.lower()
                if "cloudflare" in lowered or "access denied" in lowered or "error 1010" in lowered:
                    raise RuntimeError(
                        "Error al obtener token AIF: el request fue bloqueado por Cloudflare/WAF. "
                        "Pedí a AIF habilitar/whitelistear el acceso a "
                        f"{self.token_url} y {self.send_url} para tu servidor/IP."
                    )
                if "fuera de servicio" in lowered or "mantenimiento" in lowered:
                    raise RuntimeError("Error al obtener token AIF: servicio temporalmente fuera de servicio.")
            raise RuntimeError(f"Error al obtener token AIF (HTTP {status}): {data}")

        token = data.get("access")
        if not token:
            raise RuntimeError(f"Respuesta de token AIF sin 'access': {data}")

        _TOKEN_CACHE["access"] = str(token)
        _TOKEN_CACHE["expires_at"] = now + max(60, self.token_ttl_seconds - 30)

        return str(token)

    def _addr_to_aif(self, addr: str) -> dict[str, str]:
        name, email = parseaddr(addr or "")
        email = (email or "").strip()
        name = (name or "").strip()
        if not email:
            raise RuntimeError("Destinatario inválido (email vacío).")
        return {"email": email, "name": name}

    def _encode_attachment(self, attachment: Any) -> dict[str, Any]:
        if not isinstance(attachment, (list, tuple)) or len(attachment) < 2:
            raise RuntimeError("Formato de adjunto no soportado por este backend (espera tupla Django).")

        filename = attachment[0]
        content = attachment[1]
        mimetype = attachment[2] if len(attachment) >= 3 else ""

        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        else:
            content_bytes = content

        if not isinstance(content_bytes, (bytes, bytearray)):
            raise RuntimeError("Contenido de adjunto inválido (debe ser bytes o str).")

        payload: dict[str, Any] = {
            "filename": filename,
            "base64": base64.b64encode(content_bytes).decode("ascii"),
        }
        if mimetype:
            payload["content_type"] = mimetype
        return payload

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        try:
            token = self._get_access_token()
        except Exception:
            if self.fail_silently:
                return 0
            raise

        sent = 0
        for message in email_messages:
            try:
                to_list = [self._addr_to_aif(a) for a in (getattr(message, "to", None) or [])]
                cc_list = [self._addr_to_aif(a) for a in (getattr(message, "cc", None) or [])]
                bcc_list = [self._addr_to_aif(a) for a in (getattr(message, "bcc", None) or [])]

                subject = (getattr(message, "subject", None) or "").strip()
                text_body = getattr(message, "body", None) or ""

                html_body = None
                if isinstance(message, EmailMultiAlternatives):
                    for alt_body, mimetype in (message.alternatives or []):
                        if (mimetype or "").lower() == "text/html":
                            html_body = alt_body
                            break

                payload: dict[str, Any] = {
                    "subject": subject,
                    "to": to_list,
                }
                if self.profile:
                    payload["profile"] = self.profile

                if html_body is not None:
                    payload["body"] = html_body
                    payload["is_html"] = True
                else:
                    payload["body"] = text_body
                    payload["is_html"] = False

                if cc_list:
                    payload["cc"] = cc_list
                if bcc_list:
                    payload["bcc"] = bcc_list

                attachments = getattr(message, "attachments", None) or []
                if attachments:
                    payload["attachments"] = [self._encode_attachment(a) for a in attachments]

                status, data = self._http_json(
                    self.send_url,
                    payload,
                    headers={"Authorization": f"Bearer {token}"},
                )

                if status < 200 or status >= 300:
                    raise RuntimeError(f"Error AIF al enviar email (HTTP {status}): {data}")

                sent += 1
            except Exception:
                if not self.fail_silently:
                    raise

        return sent
