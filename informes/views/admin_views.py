from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from ..decorators import admin_required
from ..models import Usuario, Profesor, Materia, AsignacionDocente, Curso,  Unidad, Tema, Division,  Institucion, Alumno

@admin_required
def cp_admin(request):
    dni_sesion = request.session.get('usuario_dni')
    if not dni_sesion:
        return redirect('index')
    usuario = get_object_or_404(Usuario, dni=dni_sesion)
    if not usuario.es_admin_sistema:
        return redirect('index')
    usuario = Usuario.objects.all()
    cursos = Curso.objects.all() 
    divisiones = Division.objects.all().select_related('curso', 'institucion')
    docentes = Profesor.objects.all()
    alumnos = Alumno.objects.all()
    instituciones = Institucion.objects.all()
    materias = Materia.objects.all()
    materias_con_temarios = Materia.objects.prefetch_related('unidad_set__temas_unidad').all()
    asignaciones = AsignacionDocente.objects.all()
    orientaciones = Materia.ORIENTACIONES
    context = {'docentes': docentes,'instituciones': instituciones,'materias': materias,'cursos': cursos,'divisiones': divisiones,'materias_con_temarios': materias_con_temarios,'asignaciones': asignaciones,'orientaciones': orientaciones, 'alumnos': alumnos, 'usuario': usuario}
    return render(request, 'adminboard/index.html', context)

@admin_required
def add_alumno(request):
    error = None
    divisiones = Division.objects.all().select_related('curso', 'institucion')
    if request.method == 'POST':
        dni = request.POST.get('dni')
        nombre_completo = request.POST.get('nombre_completo')
        email = request.POST.get('email')
        clave = request.POST.get('clave')
        division_id = request.POST.get('division')

        if not dni or not nombre_completo or not clave or not division_id:
            messages.error(request, "Faltan datos.")
            return redirect(reverse('cp_admin') + '?tab=alumnos')
        elif Usuario.objects.filter(dni=dni).exists():
            messages.error(request, f"El {dni} ya se encuetra registrado.")
            return redirect(reverse('cp_admin') + '?tab=alumnos')
        elif Usuario.objects.filter(email=email).exists():
            messages.error(request, f"El {email} ya se encuetra registrado.")
            return redirect(reverse('cp_admin') + '?tab=alumnos')
        else:
            usuario = Usuario.objects.create(dni=dni,nombre_completo=nombre_completo,email=email if email else None,clave=clave,es_alumno=True,rol_primario='Alumno')

            division = Division.objects.get(id=division_id)
            Alumno.objects.create(usuario=usuario,division=division)

            return redirect(reverse('cp_admin') + '?tab=alumnos')
            
    return render(request, 'adminboard/index.html', {'divisiones': divisiones})

@admin_required
def mod_alumno(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)
    usuario = alumno.usuario

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        division_id = request.POST.get('division')
        nueva_clave = request.POST.get('clave')

        try:
            usuario.nombre_completo = nombre
            if nueva_clave and nueva_clave.strip():
                usuario.clave = nueva_clave
            usuario.save()

            nueva_div = get_object_or_404(Division, id=division_id)
            alumno.division = nueva_div
            alumno.save()

            messages.success(request, f"Alumno {nombre} actualizado correctamente.")
        except Exception as e:
            messages.error(request, f"Error al actualizar: {e}")

        return redirect(reverse('cp_admin') + '?tab=alumnos')

    return redirect('cp_admin')

@admin_required
def eliminar_alumno(request, alumno_id):
    alumno = get_object_or_404(Alumno, id=alumno_id)
    try:
        nombre = alumno.usuario.nombre_completo
        alumno.usuario.delete() 
        messages.success(request, f"El alumno {nombre} y su cuenta de usuario han sido eliminados.")
    except Exception as e:
        messages.error(request, f"Error al eliminar: {e}")
    
    return redirect(reverse('cp_admin') + '?tab=alumnos')

@admin_required
def reg_docente_cp(request):
    instituciones = Institucion.objects.all()
    if request.method == 'POST':
        dni = request.POST.get('dni')
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        clave = request.POST.get('clave')
        id_institucion = request.POST.get('institucion')
        if len(dni) > 8:
            messages.error(request, "El DNI tiene que ser de 8 números.")
            return redirect(reverse('cp_admin') + '?tab=docentes')
        if not dni.isdigit():
            messages.error(request, "El DNI solo puede tener números.")
            return redirect(reverse('cp_admin') + '?tab=docentes')
        if Usuario.objects.filter(dni=dni).exists():
            messages.error(request, "El DNI ya se encuentra registrado en el sistema.")
            return redirect(reverse('cp_admin') + '?tab=docentes')
        if email and Usuario.objects.filter(email=email).exists():
            messages.error(request, "El Mail ya se encuentra registrado en el sistema.")
            return redirect(reverse('cp_admin') + '?tab=docentes')
        try:
            nuevo_usuario = Usuario.objects.create(dni=dni,nombre_completo=nombre,email=email,clave=clave,es_profesor=True,rol_primario="DOCENTE")
            inst = Institucion.objects.get(id=id_institucion)
            Profesor.objects.create(usuario=nuevo_usuario,institucion=inst)
            return redirect('cp_admin')
        except Exception as e:
            return redirect(cp_admin, {'error': f"Error al crear el docente: {e}",'instituciones': instituciones, 'ocultar_nav': True})
    return redirect(cp_admin)

