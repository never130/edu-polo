from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg
from django.http import HttpResponse
from django.conf import settings
import os
from datetime import datetime

from apps.modulo_1.roles.models import Estudiante
from apps.modulo_2.inscripciones.models import Inscripcion
from apps.modulo_4.asistencia.models import Asistencia, RegistroAsistencia
from apps.modulo_3.cursos.models import Material

try:
    from reportlab.lib.pagesizes import letter, A4, landscape
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    from reportlab.platypus import Paragraph, Frame
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


@login_required
def mi_progreso(request):
    """Vista de progreso del estudiante"""
    try:
        estudiante = Estudiante.objects.get(usuario__persona__dni=request.user.username)
        
        # Obtener inscripciones confirmadas
        inscripciones = Inscripcion.objects.filter(
            estudiante=estudiante,
            estado='confirmado',
            comision__publicada=True,
        ).select_related('comision__fk_id_curso')
        
        # Calcular progreso para cada inscripción
        inscripciones_con_progreso = []
        for inscripcion in inscripciones:
            # Obtener o crear registro de asistencia
            registro, created = RegistroAsistencia.objects.get_or_create(
                inscripcion=inscripcion
            )

            registro.calcular_porcentaje()

            total_programadas = None
            comision = inscripcion.comision
            if hasattr(comision, 'get_total_clases_programadas'):
                total_programadas = comision.get_total_clases_programadas(hasta=comision.fecha_fin)
            if total_programadas is None:
                total_programadas = registro.total_clases

            inscripcion.progreso = int(registro.porcentaje_asistencia)
            inscripcion.total_clases = total_programadas
            inscripcion.asistencias_count = registro.clases_asistidas
            inscripcion.cumple_certificado = registro.cumple_requisito_certificado
            
            inscripciones_con_progreso.append(inscripcion)
        
        context = {
            'estudiante': estudiante,
            'inscripciones': inscripciones_con_progreso,
        }
        return render(request, 'usuario/mi_progreso.html', context)
        
    except Estudiante.DoesNotExist:
        messages.error(request, 'No tienes perfil de estudiante.')
        return redirect('dashboard')


@login_required
def mis_certificados(request):
    """Vista de certificados del estudiante"""
    try:
        estudiante = Estudiante.objects.get(usuario__persona__dni=request.user.username)
        
        # Obtener registros de asistencia que cumplen requisito
        registros = RegistroAsistencia.objects.filter(
            inscripcion__estudiante=estudiante,
            cumple_requisito_certificado=True
        ).select_related('inscripcion__comision__fk_id_curso')
        
        context = {
            'estudiante': estudiante,
            'registros': registros,
        }
        return render(request, 'usuario/mis_certificados.html', context)
        
    except Estudiante.DoesNotExist:
        messages.error(request, 'No tienes perfil de estudiante.')
        return redirect('dashboard')


