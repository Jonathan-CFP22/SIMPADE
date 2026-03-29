""" from functools import wraps
from django.db.models import Count
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Usuario, Profesor, Institucion, Materia, AsignacionDocente, Division, Curso, Alumno, InformeTrimestral, Unidad, Tema, TemasTrimestre, DetalleEvaluacionTema

def login_requerido_custom(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if 'usuario_dni' not in request.session:
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def admin_requerido_custom(view_func):
    def _wrapped_view(request, *args, **kwargs):
        dni = request.session.get('usuario_dni')
        if not dni:
            return redirect('index')
        
        from .models import Usuario
        usuario = Usuario.objects.get(dni=dni)
        if not usuario.es_admin_sistema:
            return redirect('index') # O a una página de "No tienes permiso"
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def index(request):
    error_login = None
    dni_en_sesion = request.session.get('usuario_dni')
    
    if dni_en_sesion:
        try:
            usuario = Usuario.objects.get(dni=dni_en_sesion)

            if usuario.es_admin_sistema:
                return redirect('cp_admin')
            elif usuario.es_profesor:
                return redirect('panel_docente')
            elif usuario.es_alumno:
                return redirect('index')
                pass 
        except Usuario.DoesNotExist:
            request.session.flush()

    if request.method == 'POST':
        rol = request.POST.get('rol')
        
        if rol == 'staff':
            dni = request.POST.get('dni')
            clave = request.POST.get('clave')
        else:
            dni = request.POST.get('dni_alumno')
            clave = request.POST.get('clave_alumno')

        try:
            if not dni or not clave:
                error_login = "Por favor, completa todos los campos."
            else:
                usuario = Usuario.objects.get(dni=dni)
                if usuario.clave == clave:
                    request.session['usuario_dni'] = usuario.dni
                    request.session['usuario_nombre'] = usuario.nombre_completo
                    
                    if usuario.es_admin_sistema:
                        return redirect('cp_admin')
                    elif usuario.es_profesor:
                        return redirect('panel_docente')
                    elif usuario.es_alumno:
                        return redirect('index') 
                    else:
                        error_login = "Tu usuario no tiene un rol válido."
                else:
                    error_login = "La contraseña es incorrecta."
        except Usuario.DoesNotExist:
            error_login = f"El DNI {dni} no está registrado como {rol}."

    return render(request, 'index.html', {
        'ocultar_nav': True, 
        'error': error_login
    })

#####Alumno
def crear_alumno(request):
    error = None
    # Traemos las divisiones con su curso e institución para armar el selector
    divisiones = Division.objects.all().select_related('curso', 'institucion')
    
    if request.method == 'POST':
        dni = request.POST.get('dni')
        nombre_completo = request.POST.get('nombre_completo')
        email = request.POST.get('email')
        clave = request.POST.get('clave')
        division_id = request.POST.get('division')
        
        # Validación básica
        if not dni or not nombre_completo or not clave or not division_id:
            error = "Por favor, completá todos los campos obligatorios."
        elif Usuario.objects.filter(dni=dni).exists():
            error = f"El DNI {dni} ya está registrado en el sistema."
        else:
            # 1. Creamos el Usuario base
            usuario = Usuario.objects.create(
                dni=dni,
                nombre_completo=nombre_completo,
                email=email if email else None,
                clave=clave,
                es_alumno=True,
                rol_primario='Alumno'
            )
            
            # 2. Creamos el perfil de Alumno vinculado a la División
            division = Division.objects.get(id=division_id)
            Alumno.objects.create(
                usuario=usuario,
                division=division # O 'curso=division.curso' si no cambiaste el modelo aún
            )
            
            # Redirigimos al panel de admin 
            return redirect('index') # Ajustá el nombre si usás 'admin_panel'
            
    return render(request, 'crear_alumno.html', {
        'divisiones': divisiones,
        'error': error,
        'ocultar_nav':True,
    })

def logout(request):
    request.session.flush() # Borra toda la información de la sesión
    return redirect('index')

def registrar_docente(request):
    instituciones = Institucion.objects.all()
    
    if request.method == 'POST':
        dni = request.POST.get('dni')
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        clave = request.POST.get('clave')
        id_institucion = request.POST.get('institucion')

        # 1. VALIDACIÓN DE LONGITUD Y FORMATO
        if len(dni) > 8:
            return render(request, 'registro_docente.html', {
                'error': "El DNI no puede tener más de 8 caracteres.",
                'instituciones': instituciones, 'ocultar_nav': True
            })
        
        if not dni.isdigit():
             return render(request, 'registro_docente.html', {
                'error': "El DNI debe contener solo números.",
                'instituciones': instituciones, 'ocultar_nav': True
            })

        # 2. VALIDACIÓN DE DUPLICADOS (DNI)
        if Usuario.objects.filter(dni=dni).exists():
            return render(request, 'registro_docente.html', {
                'error': "El DNI ya se encuentra registrado en el sistema.",
                'instituciones': instituciones, 'ocultar_nav': True
            })

        # 3. VALIDACIÓN DE DUPLICADOS (EMAIL)
        if email and Usuario.objects.filter(email=email).exists():
            return render(request, 'registro_docente.html', {
                'error': "El correo electrónico ya está en uso por otro usuario.",
                'instituciones': instituciones, 'ocultar_nav': True
            })

        try:
            # Iniciamos la creación
            nuevo_usuario = Usuario.objects.create(
                dni=dni,
                nombre_completo=nombre,
                email=email,
                clave=clave,
                es_profesor=True,
                rol_primario="DOCENTE"  # Asegurate que coincida con tu limit_choices_to
            )

            # Vinculamos con la Institución a través del modelo Profesor
            inst = Institucion.objects.get(id=id_institucion)
            Profesor.objects.create(
                usuario=nuevo_usuario,
                institucion=inst
            )
            
            return redirect('cp_admin')

        except Exception as e:
            return render(request, 'registro_docente.html', {
                'error': f"Error al crear el docente: {e}",
                'instituciones': instituciones, 'ocultar_nav': True
            })

    return render(request, 'registro_docente.html', {
        'instituciones': instituciones, 
        'ocultar_nav': True
    })

def reg_docente_cp(request):
    instituciones = Institucion.objects.all()
    
    if request.method == 'POST':
        dni = request.POST.get('dni')
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        clave = request.POST.get('clave')
        id_institucion = request.POST.get('institucion')

        # 1. VALIDACIÓN DE LONGITUD Y FORMATO
        if len(dni) > 8:
            return redirect('cp_admin', {
                'error': "El DNI no puede tener más de 8 caracteres.",
                'instituciones': instituciones, 'ocultar_nav': True
            })
        
        if not dni.isdigit():
             return redirect(cp_admin, {
                'error': "El DNI debe contener solo números.",
                'instituciones': instituciones, 'ocultar_nav': True
            })

        # 2. VALIDACIÓN DE DUPLICADOS (DNI)
        if Usuario.objects.filter(dni=dni).exists():
            return redirect(cp_admin, {
                'error': "El DNI ya se encuentra registrado en el sistema.",
                'instituciones': instituciones, 'ocultar_nav': True
            })

        # 3. VALIDACIÓN DE DUPLICADOS (EMAIL)
        if email and Usuario.objects.filter(email=email).exists():
            return redirect(cp_admin, {
                'error': "El correo electrónico ya está en uso por otro usuario.",
                'instituciones': instituciones, 'ocultar_nav': True
            })

        try:
            # Iniciamos la creación
            nuevo_usuario = Usuario.objects.create(
                dni=dni,
                nombre_completo=nombre,
                email=email,
                clave=clave,
                es_profesor=True,
                rol_primario="DOCENTE"  # Asegurate que coincida con tu limit_choices_to
            )

            # Vinculamos con la Institución a través del modelo Profesor
            inst = Institucion.objects.get(id=id_institucion)
            Profesor.objects.create(
                usuario=nuevo_usuario,
                institucion=inst
            )
            
            return redirect('cp_admin')

        except Exception as e:
            return redirect(cp_admin, {
                'error': f"Error al crear el docente: {e}",
                'instituciones': instituciones, 'ocultar_nav': True
            })

    return redirect(cp_admin)

@admin_requerido_custom
def asignar_docente(request):
    docentes = Usuario.objects.filter(es_profesor=True)
    materias = Materia.objects.all()
    divisiones = Division.objects.select_related('institucion', 'curso').all().order_by('institucion__nombre', 'curso__nombre')

    if request.method == 'POST':
        docente_id = request.POST.get('docente')
        materia_id = request.POST.get('materia')
        division_id = request.POST.get('division')
        ciclo = request.POST.get('ciclo', 2026)
        existe = AsignacionDocente.objects.filter(
            docente_id=docente_id,
            materia_id=materia_id,
            division_id=division_id,
            ciclo_lectivo=ciclo
        ).exists()
        if existe:
            # Si ya existe, mandamos el error de vuelta al HTML
            return render(request, 'adminboard/asignar_docente.html', {
                'error': "Error: Este docente ya está asignado a esa materia en esa división para este ciclo lectivo.",
                'docentes': Usuario.objects.filter(es_profesor=True),
                'materias': Materia.objects.all(),
                'divisiones': Division.objects.all(),
            })
        if docente_id and materia_id and division_id:
            # get_or_create con la nueva lógica
            asignacion, created = AsignacionDocente.objects.get_or_create(
                materia_id=materia_id,
                division_id=division_id,
                ciclo_lectivo=ciclo,
                defaults={'docente_id': docente_id} # Si no existe, lo crea con este docente
            )
            
            if not created:
                # Si ya existe, podemos actualizar el docente (por si cambió)
                asignacion.docente_id = docente_id
                asignacion.save()
            
            return redirect('cp_admin')

    return render(request, 'adminboard/asignar_docente.html', {
        'docentes': docentes,
        'materias': materias,
        'divisiones': divisiones
    })

@admin_requerido_custom
def eliminar_asignacion(request, asignacion_id):
    # Busca la asignación por su ID y la borra
    asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id)
    asignacion.delete()
    return redirect('cp_admin')

@admin_requerido_custom
def cp_admin(request):
    dni_sesion = request.session.get('usuario_dni')
    
    if not dni_sesion:
        return redirect('index') # Si no hay sesión, al login
    
    usuario = get_object_or_404(Usuario, dni=dni_sesion)
    
    # 2. Verificamos que sea realmente un admin
    if not usuario.es_admin_sistema:
        return redirect('index')

    # Consultas a la base de datos
    cursos = Curso.objects.all() 
    divisiones = Division.objects.all().select_related('curso', 'institucion')
    docentes = Profesor.objects.all()
    instituciones = Institucion.objects.all()
    materias = Materia.objects.all()
    materias_con_temarios = Materia.objects.prefetch_related('unidad_set__temas_unidad').all()
    asignaciones = AsignacionDocente.objects.all().select_related(
        'docente', 'materia', 'division__curso', 'division__institucion'
    )
    context = {
        'docentes': docentes, 
        'instituciones': instituciones,
        'materias': materias, 
        'cursos': cursos,
        'divisiones': divisiones,
        'materias_con_temarios': materias_con_temarios,
        'asignaciones': asignaciones
    }
    
    return render(request, 'adminboard/index.html', context)

# Función rápida para eliminar
def eliminar_docente(request, dni):
    usuario = Usuario.objects.get(dni=dni)
    usuario.delete() # Esto borra en cascada al Profesor
    return redirect('cp_admin')

@admin_requerido_custom # Solo el admin puede editar
def mod_docente(request, dni):
    usuario = get_object_or_404(Usuario, dni=dni)
    profesor = get_object_or_404(Profesor, usuario=usuario)
    instituciones = Institucion.objects.all()

    if request.method == 'POST':
        # 1. Capturamos los datos del formulario
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        id_inst = request.POST.get('institucion')
        
        # 2. Actualizamos el objeto Usuario
        usuario.nombre_completo = nombre
        usuario.email = email
        usuario.save()

        # 3. Actualizamos la Institución en el perfil de Profesor
        nueva_inst = Institucion.objects.get(id=id_inst)
        profesor.institucion = nueva_inst
        profesor.save()

        return redirect('cp_admin') # Volvemos al panel tras guardar

    # Si es GET, simplemente mostramos el form
    return render(request, 'adminboard/mod_docente.html', {
        'usuario': usuario, 
        'profesor': profesor, 
        'instituciones': instituciones
    })

def eliminar_institucion(request, id_inst):
    inst = Institucion.objects.get(id=id_inst)
    inst.delete()
    return redirect('cp_admin')

def crear_institucion(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        direccion = request.POST.get('direccion')
        
        if nombre:
            Institucion.objects.create(
                nombre=nombre,
                direccion=direccion
            )
    return redirect('cp_admin')

@admin_requerido_custom
def editar_institucion(request, id_inst):
    # Buscamos la institución por su ID único
    institucion = get_object_or_404(Institucion, id=id_inst)
    
    if request.method == 'POST':
        # Capturamos los nuevos datos del formulario
        nombre = request.POST.get('nombre')
        direccion = request.POST.get('direccion')
        
        # Actualizamos el objeto y guardamos en la BD
        if nombre:
            institucion.nombre = nombre
            institucion.direccion = direccion
            institucion.save()
            return redirect('cp_admin') # Volvemos a la lista general
            
    # Si entramos por primera vez, mostramos el formulario con los datos actuales
    return render(request, 'adminboard/mod_insti.html', {'institucion': institucion})

@admin_requerido_custom
def crear_curso(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre') # Ej: "1ro", "2do"
        if nombre:
            Curso.objects.get_or_create(nombre=nombre)
            return redirect('cp_admin')
    return render(request, 'adminboard/crear_curso.html')

@admin_requerido_custom
def crear_division(request):
    cursos = Curso.objects.all()
    instituciones = Institucion.objects.all()
    
    if request.method == 'POST':
        nombre_div = request.POST.get('nombre') # Ej: "A", "B", "1ra"
        curso_id = request.POST.get('curso')
        inst_id = request.POST.get('institucion')
        
        if nombre_div and curso_id and inst_id:
            Division.objects.get_or_create(
                nombre=nombre_div,
                curso_id=curso_id,
                institucion_id=inst_id
            )
            return redirect('cp_admin')
            
    return render(request, 'adminboard/crear_divison.html', {
        'cursos': cursos,
        'instituciones': instituciones
    })

@admin_requerido_custom
def gestionar_temarios(request):
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion == 'crear_unidad':
            materia_id = request.POST.get('materia_id')
            nro_unidad = request.POST.get('nro_unidad')
            nombre_unidad = request.POST.get('nombre_unidad')
            
            if materia_id and nro_unidad and nombre_unidad:
                materia = Materia.objects.get(id=materia_id)
                
                # VERIFICACIÓN: Evitamos que se duplique la unidad en la materia
                if Unidad.objects.filter(materia=materia, nro_unidad=nro_unidad).exists():
                    messages.error(request, f"Error: La Unidad {nro_unidad} ya existe en {materia.nombre}.")
                else:
                    Unidad.objects.create(
                        materia=materia, 
                        nro_unidad=nro_unidad, 
                        nombre_unidad=nombre_unidad
                    )
                    messages.success(request, f"Unidad {nro_unidad} creada correctamente.")
                
        elif accion == 'crear_tema':
            unidad_id = request.POST.get('unidad_id')
            nombre_tema = request.POST.get('nombre_tema')
            
            if unidad_id and nombre_tema:
                unidad = Unidad.objects.get(id=unidad_id)
                
                # VERIFICACIÓN: Evitamos que se duplique el tema en la misma unidad
                # usamos __iexact para que "Tema 1" y "tema 1" cuenten como el mismo
                if Tema.objects.filter(unidad=unidad, nombre_tema__iexact=nombre_tema).exists():
                    messages.warning(request, f"El tema '{nombre_tema}' ya está registrado en esta unidad.")
                else:
                    Tema.objects.create(
                        unidad=unidad, 
                        nombre_tema=nombre_tema
                    )
                    messages.success(request, "Tema agregado correctamente.")
                
        return redirect('gestionar_temarios')

    # Traemos las materias simples para el formulario
    materias_simples = Materia.objects.all()
    
    # Traemos las materias con sus temarios. 
    # Usamos .distinct() para evitar que el QuerySet te devuelva materias duplicadas en el GET
    materias_con_temarios = Materia.objects.prefetch_related('unidad_set__temas_unidad').distinct()

    # CORRECCIÓN DE VARIABLES: Ahora los nombres coinciden con lo que pide el HTML
    contexto = {
        'materias_simples': materias_simples,
        'materias_con_temarios': materias_con_temarios, 
    }

    return render(request, 'adminboard/gestionar_temarios.html', contexto)

@admin_requerido_custom
def eliminar_unidad(request, unidad_id):
    unidad = get_object_or_404(Unidad, id=unidad_id)
    nombre = unidad.nombre_unidad
    # Al eliminar la unidad, Django eliminará automáticamente sus temas por el on_delete=models.CASCADE
    unidad.delete()
    messages.success(request, f"La unidad '{nombre}' y todos sus temas fueron eliminados.")
    return redirect('gestionar_temarios')

@admin_requerido_custom
def eliminar_tema(request, tema_id):
    tema = get_object_or_404(Tema, id=tema_id)
    nombre = tema.nombre_tema
    tema.delete()
    messages.success(request, f"El tema '{nombre}' fue eliminado.")
    return redirect('gestionar_temarios')

@admin_requerido_custom
def add_materia(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        orientacion = request.POST.get('orientacion')
        
        if nombre and orientacion:
            # Django ejecutará el método save() y creará el código solo
            Materia.objects.create(
                nombre=nombre,
                orientacion=orientacion
            )
            return redirect('cp_admin') # Volvemos al panel principal
            
    return render(request, 'adminboard/add_materia.html', {'orientaciones': Materia.ORIENTACIONES})

#Panel docente


def docente_requerido(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        dni_sesion = request.session.get('usuario_dni')
        if not dni_sesion:
            return redirect('index')
        
        usuario = get_object_or_404(Usuario, dni=dni_sesion)
        
        if not usuario.es_profesor and not usuario.es_admin_sistema:
            return redirect('index')
            
        try:
            usuario = Usuario.objects.get(dni=dni_sesion)
            # Verificamos que tenga el tilde de profesor
            if not usuario.es_profesor:
                return redirect('login') # O podés redirigirlo a un 'acceso_denegado'
                
            # Pasamos el objeto usuario a la request para usarlo en la vista fácilmente
            request.usuario_actual = usuario 
            return view_func(request, *args, **kwargs)
            
        except Usuario.DoesNotExist:
            return redirect('login')
            
    return _wrapped_view

@docente_requerido
def panel_docente(request):
    docente = request.usuario_actual
    
    asignaciones_totales = AsignacionDocente.objects.filter(docente=docente).select_related(
        'materia', 'division', 'division__curso', 'division__institucion'
    )
    
    instituciones_ids = asignaciones_totales.values_list('division__institucion', flat=True).distinct()
    instituciones = Institucion.objects.filter(id__in=instituciones_ids)
    
    inst_id = request.GET.get('inst')
    institucion_seleccionada = None
    asignaciones_filtradas = None
    
    if inst_id:
        institucion_seleccionada = Institucion.objects.filter(id=inst_id).first()
        if institucion_seleccionada:
            # Traemos las asignaciones de esta escuela
            asignaciones_filtradas = asignaciones_totales.filter(division__institucion_id=inst_id)
            
            # MAGIA AQUÍ: Calculamos el estado del 1° Trimestre para cada materia
            for asig in asignaciones_filtradas:
                # 1. Buscamos los alumnos de esa división (ajustá 'division=' según tu modelo Alumno)
                alumnos_division = Alumno.objects.filter(division=asig.division)
                total_alumnos = alumnos_division.count()
                
                # 2. Contamos cuántos informes del Trimestre 1 ya existen para esta materia y estos alumnos
                informes_cargados = InformeTrimestral.objects.filter(
                    materia=asig.materia,
                    trimestre=1,
                    alumno__in=alumnos_division
                ).count()
                
                # 3. Guardamos variables temporales en el objeto 'asig' para usarlas en el HTML
                asig.total_alumnos = total_alumnos
                asig.informes_cargados = informes_cargados
                # Si hay alumnos y ya cargó todos los informes, se bloquea:
                asig.trim_1_completo = (total_alumnos > 0 and informes_cargados >= total_alumnos)

    contexto = {
        'docente': docente,
        'instituciones': instituciones,
        'institucion_seleccionada': institucion_seleccionada,
        'asignaciones_filtradas': asignaciones_filtradas
    }
    return render(request, 'panel_docente.html', contexto)

@docente_requerido
def lista_alumnos_informe(request, asignacion_id, trimestre):
    asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id, docente=request.usuario_actual)
    
    temas_trimestre, created = TemasTrimestre.objects.get_or_create(
        asignacion=asignacion,
        trimestre=trimestre
    )
    
    # Verificamos si ya hay temas ANTES de procesar el POST
    tiene_temas_cargados = temas_trimestre.temas_dados.exists()

    if request.method == 'POST':
        # Candado de seguridad: si ya tiene temas, rechazamos el POST
        if tiene_temas_cargados:
            messages.error(request, "Los temas de este trimestre ya fueron guardados y no se pueden modificar.")
        else:
            temas_seleccionados_ids = request.POST.getlist('temas_dados')
            if temas_seleccionados_ids: # Validamos que haya marcado al menos uno
                temas_trimestre.temas_dados.set(temas_seleccionados_ids)
                messages.success(request, "¡Temas guardados exitosamente! Ya puedes evaluar a los alumnos.")
            else:
                messages.warning(request, "Debes seleccionar al menos un tema antes de guardar.")
                
        return redirect('lista_alumnos_informe', asignacion_id=asignacion.id, trimestre=trimestre)

    unidades_materia = Unidad.objects.filter(materia=asignacion.materia).prefetch_related('temas_unidad').order_by('nro_unidad')
    temas_dados_ids = temas_trimestre.temas_dados.values_list('id', flat=True)
    # Volvemos a consultar por si se acaba de guardar en el POST
    tiene_temas_cargados = temas_trimestre.temas_dados.exists()

    alumnos = Alumno.objects.filter(division=asignacion.division).order_by('usuario__nombre_completo')
    
    informes_existentes = InformeTrimestral.objects.filter(
        materia=asignacion.materia,
        trimestre=trimestre,
        alumno__in=alumnos
    )
    alumnos_con_nota = informes_existentes.values_list('alumno_id', flat=True)

    contexto = {
        'asignacion': asignacion,
        'trimestre': trimestre,
        'alumnos': alumnos,
        'alumnos_con_nota': alumnos_con_nota,
        'unidades_materia': unidades_materia,
        'temas_dados_ids': temas_dados_ids,
        'tiene_temas_cargados': tiene_temas_cargados,
    }
    return render(request, 'lista_alumnos_informe.html', contexto)

@docente_requerido
def evaluar_alumno(request, asignacion_id, trimestre, alumno_id):
    asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id, docente=request.usuario_actual)
    alumno = get_object_or_404(Alumno, id=alumno_id, division=asignacion.division)
    
    # 1. Buscamos los temas que el profe seleccionó para este trimestre
    temas_trimestre = get_object_or_404(TemasTrimestre, asignacion=asignacion, trimestre=trimestre)
    temas_disponibles = temas_trimestre.temas_dados.all() 

    if request.method == 'POST':
        # 1. Capturamos los porcentajes totales ocultos que calculó JavaScript
        porcentaje_final = request.POST.get('porcentaje_final', 0)
        porcentaje_rubrica = request.POST.get('porcentaje_rubrica_final', 0)

        # 2. Creamos o actualizamos el informe general
        informe, created = InformeTrimestral.objects.update_or_create(
            alumno=alumno,
            materia=asignacion.materia,
            trimestre=trimestre,
            defaults={
                'porcentaje_final_trimestre': porcentaje_final,
                'porcentaje_rubrica_docente': porcentaje_rubrica,
                'fecha_trimestre_completada': True
            }
        )

        # Limpiamos evaluaciones viejas de este informe por si el docente está re-guardando
        informe.detalles_temas.all().delete()

        # 3. Recorremos cada tema de la tabla y guardamos sus datos fila por fila
        for tema in temas_disponibles:
            eval_fecha = request.POST.get(f'evaluado_{tema.id}') == 'SI'
            tpi = request.POST.get(f'tpi_{tema.id}') == 'SI'
            
            reconoce = request.POST.get(f'reconoce_{tema.id}') == 'SI'
            utiliza = request.POST.get(f'utiliza_{tema.id}') == 'SI'
            contextualiza = request.POST.get(f'contextualiza_{tema.id}') == 'SI'
            
            estado = request.POST.get(f'estado_{tema.id}')
            observacion = request.POST.get(f'observacion_{tema.id}', '')

            # Creamos el detalle de esa fila
            DetalleEvaluacionTema.objects.create(
                informe=informe,
                tema=tema,
                evaluado_fecha=eval_fecha,
                tpi=tpi,
                reconoce=reconoce,
                utiliza=utiliza,
                contextualiza=contextualiza,
                estado=estado,
                observacion=observacion
            )

        messages.success(request, f"¡Informe guardado con éxito para {alumno.usuario.nombre_completo}!")
        return redirect('lista_alumnos_informe', asignacion_id=asignacion.id, trimestre=trimestre)

    contexto = {
        'asignacion': asignacion,
        'trimestre': trimestre,
        'alumno': alumno,
        'temas_disponibles': temas_disponibles
    }
    return render(request, 'evaluar_alumno.html', contexto)



##################Estadisticas
def estadisticas_institucionales(request):
    # 1. Validar sesión
    dni_sesion = request.session.get('usuario_dni')
    if not dni_sesion: 
        return redirect('index')
    
    # --- GRÁFICO 1: TEMAS (EL QUE YA TENÍAS) ---
    stats_temas = DetalleEvaluacionTema.objects.values('estado').annotate(total=Count('id'))
    labels_temas = []
    data_temas = []
    for item in stats_temas:
        nombre = item['estado'].replace('_', ' ').capitalize() if item['estado'] else "Pendiente"
        labels_temas.append(nombre)
        data_temas.append(item['total'])

    # --- GRÁFICO 2: ALUMNOS (PERSONAS) ---
    informes = InformeTrimestral.objects.all()
    conteo_alumnos = {'Alcanzado': 0, 'En Proceso': 0, 'Sin Evaluar': 0}

    for inf in informes:
        temas = DetalleEvaluacionTema.objects.filter(informe=inf)
        if not temas.exists():
            conteo_alumnos['Sin Evaluar'] += 1
        else:
            # Lógica: Si tiene algún "EN_PROCESO", el alumno todavía no alcanzó el total
            estados = temas.values_list('estado', flat=True)
            if 'EN_PROCESO' in estados:
                conteo_alumnos['En Proceso'] += 1
            else:
                conteo_alumnos['Alcanzado'] += 1

    return render(request, 'estadisticas.html', {
        'labels_temas': labels_temas,
        'data_temas': data_temas,
        'labels_alumnos': list(conteo_alumnos.keys()),
        'data_alumnos': list(conteo_alumnos.values()),
        'total_alumnos': informes.count()
    })  """