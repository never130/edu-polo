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
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
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
            estado='confirmado'
        ).select_related('comision__fk_id_curso')
        
        # Calcular progreso para cada inscripción
        inscripciones_con_progreso = []
        for inscripcion in inscripciones:
            # Obtener o crear registro de asistencia
            registro, created = RegistroAsistencia.objects.get_or_create(
                inscripcion=inscripcion
            )
            
            # Calcular asistencias
            total_asistencias = Asistencia.objects.filter(inscripcion=inscripcion).count()
            asistencias_presentes = Asistencia.objects.filter(inscripcion=inscripcion, presente=True).count()
            
            if total_asistencias > 0:
                porcentaje = int((asistencias_presentes / total_asistencias) * 100)
            else:
                porcentaje = 0
            
            inscripcion.progreso = porcentaje
            inscripcion.total_clases = total_asistencias
            inscripcion.asistencias_count = asistencias_presentes
            inscripcion.cumple_certificado = 80 <= porcentaje <= 100
            
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
        
        # Verificar que cumpla con el requisito (60% o más de asistencia)
        if not registro.cumple_requisito_certificado:
            messages.error(request, '❌ No cumples con el requisito mínimo de 60% de asistencia para obtener el certificado.')
            return redirect('usuario:mi_progreso')
        
        # Crear el PDF
        response = HttpResponse(content_type='application/pdf')
        nombre_archivo = f"Certificado_{inscripcion.comision.fk_id_curso.nombre.replace(' ', '_')}_{estudiante.usuario.persona.dni}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        
        # Crear el documento PDF
        doc = SimpleDocTemplate(response, pagesize=A4)
        story = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#334155'),
            alignment=TA_JUSTIFY,
            spaceAfter=15,
            leading=20
        )
        
        # Logo
        logo_path = os.path.join(settings.STATIC_ROOT or settings.STATICFILES_DIRS[0], 'img', 'LOGO COLOR.png')
        if not os.path.exists(logo_path):
            # Intentar con STATICFILES_DIRS
            logo_path = os.path.join(settings.BASE_DIR, 'stc', 'img', 'LOGO COLOR.png')
        
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=3*inch, height=1*inch)
            logo.hAlign = 'CENTER'
            story.append(logo)
            story.append(Spacer(1, 0.3*inch))
        
        # Título del certificado
        story.append(Paragraph("CERTIFICADO DE FINALIZACIÓN", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Texto del certificado
        texto_certificado = f"""
        Por medio del presente, se certifica que <b>{estudiante.usuario.persona.nombre_completo}</b>, 
        con DNI <b>{estudiante.usuario.persona.dni}</b>, ha completado exitosamente el curso:
        """
        story.append(Paragraph(texto_certificado, body_style))
        story.append(Spacer(1, 0.1*inch))
        
        # Nombre del curso (destacado)
        curso_style = ParagraphStyle(
            'CursoStyle',
            parent=styles['Heading2'],
            fontSize=20,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        story.append(Paragraph(inscripcion.comision.fk_id_curso.nombre, curso_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Información adicional
        info_texto = f"""
        Habiendo cumplido con el <b>{registro.porcentaje_asistencia:.2f}%</b> de asistencia 
        ({registro.clases_asistidas} de {registro.total_clases} clases), 
        cumpliendo así con los requisitos establecidos para la obtención del presente certificado.
        """
        story.append(Paragraph(info_texto, body_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Fecha
        fecha_actual = datetime.now().strftime("%d de %B de %Y")
        fecha_texto = f"Emitido el {fecha_actual}"
        fecha_style = ParagraphStyle(
            'FechaStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#64748b'),
            alignment=TA_CENTER,
            spaceAfter=0.5*inch
        )
        story.append(Paragraph(fecha_texto, fecha_style))
        
        # Firma (espacio para firma)
        firma_data = [
            ['', ''],
            ['_________________________', '_________________________'],
            ['Agencia de Innovación', 'Director/a']
        ]
        firma_table = Table(firma_data, colWidths=[3*inch, 3*inch])
        firma_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#64748b')),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(firma_table)
        
        # Construir el PDF
        doc.build(story)
        
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
            estado='confirmado'
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
            estado='confirmado'
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