@login_required
def descargar_certificado(request, inscripcion_id):
    """Generar y descargar certificado en PDF"""
    if not REPORTLAB_AVAILABLE:
        messages.error(request, '❌ La funcionalidad de certificados PDF no está disponible. Por favor, contacta al administrador.')
        return redirect('usuario:mis_certificados')
    
    try:
        estudiante = Estudiante.objects.get(usuario__persona__dni=request.user.username)
        inscripcion = get_object_or_404(Inscripcion, id=inscripcion_id, estudiante=estudiante, estado='confirmado')
        
        # Verificar que el estudiante tenga acceso a este certificado
        if inscripcion.estudiante != estudiante:
            messages.error(request, '❌ No tienes permiso para descargar este certificado.')
            return redirect('usuario:mis_certificados')
        
        # Obtener o crear registro de asistencia
        registro, created = RegistroAsistencia.objects.get_or_create(inscripcion=inscripcion)
        
        if not registro.cumple_requisito_certificado:
            fecha_fin = inscripcion.comision.fecha_fin
            hoy = datetime.now().date()
            if fecha_fin and fecha_fin > hoy:
                messages.error(request, '❌ El certificado se habilita al finalizar la comisión.')
            else:
                messages.error(request, '❌ No cumples con el requisito mínimo de 80% de asistencia para obtener el certificado.')
            return redirect('usuario:mi_progreso')
        
        response = HttpResponse(content_type='application/pdf')
        nombre_archivo = f"Certificado_{inscripcion.comision.fk_id_curso.nombre.replace(' ', '_')}_{estudiante.usuario.persona.dni}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'

        page_size = landscape(A4)
        page_width, page_height = page_size
        pdf = canvas.Canvas(response, pagesize=page_size)

        template_path = os.path.join(settings.STATIC_ROOT or settings.STATICFILES_DIRS[0], 'img', 'plantilla.png')
        if not os.path.exists(template_path):
            template_path = os.path.join(settings.BASE_DIR, 'stc', 'img', 'plantilla.png')

        if os.path.exists(template_path):
            pdf.drawImage(template_path, 0, 0, width=page_width, height=page_height, mask='auto')

        img_w = 1091
        img_h = 789

        def sx(value):
            return value / img_w * page_width

        def sy(value):
            return value / img_h * page_height

        def frame_from_top(x, top, w, h):
            return (sx(x), page_height - sy(top + h), sx(w), sy(h))

        nombre = estudiante.usuario.persona.nombre_completo
        dni = estudiante.usuario.persona.dni
        curso = inscripcion.comision.fk_id_curso.nombre

        styles = getSampleStyleSheet()
        name_style = ParagraphStyle(
            'CertName',
            parent=styles['Normal'],
            fontSize=26,
            textColor=colors.HexColor('#333333'),
            alignment=TA_CENTER,
            leading=30,
            fontName='Helvetica-Bold'
        )
        body_style = ParagraphStyle(
            'CertBody',
            parent=styles['Normal'],
            fontSize=15.5,
            textColor=colors.HexColor('#4b5563'),
            alignment=TA_JUSTIFY,
            leading=22
        )

        name_frame = Frame(*frame_from_top(140, 230, 810, 60), showBoundary=0)
        body_frame = Frame(*frame_from_top(140, 310, 810, 140), showBoundary=0)

        name_para = Paragraph(f"{nombre}, D.N.I {dni}", name_style)
        body_text = (
            f"ha asistido y aprobado el curso de <b>{curso}</b>, desarrollado en el marco de las actividades de "
            "formación de los Polos Creativos, dependiente de la Agencia de Innovación de la Provincia de "
            "Tierra del Fuego, Antártida e Islas del Atlántico Sur."
        )
        body_para = Paragraph(body_text, body_style)

        name_frame.addFromList([name_para], pdf)
        body_frame.addFromList([body_para], pdf)

        pdf.showPage()
        pdf.save()
        return response
        
    except Estudiante.DoesNotExist:
        messages.error(request, 'No tienes perfil de estudiante.')
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f'❌ Error al generar el certificado: {str(e)}')
        return redirect('usuario:mis_certificados')


@login_required
def materiales_estudiante(request):
    """Vista para que el estudiante vea los materiales de sus comisiones"""
    try:
        estudiante = Estudiante.objects.get(usuario__persona__dni=request.user.username)
        
        # Obtener inscripciones confirmadas
        inscripciones = Inscripcion.objects.filter(
            estudiante=estudiante,
            estado='confirmado',
            comision__publicada=True,
        ).select_related('comision__fk_id_curso', 'comision__fk_id_polo').order_by('comision__fk_id_curso__nombre')
        
        # Agrupar materiales por comisión
        materiales_por_comision = []
        for inscripcion in inscripciones:
            materiales = Material.objects.filter(
                fk_id_comision=inscripcion.comision
            ).order_by('-fecha_subida')
            
            if materiales.exists():
                materiales_por_comision.append({
                    'inscripcion': inscripcion,
                    'comision': inscripcion.comision,
                    'curso': inscripcion.comision.fk_id_curso,
                    'materiales': materiales,
                    'total_materiales': materiales.count(),
                })
        
        context = {
            'estudiante': estudiante,
            'materiales_por_comision': materiales_por_comision,
        }
        return render(request, 'usuario/materiales_estudiante.html', context)
        
    except Estudiante.DoesNotExist:
        messages.error(request, 'No tienes perfil de estudiante.')
        return redirect('dashboard')


@login_required
def materiales_comision_estudiante(request, comision_id):
    """Vista para que el estudiante vea los materiales de una comisión específica"""
    try:
        estudiante = Estudiante.objects.get(usuario__persona__dni=request.user.username)
        
        # Verificar que el estudiante esté inscrito en esta comisión
        inscripcion = get_object_or_404(
            Inscripcion,
            estudiante=estudiante,
            comision_id=comision_id,
            estado='confirmado',
            comision__publicada=True,
        )
        
        # Obtener materiales de la comisión
        materiales = Material.objects.filter(
            fk_id_comision=inscripcion.comision
        ).order_by('-fecha_subida')
        
        context = {
            'estudiante': estudiante,
            'inscripcion': inscripcion,
            'comision': inscripcion.comision,
            'curso': inscripcion.comision.fk_id_curso,
            'materiales': materiales,
        }
        return render(request, 'usuario/materiales_comision_estudiante.html', context)
        
    except Estudiante.DoesNotExist:
        messages.error(request, 'No tienes perfil de estudiante.')
        return redirect('dashboard')
