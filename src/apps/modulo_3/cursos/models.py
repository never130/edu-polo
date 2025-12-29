from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db import models

from apps.modulo_1.usuario.models import Usuario

import re
import unicodedata


class PoloCreativo(models.Model):
    """Sedes físicas donde se imparten los cursos"""
    CIUDADES = [
        ('Ushuaia', 'Ushuaia'),
        ('Rio Grande', 'Río Grande'),
        ('Tolhuin', 'Tolhuin'),
    ]
    
    id_polo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Polo")
    ciudad = models.CharField(max_length=50, choices=CIUDADES, verbose_name="Ciudad")
    direccion = models.CharField(max_length=255, verbose_name="Dirección")
    telefono = models.CharField(max_length=15, blank=True, null=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    
    class Meta:
        verbose_name = "Polo Creativo"
        verbose_name_plural = "Polos Creativos"
        ordering = ['ciudad', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} - {self.ciudad}"

class Curso(models.Model):
    OPCIONES_ESTADO_CURSO = [
        ('Abierto', 'Abierto'), # Se pueden crear comisiones
        ('Cerrado', 'Cerrado'), # Es un curso histórico
    ]
    id_curso = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, null=False) 
    descripcion = models.TextField(blank=True, null=True) 
    edad_minima = models.IntegerField(blank=True, null=True, verbose_name="Edad Mínima") 
    edad_maxima = models.IntegerField(blank=True, null=True, verbose_name="Edad Máxima")
    requisitos = models.TextField(blank=True, null=True) 
    contenido_multimedia = models.URLField(max_length=255, blank=True, null=True) 
    estado = models.CharField(max_length=10, choices=OPCIONES_ESTADO_CURSO, default='Abierto')
    orden = models.IntegerField(default=0, verbose_name="Orden de Visualización", help_text="Número que determina el orden de visualización en el index (menor número = más arriba)")

    class Meta:
        ordering = ['orden', 'id_curso']

    def __str__(self):
        return self.nombre

