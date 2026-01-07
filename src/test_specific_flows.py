import os
import django
from datetime import date
from django.conf import settings

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from apps.modulo_1.usuario.models import Persona, Usuario
from apps.modulo_1.roles.models import Estudiante, Rol, UsuarioRol
from apps.modulo_3.cursos.models import Curso, Comision, PoloCreativo
from apps.modulo_2.inscripciones.models import Inscripcion
from apps.modulo_4.asistencia.models import Asistencia

def run_tests():
    print("Iniciando pruebas específicas: Progreso y Mesa de Entrada...")
    
    prefix = "TEST_SPEC_"
    
    # 1. Crear Datos Base
    print("1. Creando datos base (Polos, Cursos, Comisiones)...")
    
    polo_ush, _ = PoloCreativo.objects.get_or_create(
        nombre=f'{prefix}Polo_USH',
        defaults={'ciudad': 'Ushuaia', 'direccion': 'Ush 123', 'activo': True}
    )
    
    polo_rg, _ = PoloCreativo.objects.get_or_create(
        nombre=f'{prefix}Polo_RG',
        defaults={'ciudad': 'Rio Grande', 'direccion': 'RG 456', 'activo': True}
    )
    
    curso, _ = Curso.objects.get_or_create(
        nombre=f'{prefix}Curso_Test',
        defaults={'estado': 'Abierto', 'orden': 200, 'edad_minima': 18, 'edad_maxima': 99}
    )
    
    comision_ush, _ = Comision.objects.get_or_create(
        fk_id_curso=curso,
        fk_id_polo=polo_ush,
        defaults={
            'dias_horarios': 'Lun-Mie-Vie 18:00',
            'fecha_inicio': date(2025, 1, 1),
            'fecha_fin': date(2026, 12, 31), # Cubre 2026
            'estado': 'Abierta',
            'cupo_maximo': 30,
            'horarios': '18:00-20:00'
        }
    )
    if comision_ush.fecha_fin < date(2026, 12, 31):
        print(f"Actualizando fecha fin comision {comision_ush.id_comision} a 2026...")
        comision_ush.fecha_fin = date(2026, 12, 31)
        comision_ush.save()
        print("Fecha actualizada.")
    
    # Asegurar días de cursada para hoy (Miércoles)
    if 'Mie' not in (comision_ush.dias_horarios or ''):
         print(f"Actualizando días horarios de '{comision_ush.dias_horarios}' a 'Lun-Mie-Vie 18:00'...")
         comision_ush.dias_horarios = 'Lun-Mie-Vie 18:00'
         comision_ush.save()

    print(f"Comision {comision_ush.id_comision} fecha fin: {comision_ush.fecha_fin}, Días: {comision_ush.dias_horarios}")

    comision_rg, _ = Comision.objects.get_or_create(
        fk_id_curso=curso,
        fk_id_polo=polo_rg,
        defaults={
            'dias_horarios': 'Martes 10:00',
            'fecha_inicio': date(2025, 1, 1),
            'fecha_fin': date(2026, 12, 31),
            'estado': 'Abierta',
            'cupo_maximo': 20
        }
    )
    
    # 2. Crear Usuarios y Roles
    print("2. Configurando Usuarios y Roles...")
    
    # Rol Mesa de Entrada
    rol_mesa, _ = Rol.objects.get_or_create(nombre='Mesa de Entrada', defaults={'jerarquia': 2})
    
    # Usuario Mesa Ushuaia
    dni_mesa_ush = "77777777"
    try:
        u_mesa_ush = User.objects.get(username=dni_mesa_ush)
        # Asegurar que tenga el rol (si ya existía el usuario pero falló la asignación antes)
        try:
            p_mesa_ush = Persona.objects.get(dni=dni_mesa_ush)
            us_mesa_ush = Usuario.objects.get(persona=p_mesa_ush)
            UsuarioRol.objects.get_or_create(usuario_id=us_mesa_ush, rol_id=rol_mesa)
        except Exception as e:
            print(f"Error recuperando usuario mesa existente: {e}")
            
    except User.DoesNotExist:
        u_mesa_ush = User.objects.create_user(username=dni_mesa_ush, password="password123")
        p_mesa_ush = Persona.objects.create(dni=dni_mesa_ush, nombre="Mesa", apellido="Ushuaia", correo="mesa.ush@test.com", ciudad_residencia='Ushuaia')
        us_mesa_ush = Usuario.objects.create(persona=p_mesa_ush, contrasena="password123")
        UsuarioRol.objects.create(usuario_id=us_mesa_ush, rol_id=rol_mesa)
    
    # Usuario Estudiante (Ushuaia)
    dni_est = "66666666"
    try:
        u_est = User.objects.get(username=dni_est)
    except User.DoesNotExist:
        u_est = User.objects.create_user(username=dni_est, password="password123")
        p_est = Persona.objects.create(dni=dni_est, nombre="Estudiante", apellido="Test", correo="est.ush@test.com", ciudad_residencia='Ushuaia')
        us_est = Usuario.objects.create(persona=p_est, contrasena="password123")
        Estudiante.objects.create(usuario=us_est)
    
    estudiante = Estudiante.objects.get(usuario__persona__dni=dni_est)
    
    # Inscribir estudiante en Comision Ushuaia
    inscripcion, _ = Inscripcion.objects.get_or_create(
        estudiante=estudiante, 
        comision=comision_ush, 
        defaults={'estado': 'confirmado'}
    )
    if inscripcion.estado != 'confirmado':
        inscripcion.estado = 'confirmado'
        inscripcion.save()

    # 3. TEST: Mesa de Entrada
    print("\n3. Ejecutando Pruebas de MESA DE ENTRADA...")
    client = Client()
    client.login(username=dni_mesa_ush, password="password123")
    
    # A. Acceso a Comision de su ciudad (Debe funcionar)
    url_asistencia = reverse('administracion:panel_asistencia')
    url_params = f'?comision_id={comision_ush.id_comision}'
    resp = client.get(url_asistencia + url_params)
    
    if resp.status_code == 200:
        print(f"✅ Mesa Entrada (Ush) ve Comision Ushuaia: OK")
    else:
        print(f"❌ Mesa Entrada (Ush) ve Comision Ushuaia: FALLÓ ({resp.status_code})")
        if resp.status_code == 302:
            print(f"   Redirige a: {resp.url}")

    # B. Acceso a Comision de OTRA ciudad (Debe ser denegado/redirect)
    url_params_rg = f'?comision_id={comision_rg.id_comision}'
    resp_rg = client.get(url_asistencia + url_params_rg)
    
    if resp_rg.status_code == 302:
        print(f"✅ Mesa Entrada (Ush) NO ve Comision RG: OK (Redirect correcto)")
        # Verificar mensaje de error si es posible (via messages)
    elif resp_rg.status_code == 200:
        # Si devuelve 200 pero muestra error en pantalla, también podría ser válido, pero esperamos redirect según código
        print(f"⚠️ Mesa Entrada (Ush) accedió a Comision RG con 200 (Revisar si mostró error en template)")
    else:
        print(f"❓ Comportamiento inesperado al acceder a otra ciudad: {resp_rg.status_code}")

    # C. POST Asistencia (Guardar)
    print("   Intentando guardar asistencia...")
    fecha_hoy = date.today().isoformat()
    post_data = {
        'comision_id': comision_ush.id_comision,
        'fecha_clase': fecha_hoy,
        'guardar_asistencia': '1',
        f'presente_{inscripcion.id}': 'on',
        f'observacion_{inscripcion.id}': 'Test auto'
    }
    
    resp_post = client.post(url_asistencia, post_data)
    
    if resp_post.status_code == 302:
        print(f"✅ POST Asistencia: Redirección exitosa (Guardado OK)")
        
        # Verificar en BD
        asistencia_db = Asistencia.objects.filter(inscripcion=inscripcion, fecha_clase=fecha_hoy).first()
        if asistencia_db and asistencia_db.presente:
            print(f"   ✨ Verificado en BD: Asistencia guardada correctamente.")
        else:
            print(f"   ❌ Error en BD: No se encontró la asistencia guardada.")
    else:
        print(f"❌ POST Asistencia: FALLÓ ({resp_post.status_code})")
        # Imprimir mensajes de error si los hay
        if resp_post.context and 'messages' in resp_post.context:
            msgs = list(resp_post.context['messages'])
            for m in msgs:
                print(f"   Mensaje UI: {m}")
        # print(f"   Contenido respuesta (primeros 500 chars): {resp_post.content.decode('utf-8')[:500]}")

    # 4. TEST: Progreso Estudiante
    print("\n4. Ejecutando Pruebas de PROGRESO ESTUDIANTE...")
    client.logout()
    client.login(username=dni_est, password="password123")
    
    url_progreso = reverse('usuario:mi_progreso')
    resp_prog = client.get(url_progreso)
    
    if resp_prog.status_code == 200:
        content = resp_prog.content.decode('utf-8')
        if curso.nombre in content:
            print(f"✅ Vista Progreso: OK (Curso encontrado)")
        else:
            print(f"⚠️ Vista Progreso: OK (200) pero no veo el nombre del curso '{curso.nombre}'")
            
        # Verificar si aparece el porcentaje (debería ser 100% o calculado según lógica)
        # Como solo hay 1 clase y asistió, debería tener % alto.
        if "100%" in content or "100,0%" in content:
             print(f"   ✨ Porcentaje de asistencia visible.")
    else:
        print(f"❌ Vista Progreso: FALLÓ ({resp_prog.status_code})")

    print("\n🏁 Fin de pruebas específicas.")

if __name__ == "__main__":
    run_tests()
