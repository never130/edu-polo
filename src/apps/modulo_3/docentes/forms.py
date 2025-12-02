from django import forms
from .models import Docente
from apps.modulo_1.usuario.models import Persona, Usuario

class DocenteForm(forms.ModelForm):
    """
    Formulario para crear y editar Docentes.
    """
    
    # Campos del modelo Persona
    dni = forms.CharField(max_length=12, label="DNI")
    nombre = forms.CharField(max_length=100, label="Nombre")
    apellido = forms.CharField(max_length=100, label="Apellido")
    correo = forms.EmailField(label="Correo Electrónico")
    telefono = forms.CharField(max_length=15, required=False, label="Teléfono")
    fecha_nacimiento = forms.DateField(
        required=False, 
        label="Fecha de Nacimiento", 
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    genero = forms.ChoiceField(
        choices=[('', '---')] + Persona.generos, 
        required=False, 
        label="Género"
    )
    domicilio = forms.CharField(max_length=255, required=False, label="Domicilio")

    class Meta:
        model = Docente
        fields = ['especialidad', 'experiencia']
        widgets = {
            'experiencia': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si estamos editando, rellenar campos de Persona
        if self.instance and self.instance.pk:
            persona = self.instance.usuario.persona
            self.fields['dni'].initial = persona.dni
            self.fields['nombre'].initial = persona.nombre
            self.fields['apellido'].initial = persona.apellido
            self.fields['correo'].initial = persona.correo
            self.fields['telefono'].initial = persona.telefono
            self.fields['fecha_nacimiento'].initial = persona.fecha_nacimiento
            self.fields['genero'].initial = persona.genero
            self.fields['domicilio'].initial = persona.domicilio

    def save(self, commit=True):
        # Datos de Persona
        datos_persona = {
            'dni': self.cleaned_data['dni'],
            'nombre': self.cleaned_data['nombre'],
            'apellido': self.cleaned_data['apellido'],
            'correo': self.cleaned_data['correo'],
            'telefono': self.cleaned_data.get('telefono'),
            'fecha_nacimiento': self.cleaned_data.get('fecha_nacimiento'),
            'genero': self.cleaned_data.get('genero'),
            'domicilio': self.cleaned_data.get('domicilio'),
        }

        # 1. Guardar/Actualizar Persona
        if self.instance and self.instance.pk:
            # Actualizando
            Persona.objects.filter(pk=self.instance.usuario.persona.pk).update(**datos_persona)
            persona = self.instance.usuario.persona
        else:
            # Creando nuevo
            persona = Persona.objects.create(**datos_persona)

        # 2. Guardar/Actualizar Usuario
        if self.instance and self.instance.pk:
            usuario = self.instance.usuario
        else:
            # Crear nuevo usuario con contraseña temporal
            usuario = Usuario.objects.create(
                persona=persona,
                contrasena='temporal123'  # Contraseña temporal
            )
        
        # 3. Guardar Docente
        docente = super().save(commit=False)
        docente.usuario = usuario
        
        if commit:
            docente.save()
            
        return docente





