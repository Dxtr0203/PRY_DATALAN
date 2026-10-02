from datetime import datetime
from functools import wraps

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache

from .auth_service import DEMO_USERS, ROLES, authenticate
from .workflow_service import add_history, get_requests, now, save_requests


def current_user(request):
    return request.session.get('identity')


def protected(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not current_user(request):
            return redirect(f'/login/?next={request.path}')
        return view(request, *args, **kwargs)
    return wrapped


def admin_only(view):
    @wraps(view)
    @protected
    def wrapped(request, *args, **kwargs):
        if request.session.get('role') != 'admin':
            return redirect('access_denied')
        return view(request, *args, **kwargs)
    return wrapped


def navigation(active, role_name, enabled_modules=None):
    if role_name == 'admin':
        items = [('INICIO', '/', '⌂', 'dashboard'), ('USUARIOS', '/usuarios/', '◌', 'users'), ('ROLES/ACCESOS', '/roles-accesos/', '♧', 'roles'), ('CLIENTES', '/clientes/', '◎', 'clients'), ('TRABAJOS', '/trabajos/', '◇', 'jobs'), ('SOLICITUDES', '/solicitudes/', '◈', 'requests'), ('INCIDENCIAS', '/incidencias/', '!', 'incidents'), ('PERMISOS', '/roles-accesos/?tab=permisos', '◷', 'permissions')]
    elif role_name == 'comercial':
        items = [('INICIO', '/comercial/', '⌂', 'INICIO'), ('SOLICITUDES', '/comercial/solicitudes/', '◌', 'SOLICITUDES'), ('NUEVA SOLICITUD', '/comercial/solicitudes/nueva/', '+', 'NUEVA SOLICITUD'), ('OBSERVADAS', '/comercial/observadas/', '◌', 'OBSERVADAS')]
    elif role_name == 'planta_encargado':
        items = [('INICIO', '/planta-tecnica/encargado/', '⌂', 'INICIO'), ('SOLICITUDES', '/planta-tecnica/encargado/solicitudes/', '◌', 'SOLICITUDES'), ('REGISTRO', '/planta-tecnica/encargado/registro/', '▤', 'REGISTRO'), ('TRABAJOS', '/planta-tecnica/encargado/trabajos/', '◇', 'TRABAJOS'), ('TECNICOS', '/planta-tecnica/encargado/tecnicos/', '♙', 'TECNICOS'), ('INCIDENCIAS', '/planta-tecnica/encargado/incidencias/', '!', 'INCIDENCIAS')]
    elif role_name == 'tecnico':
        items = [('INICIO', '/planta-tecnica/tecnico/', '⌂', 'INICIO'), ('MIS TRABAJOS', '/planta-tecnica/tecnico/trabajos/', '◇', 'MIS TRABAJOS'), ('PERMISOS', '/planta-tecnica/tecnico/permisos/', '◷', 'PERMISOS'), ('ASISTENCIA', '/planta-tecnica/tecnico/asistencia/', '◌', 'ASISTENCIA')]
    elif role_name == 'sistemas_encargado':
        items = [('INICIO', '/sistemas/', '⌂', 'INICIO'), ('SOLICITUDES', '/sistemas/solicitudes/', '◌', 'SOLICITUDES'), ('REGISTRO', '/sistemas/registro/', '▤', 'REGISTRO'), ('TRABAJOS', '/sistemas/trabajos/', '◇', 'TRABAJOS'), ('OPTIMIZACIÓN', '/sistemas/optimizacion/', '↗', 'OPTIMIZACIÓN'), ('SOPORTE', '/sistemas/soporte-personal/', '♧', 'SOPORTE'), ('INCIDENCIAS', '/sistemas/incidencias/', '!', 'INCIDENCIAS')]
    elif role_name == 'soporte_sistemas':
        items = [('INICIO', '/sistemas/soporte/', '⌂', 'INICIO'), ('MIS TRABAJOS', '/sistemas/soporte/trabajos/', '◇', 'MIS TRABAJOS'), ('PERMISOS', '/sistemas/soporte/permisos/', '◷', 'PERMISOS'), ('ASISTENCIA', '/sistemas/soporte/asistencia/', '◌', 'ASISTENCIA')]
    else:
        home = ROLES[role_name]['home']
        items = [('Dashboard', home, '▦', 'dashboard'), ('Solicitudes operativas', '#', '◈', 'requests'), ('Consultas', '#', '?', 'queries')]
    if role_name != 'admin' and enabled_modules is not None:
        items = [item for item in items if item[3] in enabled_modules]
    active_aliases = {
        'INICIO': 'dashboard', 'SOLICITUDES': 'requests', 'NUEVA SOLICITUD': 'new_request',
        'EN PROCESO': 'in_process', 'APROBADAS': 'approved', 'RECHAZADAS': 'rejected',
        'OBSERVADAS': 'observed', 'TRABAJOS': 'plant_work', 'TECNICOS': 'plant_technicians',
        'INCIDENCIAS': 'plant_incidents', 'MIS TRABAJOS': 'technician_work',
        'PERMISOS': 'technician_leave', 'ASISTENCIA': 'technician_attendance', 'SOPORTE': 'systems_support',
        'OPTIMIZACIÓN': 'systems_optimization',
        'REGISTRO': 'plant_register',
    }
    if role_name == 'sistemas_encargado':
        active_aliases['TRABAJOS'] = 'systems_work'
        active_aliases['REGISTRO'] = 'systems_register'
    if role_name == 'soporte_sistemas':
        active_aliases['MIS TRABAJOS'] = 'support_work'
    nav_items = [{'label': label, 'url': url, 'icon': icon, 'active': active == item or active == active_aliases.get(item) or (role_name == 'comercial' and item == 'SOLICITUDES' and active in {'pending', 'in_process', 'approved', 'rejected'})} for label, url, icon, item in items]
    if role_name == 'sistemas_encargado':
        optimization = next((item for item in nav_items if item['label'] == 'OPTIMIZACIÓN'), None)
        nav_items = [item for item in nav_items if item['label'] != 'OPTIMIZACIÓN']
        for item in nav_items:
            if item['label'] == 'SOLICITUDES':
                item['expanded'] = active in {'requests', 'systems_requests', 'systems_optimization'}
                item['children'] = [optimization] if optimization else []
    return nav_items


def enabled_modules_for_role(role_name, configured_modules):
    enabled_modules = ([module for module in configured_modules if module in ROLES[role_name]['modules']]
                       if configured_modules is not None else list(ROLES[role_name]['modules']))
    if configured_modules is not None and role_name == 'sistemas_encargado' and 'OPTIMIZACIÓN' not in enabled_modules:
        enabled_modules.append('OPTIMIZACIÓN')
    if configured_modules is not None and role_name == 'planta_encargado' and 'REGISTRO' not in enabled_modules:
        enabled_modules.append('REGISTRO')
    if configured_modules is not None and role_name == 'sistemas_encargado' and 'REGISTRO' not in enabled_modules:
        enabled_modules.append('REGISTRO')
    return enabled_modules


def plant_decision_for(item):
    evaluation = item.get('plant_evaluation', {})
    decision = item.get('plant_status') or evaluation.get('decision')
    if decision in {'APROBADO', 'RECHAZADO'}:
        return decision
    return {'FACTIBLE': 'APROBADO', 'NO FACTIBLE': 'RECHAZADO'}.get(evaluation.get('feasibility'))


def context(request, page_title, active='dashboard'):
    role_name = request.session['role']
    configured_modules = request.session.get('role_permissions', {}).get(role_name)
    enabled_modules = enabled_modules_for_role(role_name, configured_modules)
    return {'current_user': current_user(request), 'role': ROLES[role_name], 'page_title': page_title, 'nav_items': navigation(active, role_name, enabled_modules)}


@never_cache
def login_view(request):
    if current_user(request):
        return redirect(ROLES[request.session['role']]['home'])
    if request.method == 'POST':
        identity = authenticate(request.POST.get('username', ''), request.POST.get('password', ''), request.session.get('demo_users', DEMO_USERS))
        if identity:
            request.session.cycle_key()
            request.session['identity'] = identity
            request.session['role'] = identity['role']
            return redirect(ROLES[identity['role']]['home'])
        return render(request, 'login.html', {'error': 'Usuario, contraseña incorrectos o cuenta inactiva.'})
    return render(request, 'login.html')


@never_cache
def logout_view(request):
    request.session.flush()
    messages.success(request, 'Sesión cerrada correctamente.')
    return redirect('login')


@never_cache
@admin_only
def dashboard(request):
    requests = get_requests(request.session)
    clients = sorted({item.get('applicant', 'Sin cliente') for item in requests})
    def service_count(items, state=None):
        return sum(1 for item in items if (state is None or item.get('status') not in {'NO FACTIBLE', 'RECHAZADA POR COMERCIAL', 'CANCELADA'}) and item.get('type', '') == state)
    pp = [item for item in requests if 'Punto a Punto' in item.get('type', '') or 'punto a punto' in item.get('type', '')]
    mp = [item for item in requests if 'Multipunto' in item.get('type', '') or 'multipunto' in item.get('type', '')]
    internet = [item for item in requests if 'Internet' in item.get('type', '') or 'internet' in item.get('type', '')]
    active = [item for item in requests if item.get('status') not in {'NO FACTIBLE', 'RECHAZADA POR COMERCIAL', 'CANCELADA'}]
    inactive = [item for item in requests if item.get('status') in {'NO FACTIBLE', 'RECHAZADA POR COMERCIAL', 'CANCELADA'}]
    activity = sorted(requests, key=lambda item: item.get('received_at', ''), reverse=True)
    data = context(request, 'Inicio')
    data.update({'client_total': len(clients), 'registered_breakdown': [len(pp), len(mp), len(internet)], 'active_breakdown': [sum(item in active for item in pp), sum(item in active for item in mp), sum(item in active for item in internet)], 'inactive_breakdown': [sum(item in inactive for item in pp), sum(item in inactive for item in mp), sum(item in inactive for item in internet)], 'installations': sum('Instalación' in item.get('type', '') for item in requests), 'retiros': sum('Retiro' in item.get('type', '') for item in requests), 'eventuales': sum('Eventual' in item.get('type', '') for item in requests), 'monthly_requests': len(requests), 'monthly_incidents': sum(item.get('status') in {'SUSPENDIDA', 'CANCELADA'} for item in requests), 'admin_activity': activity, 'chart_values': [len(pp), len(mp), len(internet), len(active), len(inactive)]})
    return render(request, 'index.html', data)


@never_cache
@protected
def role_dashboard(request, role_name):
    if request.session.get('role') != role_name:
        return redirect('access_denied')
    stats = {'comercial': [('Solicitudes registradas', '86'), ('Solicitudes pendientes', '19'), ('Solicitudes aprobadas', '52'), ('Solicitudes rechazadas', '15')], 'sistemas': [('Solicitudes recibidas', '64'), ('En revisión', '18'), ('Solicitudes factibles', '38'), ('Solicitudes asignadas', '27')], 'planta': [('Solicitudes recibidas', '42'), ('Evaluaciones pendientes', '11'), ('Factibles', '23'), ('No factibles', '8')]}[role_name]
    data = context(request, 'Dashboard')
    data.update({'stats': [(label, value, 'Datos de demostración') for label, value in stats], 'activities': [('Solicitud SOL-0148', 'Revisión operativa', 'Hace 20 min'), ('Solicitud SOL-0142', 'Actualización recibida', 'Hace 1 h'), ('Solicitud SOL-0139', 'Proceso completado', 'Ayer')]})
    return render(request, 'role_dashboard.html', data)


@admin_only
def users(request):
    data = context(request, 'Usuarios', 'users')
    role_filter = request.GET.get('rol', 'TODOS')
    all_users = request.session.get('demo_users', DEMO_USERS)
    indexed_users = [dict(user, index=index) for index, user in enumerate(all_users)]
    data['demo_users'] = indexed_users if role_filter == 'TODOS' else [user for user in indexed_users if user.get('role') == role_filter]
    data['role_filter'] = role_filter
    data['role_options'] = [('TODOS', 'TODOS'), ('comercial', 'COMERCIAL'), ('planta_encargado', 'ENCARGADO PLANTA TÉCNICA'), ('tecnico', 'TÉCNICO'), ('sistemas_encargado', 'ENCARGADO DE SISTEMAS'), ('soporte_sistemas', 'SOPORTE'), ('admin', 'ADMINISTRADOR')]
    return render(request, 'users.html', data)


@admin_only
def user_create(request):
    if request.method == 'POST':
        if request.POST.get('password') != request.POST.get('confirm_password'):
            messages.error(request, 'Las contraseñas no coinciden.')
            return redirect('user_create')
        users = list(request.session.get('demo_users', DEMO_USERS))
        users.append({'full_name': request.POST['full_name'], 'username': request.POST['username'], 'email': request.POST['email'], 'password': request.POST['password'], 'role': request.POST['role'], 'active': True, 'last_access': 'Nunca'})
        request.session['demo_users'] = users
        request.session.modified = True
        messages.success(request, 'Usuario creado en la sesión de demostración.')
        return redirect('users')
    data = context(request, 'Nuevo usuario', 'users')
    data['roles'] = ROLES
    return render(request, 'user_form.html', data)


@admin_only
def toggle_user(request, user_index):
    users = request.session.get('demo_users', DEMO_USERS)
    if 0 <= user_index < len(users):
        users[user_index]['active'] = not users[user_index]['active']
        request.session['demo_users'] = users
        request.session.modified = True
        messages.success(request, 'Estado del usuario actualizado.')
    return redirect('users')


@admin_only
def user_delete(request, user_index):
    users = request.session.get('demo_users', DEMO_USERS)
    if 0 <= user_index < len(users) and users[user_index]['username'] != request.session['identity']['username']:
        users.pop(user_index)
        request.session['demo_users'] = users
        request.session.modified = True
        messages.success(request, 'Usuario eliminado de la sesión de demostración.')
    return redirect('users')


@admin_only
def roles_access(request):
    data = context(request, 'Roles y accesos', 'roles')
    data['roles'] = ROLES
    if request.method == 'POST':
        permissions = request.session.get('role_permissions', {})
        role_name = request.POST.get('role')
        if role_name in ROLES:
            permissions[role_name] = [module for module in request.POST.getlist('modules') if module in ROLES[role_name]['modules']]
            request.session['role_permissions'] = permissions
            request.session.modified = True
            messages.success(request, f'Permisos de {ROLES[role_name]["label"]} actualizados.')
        return redirect('/roles-accesos/')
    permission_map = request.session.get('role_permissions', {})
    data['role_cards'] = [{'key': key, 'item': item, 'enabled_modules': enabled_modules_for_role(key, permission_map.get(key))} for key, item in ROLES.items() if key != 'admin']
    return render(request, 'roles.html', data)


def admin_records(request, section):
    items = list(get_requests(request.session))
    if section == 'clients':
        clients = {}
        for item in items:
            name = item.get('applicant', 'Sin cliente')
            clients.setdefault(name, []).append(item)
        data = context(request, 'Clientes', 'clients')
        data['clients'] = [{'name': name, 'requests': records, 'last_request': records[0].get('received_at', '-')} for name, records in sorted(clients.items(), key=lambda entry: entry[0].lower())]
        return render(request, 'clients.html', data)
    if section == 'jobs':
        filter_name = request.GET.get('tipo', 'TODOS').upper()
        jobs = [item for item in items if item.get('status') in {'ASIGNADA', 'EN EJECUCIÓN', 'FINALIZADA'}]
        if filter_name != 'TODOS':
            type_marker = {'INSTALACIONES': 'INSTAL', 'RETIROS': 'RETIRO', 'EVENTUALES': 'EVENTUAL'}.get(filter_name, filter_name)
            jobs = [item for item in jobs if type_marker in item.get('type', '').upper()]
        data = context(request, 'Trabajos', 'jobs')
        data.update({'jobs': jobs, 'job_filter': filter_name})
        return render(request, 'jobs.html', data)
    filter_name = request.GET.get('estado', 'TODOS').upper()
    requests = items
    status_map = {'PENDIENTES': {'EN PROCESO', 'REGISTRADA', 'EN REVISIÓN PLANTA TÉCNICA', 'EN REVISIÓN SISTEMAS'}, 'APROBADOS': {'APROBADO', 'APROBADA', 'ASIGNADA', 'EN EJECUCIÓN', 'FINALIZADA'}, 'RECHAZADOS': {'RECHAZADO', 'NO FACTIBLE', 'RECHAZADA POR COMERCIAL', 'CANCELADA', 'NO APROBADA POR SISTEMAS'}, 'OBSERVADOS': {'OBSERVADO'}}
    if filter_name in status_map:
        requests = [item for item in requests if item.get('commercial_status', item.get('status', '')).upper() in status_map[filter_name] or item.get('status', '').upper() in status_map[filter_name]]
    data = context(request, 'Solicitudes', 'requests')
    data.update({'admin_requests': requests, 'request_filter': filter_name})
    return render(request, 'admin_requests.html', data)


@protected
def placeholder(request, page_title):
    return render(request, 'placeholder.html', context(request, page_title))


def access_denied(request):
    identity = current_user(request)
    return render(request, 'access_denied.html', {'identity': identity, 'home': ROLES[identity['role']]['home'] if identity else '/login/'})


@admin_only
def admin_gate(request):
    return redirect('dashboard')


def profile_only(role_name):
    def decorator(view):
        @wraps(view)
        @protected
        def wrapped(request, *args, **kwargs):
            if request.session.get('role') != role_name:
                return redirect('access_denied')
            return view(request, *args, **kwargs)
        return wrapped
    return decorator


def workflow_context(request, title, active, requests):
    data = context(request, title, active)
    data.update({'requests': requests, 'equipment': ['Media Converter', 'SFP', 'ONT', 'Router', 'Switch', 'ODF', 'Patch Panel', 'Patch Cord', 'MC1500R', 'Otros'], 'technicians': ['Carlos Torres', 'Luis Pérez', 'Sofía Rojas'], 'support_staff': ['Ana López', 'Diego Ramírez', 'Soporte de Sistemas']})
    return data


@never_cache
@protected
def workflow(request, role_name, screen='dashboard', request_index=None, request_cite=None):
    if request.session.get('role') != role_name:
        return redirect('access_denied')
    screen_modules = {
        'dashboard': 'INICIO', 'requests': 'SOLICITUDES', 'pending': 'SOLICITUDES', 'new_request': 'NUEVA SOLICITUD',
        'forward_request': 'SOLICITUDES', 'reject_request': 'SOLICITUDES', 'cancel_request': 'SOLICITUDES', 'approved': 'APROBADAS',
        'rejected': 'RECHAZADAS', 'in_process': 'EN PROCESO', 'observed': 'OBSERVADAS',
        'plant_requests': 'SOLICITUDES', 'plant_request': 'SOLICITUDES', 'plant_evaluate': 'SOLICITUDES',
        'plant_decision': 'SOLICITUDES', 'plant_forward': 'SOLICITUDES', 'plant_register': 'REGISTRO', 'plant_work': 'TRABAJOS',
        'plant_technicians': 'TECNICOS', 'plant_incidents': 'INCIDENCIAS', 'technician_work': 'MIS TRABAJOS',
        'technician_leave': 'PERMISOS', 'technician_attendance': 'ASISTENCIA', 'work_report': 'MIS TRABAJOS',
        'systems_requests': 'SOLICITUDES', 'systems_decision': 'SOLICITUDES', 'systems_work': 'TRABAJOS', 'systems_support': 'SOPORTE',
        'systems_register': 'REGISTRO', 'systems_incidents': 'INCIDENCIAS', 'systems_optimization': 'OPTIMIZACIÓN', 'assignment': 'TRABAJOS', 'support_work': 'MIS TRABAJOS',
        'support_leave': 'PERMISOS', 'support_attendance': 'ASISTENCIA', 'systems_verify': 'MIS TRABAJOS',
    }
    configured_modules = request.session.get('role_permissions', {}).get(role_name)
    enabled_modules = enabled_modules_for_role(role_name, configured_modules)
    if screen_modules.get(screen, 'INICIO') not in enabled_modules:
        return redirect('access_denied')
    requests = get_requests(request.session)
    if role_name == 'tecnico':
        requests = [item for item in requests if item.get('assignment', {}).get('leader') == request.session['identity']['full_name'] or request.session['identity']['full_name'] in item.get('assignment', {}).get('others', [])]
    selected = requests[request_index] if request_index is not None and request_index < len(requests) else None
    if request_cite:
        selected = next((item for item in requests if item.get('cite') == request_cite), None)
    editing_request = None
    if role_name == 'comercial' and screen == 'new_request' and request.GET.get('edit_cite'):
        editing_request = next((item for item in requests if item.get('cite') == request.GET['edit_cite'] and item.get('status') == 'REGISTRADA'), None)
        if editing_request and editing_request.get('type') == 'Instalación Punto Multipunto':
            editing_request = dict(editing_request)
            for destination_field, legacy_field in (('destination', 'installation'), ('destination_location', 'installation_location'), ('destination_coordinates', 'installation_coordinates')):
                editing_request[destination_field] = editing_request.get(destination_field) or editing_request.get(legacy_field, '')
    user = request.session['identity']['full_name']
    if request.method == 'POST':
        if screen == 'new_request':
            required_fields = {'applicant': 'El nombre del solicitante es obligatorio.', 'email': 'Ingresa un correo electrónico válido.', 'type': 'Selecciona el tipo de solicitud.', 'priority': 'Selecciona una prioridad.'}
            missing = next((message for field, message in required_fields.items() if not request.POST.get(field, '').strip()), None)
            if missing:
                messages.error(request, missing)
                return redirect('new_request')
            try:
                validate_email(request.POST['email'].strip())
            except ValidationError:
                messages.error(request, 'Ingresa un correo electrónico válido.')
                return redirect('new_request')
            edit_cite = request.POST.get('edit_cite', '').strip()
            if edit_cite:
                item = next((row for row in requests if row.get('cite') == edit_cite and row.get('status') == 'REGISTRADA'), None)
                if not item:
                    messages.error(request, 'Solo puedes editar solicitudes pendientes de derivación.')
                    return redirect('commercial_pending')
                for field in ('applicant', 'email', 'type', 'priority', 'origin', 'origin_location', 'origin_coordinates', 'destination', 'destination_location', 'destination_coordinates', 'installation', 'installation_location', 'installation_coordinates', 'applicant_kind', 'company', 'speed', 'equipment_type', 'requirements'):
                    item[field] = request.POST.get(field, '').strip()
                item['equipment_enabled'] = request.POST.get('equipment_enabled') == 'on'
                add_history(item, user, 'Comercial', 'Solicitud editada antes de derivar')
                save_requests(request.session, requests)
                messages.success(request, f'{item["cite"]} actualizada correctamente.')
                return redirect('commercial_pending')
            item = {'cite': f'CITE-2026-{len(requests) + 149:04d}', 'type': request.POST['type'], 'applicant': request.POST['applicant'], 'email': request.POST['email'], 'origin': request.POST.get('origin', ''), 'origin_location': request.POST.get('origin_location', ''), 'origin_coordinates': request.POST.get('origin_coordinates', ''), 'destination': request.POST.get('destination', ''), 'destination_location': request.POST.get('destination_location', ''), 'destination_coordinates': request.POST.get('destination_coordinates', ''), 'installation': request.POST.get('installation', ''), 'installation_location': request.POST.get('installation_location', ''), 'installation_coordinates': request.POST.get('installation_coordinates', ''), 'applicant_kind': request.POST.get('applicant_kind', 'CLIENTE'), 'company': request.POST.get('company', ''), 'equipment_enabled': request.POST.get('equipment_enabled') == 'on', 'speed': request.POST.get('speed', ''), 'equipment_type': request.POST.get('equipment_type', ''), 'commercial_user': user, 'requirements': request.POST.get('requirements', ''), 'received_at': now(), 'forwarded_at': '', 'status': 'REGISTRADA', 'commercial_status': 'EN PROCESO', 'priority': request.POST.get('priority', 'Media'), 'plant_evaluation': {}, 'systems_check': {}, 'assignment': {}, 'reports': [], 'history': []}
            add_history(item, user, 'Comercial', 'Solicitud registrada', 'Solicitud creada en la demostración.')
            requests.append(item)
            save_requests(request.session, requests)
            messages.success(request, f'{item["cite"]} registrada correctamente.')
            return redirect('commercial_pending')
        if selected and screen == 'forward_request' and request.POST.get('confirm'):
            if selected.get('status') != 'REGISTRADA':
                messages.error(request, 'Solo se pueden derivar solicitudes recién registradas.')
                return redirect('commercial_requests')
            selected['forwarded_at'] = now(); selected['status'] = 'EN REVISIÓN PLANTA TÉCNICA'; add_history(selected, user, 'Comercial', 'Solicitud derivada a Planta Técnica'); save_requests(request.session, requests); messages.success(request, 'Solicitud derivada a Planta Técnica.'); return redirect('commercial_in_process')
        if selected and screen == 'cancel_request' and request.POST.get('confirm') == 'yes':
            if selected.get('status') != 'REGISTRADA':
                messages.error(request, 'Solo puedes cancelar solicitudes pendientes de derivación.')
                return redirect('commercial_pending')
            selected['status'] = 'CANCELADA'; selected['commercial_status'] = 'CANCELADO'
            add_history(selected, user, 'Comercial', 'Solicitud cancelada antes de derivar')
            save_requests(request.session, requests)
            messages.success(request, f'{selected["cite"]} cancelada correctamente.')
            return redirect('commercial_pending')
        if selected and screen == 'reject_request' and request.POST.get('confirm'):
            reason = request.POST.get('reason', '').strip()
            if not reason:
                messages.error(request, 'Indica el motivo del rechazo.')
                return redirect('commercial_requests')
            selected['commercial_status'] = 'RECHAZADO'; selected['status'] = 'RECHAZADA POR COMERCIAL'; selected['rejection_reason'] = reason
            add_history(selected, user, 'Comercial', 'Solicitud rechazada', reason); save_requests(request.session, requests)
            messages.success(request, f'{selected["cite"]} fue rechazada correctamente.')
            return redirect('commercial_requests')
        if selected and screen == 'plant_decision' and request.POST.get('decision') in {'APROBADO', 'RECHAZADO'}:
            decision = request.POST['decision']
            selected['plant_evaluation'] = {'feasibility': 'FACTIBLE' if decision == 'APROBADO' else 'NO FACTIBLE', 'evaluator': user, 'decision': decision, 'reason': request.POST.get('reason', '').strip()}
            selected['plant_status'] = decision
            selected['status'] = 'EN REVISIÓN SISTEMAS'
            selected['plant_approved_at'] = now() if decision == 'APROBADO' else ''
            if decision == 'RECHAZADO':
                selected['commercial_status'] = 'RECHAZADO'
            add_history(selected, user, 'Planta Técnica', 'Solicitud aprobada y derivada a Sistemas' if decision == 'APROBADO' else 'Solicitud rechazada', request.POST.get('reason', '').strip())
            save_requests(request.session, requests)
            messages.success(request, f'{selected["cite"]}: solicitud {decision.lower()} por Planta Técnica.')
            return redirect('planta_encargado')
        if selected and screen == 'plant_evaluate' and request.POST.get('feasibility'):
            feasible = request.POST['feasibility'] == 'FACTIBLE'
            selected['plant_evaluation'] = dict(request.POST.items()); selected['plant_status'] = 'APROBADO' if feasible else 'RECHAZADO'; selected['status'] = 'EN REVISIÓN SISTEMAS'; selected['commercial_status'] = 'EN PROCESO' if feasible else 'RECHAZADO'; selected['plant_approved_at'] = now() if feasible else ''; add_history(selected, user, 'Planta Técnica', 'Solicitud aprobada y derivada a Sistemas' if feasible else 'Evaluación técnica no factible; enviada a Sistemas para valoración independiente'); save_requests(request.session, requests); messages.success(request, 'Solicitud enviada a Sistemas para valoración.' if feasible else 'Evaluación técnica no factible enviada a Sistemas para valoración.'); return redirect('planta_encargado')
        if selected and screen == 'plant_forward' and request.POST.get('confirm') and selected.get('plant_evaluation', {}).get('feasibility') == 'FACTIBLE':
            selected['status'] = 'EN REVISIÓN SISTEMAS'; add_history(selected, user, 'Planta Técnica', 'Solicitud derivada a Sistemas'); save_requests(request.session, requests); messages.success(request, 'Solicitud derivada a Sistemas.'); return redirect('planta_encargado')
        if selected and screen == 'systems_decision' and not selected.get('systems_status') and plant_decision_for(selected) in {'APROBADO', 'RECHAZADO'}:
            decision = request.POST.get('decision')
            if decision in {'APROBADO', 'RECHAZADO'}:
                approved = decision == 'APROBADO'
                plant_approved = plant_decision_for(selected) == 'APROBADO'
                selected['systems_status'] = decision
                selected['systems_check'] = {'result': decision, 'evaluator': user, 'reason': request.POST.get('reason', '').strip()}
                selected['status'] = 'APROBADA' if approved and plant_approved else 'NO APROBADA POR SISTEMAS' if not approved else 'NO FACTIBLE'
                selected['commercial_status'] = 'APROBADO' if approved and plant_approved else 'RECHAZADO'
                selected['approved_at'] = now() if approved and plant_approved else ''
                add_history(selected, user, 'Sistemas', f'Solicitud {decision.lower()}')
                save_requests(request.session, requests)
                messages.success(request, f'{selected["cite"]}: solicitud {decision.lower()} por Sistemas.')
            else:
                messages.error(request, 'La solicitud ya no está pendiente o la decisión no es válida.')
            return redirect('systems_requests')
        if selected and screen == 'systems_verify' and request.POST.get('confirm'):
            selected['systems_check'] = dict(request.POST.items()); add_history(selected, user, 'Soporte de Sistemas', 'Verificación de equipos realizada'); save_requests(request.session, requests); messages.success(request, 'Verificación guardada para revisión del Encargado de Sistemas.'); return redirect('soporte_sistemas')
        if selected and screen == 'assignment' and request.POST.get('leader') and selected.get('status') in {'APROBADA', 'ASIGNADA'}:
            selected['assignment'] = {'leader': request.POST['leader'], 'others': request.POST.getlist('others'), 'date': request.POST['scheduled_date']}; selected['status'] = 'ASIGNADA'; selected['commercial_status'] = 'APROBADO'; add_history(selected, user, 'Sistemas', 'Personal asignado'); save_requests(request.session, requests); messages.success(request, 'Personal asignado al trabajo.'); return redirect('sistemas_encargado')
        if selected and screen == 'assignment' and request.POST.get('leader'):
            messages.error(request, 'El trabajo solo puede asignarse después de la aprobación de Planta Técnica y Sistemas.')
            return redirect('systems_requests')
        if screen == 'work_report' and request.POST.get('activities'):
            report = dict(request.POST.items()); report['technician'] = user; report['submitted_at'] = now(); requests[0]['reports'].append(report); requests[0]['status'] = request.POST['result']; requests[0]['concluded_at'] = now() if request.POST['result'] == 'FINALIZADA' else ''; add_history(requests[0], user, 'Planta Técnica', 'Trabajo reportado'); save_requests(request.session, requests); messages.success(request, 'Reporte de trabajo enviado.'); return redirect('tecnico')
    def received_at_value(item):
        try:
            return datetime.strptime(item.get('received_at', ''), '%d/%m/%Y %H:%M')
        except ValueError:
            return datetime.min

    def decision_at_value(item, area, timestamp_field, action_prefixes):
        timestamp = item.get(timestamp_field, '')
        if timestamp:
            try:
                return datetime.strptime(timestamp, '%d/%m/%Y %H:%M')
            except ValueError:
                pass
        for event in reversed(item.get('history', [])):
            action = event.get('action', '').casefold()
            if event.get('area') != area or not any(action.startswith(prefix) for prefix in action_prefixes):
                continue
            try:
                return datetime.strptime(f"{event.get('date', '')} {event.get('time', '00:00')}", '%d/%m/%Y %H:%M')
            except ValueError:
                continue
        return received_at_value(item)

    for request_index, item in enumerate(requests):
        item['_request_index'] = request_index
    commercial_requests = sorted(requests, key=received_at_value, reverse=True)
    plant_requests = [item for item in commercial_requests if item.get('status') == 'EN REVISIÓN PLANTA TÉCNICA' and not item.get('plant_evaluation')] if role_name == 'planta_encargado' else []
    plant_records = []
    if role_name == 'planta_encargado':
        for item in commercial_requests:
            plant_status = plant_decision_for(item)
            if plant_status:
                multipoint = item.get('type') == 'Instalación Punto Multipunto'
                company = item.get('company') or ''
                client = company if item.get('applicant_kind') == 'ENTIDAD' and company else item.get('applicant') or company or '-'
                plant_records.append({
                    **item,
                    'plant_record_client': client,
                    'plant_record_type': 'PUNTO MULTIPUNTO' if multipoint else 'PUNTO A PUNTO',
                    'plant_record_is_multipoint': multipoint,
                    'plant_record_origin': '---' if multipoint else item.get('origin') or '-',
                    'plant_record_destination': item.get('destination') or (item.get('installation') if multipoint else '') or '-',
                    'plant_record_status': plant_status,
                    'plant_record_distance': '',
                })
        plant_records.sort(key=lambda item: decision_at_value(item, 'Planta Técnica', 'plant_approved_at', ('solicitud aprob', 'solicitud rechaz', 'evaluación técnica no factible')), reverse=True)
    if role_name == 'comercial':
        if screen == 'pending':
            commercial_requests = [item for item in commercial_requests if item.get('status') == 'REGISTRADA' and item.get('commercial_status') == 'EN PROCESO']
        elif screen == 'approved':
            commercial_requests = [item for item in commercial_requests if item.get('commercial_status') == 'APROBADO']
        elif screen == 'rejected':
            commercial_requests = [item for item in commercial_requests if item.get('commercial_status') == 'RECHAZADO']
        elif screen == 'observed':
            commercial_requests = [item for item in commercial_requests if item.get('commercial_status') == 'OBSERVADO']
        elif screen == 'in_process':
            commercial_requests = [item for item in commercial_requests if item.get('commercial_status') == 'EN PROCESO' and item.get('status') != 'REGISTRADA']
    commercial_counts = {
        'in_process': sum(item.get('commercial_status') == 'EN PROCESO' for item in requests),
        'approved': sum(item.get('commercial_status') == 'APROBADO' for item in requests),
        'rejected': sum(item.get('commercial_status') == 'RECHAZADO' for item in requests),
        'observed': sum(item.get('commercial_status') == 'OBSERVADO' for item in requests),
    }
    for item in commercial_requests:
        item['commercial_display_status'] = 'PENDIENTE' if item.get('status') == 'REGISTRADA' else item.get('commercial_status', 'EN PROCESO')
    active = 'dashboard' if screen == 'dashboard' else screen
    render_screen = screen
    data = workflow_context(request, 'Inicio' if role_name == 'comercial' and screen == 'dashboard' else ROLES[role_name]['label'], active, requests)
    fully_approved_statuses = {'APROBADA', 'ASIGNADA', 'EN EJECUCIÓN', 'FINALIZADA'}
    plant_jobs = [item for item in commercial_requests if item.get('status') in fully_approved_statuses and item.get('plant_evaluation', {}).get('feasibility') == 'FACTIBLE']
    plant_incidents = [item for item in commercial_requests if item.get('status') in {'SUSPENDIDA', 'CANCELADA'} or any(report.get('problems', '').strip() for report in item.get('reports', []))]
    plant_stats = [('SOLICITUDES RECIBIDAS', str(len(plant_requests)), 'Enviadas por Comercial'), ('FACTIBLE', str(sum(item.get('plant_evaluation', {}).get('feasibility') == 'FACTIBLE' for item in requests)), 'Trabajos aprobados'), ('NO FACTIBLES', str(sum(item.get('plant_evaluation', {}).get('feasibility') == 'NO FACTIBLE' for item in requests)), 'Trabajos no aprobados'), ('CONCLUIDOS', str(sum(item.get('status') == 'FINALIZADA' for item in requests)), 'Trabajos finalizados')]
    systems_requests = [dict(item, plant_display_status=plant_decision_for(item)) for item in commercial_requests if role_name == 'sistemas_encargado' and not item.get('systems_status') and plant_decision_for(item) in {'APROBADO', 'RECHAZADO'}]
    systems_records = []
    if role_name == 'sistemas_encargado':
        for item in commercial_requests:
            systems_status = item.get('systems_status')
            if systems_status in {'APROBADO', 'RECHAZADO'}:
                multipoint = item.get('type') == 'Instalación Punto Multipunto'
                company = item.get('company') or ''
                client = company if item.get('applicant_kind') == 'ENTIDAD' and company else item.get('applicant') or company or '-'
                systems_records.append({
                    **item,
                    'systems_record_client': client,
                    'systems_record_type': 'PUNTO MULTIPUNTO' if multipoint else 'PUNTO A PUNTO',
                    'systems_record_is_multipoint': multipoint,
                    'systems_record_origin': '---' if multipoint else item.get('origin') or '-',
                    'systems_record_destination': item.get('destination') or (item.get('installation') if multipoint else '') or '-',
                    'systems_record_status': systems_status,
                    'systems_record_distance': '',
                })
        systems_records.sort(key=lambda item: decision_at_value(item, 'Sistemas', 'approved_at', ('solicitud aprob', 'solicitud rechaz')), reverse=True)
    systems_jobs = [item for item in commercial_requests if item.get('status') in fully_approved_statuses and item.get('plant_evaluation', {}).get('feasibility') == 'FACTIBLE'] if role_name == 'sistemas_encargado' else []
    systems_incidents = [item for item in commercial_requests if item.get('status') in {'NO APROBADA POR SISTEMAS', 'SUSPENDIDA', 'CANCELADA'}] if role_name == 'sistemas_encargado' else []
    systems_optimization_requests = [item for item in commercial_requests if item.get('status') in fully_approved_statuses and item.get('plant_evaluation', {}).get('feasibility') == 'FACTIBLE' and item.get('status') not in {'FINALIZADA', 'CANCELADA'}] if role_name == 'sistemas_encargado' else []
    optimization_examples = [{
        'cite': item.get('cite'), 'client': item.get('applicant'), 'priority': item.get('priority', 'Media'),
        'feasibility': item.get('plant_evaluation', {}).get('feasibility', 'FACTIBLE'),
        'coverage': item.get('plant_evaluation', {}).get('coverage', 'Disponible'),
        'difficulty': item.get('plant_evaluation', {}).get('difficulty', 'Media'),
        'equipment': item.get('systems_check', {}).get('availability', 'Disponible'),
        'distance': item.get('plant_evaluation', {}).get('distance', '2.5 km'),
        'fitness': 'Pendiente de cálculo',
    } for item in systems_optimization_requests] if role_name == 'sistemas_encargado' else []
    example_requests = [
        {'cite': 'CITE-2026-0150', 'client': 'Andina Logística', 'priority': 'Alta', 'feasibility': 'FACTIBLE', 'coverage': 'Disponible', 'difficulty': 'Alta', 'equipment': 'Disponible', 'distance': '8.0 km', 'fitness': 'Ejemplo'},
        {'cite': 'CITE-2026-0154', 'client': 'Clínica Norte', 'priority': 'Media', 'feasibility': 'FACTIBLE', 'coverage': 'Disponible', 'difficulty': 'Baja', 'equipment': 'Disponible', 'distance': '3.2 km', 'fitness': 'Ejemplo'},
        {'cite': 'CITE-2026-0160', 'client': 'Cooperativa Centro', 'priority': 'Baja', 'feasibility': 'FACTIBLE', 'coverage': 'Disponible', 'difficulty': 'Media', 'equipment': 'Parcial', 'distance': '12.0 km', 'fitness': 'Ejemplo'},
        {'cite': 'CITE-2026-0167', 'client': 'Universidad Sur', 'priority': 'Media', 'feasibility': 'FACTIBLE', 'coverage': 'Disponible', 'difficulty': 'Alta', 'equipment': 'Disponible', 'distance': '5.4 km', 'fitness': 'Ejemplo'},
        {'cite': 'CITE-2026-0171', 'client': 'Planta Industrial', 'priority': 'Alta', 'feasibility': 'FACTIBLE', 'coverage': 'Disponible', 'difficulty': 'Media', 'equipment': 'Disponible', 'distance': '6.1 km', 'fitness': 'Ejemplo'},
    ]
    if role_name == 'sistemas_encargado':
        example_cites = {item['cite'] for item in optimization_examples}
        optimization_examples += [item for item in example_requests if item['cite'] not in example_cites]
    systems_stats = [('SOLICITUDES RECIBIDAS', str(len(systems_requests)), 'Enviadas para verificación'), ('FACTIBLE', str(sum(item.get('plant_evaluation', {}).get('feasibility') == 'FACTIBLE' for item in requests)), 'Trabajos aprobados'), ('NO FACTIBLES', str(sum(item.get('plant_evaluation', {}).get('feasibility') == 'NO FACTIBLE' for item in requests)), 'Trabajos no aprobados'), ('CONCLUIDOS', str(sum(item.get('status') == 'FINALIZADA' for item in requests)), 'Trabajos finalizados')]
    technician_jobs = requests if role_name == 'tecnico' else []
    technician_stats = [('TRABAJOS EN PROCESO', str(sum(item.get('status') in {'ASIGNADA', 'EN EJECUCIÓN'} for item in technician_jobs)), 'Trabajos asignados'), ('TRABAJOS CONCLUIDOS', str(sum(item.get('status') == 'FINALIZADA' for item in technician_jobs)), 'Trabajos finalizados')]
    support_jobs = [item for item in commercial_requests if item.get('assignment') or item.get('systems_check', {}).get('result') == 'APROBADO'] if role_name == 'soporte_sistemas' else []
    support_stats = [('TRABAJOS EN PROCESO', str(sum(item.get('status') in {'ASIGNADA', 'EN EJECUCIÓN'} for item in support_jobs)), 'Trabajos asignados'), ('TRABAJOS CONCLUIDOS', str(sum(item.get('status') == 'FINALIZADA' for item in support_jobs)), 'Trabajos finalizados')]
    data.update({'screen': render_screen, 'selected': selected, 'editing_request': editing_request, 'request_index': request_index, 'profile_role': role_name, 'commercial_requests': commercial_requests, 'plant_requests': plant_requests, 'plant_records': plant_records, 'plant_jobs': plant_jobs, 'plant_incidents': plant_incidents, 'plant_stats': plant_stats, 'systems_requests': systems_requests, 'systems_records': systems_records, 'systems_jobs': systems_jobs, 'systems_incidents': systems_incidents, 'systems_optimization_requests': systems_optimization_requests, 'optimization_examples': optimization_examples, 'systems_stats': systems_stats, 'technician_jobs': technician_jobs, 'technician_stats': technician_stats, 'support_jobs': support_jobs, 'support_stats': support_stats, 'commercial_counts': commercial_counts})
    return render(request, 'workflow.html', data)