class Comision(models.Model):
    """
    Instancia específica de un Curso con horarios, lugar y cupos definidos.
    Un curso puede tener múltiples comisiones.
    """
    OPCIONES_ESTADO_COMISION = [
        ('Abierta', 'Inscripción Abierta'),
        ('Cerrada', 'Inscripción Cerrada'),
        ('En proceso', 'En Proceso'),
        ('Finalizada', 'Finalizada'),
    ]
    
    MODALIDADES = [
        ('Presencial', 'Presencial'),
        ('Virtual', 'Virtual'),
        ('Hibrido', 'Híbrido'),
    ]
    
    id_comision = models.AutoField(primary_key=True)
    fk_id_curso = models.ForeignKey(Curso, on_delete=models.CASCADE, db_column='fk_id_curso', verbose_name="Curso") 
    fk_id_polo = models.ForeignKey(PoloCreativo, on_delete=models.SET_NULL, null=True, blank=True, related_name='comisiones', verbose_name="Polo Creativo")
    
    # Detalles de la comisión
    modalidad = models.CharField(max_length=15, choices=MODALIDADES, default='Presencial', verbose_name="Modalidad")
    dias_horarios = models.TextField(blank=True, null=True, verbose_name="Días y Horarios") 
    lugar = models.CharField(max_length=100, blank=True, null=True, verbose_name="Lugar") 
    fecha_inicio = models.DateField(blank=True, null=True, verbose_name="Fecha de Inicio") 
    fecha_fin = models.DateField(blank=True, null=True, verbose_name="Fecha de Fin") 
    cupo_maximo = models.IntegerField(default=25, verbose_name="Cupo Máximo") 
    estado = models.CharField(max_length=15, choices=OPCIONES_ESTADO_COMISION, default='Abierta', verbose_name="Estado") 

    docentes = models.ManyToManyField(
        Usuario, 
        through='ComisionDocente',
        related_name='comisiones_asignadas'
    )

    @staticmethod
    def _normalizar_texto(texto):
        if not texto:
            return ''
        normalized = unicodedata.normalize('NFKD', texto)
        normalized = ''.join(ch for ch in normalized if not unicodedata.combining(ch))
        return normalized.lower()

    def get_dias_semana_indices(self):
        texto = self._normalizar_texto(self.dias_horarios or '')
        if not texto:
            return set()

        tokens = set(re.findall(r"[a-z]+", texto))
        dias = set()

        if {'lunes', 'lun', 'lu'} & tokens:
            dias.add(0)
        if {'martes', 'mar', 'ma'} & tokens:
            dias.add(1)
        if {'miercoles', 'miércoles', 'mie', 'mi', 'x'} & tokens:
            dias.add(2)
        if {'jueves', 'jue', 'ju'} & tokens:
            dias.add(3)
        if {'viernes', 'vie', 'vi'} & tokens:
            dias.add(4)
        if {'sabado', 'sábado', 'sab', 'sa'} & tokens:
            dias.add(5)
        if {'domingo', 'dom'} & tokens:
            dias.add(6)

        return dias

    def get_fechas_clase_programadas(self, hasta=None):
        fecha_inicio = self.fecha_inicio
        if not fecha_inicio:
            try:
                from django.db.models import Min
                from apps.modulo_4.asistencia.models import Asistencia

                fecha_inicio = Asistencia.objects.filter(inscripcion__comision=self).aggregate(
                    Min('fecha_clase')
                )['fecha_clase__min']
            except Exception:
                fecha_inicio = None

        if not fecha_inicio:
            return []

        fecha_fin = self.fecha_fin or (hasta or date.today())
        if hasta and fecha_fin > hasta:
            fecha_fin = hasta
        if fecha_fin < fecha_inicio:
            return []

        dias = self.get_dias_semana_indices()
        if not dias:
            return []

        fechas = []
        current = fecha_inicio
        while current <= fecha_fin:
            if current.weekday() in dias:
                fechas.append(current)
            current = current + timedelta(days=1)
        return fechas

    def get_total_clases_programadas(self, hasta=None):
        fechas = self.get_fechas_clase_programadas(hasta=hasta)
        if not fechas:
            return None
        return len(fechas)

    def clean(self):
        super().clean()

        if self.fecha_inicio and self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValidationError({'fecha_fin': 'La fecha de fin no puede ser anterior a la fecha de inicio.'})

        if (self.fecha_inicio or self.fecha_fin) and not self.get_dias_semana_indices():
            raise ValidationError({'dias_horarios': 'Debe indicar días/horarios válidos para poder calcular el calendario de clases.'})

    def __str__(self):
        return f"{self.fk_id_curso.nombre} - (Comisión N°: {self.id_comision})"
    
    @property
    def inscritos_count(self):
        """Cuenta de estudiantes inscritos confirmados"""
        return self.inscripciones.filter(estado__in=['confirmado', 'pre_inscripto']).count()
    
    @property
    def cupos_disponibles(self):
        """Calcula cupos disponibles en tiempo real"""
        return max(self.cupo_maximo - self.inscritos_count, 0)
    
    @property
    def cupo_lleno(self):
        """Verifica si el cupo está completo"""
        return self.cupos_disponibles <= 0
    
    @property
    def cupos_limitados(self):
        """Verifica si quedan pocos cupos (≤5)"""
        return 0 < self.cupos_disponibles <= 5
    
    @property
    def porcentaje_ocupacion(self):
        """Calcula el porcentaje de ocupación"""
        if self.cupo_maximo == 0:
            return 0
        return int((self.inscritos_count / self.cupo_maximo) * 100)

class ComisionDocente(models.Model):
    # Tabla intermedia para asignar Docentes (Usuarios) a Comisiones
    fk_id_comision = models.ForeignKey(Comision, on_delete=models.CASCADE, db_column='fk_id_comision')
    # Usamos el modelo 'Usuario' que importamos
    fk_id_docente = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='fk_id_docente') 

    class Meta:
        unique_together = ('fk_id_comision', 'fk_id_docente') 

    def __str__(self):
        return f"{self.fk_id_comision} / {self.fk_id_docente}"

class Material(models.Model):
    # Modelo para "Gestión de Materiales" 
    TIPO_MATERIAL = [
        ('archivo', 'Archivo (PDF, etc.)'),
        ('enlace', 'Enlace/URL'),
    ]
    
    id_material = models.AutoField(primary_key=True)
    fk_id_comision = models.ForeignKey(Comision, on_delete=models.CASCADE, db_column='fk_id_comision')
    # Usamos el modelo 'Usuario' importado (el docente que lo sube)
    fk_id_docente = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, db_column='fk_id_docente')
    nombre_archivo = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    tipo = models.CharField(max_length=10, choices=TIPO_MATERIAL, default='archivo', verbose_name="Tipo de Material")
    archivo = models.FileField(upload_to='materiales_cursos/', blank=True, null=True) # Guarda el archivo en /media/materiales_cursos/
    enlace = models.URLField(max_length=500, blank=True, null=True, verbose_name="Enlace/URL")
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre_archivo
    
    def clean(self):
        """Validar que tenga archivo o enlace según el tipo"""
        from django.core.exceptions import ValidationError
        if self.tipo == 'archivo' and not self.archivo:
            raise ValidationError({'archivo': 'Debe subir un archivo para materiales de tipo archivo.'})
        if self.tipo == 'enlace' and not self.enlace:
            raise ValidationError({'enlace': 'Debe proporcionar un enlace para materiales de tipo enlace.'})
