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
from apps.modulo_1.roles.models import Estudiante, Docente, Rol, UsuarioRol
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
                zona_residencia = request.POST.get('zona_residencia', '')
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
                datos_veridicos = request.POST.get('datos_veridicos')

                tipo_usuario = (request.POST.get('tipo_usuario') or 'estudiante').strip().lower()
                if tipo_usuario not in {'estudiante', 'empresa'}:
                    messages.error(request, 'El tipo de usuario seleccionado no es válido.')
                    return render(request, 'usuario/registro.html')

                # Combinar observaciones en condiciones_medicas
                condiciones_medicas_list = []
                if observaciones_discapacidad:
                    condiciones_medicas_list.append(f"Discapacidad/Adaptaciones: {observaciones_discapacidad}")
                if observaciones_salud:
                    condiciones_medicas_list.append(f"Condiciones Médicas: {observaciones_salud}")
                if observaciones_generales:
                    condiciones_medicas_list.append(f"Otras Observaciones: {observaciones_generales}")
                
                condiciones_medicas = "\n".join(condiciones_medicas_list)
                
                # Validaciones
                if not politica_datos:
                    messages.error(request, 'Debes aceptar la política de uso de datos personales.')
                    return render(request, 'usuario/registro.html')

                if not datos_veridicos:
                    messages.error(request, 'Debes confirmar que los datos ingresados son verídicos.')
                    return render(request, 'usuario/registro.html')

                if password != password_confirm:
                    messages.error(request, 'Las contraseñas no coinciden.')
                    return render(request, 'usuario/registro.html')
                
                if Persona.objects.filter(dni=dni).exists():
                    messages.error(request, 'Ya existe una persona con ese DNI.')
                    return render(request, 'usuario/registro.html')
                
                if not telefono:
                    messages.error(request, 'El teléfono es obligatorio.')
                    return render(request, 'usuario/registro.html')
                
                if User.objects.filter(username=dni).exists():
                    messages.error(request, 'Ya existe un usuario con ese DNI.')
                    return render(request, 'usuario/registro.html')

                fecha_nacimiento_date = None
                if fecha_nacimiento:
                    try:
                        fecha_nacimiento_date = date.fromisoformat(fecha_nacimiento)
                    except ValueError:
                        messages.error(request, 'La fecha de nacimiento no es válida.')
                        return render(request, 'usuario/registro.html')

                    if fecha_nacimiento_date > date.today():
                        messages.error(request, 'La fecha de nacimiento no puede ser futura.')
                        return render(request, 'usuario/registro.html')

                empresa_form = None
                if tipo_usuario == 'empresa':
                    if not fecha_nacimiento_date:
                        messages.error(request, 'Para registrarte como empresa, la fecha de nacimiento es obligatoria.')
                        return render(request, 'usuario/registro.html')

                    hoy = date.today()
                    edad = hoy.year - fecha_nacimiento_date.year - (
                        (hoy.month, hoy.day) < (fecha_nacimiento_date.month, fecha_nacimiento_date.day)
                    )
                    if edad < 18:
                        messages.error(request, 'El Punto Empresarial está disponible solo para mayores de 18 años.')
                        return render(request, 'usuario/registro.html')

                    from apps.modulo_7.empresas.forms import EmpresaForm

                    empresa_form = EmpresaForm(
                        data={
                            'nombre': (request.POST.get('empresa_nombre') or '').strip(),
                            'condicion_fiscal': (request.POST.get('condicion_fiscal') or '').strip(),
                            'cuit': (request.POST.get('cuit') or '').strip(),
                            'cantidad_miembros': (request.POST.get('cantidad_miembros') or '').strip(),
                            'nomina_socios_link': (request.POST.get('nomina_socios_link') or '').strip(),
                            'rubro': (request.POST.get('empresa_rubro') or '').strip(),
                            'descripcion': (request.POST.get('empresa_descripcion') or '').strip(),
                            'acepto_terminos': request.POST.get('empresa_acepto_terminos') == 'on',
                        },
                        files=request.FILES,
                    )
                    if not empresa_form.is_valid():
                        for _, errs in empresa_form.errors.items():
                            for err in errs:
                                messages.error(request, str(err))
                        return render(request, 'usuario/registro.html')
                
                # Crear Persona
                persona = Persona.objects.create(
                    dni=dni,
                    nombre=nombre,
                    apellido=apellido,
                    correo=correo,
                    telefono=telefono,
                    fecha_nacimiento=fecha_nacimiento_date,
                    genero=genero,
                    ciudad_residencia=ciudad if ciudad else None,
                    zona_residencia=zona_residencia if zona_residencia else None,
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

                if tipo_usuario == 'estudiante':
                    nivel_estudios = (request.POST.get('nivel_estudios') or '').strip() or 'OT'
                    institucion_actual = (request.POST.get('institucion_actual') or '').strip() or 'Por definir'
                    Estudiante.objects.create(
                        usuario=usuario,
                        nivel_estudios=nivel_estudios,
                        institucion_actual=institucion_actual,
                    )
                    rol_estudiante, _ = Rol.objects.get_or_create(
                        nombre='Estudiante',
                        defaults={'descripcion': 'Rol para estudiantes', 'jerarquia': 3},
                    )
                    UsuarioRol.objects.get_or_create(usuario_id=usuario, rol_id=rol_estudiante)
                else:
                    rol_empresa, _ = Rol.objects.get_or_create(
                        nombre='Empresa',
                        defaults={'descripcion': 'Rol para empresas', 'jerarquia': 3},
                    )
                    UsuarioRol.objects.get_or_create(usuario_id=usuario, rol_id=rol_empresa)

                    if empresa_form is not None:
                        empresa_obj = empresa_form.save(commit=False)
                        empresa_obj.responsable = usuario
                        empresa_obj.estado = 'pendiente'
                        empresa_obj.save()
                
                # Redirigir a login
                messages.success(request, f'¡Registro exitoso! Usuario: {dni}. Ahora puedes iniciar sesión.')
                return redirect('login')
                
        except Exception as e:
            messages.error(request, f'Error al registrar: {str(e)}')
            return render(request, 'usuario/registro.html')