@admin_required
def eliminar_docente(request, dni):
    usuario = Usuario.objects.get(dni=dni)
    usuario.delete()
    return redirect('cp_admin')

@admin_required
def mod_docente(request, dni):
    usuario = get_object_or_404(Usuario, dni=dni)
    profesor = get_object_or_404(Profesor, usuario=usuario)
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        nueva_clave = request.POST.get('clave')
        usuario.nombre_completo = nombre
        usuario.email = email
        if nueva_clave and nueva_clave.strip():
            usuario.clave = nueva_clave 
        
        try:
            usuario.save()
            profesor.save()   
            messages.success(request, f"Docente {nombre} actualizado con éxito.")
            return redirect(reverse('cp_admin') + '?tab=docentes')
        except Exception as e:
            messages.error(request, f"Error al actualizar: {e}")

    return redirect('cp_admin')

@admin_required
def asignar_docente(request):

    if request.method == 'POST':
        docente_id = request.POST.get('docente')
        materia_id = request.POST.get('materia')
        division_id = request.POST.get('division')
        ciclo = request.POST.get('ciclo', 2026)
        existe = AsignacionDocente.objects.filter(docente_id=docente_id,materia_id=materia_id,division_id=division_id,ciclo_lectivo=ciclo).exists()
        if existe:
            messages.error(request, "Error: Este docente ya tiene esta asignación para el ciclo actual.")
            return redirect(reverse('cp_admin') + '?tab=asignaciones')
        if docente_id and materia_id and division_id:
            asignacion, created = AsignacionDocente.objects.get_or_create(materia_id=materia_id,division_id=division_id,ciclo_lectivo=ciclo,defaults={'docente_id': docente_id})
            if not created:
                asignacion.docente_id = docente_id
                messages.success(request, "Asignación creada con éxito.")
                asignacion.save()
                return redirect(reverse('cp_admin') + '?tab=asignaciones')

    return redirect(reverse('cp_admin') + '?tab=asignaciones')

@admin_required
def eliminar_asignacion(request, asignacion_id):
    asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id)
    asignacion.delete()
    return redirect(reverse('cp_admin') + '?tab=asignaciones')

