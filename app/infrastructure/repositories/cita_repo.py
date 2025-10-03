from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from string import Template
from typing import Literal, Optional, Tuple
from beanie import PydanticObjectId
from pydantic import EmailStr
# from app.application.services.notification_service import notificar_evento_cita
from app.core.exceptions import raise_duplicate_entity, raise_forbidden, raise_not_found
from app.core.config import settings
from app.domain.entities.cita_entity import CitaCreate, CitaOut
from app.infrastructure.notifiers.email_notifier import send_sendgrid_email
from app.infrastructure.repositories.especialidad_repo import especialidad_to_out, get_especialidad_by_id
from app.infrastructure.repositories.especialista_repo import especialista_to_out, get_especialista_by_id, get_especialista_profile_by_id
from app.infrastructure.repositories.estadoCita_repo import estado_cita_to_out, get_estado_cita_by_id, get_estado_cita_by_name
from app.infrastructure.repositories.officeConfig_repo import get_office_config_by_name, get_office_timezone
from app.infrastructure.repositories.office_repo import get_benedetta_office
from app.infrastructure.repositories.paciente_repo import get_paciente_by_id, get_paciente_profile_by_id, get_pacientes_with_user, paciente_to_out
from app.infrastructure.repositories.user_repo import get_admin_user, get_user_by_id, user_to_out
from app.infrastructure.schemas.cita import Cita
from beanie.operators import And, GTE, LTE, LT, GT, NE

from app.infrastructure.schemas.estadoCita import ESTADOS_CITA
from app.shared.dto.mailData_dto import MailData, ReceiverData
from app.shared.utils import get_mail_html


async def get_cita_by_id(cita_id: str, tenant_id: str) -> Cita:
    return await Cita.find(And(
        Cita.tenant_id == PydanticObjectId(tenant_id),
        Cita.id == PydanticObjectId(cita_id)
    )).first_or_none()

async def get_citas_by_paciente_id(paciente_id: str, tenant_id: str) -> list[Cita]:
    return await Cita.find(And(
        Cita.tenant_id == PydanticObjectId(tenant_id),
        Cita.paciente_id == PydanticObjectId(paciente_id)
    )).to_list()

async def get_citas_by_especialista_id(
    especialista_id: str,
    tenant_id: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = 200,
    skip: int = 0,
):
    filtros = [
        Cita.tenant_id == PydanticObjectId(tenant_id),
        Cita.especialista_id == PydanticObjectId(especialista_id)
    ]
    if start:
        filtros.append(GTE(Cita.fecha_inicio, start))
    if end:
        filtros.append(LTE(Cita.fecha_inicio, end))

    cursor = Cita.find(And(*filtros)).sort(-Cita.fecha_inicio)  # más recientes primero
    if skip:
        cursor = cursor.skip(skip)
    if limit:
        cursor = cursor.limit(limit)
    return await cursor.to_list()

async def exists_cita_same_day(paciente_id: str, especialista_id: str, fecha_ref_utc: datetime, tenant_id: str, exclude_cita_id: str | None = None) -> bool:
    tz = await get_office_timezone(tenant_id)
    dt_local = fecha_ref_utc.astimezone(tz)

    start_local = dt_local.replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = start_local + timedelta(days=1)

    start_utc = start_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)
    
    filters = [
        Cita.tenant_id == PydanticObjectId(tenant_id),
        Cita.paciente_id == PydanticObjectId(paciente_id),
        Cita.especialista_id == PydanticObjectId(especialista_id),
        GTE(Cita.fecha_inicio, start_utc),
        LT(Cita.fecha_inicio, end_utc),
        Cita.estado_id != ESTADOS_CITA.cancelada.value,  # ignora canceladas
    ]

    if exclude_cita_id:
        filters.append(NE(Cita.id, PydanticObjectId(exclude_cita_id)))
    
    count = await Cita.find(And(*filters)).count()
    return count > 0
    

async def exists_solapamiento(especialista_id: str, fecha_inicio: datetime, fecha_fin: datetime, tenant_id: str) -> bool:
    cita = await Cita.find(And(
        Cita.tenant_id == PydanticObjectId(tenant_id),
        Cita.especialista_id == PydanticObjectId(especialista_id),
        LT(Cita.fecha_inicio, fecha_fin),
        GT(Cita.fecha_fin, fecha_inicio)
    )).first_or_none()
    return cita is not None

