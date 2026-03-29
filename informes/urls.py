from django.urls import path
from .views import admin_views, docente_views, general_views, estad_views

urlpatterns = [
    #-- GENERALES --#
    path('', general_views.index, name='index'),
    path('logout/', general_views.logout, name='logout'),
    path('registro-docente/', general_views.registrar_docente, name='registro_docente'),
    path('registro-alumno/', general_views.crear_alumno, name='crear_alumno'),

    #--- DOCENTES ---#
    path('panel-docente/', docente_views.panel_docente, name='panel_docente'),
    path('panel-docente/asignacion/<int:asignacion_id>/trimestre/<int:trimestre>/', docente_views.lista_alumnos_informe, name='lista_alumnos_informe'),
    path('panel-docente/asignacion/<int:asignacion_id>/trimestre/<int:trimestre>/alumno/<int:alumno_id>/evaluar/', docente_views.evaluar_alumno, name='evaluar_alumno'),
    
    #--- ESTADISTICAS ---#
    path('estadisticas-general/', estad_views.estadisticas_institucionales, name='ver_estadisticas'),

    #--- ADMIN --#
    path('adminboard/', admin_views.cp_admin, name='cp_admin'),
    path('toggle-trimestre/<int:asig_id>/<int:num_trim>/', admin_views.toggle_habilitacion_trimestre, name='toggle_trimestre'),
    path('mod_docente/<str:dni>/', admin_views.mod_docente, name='mod_docente'),
    path('mod_alumno/<str:alumno_id>/', admin_views.mod_alumno, name='mod_alumno'),
    path('mod-institucion/<int:id_inst>/', admin_views.editar_institucion, name='mod_institucion'),
    path('del-docente/<str:dni>/', admin_views.eliminar_docente, name='del_docente'),
    path('del-institucion/<int:id_inst>/', admin_views.eliminar_institucion, name='del_inst'),
    path('del-materia/<str:materia_id>/', admin_views.eliminar_materia, name='del_materia'),
    path('del-curso/<str:curso_id>/', admin_views.eliminar_curso, name='del_curso'),
    path('del-division/<str:division_id>/', admin_views.eliminar_division, name='del_division'),
    path('del-alumno/<int:alumno_id>/', admin_views.eliminar_alumno, name='del_alumno'),
    path('asignar-docente/', admin_views.asignar_docente, name='asignar_docente'),
    path('crear-docente/', admin_views.reg_docente_cp, name='reg_docente_cp'),
    path('crear-institucion/', admin_views.crear_institucion, name='crear_inst'), 
    path('crear-materia/', admin_views.add_materia, name='add_materia'),
    path('crear-curso/', admin_views.crear_curso, name='crear_curso'),
    path('crear-division/', admin_views.crear_division, name='crear_division'),
    path('crear-alumno/', admin_views.add_alumno, name='add_alumno'),

    path('adminboard/temarios/', admin_views.gestionar_temarios, name='gestionar_temarios'),
    path('adminboard/temario/eliminar_unidad/<int:unidad_id>/', admin_views.eliminar_unidad, name='eliminar_unidad'),
    path('adminboard/temario/eliminar_tema/<int:tema_id>/', admin_views.eliminar_tema, name='eliminar_tema'),
    
    
    
    path('del-asign/<int:asignacion_id>/', admin_views.eliminar_asignacion, name='eliminar_asignacion'),
    
    
]