"""Temporary role provider isolated for an easy Django Auth migration."""

ROLES = {
    'admin': {
        'label': 'Administrador',
        'home': '/',
        'modules': ['INICIO', 'USUARIOS', 'ROLES/ACCESOS', 'CLIENTES', 'TRABAJOS', 'SOLICITUDES', 'INCIDENCIAS', 'PERMISOS'],
    },
    'comercial': {
        'label': 'Personal Comercial',
        'home': '/comercial/',
        'modules': ['INICIO', 'SOLICITUDES', 'NUEVA SOLICITUD', 'EN PROCESO', 'APROBADAS', 'RECHAZADAS', 'OBSERVADAS'],
        'area': 'Comercial',
    },
    'planta_encargado': {
        'label': 'Encargado de Planta Técnica',
        'home': '/planta-tecnica/encargado/',
        'modules': ['INICIO', 'SOLICITUDES', 'REGISTRO', 'TRABAJOS', 'TECNICOS', 'INCIDENCIAS'],
        'area': 'Planta Técnica',
    },
    'tecnico': {
        'label': 'Técnico',
        'home': '/planta-tecnica/tecnico/',
        'modules': ['INICIO', 'MIS TRABAJOS', 'PERMISOS', 'ASISTENCIA'],
        'area': 'Planta Técnica',
    },
    'sistemas_encargado': {
        'label': 'Encargado de Sistemas',
        'home': '/sistemas/',
        'modules': ['INICIO', 'SOLICITUDES', 'REGISTRO', 'TRABAJOS', 'OPTIMIZACIÓN', 'SOPORTE', 'INCIDENCIAS'],
        'area': 'Sistemas',
    },
    'soporte_sistemas': {
        'label': 'Soporte de Sistemas',
        'home': '/sistemas/soporte/',
        'modules': ['INICIO', 'MIS TRABAJOS', 'PERMISOS', 'ASISTENCIA'],
        'area': 'Sistemas',
    },
}

DEMO_USERS = [
    {'full_name': 'Admin Root', 'username': 'admin', 'email': 'admin@datalan.local', 'password': 'admin123', 'role': 'admin', 'active': True, 'last_access': 'Hoy, 09:42'},
    {'full_name': 'Laura Méndez', 'username': 'comercial', 'email': 'laura@datalan.local', 'password': 'comercial123', 'role': 'comercial', 'active': True, 'last_access': 'Ayer, 16:20'},
    {'full_name': 'Diego Ramírez', 'username': 'sistemas', 'email': 'diego@datalan.local', 'password': 'sistemas123', 'role': 'sistemas_encargado', 'active': True, 'last_access': 'Hoy, 08:15'},
    {'full_name': 'Marta Silva', 'username': 'planta', 'email': 'marta@datalan.local', 'password': 'planta123', 'role': 'planta_encargado', 'active': True, 'last_access': 'Lun, 11:06'},
    {'full_name': 'Carlos Torres', 'username': 'tecnico', 'email': 'carlos@datalan.local', 'password': 'tecnico123', 'role': 'tecnico', 'active': True, 'last_access': 'Hoy, 07:50'},
    {'full_name': 'Ana López', 'username': 'soporte', 'email': 'ana@datalan.local', 'password': 'soporte123', 'role': 'soporte_sistemas', 'active': True, 'last_access': 'Hoy, 08:05'},
]


def authenticate(username, password, users=None):
    """Return a safe session identity, ready to be replaced by authenticate()."""
    for user in users or DEMO_USERS:
        if user['username'].lower() == username.strip().lower() and user['password'] == password and user['active']:
            return {'username': user['username'], 'full_name': user['full_name'], 'role': user['role']}
    return None


def role_for(request):
    return ROLES.get(request.session.get('role'))
