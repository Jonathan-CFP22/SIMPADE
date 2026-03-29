from django.db import models

# --- 1. USUARIOS Y ROLES ---
class Usuario(models.Model):
    dni = models.CharField(max_length=8, primary_key=True)
    nombre_completo = models.CharField(max_length=150)
    clave = models.CharField(max_length=128)
    email = models.EmailField(max_length=255, unique=True, null=True, blank=True)
    es_director = models.BooleanField(default=False)
    es_admin_sistema = models.BooleanField(default=False)
    es_profesor = models.BooleanField(default=False)
    es_preceptor = models.BooleanField(default=False)
    es_alumno = models.BooleanField(default=False)
    rol_primario = models.CharField(max_length=50)
    def __str__(self): return f"{self.nombre_completo} ({self.dni})"

# --- 2. INSTITUCIONAL ---
class Institucion(models.Model):
    nombre = models.CharField(max_length=200)
    direccion = models.CharField(max_length=255)

class Curso(models.Model):
    nombre = models.CharField(max_length=50) 
    
    def __str__(self):
        return self.nombre
    
class Division(models.Model):
    # Ej: "A", "B", "1ra"
    nombre = models.CharField(max_length=10)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    institucion = models.ForeignKey(Institucion, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('nombre', 'curso', 'institucion')

    def __str__(self):
        return f"{self.curso.nombre} '{self.nombre}' - {self.institucion.nombre}"

class Alumno(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='alumnos', null=True, blank=True)
    def __str__(self):
        return f"{self.usuario.nombre_completo} - {self.division}"

class Materia(models.Model):
    ORIENTACIONES = [
        ('BASICO', 'Ciclo Básico'),
        ('ECONOMIA', 'Economía y Administración'),
        ('NATURALES', 'Ciencias Naturales'),
        ('SOCIALES', 'Ciencias Sociales'),
        ('INFORMATICA', 'Informática'),
        ('ARTE', 'Arte'),
    ]

    nombre = models.CharField(max_length=100)
    # Lo dejamos como editable=False para que no aparezca en los formularios
    codigo = models.CharField(max_length=20, unique=True, editable=False)
    orientacion = models.CharField(max_length=50, choices=ORIENTACIONES, default='BASICO')

    def save(self, *args, **kwargs):
        if not self.codigo:
            # Generamos un código: MAT-ECO-123 (Primeras 3 letras de cada uno)
            prefix_nom = self.nombre[:3].upper()
            prefix_ori = self.orientacion[:3].upper()
            # Agregamos un sufijo aleatorio o el ID si existiera para evitar choques
            import random
            num = random.randint(100, 999)
            self.codigo = f"{prefix_nom}-{prefix_ori}-{num}"
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.codigo}) ({self.get_orientacion_display()})"
    
class AsignacionDocente(models.Model):
    docente = models.ForeignKey('Usuario', on_delete=models.CASCADE, limit_choices_to={'rol_primario': 'DOCENTE'})
    materia = models.ForeignKey('Materia', on_delete=models.CASCADE)
    division = models.ForeignKey(Division, on_delete=models.CASCADE) 
    ciclo_lectivo = models.IntegerField(default=2026) 
    observaciones = models.TextField(blank=True, null=True)
    trimestre_1_habilitado = models.BooleanField(default=True)
    trimestre_2_habilitado = models.BooleanField(default=False)
    trimestre_3_habilitado = models.BooleanField(default=False)
    trimestre_4_habilitado = models.BooleanField(default=False)

    # Control de Cierre (Lo que el docente marca como finalizado)
    trimestre_1_finalizado = models.BooleanField(default=False)
    trimestre_2_finalizado = models.BooleanField(default=False)
    trimestre_3_finalizado = models.BooleanField(default=False)
    trimestre_4_finalizado = models.BooleanField(default=False)
    class Meta:
        # Evita que asignes el mismo docente a la misma materia en la misma institución dos veces
        unique_together = ('materia', 'division', 'ciclo_lectivo')
        verbose_name = "Asignación de Docente"
        verbose_name_plural = "Asignaciones de Docentes"

    def __str__(self):
        return f"{self.materia.nombre} en {self.division} ({self.docente.nombre_completo})"

class Profesor(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    institucion = models.ForeignKey(Institucion, on_delete=models.CASCADE)

class Preceptor(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    institucion = models.ForeignKey(Institucion, on_delete=models.CASCADE)

# --- 3. CONTENIDOS Y PLANIFICACIÓN ---
class Unidad(models.Model):
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    nro_unidad = models.IntegerField()
    nombre_unidad = models.CharField(max_length=200)

class Tema(models.Model):
    unidad = models.ForeignKey(Unidad, on_delete=models.CASCADE, related_name='temas_unidad')
    nombre_tema = models.CharField(max_length=200)

class TemasTrimestre(models.Model):
    asignacion = models.ForeignKey(AsignacionDocente, on_delete=models.CASCADE)
    trimestre = models.IntegerField()
    temas_dados = models.ManyToManyField(Tema, blank=True)

    class Meta:
        unique_together = ('asignacion', 'trimestre')

    def __str__(self):
        return f"Temas de {self.asignacion} - Trimestre {self.trimestre}"

class LibroDeTema(models.Model):
    TRIMESTRES = [(1, '1° Trim'), (2, '2° Trim'), (3, '3° Trim'), (4, '4° Trim')]
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE)
    trimestre_dictado = models.IntegerField(choices=TRIMESTRES)
    fecha_dictado = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"T{self.trimestre_dictado} - {self.tema.nombre_tema}"

# --- 4. EL INFORME (Con guardado individual de temas) ---
class InformeTrimestral(models.Model):
    TRIMESTRES = [(1, '1° Trim'), (2, '2° Trim'), (3, '3° Trim'), (4, '4° Trim')]
    # AVANCE lo pasamos al detalle de abajo, pero lo dejamos acá si querés mantener datos viejos.

    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    trimestre = models.IntegerField(choices=TRIMESTRES)
    
    # Control Docente
    fecha_trimestre_completada = models.BooleanField(default=False)
    trabajo_integrador_entregado = models.BooleanField(default=False)

    # Porcentajes (Ahora vienen calculados del HTML)
    porcentaje_rubrica_docente = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    porcentaje_final_trimestre = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # IMPORTANTE: A estos campos viejos les ponemos null=True, blank=True 
    # para que no tiren el error "NOT NULL constraint failed"
    registro_avance = models.CharField(max_length=20, null=True, blank=True)
    observaciones = models.CharField(max_length=255, null=True, blank=True)
    d_reconoce = models.BooleanField(default=False)
    d_utiliza = models.BooleanField(default=False)
    d_contextualiza = models.BooleanField(default=False)

    class Meta:
        unique_together = ('alumno', 'materia', 'trimestre')

class DetalleEvaluacionTema(models.Model):
    informe = models.ForeignKey(InformeTrimestral, on_delete=models.CASCADE, related_name='detalles_temas')
    
    # ¡AQUÍ ESTÁ EL CAMBIO! Cambiamos LibroDeTema por Tema
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE) 
    
    evaluado_fecha = models.BooleanField(default=False)
    tpi = models.BooleanField(default=False)
    
    reconoce = models.BooleanField(default=False)
    utiliza = models.BooleanField(default=False)
    contextualiza = models.BooleanField(default=False)
    
    estado = models.CharField(max_length=20, choices=[('ALCANZADO', 'Alcanzado'), ('EN_PROCESO', 'En proceso')])
    observacion = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.tema} - {self.informe.alumno}"