async def create_cita(data: CitaCreate, tenant_id: str) -> Cita:
    duracion_parameter = await get_office_config_by_name('duracion_cita_minutos', tenant_id);
    duracion = timedelta(minutes=float(duracion_parameter.value))

    tz = await get_office_timezone(tenant_id)
    dt_local = data.fecha_inicio
    if dt_local.tzinfo is None:
        dt_local = dt_local.replace(tzinfo=tz)
    else:
        dt_local = dt_local.astimezone(tz)
    
    dt_utc = dt_local.astimezone(timezone.utc)

    fecha_fin_utc = dt_utc + duracion

    paciente = await get_paciente_profile_by_id(data.paciente_id, tenant_id)

    if not paciente:
        raise_not_found('Paciente')

    especialista = await get_especialista_profile_by_id(data.especialista_id, tenant_id)
    if not especialista:
        raise_not_found('Especialista')

    if not await get_especialidad_by_id(data.especialidad_id, tenant_id):
        raise_not_found('Especialidad')

    if await exists_solapamiento(data.especialista_id, dt_utc, fecha_fin_utc, tenant_id):
        raise raise_duplicate_entity(f'Cita con la hora seleccionada para el especialista')
    
    if await exists_cita_same_day(data.paciente_id, data.especialista_id, dt_utc, tenant_id):
        raise raise_duplicate_entity('El paciente ya teiene una cita con este especilista el mismo dia')
    
    confirmacion_parameter = await get_office_config_by_name('confirmacion_automatica', tenant_id)

    estado_inicial = ESTADOS_CITA.confirmada if confirmacion_parameter.value == '1' else ESTADOS_CITA.pendiente

    estado = await get_estado_cita_by_id(estado_inicial.value, tenant_id)
    if not estado:
        raise raise_not_found(f'Estado de cita {estado_inicial}')
    
    cita = Cita(
        paciente_id=PydanticObjectId(data.paciente_id),
        especialista_id=PydanticObjectId(data.especialista_id),
        paciente_name=f'{paciente.user.name} {paciente.user.lastname}',
        especialista_name=f'{especialista.user.name} {especialista.user.lastname}',
        fecha_inicio=dt_utc,
        fecha_fin=fecha_fin_utc,
        duration_minutes=int(duracion_parameter.value),
        motivo=data.motivo,
        estado_id=estado.estado_id,
        tenant_id=PydanticObjectId(tenant_id),
        especialidad_id=data.especialidad_id
    )

    cita_guardada = await cita.insert()

    # await notificar_evento_cita(estado.nombre, f'{cita_guardada.id} {cita_guardada.fecha_inicio} {cita_guardada.fecha_fin}')

    return cita_guardada

async def confirm_cita(cita_id: str, tenant_id: str) -> Cita:
    cita = await Cita.find(And(
        Cita.tenant_id == PydanticObjectId(tenant_id),
        Cita.id == PydanticObjectId(cita_id)
    )).first_or_none();

    if not cita:
        raise raise_not_found('Cita')
    
    estado_cita = await get_estado_cita_by_id(cita.estado_id, tenant_id)
    if estado_cita.nombre != ESTADOS_CITA.pendiente.name:
        raise raise_duplicate_entity('La cita tiene un estado distindo a pendiente')

    estado = await get_estado_cita_by_id(ESTADOS_CITA.confirmada.value, tenant_id)
    if not estado:
        raise raise_not_found(f'Estado de cita {ESTADOS_CITA.confirmada.value}')
    
    cita.estado_id=estado.estado_id

    cita_guardada = await cita.save()
    # await notificar_evento_cita(estado.nombre, f'{cita_guardada.id} {cita_guardada.fecha_inicio} {cita_guardada.fecha_fin}')
    return cita_guardada

async def set_attended_cita(cita_id: str, tenant_id: str) -> Cita:
    cita = await get_cita_by_id(cita_id, tenant_id);

    if not cita:
        raise raise_not_found('Cita')
    
    cita.estado_id = ESTADOS_CITA.atendida.value

    cita_guardada = await cita.save()

    return cita_guardada

async def cancel_cita(cita_id: str, tenant_id: str, user_id: str, motivo: str) -> Cita:
    cita = await Cita.find(And(
        Cita.tenant_id == PydanticObjectId(tenant_id),
        Cita.id == PydanticObjectId(cita_id)
    )).first_or_none()

    if not cita:
        raise raise_not_found('Cita')
    
    if cita.canceledBy:
        raise raise_duplicate_entity('La cita ya se encuentra cancelada');
    
    if not motivo:
        raise raise_duplicate_entity('Debe proporcionar un motivo para cancelar la cita.')

    estado = await get_estado_cita_by_id(ESTADOS_CITA.cancelada.value, tenant_id)
    if not estado:
        raise raise_not_found(f'Estado de cita {ESTADOS_CITA.cancelada.value}')
    
    
    user = await get_user_by_id(user_id, tenant_id)
    if not estado:
        raise raise_not_found(f'Estado de cita {ESTADOS_CITA.cancelada.value}')
    
    cita.estado_id=estado.estado_id
    cita.canceledBy=user.id
    cita.motivo_cancelacion=motivo

    cita_guardada = await cita.save()
    # await notificar_evento_cita(estado.nombre, f'{cita_guardada.id} {cita_guardada.fecha_inicio} {cita_guardada.fecha_fin}')

    

    return cita_guardada

def _as_aware_utc(dt):
    if dt is None:
        return None
    
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)

