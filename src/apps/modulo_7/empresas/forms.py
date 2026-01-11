from django import forms
import re

from apps.modulo_1.usuario.models import Persona, Usuario

from .models import Empresa


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nombre', 'logo', 'rubro', 'descripcion', 'acepto_terminos']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nombre de la empresa'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-input'}),
            'rubro': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Rubro'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Ej: Qué software desarrollan, para quién y objetivo'}),
        }

    def clean_rubro(self):
        rubro = (self.cleaned_data.get('rubro') or '').strip()
        if not rubro:
            raise forms.ValidationError('Indicá el rubro.')
        if not re.search(
            r'(software|tecnolog|programaci|desarroll|sistemas|app|apps|web|saas|it\b|ia\b|ml\b|machine\s*learning|datos|data|bi\b|analit|big\s*data|ciberseg|seguridad\s*inform|cloud|nube|devops|sre\b|infra|microserv|api|qa\b|test|testing|automat|rpa|blockchain|fintech|edtech|healthtech|e-?commerce|comercio\s*electr|videojueg|gaming|iot\b|embeb|embedded|realidad\s*(aumentada|virtual)|ar\b|vr\b)',
            rubro,
            re.IGNORECASE,
        ):
            raise forms.ValidationError('El rubro debe ser exclusivamente de Software / Tecnología.')
        return rubro

    def clean_acepto_terminos(self):
        acepto = self.cleaned_data.get('acepto_terminos')
        if not acepto:
            raise forms.ValidationError('Debes aceptar los términos para enviar la solicitud.')
        return acepto


class ActualizarLogoEmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['logo']
        widgets = {
            'logo': forms.FileInput(attrs={'class': 'form-input'}),
        }


class RechazarEmpresaForm(forms.Form):
    motivo_rechazo = forms.CharField(
        label='Motivo principal',
        widget=forms.Textarea(
            attrs={
                'class': 'form-input',
                'rows': 4,
                'placeholder': 'Ej: Rubro fuera de Software/Tecnología, información insuficiente, datos inconsistentes, etc.',
            }
        ),
        max_length=800,
    )


class AgregarMiembroForm(forms.Form):
    dni_usuario = forms.CharField(
        label='DNI del usuario',
        max_length=12,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'DNI'}),
    )
    rol = forms.CharField(
        label='Rol',
        max_length=80,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: CTO, Product, QA, etc. (opcional)'}),
    )
    es_socio = forms.BooleanField(label='Es socio', required=False)

    def clean_dni_usuario(self):
        dni_raw = self.cleaned_data.get('dni_usuario') or ''
        dni = Persona.limpiar_dni(dni_raw)
        if not dni:
            raise forms.ValidationError('Ingresá un DNI válido.')
        try:
            usuario = Usuario.objects.get(persona__dni=dni)
        except Usuario.DoesNotExist:
            raise forms.ValidationError('No existe ningún usuario registrado con este DNI.')
        return usuario
