from django import forms
import re

from apps.modulo_1.usuario.models import Persona, Usuario

from .models import Empresa


def _validar_archivo(archivo, allowed_content_types, allowed_exts, max_bytes, message_tipo, message_size):
    if not archivo:
        return archivo

    content_type = (getattr(archivo, 'content_type', '') or '').lower()
    name = (getattr(archivo, 'name', '') or '').lower()

    if content_type and content_type not in allowed_content_types:
        raise forms.ValidationError(message_tipo)
    if not content_type and name and not name.endswith(allowed_exts):
        raise forms.ValidationError(message_tipo)

    if getattr(archivo, 'size', 0) and archivo.size > max_bytes:
        raise forms.ValidationError(message_size)

    return archivo


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = [
            'nombre',
            'condicion_fiscal',
            'cuit',
            'cantidad_miembros',
            'dni_responsable_archivo',
            'nomina_socios_archivo',
            'nomina_socios_link',
            'logo',
            'rubro',
            'descripcion',
            'acepto_terminos',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nombre de la empresa'}),
            'condicion_fiscal': forms.Select(attrs={'class': 'form-input'}),
            'cuit': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'CUIT (11 dígitos)'}),
            'cantidad_miembros': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'placeholder': 'Ej: 3'}),
            'dni_responsable_archivo': forms.ClearableFileInput(
                attrs={'class': 'form-input', 'accept': 'application/pdf,image/png,image/jpeg'}
            ),
            'nomina_socios_archivo': forms.ClearableFileInput(
                attrs={'class': 'form-input', 'accept': 'application/pdf,image/png,image/jpeg'}
            ),
            'nomina_socios_link': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://...'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-input', 'accept': 'image/png,image/jpeg'}),
            'rubro': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Rubro'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Ej: Qué software desarrollan, para quién y objetivo'}),
        }
        labels = {
            'condicion_fiscal': 'Condición Fiscal / Tipo Societario',
            'cuit': 'CUIT (del proyecto)',
            'cantidad_miembros': 'Cantidad de miembros / socios',
            'dni_responsable_archivo': 'Adjuntar DNI del responsable (PDF o imagen)',
            'nomina_socios_archivo': 'Adjuntar nómina de miembros/socios (PDF o imagen)',
            'nomina_socios_link': 'Link a nómina (opcional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['condicion_fiscal'].required = True
        base_choices = [c for c in self.fields['condicion_fiscal'].choices if c[0] != '']
        self.fields['condicion_fiscal'].choices = [('', 'Seleccioná una opción')] + base_choices

        self.fields['cuit'].required = False
        self.fields['cantidad_miembros'].required = True

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

    def clean_cantidad_miembros(self):
        cantidad = self.cleaned_data.get('cantidad_miembros')
        if cantidad is None:
            raise forms.ValidationError('Indicá cuántos miembros/socios forman parte.')
        if cantidad < 1:
            raise forms.ValidationError('La cantidad debe ser mayor o igual a 1.')
        if cantidad > 500:
            raise forms.ValidationError('La cantidad ingresada es demasiado grande.')
        return cantidad

    def clean_dni_responsable_archivo(self):
        archivo = self.cleaned_data.get('dni_responsable_archivo')
        return _validar_archivo(
            archivo=archivo,
            allowed_content_types={'application/pdf', 'image/png', 'image/jpeg'},
            allowed_exts=('.pdf', '.png', '.jpg', '.jpeg'),
            max_bytes=5 * 1024 * 1024,
            message_tipo='El DNI debe ser un PDF o una imagen (PNG/JPG).',
            message_size='El DNI supera el tamaño máximo permitido (5MB).',
        )

    def clean_nomina_socios_archivo(self):
        archivo = self.cleaned_data.get('nomina_socios_archivo')
        return _validar_archivo(
            archivo=archivo,
            allowed_content_types={'application/pdf', 'image/png', 'image/jpeg'},
            allowed_exts=('.pdf', '.png', '.jpg', '.jpeg'),
            max_bytes=10 * 1024 * 1024,
            message_tipo='La nómina debe ser un PDF o una imagen (PNG/JPG).',
            message_size='La nómina supera el tamaño máximo permitido (10MB).',
        )

    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if not logo:
            return logo

        content_type = (getattr(logo, 'content_type', '') or '').lower()
        if content_type not in {'image/png', 'image/jpeg'}:
            raise forms.ValidationError('El logo debe ser una imagen PNG o JPG.')

        max_bytes = 2 * 1024 * 1024
        if getattr(logo, 'size', 0) and logo.size > max_bytes:
            raise forms.ValidationError('El logo supera el tamaño máximo permitido (2MB).')

        return logo

    def clean(self):
        cleaned_data = super().clean()

        condicion_fiscal = cleaned_data.get('condicion_fiscal') or ''
        cuit_raw = cleaned_data.get('cuit') or ''
        cuit_digits = re.sub(r'\D', '', cuit_raw)

        if condicion_fiscal and condicion_fiscal != 'en_formacion':
            if not cuit_digits:
                self.add_error('cuit', 'Ingresá el CUIT (11 dígitos).')
            elif len(cuit_digits) != 11:
                self.add_error('cuit', 'El CUIT debe tener 11 dígitos.')
            else:
                cleaned_data['cuit'] = cuit_digits
        else:
            if cuit_digits and len(cuit_digits) != 11:
                self.add_error('cuit', 'El CUIT debe tener 11 dígitos.')
            cleaned_data['cuit'] = cuit_digits

        return cleaned_data

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
            'logo': forms.FileInput(attrs={'class': 'form-input', 'accept': 'image/png,image/jpeg'}),
        }

    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if not logo:
            return logo

        content_type = (getattr(logo, 'content_type', '') or '').lower()
        if content_type not in {'image/png', 'image/jpeg'}:
            raise forms.ValidationError('El logo debe ser una imagen PNG o JPG.')

        max_bytes = 2 * 1024 * 1024
        if getattr(logo, 'size', 0) and logo.size > max_bytes:
            raise forms.ValidationError('El logo supera el tamaño máximo permitido (2MB).')

        return logo


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
