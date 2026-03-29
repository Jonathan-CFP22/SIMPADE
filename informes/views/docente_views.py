from django.shortcuts import render, redirect, get_object_or_404
from functools import wraps
from django.contrib import messages
from ..models import InformeTrimestral, DetalleEvaluacionTema,Usuario, AsignacionDocente, Alumno, Unidad, AsignacionDocente, TemasTrimestre, Institucion

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
    asignaciones_filtradas = []

    if inst_id:
        institucion_seleccionada = Institucion.objects.filter(id=inst_id).first()
        if institucion_seleccionada:
            asignaciones_filtradas = asignaciones_totales.filter(division__institucion_id=inst_id)

            for asig in asignaciones_filtradas:
                alumnos_division = Alumno.objects.filter(division=asig.division)
                total_alumnos = alumnos_division.count()
                asig.total_alumnos = total_alumnos

                def check_trimestre(nro):
                    cargados = InformeTrimestral.objects.filter(materia=asig.materia,trimestre=nro,).count()
                    return cargados, (total_alumnos > 0 and cargados >= total_alumnos)

                asig.cargados_t1, asig.trim_1_completo = check_trimestre(1)
                asig.cargados_t2, asig.trim_2_completo = check_trimestre(2)
                asig.cargados_t3, asig.trim_3_completo = check_trimestre(3)
                asig.cargados_t4, asig.trim_4_completo = check_trimestre(4)

                asig.informes_cargados = asig.cargados_t1 # O la suma si prefieres

    contexto = {'docente': docente,'instituciones': instituciones,'institucion_seleccionada': institucion_seleccionada,'asignaciones_filtradas': asignaciones_filtradas}
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