async def cita_to_out(cita: Cita) -> CitaOut:

    # paciente = await get_paciente_profile_by_id(str(cita.paciente_id), str(cita.tenant_id))
    
    # especialista = await get_especialista_profile_by_id(str(cita.especialista_id), str(cita.tenant_id))
    tenant_id = str(cita.tenant_id)
    tz = await get_office_timezone(tenant_id)

    inicio_utc = _as_aware_utc(cita.fecha_inicio)
    fin_utc = _as_aware_utc(cita.fecha_fin)

    inicio_local_aw = inicio_utc.astimezone(tz) if inicio_utc else None
    fin_local_aw = fin_utc.astimezone(tz) if fin_utc else None

    # import logging
    # logger = logging.getLogger("app.cita_to_out")
    # logger.info("cita_to_out | utc=%s -> local=%s tz=%s",
    #             cita.fecha_inicio.isoformat() if cita.fecha_inicio else None,
    #             inicio_local_aw.isoformat() if inicio_local_aw else None,
    #             getattr(tz, "key", str(tz)))

    especialidad = await get_especialidad_by_id(str(cita.especialidad_id), str(cita.tenant_id))
    estado = await get_estado_cita_by_id(cita.estado_id, str(cita.tenant_id))
    
    canceledByUser = None
    if cita.canceledBy:
        canceledByUser = await get_user_by_id(cita.canceledBy, str(cita.tenant_id))

    cita_out = CitaOut(
        id=str(cita.id),
        paciente=str(cita.paciente_id),
        pacienteName=cita.paciente_name if cita.paciente_name else '',
        duration_minutes=cita.duration_minutes,
        especialidad=especialidad.nombre,
        especialista=cita.especialista_name if cita.especialista_name else '',
        estado=estado_cita_to_out(estado) if estado else None,
        fecha_fin=fin_local_aw,
        fecha_inicio=inicio_local_aw,
        motivo=cita.motivo,
        cancel_motivo=cita.motivo_cancelacion,
        canceledBy=user_to_out(canceledByUser) if canceledByUser else None,
        
    )

    return cita_out

async def get_citas_by_tenant_id(tenant_id: str) -> list[Cita]:
    return await Cita.find(Cita.tenant_id == PydanticObjectId(tenant_id)).to_list()

async def send_cita_email(event: Literal['reserva', 'confirmacion', 'cancelacion', 'recordatorio'], cita: Cita) -> None:

    office = await get_benedetta_office()

    email_sending_parameter = await get_office_config_by_name('correos_encendidos', str(office.id))

    if email_sending_parameter.value == '0':
        return
        # raise raise_forbidden('El envio de correos esta desactivado, activelo pasando el valor de 1 al parametro "correos_encendidos" en la pagina de configuraciones.')

    data: list[Tuple[str, EmailStr]] = []

    admin_user = await get_admin_user(str(office.id))

    especialista_user = await get_especialista_profile_by_id(str(cita.especialista_id), str(office.id))
    especialista_full_name = f'{especialista_user.user.name} {especialista_user.user.lastname}'

    paciente_user = await get_paciente_profile_by_id(str(cita.paciente_id), str(office.id))
    paciente_full_name = f'{paciente_user.user.name} {paciente_user.user.lastname}'

    especialidad = await get_especialidad_by_id(str(cita.especialidad_id), str(office.id))

    tz = await get_office_timezone(str(office.id))
    inicio_local = cita.fecha_inicio.astimezone(tz)

    base_data = MailData(
        fecha=inicio_local.strftime('%d/%m/%Y'),
        hora=inicio_local.strftime('%H:%M'),
        nombre_consultorio=office.name,
        nombre_especialidad=especialidad.nombre,
        nombre_especialista=especialista_full_name,
        nombre_paciente=paciente_full_name
    )

    data = list[Tuple[str, EmailStr]]
    if event == 'recordatorio':
        data = [
            (get_email_message(event, base_data, nombre_receptor=paciente_full_name), paciente_user.user.email),
        ]
        
        mail_subject = 'Recordatorio Cita'
    else:


        data = [
            (get_email_message(event, base_data, nombre_receptor=paciente_full_name), paciente_user.user.email),
            (get_email_message(event, base_data, nombre_receptor=especialista_full_name), especialista_user.user.email),
            (get_email_message(event, base_data, nombre_receptor=admin_user.name), admin_user.email),
        ]

        mail_subject = f'{event.capitalize()} de Cita'

    for mail in data:
        await send_sendgrid_email(mail[1], mail_subject ,mail[0])


def get_email_message(event: Literal['reserva', 'confirmacion', 'cancelacion', 'recordatorio'], mailData: MailData, nombre_receptor: str) -> str:
    if event == 'reserva':
        mail_template_name = 'reserva_mail_template.html'
        
    if event == 'cancelacion':
        mail_template_name = 'cancelacion_mail_template.html'

    if event == 'confirmacion':
        mail_template_name = 'confirmacion_mail_template.html'
    
    if event == 'recordatorio':
        mail_template_name = 'recordatorio_mail_template.html'

    values = {
        **mailData.model_dump(),
        'nombre_receptor':nombre_receptor
    }

    if event == 'recordatorio':
        values['cta_url'] = settings.FRONTEND_APP_URL

    html = get_mail_html(mail_template_name, values)

    return html
