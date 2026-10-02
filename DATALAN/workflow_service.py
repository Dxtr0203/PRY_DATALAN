"""Persistence adapter for operational requests stored in PostgreSQL."""

from datetime import datetime
import json

from django.db import connection, transaction
from django.utils import timezone

STATUS = ['REGISTRADA', 'EN REVISIÓN PLANTA TÉCNICA', 'FACTIBLE', 'NO FACTIBLE', 'EN REVISIÓN SISTEMAS', 'NO APROBADA POR SISTEMAS', 'APROBADA', 'ASIGNADA', 'EN EJECUCIÓN', 'SUSPENDIDA', 'FINALIZADA', 'CANCELADA']
STATUS_LABELS = {
    'REGISTRADA': 'REGISTRADA', 'EN_REVISION_PLANTA': 'EN REVISIÓN PLANTA TÉCNICA',
    'FACTIBLE': 'FACTIBLE', 'NO_FACTIBLE': 'NO FACTIBLE', 'EN_REVISION_SISTEMAS': 'EN REVISIÓN SISTEMAS',
    'NO_APROBADA_SISTEMAS': 'NO APROBADA POR SISTEMAS', 'APROBADA': 'APROBADA', 'ASIGNADA': 'ASIGNADA',
    'EN_EJECUCION': 'EN EJECUCIÓN', 'SUSPENDIDA': 'SUSPENDIDA', 'FINALIZADA': 'FINALIZADA',
    'CANCELADA': 'CANCELADA', 'RECHAZADA_COMERCIAL': 'RECHAZADA POR COMERCIAL',
}
STATUS_KEYS = {label: key for key, label in STATUS_LABELS.items()}


def now():
    return datetime.now().strftime('%d/%m/%Y %H:%M')


def demo_requests():
    return [{
        'cite': '3840', 'type': 'Instalación Punto a Punto', 'applicant': 'Ejemplo Empresa S.R.L.',
        'email': 'contacto@andina.local', 'origin': '', 'destination': '', 'installation': 'Av. Central 145',
        'commercial_user': 'Laura Méndez', 'requirements': 'Conectividad empresarial de 300 Mbps.',
        'received_at': '02/09/2026 08:40', 'forwarded_at': '02/09/2026 09:05', 'status': 'EN REVISIÓN PLANTA TÉCNICA', 'commercial_status': 'EN PROCESO',
        'priority': 'Alta', 'plant_evaluation': {}, 'systems_check': {}, 'assignment': {}, 'reports': [],
        'history': [{'date': '02/09/2026', 'time': '08:40', 'user': 'Laura Méndez', 'area': 'Comercial', 'action': 'Solicitud registrada', 'note': 'Solicitud recibida del cliente.'}],
    }, {
        'cite': 'CITE-2026-0142', 'type': 'Enlace punto a punto', 'applicant': 'Redes del Sur',
        'email': 'redes@sur.local', 'origin': 'Nodo Norte', 'destination': 'Sucursal Sur', 'installation': '',
        'commercial_user': 'Laura Méndez', 'requirements': 'Enlace dedicado con continuidad operativa.',
        'received_at': '01/09/2026 14:20', 'forwarded_at': '01/09/2026 15:10', 'status': 'ASIGNADA', 'commercial_status': 'APROBADO',
        'priority': 'Media', 'plant_evaluation': {'feasibility': 'FACTIBLE'}, 'systems_check': {'result': 'APROBADO'},
        'assignment': {'leader': 'Carlos Torres', 'others': ['Luis Pérez'], 'date': '03/09/2026'}, 'reports': [],
        'history': [{'date': '01/09/2026', 'time': '14:20', 'user': 'Laura Méndez', 'area': 'Comercial', 'action': 'Solicitud registrada', 'note': 'Solicitud recibida del cliente.'}, {'date': '02/09/2026', 'time': '08:30', 'user': 'Diego Ramírez', 'area': 'Sistemas', 'action': 'Personal asignado', 'note': 'Carlos Torres, técnico líder.'}],
    }, {
        'cite': 'CITE-2026-0136', 'type': 'Instalación Punto Multipunto', 'applicant': 'Cooperativa Horizonte',
        'email': 'contacto@horizonte.local', 'origin': '', 'destination': '', 'installation': 'Zona Industrial Norte',
        'commercial_user': 'Laura Méndez', 'requirements': 'La cobertura solicitada no es técnicamente viable en la zona.',
        'received_at': '30/08/2026 11:15', 'forwarded_at': '30/08/2026 12:00', 'status': 'NO FACTIBLE', 'commercial_status': 'RECHAZADO',
        'priority': 'Baja', 'plant_evaluation': {'feasibility': 'NO FACTIBLE'}, 'systems_check': {}, 'assignment': {}, 'reports': [],
        'history': [{'date': '30/08/2026', 'time': '11:15', 'user': 'Laura Méndez', 'area': 'Comercial', 'action': 'Solicitud registrada', 'note': 'Solicitud enviada a evaluación.'}],
    }, {
        'cite': 'CITE-2026-0131', 'type': 'Instalación Punto a Punto', 'applicant': 'Clínica Santa María',
        'email': 'infraestructura@santamaria.local', 'origin': 'Av. Salud 120', 'destination': 'Sucursal Centro', 'installation': '',
        'commercial_user': 'Laura Méndez', 'requirements': 'Falta confirmar las coordenadas exactas del punto destino.',
        'received_at': '28/08/2026 09:30', 'forwarded_at': '', 'status': 'REGISTRADA', 'commercial_status': 'OBSERVADO',
        'priority': 'Media', 'plant_evaluation': {}, 'systems_check': {}, 'assignment': {}, 'reports': [],
        'history': [{'date': '28/08/2026', 'time': '09:30', 'user': 'Laura Méndez', 'area': 'Comercial', 'action': 'Solicitud observada', 'note': 'Se requiere completar información de ubicación.'}],
    }]


