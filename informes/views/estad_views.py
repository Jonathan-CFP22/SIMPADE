from ..models import DetalleEvaluacionTema, InformeTrimestral
from django.shortcuts import render, redirect
from django.db.models import Count

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
    })