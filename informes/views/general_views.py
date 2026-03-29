from django.shortcuts import render, redirect
import urllib.request
import urllib.parse
import json
from ..models import Usuario, Institucion, Profesor, Division, Alumno

def index(request):
    """if request.method == 'POST':
        recaptcha_response = request.POST.get('g-recaptcha-response')
        url = 'https://www.google.com/recaptcha/api/siteverify'
        values = {
            'secret': '6LdulJwsAAAAAOXREqMm1kco0pkK7Y5BuQbVntbu',
            'response': recaptcha_response
        }
        data = urllib.parse.urlencode(values).encode()
        req = urllib.request.Request(url, data=data)       
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
        if not result.get('success'):
            return render(request, 'index.html', {'error': 'Validación de seguridad fallida. Por favor, marca "No soy un robot".'})"""
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
        elif rol == 'docente':
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

    return render(request, 'index.html', {'ocultar_nav': True,'error': error_login})

def logout(request):
    request.session.flush()
    return redirect('index')

def registrar_docente(request):
    if request.method == 'POST':
        recaptcha_response = request.POST.get('g-recaptcha-response')
        url = 'https://www.google.com/recaptcha/api/siteverify'
        values = {
            'secret': '6LdulJwsAAAAAOXREqMm1kco0pkK7Y5BuQbVntbu',
            'response': recaptcha_response
        }
        data = urllib.parse.urlencode(values).encode()
        req = urllib.request.Request(url, data=data)       
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
        if not result.get('success'):
            return render(request, 'index.html', {'error': 'Validación de seguridad fallida. Por favor, marca "No soy un robot".'})
    instituciones = Institucion.objects.all()
    
    if request.method == 'POST':
        dni = request.POST.get('dni')
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        clave = request.POST.get('clave')
        id_institucion = request.POST.get('institucion')

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

        if Usuario.objects.filter(dni=dni).exists():
            return render(request, 'registro_docente.html', {
                'error': "El DNI ya se encuentra registrado en el sistema.",
                'instituciones': instituciones, 'ocultar_nav': True
            })

        if email and Usuario.objects.filter(email=email).exists():
            return render(request, 'registro_docente.html', {
                'error': "El correo electrónico ya está en uso por otro usuario.",
                'instituciones': instituciones, 'ocultar_nav': True
            })

        try:

            nuevo_usuario = Usuario.objects.create(
                dni=dni,
                nombre_completo=nombre,
                email=email,
                clave=clave,
                es_profesor=True,
                rol_primario="DOCENTE"  # Asegurate que coincida con tu limit_choices_to
            )

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

def crear_alumno(request):
    if request.method == 'POST':
        recaptcha_response = request.POST.get('g-recaptcha-response')
        url = 'https://www.google.com/recaptcha/api/siteverify'
        values = {
            'secret': '6LdulJwsAAAAAOXREqMm1kco0pkK7Y5BuQbVntbu',
            'response': recaptcha_response
        }
        data = urllib.parse.urlencode(values).encode()
        req = urllib.request.Request(url, data=data)       
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
        if not result.get('success'):
            return render(request, 'index.html', {'error': 'Validación de seguridad fallida. Por favor, marca "No soy un robot".'})
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