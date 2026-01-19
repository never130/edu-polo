import time

from django.contrib.messages import get_messages
from django.core import mail
from django.core.signing import TimestampSigner
from django.test import TestCase, override_settings
from django.urls import reverse
from urllib.parse import unquote

from apps.modulo_1.usuario.models import Persona, Usuario
from apps.modulo_6.seguridad.backends import DNIAuthenticationBackend


class SeguridadAuthTests(TestCase):
    def setUp(self):
        self.dni = '80000000'
        self.password = 'pw'
        self.persona = Persona.objects.create(
            dni=self.dni,
            nombre='Ana',
            apellido='Test',
            correo='ana@test.com',
        )
        self.usuario = Usuario.objects.create(persona=self.persona, contrasena=self.password)

    def test_backend_autentica_y_crea_django_user(self):
        backend = DNIAuthenticationBackend()
        django_user = backend.authenticate(request=None, username=self.dni, password=self.password)
        self.assertIsNotNone(django_user)
        self.assertEqual(django_user.username, self.dni)
        self.assertEqual(django_user.first_name, self.persona.nombre)
        self.assertEqual(django_user.last_name, self.persona.apellido)

    def test_backend_falla_con_contrasena_incorrecta(self):
        backend = DNIAuthenticationBackend()
        django_user = backend.authenticate(request=None, username=self.dni, password='wrong')
        self.assertIsNone(django_user)

    def test_login_get_redirige_landing(self):
        response = self.client.get(reverse('login'), secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('landing'))

    def test_login_post_sin_campos_redirige_landing_y_mensaje(self):
        response = self.client.post(reverse('login'), data={'username': '', 'password': ''}, follow=True, secure=True)
        self.assertEqual(response.status_code, 200)
        mensajes = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn('Por favor, ingresa tu DNI y contraseña.', mensajes)

    def test_login_post_invalido_redirige_landing_y_mensaje(self):
        response = self.client.post(
            reverse('login'),
            data={'username': self.dni, 'password': 'bad'},
            follow=True,
            secure=True,
        )
        self.assertEqual(response.status_code, 200)
        mensajes = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn('❌ DNI o contraseña incorrectos. Por favor, verifica tus datos.', mensajes)

    def test_login_post_valido_redirige_a_next(self):
        url = f"{reverse('login')}?next={reverse('dashboard')}"
        response = self.client.post(url, data={'username': self.dni, 'password': self.password}, secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))


class PasswordResetTests(TestCase):
    def setUp(self):
        self.dni = '81000000'
        self.password = 'pw'
        self.persona = Persona.objects.create(
            dni=self.dni,
            nombre='Ana',
            apellido='Test',
            correo='ana@test.com',
        )
        self.usuario = Usuario.objects.create(persona=self.persona, contrasena=self.password)

    def test_password_reset_request_valida_campos(self):
        response = self.client.post(reverse('password_reset_request'), data={'dni': '', 'email': ''}, secure=True)
        self.assertEqual(response.status_code, 200)
        mensajes = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn('❌ Por favor, ingresa tu DNI.', mensajes)

    def test_password_reset_request_get_renderiza_formulario(self):
        response = self.client.get(reverse('password_reset_request'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="dni"')
        self.assertContains(response, 'name="email"')

    def test_password_reset_request_rechaza_email_distinto(self):
        response = self.client.post(
            reverse('password_reset_request'),
            data={'dni': self.dni, 'email': 'otro@test.com'},
            secure=True,
        )
        self.assertEqual(response.status_code, 200)
        mensajes = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn('❌ El correo electrónico no coincide con el registrado para este DNI.', mensajes)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_password_reset_request_envia_email_y_setea_sesion(self):
        response = self.client.post(
            reverse('password_reset_request'),
            data={'dni': self.dni, 'email': self.persona.correo},
            secure=True,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertIn(f"https://testserver{reverse('password_reset_confirm')}?token=", email.body)
        token = email.body.split("token=", 1)[1].split()[0].strip()
        token = token.replace("&amp;", "&")
        token = unquote(token)
        signer = TimestampSigner(salt="password-reset")
        self.assertEqual(signer.unsign(token, max_age=60 * 60 * 24), self.dni)

    def test_password_reset_confirm_sin_params_redirige(self):
        response = self.client.get(reverse('password_reset_confirm'), secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('password_reset_request'))

    def test_password_reset_confirm_token_invalido_redirige(self):
        response = self.client.get(
            f"{reverse('password_reset_confirm')}?token=bad",
            secure=True,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('password_reset_request'))

    @override_settings(PASSWORD_RESET_TOKEN_MAX_AGE=1)
    def test_password_reset_confirm_expirado_redirige(self):
        signer = TimestampSigner(salt="password-reset")
        token = signer.sign(self.dni)
        time.sleep(2)

        response = self.client.get(
            f"{reverse('password_reset_confirm')}?token={token}",
            follow=True,
            secure=True,
        )
        self.assertEqual(response.status_code, 200)
        mensajes = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn('❌ El enlace ha expirado. Por favor, solicita uno nuevo.', mensajes)

    def test_password_reset_confirm_post_valida_y_actualiza(self):
        signer = TimestampSigner(salt="password-reset")
        token = signer.sign(self.dni)

        response = self.client.post(
            f"{reverse('password_reset_confirm')}?token={token}",
            data={'password': 'nueva123', 'password_confirm': 'nueva123'},
            secure=True,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))

        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.contrasena, 'nueva123')

    def test_password_reset_confirm_post_rechaza_passwords_distintas(self):
        signer = TimestampSigner(salt="password-reset")
        token = signer.sign(self.dni)

        response = self.client.post(
            f"{reverse('password_reset_confirm')}?token={token}",
            data={'password': 'abc123', 'password_confirm': 'zzz999'},
            follow=True,
            secure=True,
        )
        self.assertEqual(response.status_code, 200)
        mensajes = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn('❌ Las contraseñas no coinciden.', mensajes)

    def test_password_reset_confirm_post_rechaza_password_corta(self):
        signer = TimestampSigner(salt="password-reset")
        token = signer.sign(self.dni)

        response = self.client.post(
            f"{reverse('password_reset_confirm')}?token={token}",
            data={'password': '123', 'password_confirm': '123'},
            follow=True,
            secure=True,
        )
        self.assertEqual(response.status_code, 200)
        mensajes = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn('❌ La contraseña debe tener al menos 6 caracteres.', mensajes)
