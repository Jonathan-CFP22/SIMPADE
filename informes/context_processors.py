from .models import Usuario

def usuario_actual(request):
    dni = request.session.get('usuario_dni')
    if dni:
        try:
            user = Usuario.objects.get(dni=dni)
            return {'user_login': user}
        except Usuario.DoesNotExist:
            return {'user_login': None}
    return {'user_login': None}