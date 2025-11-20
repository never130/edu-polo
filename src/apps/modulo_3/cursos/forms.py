from django import forms
from .models import Curso, Comision, Material
# Importamos el modelo Usuario para poder filtrar por docentes
from apps.modulo_1.usuario.models import Usuario
from apps.modulo_1.roles.models import Rol

class CursoForm(forms.ModelForm):
    """Formulario para el modelo Curso."""
    class Meta:
        model = Curso
        fields = [
            'nombre', 
            'descripcion', 
            'edad_minima', 
            'requisitos', 
            'contenido_multimedia', 
            'estado'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'requisitos': forms.Textarea(attrs={'rows': 3}),
        }

class ComisionForm(forms.ModelForm):
    """Formulario para el modelo Comision."""
    class Meta:
        model = Comision
        fields = [
            'fk_id_curso',
            'dias_horarios',
            'lugar',
            'fecha_inicio',
            'fecha_fin',
            'cupo_maximo',
            'estado'
        ]
        # Para usar un selector de fecha en los campos de fecha
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
            'dias_horarios': forms.Textarea(attrs={'rows': 2}),
        }

class MaterialForm(forms.ModelForm):
    """Formulario para subir materiales."""
    class Meta:
        model = Material
        fields = ['nombre_archivo', 'descripcion', 'tipo', 'archivo', 'enlace']
        widgets = {
            'tipo': forms.Select(attrs={'id': 'id_tipo_material', 'onchange': 'toggleMaterialFields()'}),
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        archivo = cleaned_data.get('archivo')
        enlace = cleaned_data.get('enlace')
        
        if tipo == 'archivo' and not archivo:
            raise forms.ValidationError({'archivo': 'Debe subir un archivo para materiales de tipo archivo.'})
        if tipo == 'enlace' and not enlace:
            raise forms.ValidationError({'enlace': 'Debe proporcionar un enlace para materiales de tipo enlace.'})
        
        return cleaned_data

class ImportarCursosForm(forms.Form):
    """Formulario simple para subir el archivo Excel."""
    archivo_excel = forms.FileField(label="Seleccionar archivo .xlsx")

class AsignacionDocenteForm(forms.Form):
    """Formulario para asignar un docente a una comisión."""
    
    docente = forms.ModelChoiceField(
        queryset=Usuario.objects.none(),  # Se actualizará en __init__
        label="Seleccionar Docente"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Obtenemos el Rol 'Docente' solo cuando se inicializa el formulario
        try:
            rol_docente = Rol.objects.get(nombre='Docente')
            # Creamos un queryset solo con usuarios que tengan el rol de Docente
            queryset_docentes = Usuario.objects.filter(fk_id_rol=rol_docente)
        except (Rol.DoesNotExist, Exception):
            # Si el rol no existe o hay algún error (ej: tabla no existe aún), el queryset estará vacío
            queryset_docentes = Usuario.objects.none()
        
        # Actualizamos el queryset del campo
        self.fields['docente'].queryset = queryset_docentes
