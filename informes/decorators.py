from django.shortcuts import redirect

def login_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if 'usuario_dni' not in request.session:
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def admin_required(view_func):
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