REQUESTS = demo_requests()


def _database_ready():
    with connection.cursor() as cursor:
        cursor.execute("SELECT to_regclass('datalan.solicitudes')")
        ready = cursor.fetchone()[0] is not None
    if not ready:
        raise RuntimeError('No se encontró datalan.solicitudes; inicializa el esquema PostgreSQL antes de usar el flujo.')
    return True


def _request_from_row(row):
    raw_data = row[0] or {}
    data = json.loads(raw_data) if isinstance(raw_data, str) else dict(raw_data)
    data.update({
        'request_id': str(row[1]),
        'cite': row[2],
        'received_at': row[3].strftime('%d/%m/%Y %H:%M') if row[3] else '',
        'forwarded_at': row[4].strftime('%d/%m/%Y %H:%M') if row[4] else '',
        'approved_at': row[5].strftime('%d/%m/%Y %H:%M') if row[5] else '',
        'concluded_at': row[6].strftime('%d/%m/%Y %H:%M') if row[6] else '',
        'status': STATUS_LABELS.get(row[7], row[7]),
        'type': row[8],
        'priority': row[9],
        'applicant': row[10],
        'email': row[11],
    })
    data.setdefault('plant_evaluation', {})
    data.setdefault('systems_check', {})
    data.setdefault('assignment', {})
    data.setdefault('reports', [])
    data.setdefault('history', [])
    return data


