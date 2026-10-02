"""
URL configuration for DATALAN project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from .views import (access_denied, admin_gate, admin_records, dashboard, login_view, logout_view,
                    placeholder, roles_access, role_dashboard, toggle_user,
                    user_create, user_delete, users, workflow)

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('acceso-denegado/', access_denied, name='access_denied'),
    path('admin/', admin_gate),
    path('admin/', admin.site.urls),
    path('usuarios/', users, name='users'),
    path('usuarios/nuevo/', user_create, name='user_create'),
    path('usuarios/<int:user_index>/estado/', toggle_user, name='toggle_user'),
    path('usuarios/<int:user_index>/eliminar/', user_delete, name='user_delete'),
    path('roles-accesos/', roles_access, name='roles_access'),
    path('clientes/', admin_records, {'section': 'clients'}, name='admin_clients'),
    path('trabajos/', admin_records, {'section': 'jobs'}, name='admin_jobs'),
    path('solicitudes/', admin_records, {'section': 'requests'}, name='admin_requests'),
    path('incidencias/', placeholder, {'page_title': 'Incidencias'}, name='admin_incidents'),
    path('configuracion/', placeholder, {'page_title': 'Configuración'}, name='configuration'),
    path('actividad/', placeholder, {'page_title': 'Actividad del sistema'}, name='activity'),
    path('comercial/', workflow, {'role_name': 'comercial'}, name='comercial'),
    path('comercial/pendientes/', workflow, {'role_name': 'comercial', 'screen': 'pending'}, name='commercial_pending'),
    path('comercial/en-proceso/', workflow, {'role_name': 'comercial', 'screen': 'in_process'}, name='commercial_in_process'),
    path('comercial/aprobadas/', workflow, {'role_name': 'comercial', 'screen': 'approved'}, name='commercial_approved'),
    path('comercial/rechazadas/', workflow, {'role_name': 'comercial', 'screen': 'rejected'}, name='commercial_rejected'),
    path('comercial/observadas/', workflow, {'role_name': 'comercial', 'screen': 'observed'}, name='commercial_observed'),
    path('comercial/solicitudes/', workflow, {'role_name': 'comercial', 'screen': 'requests'}, name='commercial_requests'),
    path('comercial/solicitudes/nueva/', workflow, {'role_name': 'comercial', 'screen': 'new_request'}, name='new_request'),
    path('comercial/solicitudes/<int:request_index>/derivar/', workflow, {'role_name': 'comercial', 'screen': 'forward_request'}, name='forward_request'),
    path('comercial/solicitudes/derivar/<str:request_cite>/', workflow, {'role_name': 'comercial', 'screen': 'forward_request'}, name='forward_request_cite'),
    path('comercial/solicitudes/cancelar/<str:request_cite>/', workflow, {'role_name': 'comercial', 'screen': 'cancel_request'}, name='cancel_request'),
    path('comercial/solicitudes/rechazar/<str:request_cite>/', workflow, {'role_name': 'comercial', 'screen': 'reject_request'}, name='reject_request'),
    path('planta-tecnica/encargado/', workflow, {'role_name': 'planta_encargado'}, name='planta_encargado'),
    path('planta-tecnica/encargado/solicitudes/', workflow, {'role_name': 'planta_encargado', 'screen': 'plant_requests'}, name='plant_requests'),
    path('planta-tecnica/encargado/registro/', workflow, {'role_name': 'planta_encargado', 'screen': 'plant_register'}, name='plant_register'),
    path('planta-tecnica/encargado/trabajos/', workflow, {'role_name': 'planta_encargado', 'screen': 'plant_work'}, name='plant_work'),
    path('planta-tecnica/encargado/tecnicos/', workflow, {'role_name': 'planta_encargado', 'screen': 'plant_technicians'}, name='plant_technicians'),
    path('planta-tecnica/encargado/incidencias/', workflow, {'role_name': 'planta_encargado', 'screen': 'plant_incidents'}, name='plant_incidents'),
    path('planta-tecnica/encargado/solicitud/<int:request_index>/', workflow, {'role_name': 'planta_encargado', 'screen': 'plant_request'}, name='plant_request'),
    path('planta-tecnica/encargado/solicitud/<int:request_index>/evaluar/', workflow, {'role_name': 'planta_encargado', 'screen': 'plant_evaluate'}, name='plant_evaluate'),
    path('planta-tecnica/encargado/solicitud/decidir/<str:request_cite>/', workflow, {'role_name': 'planta_encargado', 'screen': 'plant_decision'}, name='plant_decision'),
    path('planta-tecnica/encargado/solicitud/<int:request_index>/derivar/', workflow, {'role_name': 'planta_encargado', 'screen': 'plant_forward'}, name='plant_forward'),
    path('planta-tecnica/tecnico/', workflow, {'role_name': 'tecnico'}, name='tecnico'),
    path('planta-tecnica/tecnico/trabajos/', workflow, {'role_name': 'tecnico', 'screen': 'technician_work'}, name='technician_work'),
    path('planta-tecnica/tecnico/permisos/', workflow, {'role_name': 'tecnico', 'screen': 'technician_leave'}, name='technician_leave'),
    path('planta-tecnica/tecnico/asistencia/', workflow, {'role_name': 'tecnico', 'screen': 'technician_attendance'}, name='technician_attendance'),
    path('planta-tecnica/tecnico/reportar/', workflow, {'role_name': 'tecnico', 'screen': 'work_report'}, name='work_report'),
    path('sistemas/', workflow, {'role_name': 'sistemas_encargado'}, name='sistemas_encargado'),
    path('sistemas/solicitudes/', workflow, {'role_name': 'sistemas_encargado', 'screen': 'systems_requests'}, name='systems_requests'),
    path('sistemas/registro/', workflow, {'role_name': 'sistemas_encargado', 'screen': 'systems_register'}, name='systems_register'),
    path('sistemas/solicitud/decidir/<str:request_cite>/', workflow, {'role_name': 'sistemas_encargado', 'screen': 'systems_decision'}, name='systems_decision'),
    path('sistemas/trabajos/', workflow, {'role_name': 'sistemas_encargado', 'screen': 'systems_work'}, name='systems_work'),
    path('sistemas/optimizacion/', workflow, {'role_name': 'sistemas_encargado', 'screen': 'systems_optimization'}, name='systems_optimization'),
    path('sistemas/soporte-personal/', workflow, {'role_name': 'sistemas_encargado', 'screen': 'systems_support'}, name='systems_support'),
    path('sistemas/incidencias/', workflow, {'role_name': 'sistemas_encargado', 'screen': 'systems_incidents'}, name='systems_incidents'),
    path('sistemas/soporte/', workflow, {'role_name': 'soporte_sistemas'}, name='soporte_sistemas'),
        path('sistemas/soporte/trabajos/', workflow, {'role_name': 'soporte_sistemas', 'screen': 'support_work'}, name='support_work'),
        path('sistemas/soporte/permisos/', workflow, {'role_name': 'soporte_sistemas', 'screen': 'support_leave'}, name='support_leave'),
        path('sistemas/soporte/asistencia/', workflow, {'role_name': 'soporte_sistemas', 'screen': 'support_attendance'}, name='support_attendance'),
    path('sistemas/soporte/solicitud/<int:request_index>/verificar/', workflow, {'role_name': 'soporte_sistemas', 'screen': 'systems_verify'}, name='systems_verify'),
    path('sistemas/asignacion/<int:request_index>/', workflow, {'role_name': 'sistemas_encargado', 'screen': 'assignment'}, name='assignment'),
]
