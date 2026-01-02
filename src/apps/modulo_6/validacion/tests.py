from django.test import TestCase

from apps.modulo_6.validacion.apps import ValidacionConfig


class ValidacionSmokeTests(TestCase):
    def test_app_config_nombre(self):
        self.assertEqual(ValidacionConfig.name, 'apps.modulo_6.validacion')