def get_requests(session=None):
    _database_ready()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT r.extra_data, r.request_id, r.cite, r.received_at, r.forwarded_at,
                   r.approved_at, r.concluded_at, s.status_key, st.label, p.label,
                   c.legal_name, COALESCE(rc.email, c.email, '')
            FROM datalan.solicitudes r
            JOIN datalan.estados_solicitud s ON s.status_id = r.current_status_id
            JOIN datalan.tipos_servicio st ON st.service_type_id = r.service_type_id
            JOIN datalan.prioridades p ON p.priority_id = r.priority_id
            JOIN datalan.clientes c ON c.client_id = r.client_id
            LEFT JOIN datalan.contactos_solicitud rc ON rc.request_id = r.request_id
            ORDER BY r.received_at DESC
        """)
        return [_request_from_row(row) for row in cursor.fetchall()]


def save_requests(session, requests):
    _database_ready()
    with transaction.atomic():
        for item in requests:
            _save_request(item)


def _database_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    parsed = datetime.strptime(value, '%d/%m/%Y %H:%M')
    return timezone.make_aware(parsed)


def _save_request(item):
    with connection.cursor() as cursor:
        cursor.execute("SELECT user_id FROM datalan.usuarios WHERE full_name = %s LIMIT 1", [item.get('commercial_user', 'Admin Root')])
        commercial_user_id = cursor.fetchone()
        if not commercial_user_id:
            cursor.execute("SELECT user_id FROM datalan.usuarios ORDER BY user_id LIMIT 1")
            commercial_user_id = cursor.fetchone()
        cursor.execute("SELECT client_id FROM datalan.clientes WHERE legal_name = %s LIMIT 1", [item.get('applicant', 'Sin cliente')])
        client_id = cursor.fetchone()
        if not client_id:
            cursor.execute("INSERT INTO datalan.clientes (legal_name, email) VALUES (%s, %s) RETURNING client_id", [item.get('applicant', 'Sin cliente'), item.get('email', '')])
            client_id = cursor.fetchone()
        cursor.execute("SELECT service_type_id FROM datalan.tipos_servicio WHERE lower(label) = lower(%s) OR lower(%s) LIKE '%%' || lower(service_key) || '%%' LIMIT 1", [item.get('type', ''), item.get('type', '')])
        service_type_id = cursor.fetchone()
        if not service_type_id:
            cursor.execute("SELECT service_type_id FROM datalan.tipos_servicio ORDER BY service_type_id LIMIT 1")
            service_type_id = cursor.fetchone()
        cursor.execute("SELECT priority_id FROM datalan.prioridades WHERE lower(label) = lower(%s) LIMIT 1", [item.get('priority', 'Media')])
        priority_id = cursor.fetchone()
        status = item.get('status', 'REGISTRADA')
        cursor.execute("SELECT status_id FROM datalan.estados_solicitud WHERE status_key = %s LIMIT 1", [STATUS_KEYS.get(status, status)])
        status_id = cursor.fetchone()
        if not all((commercial_user_id, client_id, service_type_id, priority_id, status_id)):
            raise ValueError(f'No se pudo resolver una relación PostgreSQL para la solicitud {item.get("cite", "sin CITE")} .')
        cursor.execute("""
            INSERT INTO datalan.solicitudes
                (cite, client_id, service_type_id, priority_id, current_status_id,
                 commercial_user_id, requirements, received_at, forwarded_at,
                 approved_at, concluded_at, extra_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (cite) DO UPDATE SET
                client_id = EXCLUDED.client_id,
                service_type_id = EXCLUDED.service_type_id,
                priority_id = EXCLUDED.priority_id,
                current_status_id = EXCLUDED.current_status_id,
                commercial_user_id = EXCLUDED.commercial_user_id,
                requirements = EXCLUDED.requirements,
                received_at = EXCLUDED.received_at,
                forwarded_at = EXCLUDED.forwarded_at,
                approved_at = EXCLUDED.approved_at,
                concluded_at = EXCLUDED.concluded_at,
                extra_data = EXCLUDED.extra_data,
                updated_at = now()
            RETURNING request_id
        """, [item.get('cite'), client_id[0], service_type_id[0], priority_id[0], status_id[0], commercial_user_id[0], item.get('requirements', ''), _database_datetime(item.get('received_at')), _database_datetime(item.get('forwarded_at')), _database_datetime(item.get('approved_at')), _database_datetime(item.get('concluded_at')), json.dumps(item)])
        item['request_id'] = str(cursor.fetchone()[0])


def add_history(request_item, user, area, action, note=''):
    stamp = datetime.now()
    request_item['history'].append({'date': stamp.strftime('%d/%m/%Y'), 'time': stamp.strftime('%H:%M'), 'user': user, 'area': area, 'action': action, 'note': note})