@admin_required
def crear_institucion(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        direccion = request.POST.get('direccion')
        if Institucion.objects.filter(nombre=nombre).exists():
            messages.error(request, "La Institucion ya se encuentra registrada.")
            return redirect(reverse('cp_admin') + '?tab=inst')
        if nombre:
            Institucion.objects.create(nombre=nombre,direccion=direccion)
    return redirect(reverse('cp_admin') + '?tab=inst')

@admin_required
def editar_institucion(request, id_inst):
    institucion = get_object_or_404(Institucion, id=id_inst)
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        direccion = request.POST.get('direccion')
        if nombre:
            institucion.nombre = nombre
            institucion.direccion = direccion
            institucion.save()
            return redirect(reverse('cp_admin') + '?tab=inst')
    return redirect('cp_admin')

@admin_required
def eliminar_institucion(request, id_inst):
    inst = Institucion.objects.get(id=id_inst)
    inst.delete()
    return redirect(reverse('cp_admin') + '?tab=inst')

@admin_required
def add_materia(request):
    orientaciones = Materia.ORIENTACIONES
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        orientacion = request.POST.get('orientacion')

        if Materia.objects.filter(nombre=nombre, orientacion=orientacion).exists():
            messages.error(request, "La materia ya se encuentra registrada.")
            return redirect(reverse('cp_admin') + '?tab=mat')
        if nombre and orientacion:
            Materia.objects.create(nombre=nombre,orientacion=orientacion)
            return redirect(reverse('cp_admin') + '?tab=mat')
            
    return render ('adminboard/cp_admin', {'orientaciones': orientaciones})

@admin_required
def eliminar_materia(request, materia_id):
    materia = Materia.objects.get(codigo=materia_id)
    materia.delete()
    return redirect(reverse('cp_admin') + '?tab=mat')

@admin_required
def crear_curso(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        if Curso.objects.filter(nombre=nombre).exists():
            messages.error(request, "El curso ya se encuentra registrado.")
            return redirect(reverse('cp_admin') + '?tab=cursos')
        if nombre:
            Curso.objects.get_or_create(nombre=nombre)
            return redirect(reverse('cp_admin') + '?tab=cursos')
    return render(request, 'adminboard/cp_admin')

@admin_required
def crear_division(request):
    cursos = Curso.objects.all()
    instituciones = Institucion.objects.all()
    
    if request.method == 'POST':
        nombre_div = request.POST.get('nombre')
        curso_id = request.POST.get('curso')
        inst_id = request.POST.get('institucion')
        if not (nombre_div and curso_id and inst_id):
            messages.warning(request, "Todos los campos son obligatorios.")
            return redirect(reverse('cp_admin') + '?tab=cursos')
        if Division.objects.filter(nombre=nombre_div, curso_id=curso_id, institucion_id=inst_id).exists():
            messages.error(request, f"La división '{nombre_div}' ya existe para ese curso en esta institución.")
            return redirect(reverse('cp_admin') + '?tab=cursos')
        try:
            Division.objects.create(nombre=nombre_div,curso_id=curso_id,institucion_id=inst_id)
            messages.success(request, "División creada con éxito.")
        except Exception as e:
            messages.error(request, f"Error al guardar: {e}")
        
        return redirect(reverse('cp_admin') + '?tab=cursos')

    return render(request, 'adminboard/cp_admin', {'cursos': cursos,'instituciones': instituciones})

@admin_required
def eliminar_division(request, division_id):
    division = Division.objects.get(id=division_id)
    division.delete()
    messages.success(request, "División eliminada con éxito.")
    return redirect(reverse('cp_admin') + '?tab=cursos')

@admin_required
def eliminar_curso(request, curso_id):
    curso = Curso.objects.get(nombre=curso_id)
    curso.delete()
    messages.success(request, "Año eliminado con éxito.")
    return redirect(reverse('cp_admin') + '?tab=cursos')

@admin_required
def gestionar_temarios(request):
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion == 'crear_unidad':
            materia_id = request.POST.get('materia_id')
            nro_unidad = request.POST.get('nro_unidad')
            nombre_unidad = request.POST.get('nombre_unidad')
            
            if materia_id and nro_unidad and nombre_unidad:
                materia = Materia.objects.get(id=materia_id)

                if Unidad.objects.filter(materia=materia, nro_unidad=nro_unidad).exists():
                    messages.error(request, f"Error: La Unidad {nro_unidad} ya existe en {materia.nombre}.")
                else:
                    Unidad.objects.create(materia=materia,nro_unidad=nro_unidad,nombre_unidad=nombre_unidad)
                    messages.success(request, f"Unidad {nro_unidad} creada correctamente.")
                
        elif accion == 'crear_tema':
            unidad_id = request.POST.get('unidad_id')
            nombre_tema = request.POST.get('nombre_tema')
            
            if unidad_id and nombre_tema:
                unidad = Unidad.objects.get(id=unidad_id)
                
                if Tema.objects.filter(unidad=unidad,nombre_tema__iexact=nombre_tema).exists():
                    messages.warning(request, f"El tema '{nombre_tema}' ya está registrado en esta unidad.")
                else:
                    Tema.objects.create(unidad=unidad,nombre_tema=nombre_tema)
                    messages.success(request, "Tema agregado correctamente.")
                
        return redirect('gestionar_temarios')

    materias_simples = Materia.objects.all()
    materias_con_temarios = Materia.objects.prefetch_related('unidad_set__temas_unidad').distinct()
    contexto = {'materias_simples': materias_simples,'materias_con_temarios': materias_con_temarios}

    return render(request, 'adminboard/gestionar_temarios.html', contexto)

@admin_required
def eliminar_unidad(request, unidad_id):
    unidad = get_object_or_404(Unidad, id=unidad_id)
    nombre = unidad.nombre_unidad
    unidad.delete()
    messages.success(request, f"La unidad '{nombre}' y todos sus temas fueron eliminados.")
    return redirect('gestionar_temarios')

@admin_required
def eliminar_tema(request, tema_id):
    tema = get_object_or_404(Tema, id=tema_id)
    nombre = tema.nombre_tema
    tema.delete()
    messages.success(request, f"El tema '{nombre}' fue eliminado.")
    return redirect('gestionar_temarios')

@admin_required
def toggle_habilitacion_trimestre(request, asig_id, num_trim):
    asignacion = get_object_or_404(AsignacionDocente, id=asig_id)
    if num_trim == 1:
        asignacion.trimestre_1_habilitado = not asignacion.trimestre_1_habilitado
    elif num_trim == 2:
        asignacion.trimestre_2_habilitado = not asignacion.trimestre_2_habilitado
    elif num_trim == 3:
        asignacion.trimestre_3_habilitado = not asignacion.trimestre_3_habilitado
    elif num_trim == 4:
        asignacion.trimestre_4_habilitado = not asignacion.trimestre_4_habilitado
    asignacion.save()
    messages.success(request, f"Estado del trimestre {num_trim} actualizado para {asignacion.materia}.")
    return redirect(request.META.get('HTTP_REFERER', reverse('cp_admin') + '?tab=asignaciones'),)