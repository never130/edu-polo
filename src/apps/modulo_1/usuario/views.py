from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.db import transaction
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from .models import Persona, Usuario
from apps.modulo_1.roles.models import Estudiante, Docente, Rol
from datetime import date

# Create your views here.
#Persona
class PersonaListView(ListView):
    model = Persona
    template_name = 'usuario/persona_list.html'

class PersonaCreateView(CreateView):
    model = Persona
    template_name = 'usuario/persona_form.html'
    fields = '__all__'
    success_url = reverse_lazy('persona_list')

class PersonaUpdateView(UpdateView):
    model = Persona
    template_name = 'usuario/persona_form.html'
    fields = '__all__'
    success_url = reverse_lazy('persona_list')

class PersonaDeleteView(DeleteView):
    model = Persona
    template_name = 'usuario/persona_confirm_delete.html'
    success_url = reverse_lazy('persona_list')

#Usuario
class UsuarioListView(ListView):
    model = Usuario
    template_name = 'usuario/usuario_list.html'

class UsuarioCreateView(CreateView):
    model = Usuario
    template_name = 'usuario/usuario_form.html'
    fields = '__all__'
    success_url = reverse_lazy('usuario_list')

class UsuarioUpdateView(UpdateView):
    model = Usuario
    template_name = 'usuario/usuario_form.html'
    fields = '__all__'
    success_url = reverse_lazy('usuario_list')

class UsuarioDeleteView(DeleteView):
    model = Usuario
    template_name = 'usuario/usuario_confirm_delete.html'
    success_url = reverse_lazy('usuario_list')


@method_decorator(csrf_protect, name='dispatch')
class RegistroView(View):
    """Vista para registro de nuevos usuarios"""
    
    def get(self, request):
        context = {}
        return render(request, 'usuario/registro.html', context)
    
    def post(self, request):
        try:
            with transaction.atomic():
                # Obtener datos del formulario
                dni = request.POST.get('dni')
                nombre = request.POST.get('nombre')
                apellido = request.POST.get('apellido')
                correo = request.POST.get('correo')
                telefono = request.POST.get('telefono', '').strip()
                fecha_nacimiento = request.POST.get('fecha_nacimiento')
                genero = request.POST.get('genero', '')
                ciudad = request.POST.get('ciudad', '')
                domicilio = request.POST.get('domicilio', '')
                password = request.POST.get('password')
                password_confirm = request.POST.get('password_confirm')
                
                # Campos de salud y autorizaciones
                observaciones_discapacidad = request.POST.get('observaciones_discapacidad', '').strip()
                observaciones_salud = request.POST.get('observaciones_salud', '').strip()
                observaciones_generales = request.POST.get('observaciones_generales', '').strip()
                
                politica_datos = request.POST.get('politica_datos')
                autorizacion_imagen = request.POST.get('autorizacion_imagen') == 'on'
                autorizacion_voz = request.POST.get('autorizacion_voz') == 'on'

                # Combinar observaciones en condiciones_medicas
                condiciones_medicas_list = []
                if observaciones_discapacidad:
                    condiciones_medicas_list.append(f"Discapacidad/Adaptaciones: {observaciones_discapacidad}")
                if observaciones_salud:
                    condiciones_medicas_list.append(f"Condiciones Médicas: {observaciones_salud}")
                if observaciones_generales:
                    condiciones_medicas_list.append(f"Otras Observaciones: {observaciones_generales}")
                
                condiciones_medicas = "\n".join(condiciones_medicas_list)

                # Solo estudiantes pueden registrarse desde el formulario público
                tipo_usuario = 'estudiante'
                
                # Validaciones
                if not politica_datos:
                    messages.error(request, 'Debes aceptar la política de uso de datos personales.')
                    return render(request, 'usuario/registro.html')

                if password != password_confirm:
                    messages.error(request, 'Las contraseñas no coinciden.')
                    return render(request, 'usuario/registro.html')
                
                if Persona.objects.filter(dni=dni).exists():
                    messages.error(request, 'Ya existe una persona con ese DNI.')
                    return render(request, 'usuario/registro.html')
                
                if Persona.objects.filter(correo=correo).exists():
                    messages.error(request, 'Ya existe una persona con ese correo.')
                    return render(request, 'usuario/registro.html')

                if not telefono:
                    messages.error(request, 'El teléfono es obligatorio.')
                    return render(request, 'usuario/registro.html')
                
                if User.objects.filter(username=dni).exists():
                    messages.error(request, 'Ya existe un usuario con ese DNI.')
                    return render(request, 'usuario/registro.html')
                
                # Crear Persona
                persona = Persona.objects.create(
                    dni=dni,
                    nombre=nombre,
                    apellido=apellido,
                    correo=correo,
                    telefono=telefono,
                    fecha_nacimiento=fecha_nacimiento if fecha_nacimiento else None,
                    genero=genero,
                    ciudad_residencia=ciudad if ciudad else None,
                    domicilio=domicilio,
                    condiciones_medicas=condiciones_medicas,
                    autorizacion_imagen=autorizacion_imagen,
                    autorizacion_voz=autorizacion_voz
                )
                
                # Crear Usuario del sistema Django
                user = User.objects.create_user(
                    username=dni,
                    email=correo,
                    password=password,
                    first_name=nombre,
                    last_name=apellido
                )
                
                # Crear Usuario personalizado
                usuario = Usuario.objects.create(
                    persona=persona,
                    contrasena=password,  # En producción debería hashearse
                    activo=True
                )
                
                # Crear perfil de estudiante (solo estudiantes pueden registrarse)
                nivel = request.POST.get('nivel_estudios', 'OT')
                institucion = request.POST.get('institucion_actual', '')
                
                Estudiante.objects.create(
                    usuario=usuario,
                    nivel_estudios=nivel,
                    institucion_actual=institucion
                )
                
                # Asignar rol de Estudiante
                from apps.modulo_1.roles.models import Rol, UsuarioRol
                rol, _ = Rol.objects.get_or_create(nombre='Estudiante', defaults={'descripcion': 'Rol para estudiantes', 'jerarquia': 3})
                UsuarioRol.objects.get_or_create(usuario_id=usuario, rol_id=rol)
                
                # Redirigir a login
                messages.success(request, f'¡Registro exitoso! Usuario: {dni}. Ahora puedes iniciar sesión.')
                return redirect('login')
                
        except Exception as e:
            messages.error(request, f'Error al registrar: {str(e)}')
            return render(request, 'usuario/registro.html')
