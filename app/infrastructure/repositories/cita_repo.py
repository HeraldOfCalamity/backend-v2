from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from string import Template
from typing import Any, Dict, List, Literal, Optional, Tuple
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

async def find_citas_de_especialista_entre(
    especialista_id: str,
    inicio: datetime,
    fin: datetime,
    tenant_id: str 
) -> List[Cita]:
    ini_utc = _as_aware_utc(inicio)
    fin_utc = _as_aware_utc(fin)

    return await Cita.find(And(
        Cita.tenant_id == PydanticObjectId(tenant_id),
        Cita.especialista_id == PydanticObjectId(especialista_id),
        LT(Cita.fecha_inicio, fin_utc),
        GT(Cita.fecha_fin, ini_utc),
        NE(Cita.estado_id, ESTADOS_CITA.cancelada.value),        
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
        GT(Cita.fecha_fin, fecha_inicio),
        NE(Cita.estado_id, ESTADOS_CITA.cancelada.value)
    )).first_or_none()
    return cita is not None

def _overlap(a_start, a_end, b_start, b_end) -> bool:
    return (a_start < b_end) and (a_end > b_start)

async def exists_inactividad_en_rango(
    especialista_id: str,
    inicio_utc_aw: datetime,   # aware UTC
    fin_utc_aw: datetime,      # aware UTC
    tenant_id: str,
) -> Optional[tuple[datetime, datetime, str]]:
    """
    Devuelve (ia_ini_aw, ia_fin_aw, motivo) si alguna inactividad del especialista
    se solapa con [inicio_utc_aw, fin_utc_aw). Caso contrario, None.

    Las inactividades están guardadas como UTC naive -> se convierten a aware UTC.
    """
    esp = await get_especialista_by_id(especialista_id, tenant_id)
    if not esp or not getattr(esp, "inactividades", None):
        return None

    for ia in esp.inactividades:
        # Soporta objetos/beanie o dicts
        ia_desde = getattr(ia, "desde", None) or (ia.get("desde") if isinstance(ia, dict) else None)
        ia_hasta = getattr(ia, "hasta", None) or (ia.get("hasta") if isinstance(ia, dict) else None)
        if not ia_desde or not ia_hasta:
            continue

        ia_ini_aw = _as_aware_utc(ia_desde)
        ia_fin_aw = _as_aware_utc(ia_hasta)

        if ia_ini_aw and ia_fin_aw and _overlap(inicio_utc_aw, fin_utc_aw, ia_ini_aw, ia_fin_aw):
            ia_motivo = getattr(ia, "motivo", None) or (ia.get("motivo") if isinstance(ia, dict) else "") or ""
            return ia_ini_aw, ia_fin_aw, ia_motivo

    return None

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

    ia_hit = await exists_inactividad_en_rango(
        data.especialista_id, dt_utc, fecha_fin_utc, tenant_id
    )
    if ia_hit:
        ia_ini_aw, ia_fin_aw, ia_motivo = ia_hit
        # Mensaje en horario local de la oficina, más claro para el usuario
        ia_ini_local = ia_ini_aw.astimezone(tz)
        ia_fin_local = ia_fin_aw.astimezone(tz)
        rango_str = f"{ia_ini_local.strftime('%d/%m %H:%M')}-{ia_fin_local.strftime('%H:%M')}"
        mensaje = f'El especialista no está disponible en ese horario (inactividad {rango_str}'
        if ia_motivo:
            mensaje += f', motivo: {ia_motivo}'
        mensaje += ').'
        raise raise_duplicate_entity(mensaje)


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

async def get_email_message_cancelacion_inactividad(mailData: MailData, nombre_receptor: str, horarios_html: str) -> str:
    values = {
        **mailData.model_dump(),
        "nombre_receptor": nombre_receptor,
        "horarios_disponibles": horarios_html or ""
    }

    return get_mail_html('cancelacion_mail_template.html', values)


async def _build_horarios_disponibles_html(
    especialista_id: str,
    tenant_id: str,
    max_por_dia: int = 6
) -> str:
    DAY_MAP = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 0: 6}
    tz = await get_office_timezone(tenant_id)
    now_local = datetime.now(tz)

    # Inicio de semana local (Lunes 00:00)
    week_start_local = (now_local - timedelta(days=now_local.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    week_end_local = week_start_local + timedelta(days=7)

    week_start_utc = week_start_local.astimezone(timezone.utc)
    week_end_utc = week_end_local.astimezone(timezone.utc)

    # Datos base
    especialista = await get_especialista_by_id(especialista_id, tenant_id)
    if not especialista:
        return "<p>No se pudo obtener la información del especialista.</p>"

    # Duración de cita (min)
    dur_param = await get_office_config_by_name("duracion_cita_minutos", tenant_id)
    try:
        step = timedelta(minutes=float(dur_param.value))
    except Exception:
        step = timedelta(minutes=45)

    # Citas no canceladas de la semana (para filtrar solapes)
    citas_semana = await Cita.find(And(
        Cita.tenant_id == PydanticObjectId(tenant_id),
        Cita.especialista_id == PydanticObjectId(especialista_id),
        LT(Cita.fecha_inicio, week_end_utc),
        GT(Cita.fecha_fin, week_start_utc),
        NE(Cita.estado_id, ESTADOS_CITA.cancelada.value),
    )).to_list()

    booked = []
    for c in citas_semana:
        b_ini = _as_aware_utc(c.fecha_inicio).astimezone(tz)
        b_fin = _as_aware_utc(c.fecha_fin).astimezone(tz)
        booked.append((b_ini, b_fin))

    # Inactividades del especialista (si existen)
    inacts = []
    for ia in getattr(especialista, "inactividades", []) or []:
        ia_ini = _as_aware_utc(getattr(ia, "desde", None))
        ia_fin = _as_aware_utc(getattr(ia, "hasta", None))
        if ia_ini and ia_fin:
            inacts.append((ia_ini, ia_fin))

    def _overlap(a_start, a_end, b_start, b_end):
        return (a_start < b_end) and (a_end > b_start)

    day_names = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    html_parts = ["<ul>"]

    # Generar slots por día
    for d in range(7):
        date_local = week_start_local + timedelta(days=d)

        # Disponibilidades del día d
        slots_out = []
        for disp in getattr(especialista, "disponibilidades", []) or []:
            disp_index = DAY_MAP.get(getattr(disp, "dia", None), None)
            if disp_index is None or disp_index != d:
                continue
            try:
                h1, m1 = map(int, str(disp.desde).split(":")[:2])
                h2, m2 = map(int, str(disp.hasta).split(":")[:2])
            except Exception:
                continue

            block_start = date_local.replace(hour=h1, minute=m1, second=0, microsecond=0)
            block_end = date_local.replace(hour=h2, minute=m2, second=0, microsecond=0)

            t = block_start
            while t + step <= block_end:
                if t > now_local:
                    slot_end = t + step
                    # Solape con citas (en local)
                    has_cita = any(_overlap(t, slot_end, b_ini, b_fin) for (b_ini, b_fin) in booked)
                    # Solape con inactividades (en UTC)
                    t_utc = t.astimezone(timezone.utc)
                    end_utc = slot_end.astimezone(timezone.utc)
                    has_inact = any(_overlap(t_utc, end_utc, ia_ini, ia_fin) for (ia_ini, ia_fin) in inacts)
                    if not has_cita and not has_inact:
                        slots_out.append(t.strftime("%H:%M"))
                        if len(slots_out) >= max_por_dia:
                            break
                t += step

        if slots_out:
            html_parts.append(f"<li><strong>{day_names[d]} {date_local.strftime('%d/%m')}</strong>: {', '.join(slots_out)}</li>")

    html_parts.append("</ul>")

    # Si no hay nada, devolvemos mensaje corto (evita correo vacío)
    html = "".join(html_parts)
    if html == "<ul></ul>":
        return "<p>No hay horarios disponibles esta semana (o ya pasaron).</p>"
    return html

async def _send_cita_email_cancelacion_inactividad(cita: Cita) -> None:
    office = await get_benedetta_office()
    email_sending_parameter = await get_office_config_by_name('correos_encendidos', str(office.id))
    if email_sending_parameter.value == '0':
        return
    
    
    admin_user = await get_admin_user(str(office.id))
    especialista_user = await get_especialista_profile_by_id(str(cita.especialista_id), str(office.id))
    especialista_full_name = f'{especialista_user.user.name} {especialista_user.user.lastname}'

    paciente_user = await get_paciente_profile_by_id(str(cita.paciente_id), str(office.id))
    paciente_full_name = f'{paciente_user.user.name} {paciente_user.user.lastname}'

    especialidad = await get_especialidad_by_id(str(cita.especialidad_id), str(office.id))
    tz = await get_office_timezone(str(office.id))
    inicio_local = _as_aware_utc(cita.fecha_inicio).astimezone(tz)

    base_data = MailData(
        fecha=inicio_local.strftime('%d/%m/%Y'),
        hora=inicio_local.strftime('%H:%M'),
        nombre_consultorio=office.name,
        nombre_especialidad=especialidad.nombre,
        nombre_especialista=especialista_full_name,
        nombre_paciente=paciente_full_name
    )

    horarios_html = await _build_horarios_disponibles_html(str(cita.especialista_id), str(office.id))

    emails = [
        (await get_email_message_cancelacion_inactividad(base_data, paciente_full_name, horarios_html), paciente_user.user.email),
        (await get_email_message_cancelacion_inactividad(base_data, especialista_full_name, horarios_html), especialista_user.user.email),
        (await get_email_message_cancelacion_inactividad(base_data, admin_user.name, horarios_html), admin_user.email),
    ]
    subject = 'Cancelación de Cita'

    for html, to_addr in emails:
        await send_sendgrid_email(to_addr, subject, html)

async def get_pacientes_con_citas_por_especialista(
    tenant_id: str,
    especialista_id: str,
    estados: Optional[List[str]] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    if not estados:
        estados = ['confirmada', 'pendiente']

    estado_ids: List[int] = []
    for name in estados:
        est = await get_estado_cita_by_name(name, tenant_id)
        if est:
            estado_ids.append(est.estado_id)

    coll = Cita.get_motor_collection()
    pipeline = [
        {
            "$match": {
                "tenant_id": PydanticObjectId(tenant_id),
                "especialista_id": PydanticObjectId(especialista_id),
                "estado_id": {"$in": estado_ids},
            }
        },
        {"$sort": {"fecha_inicio": -1}},
        {
            "$group": {
                "_id": "$paciente_id",
                "last_cita": {"$first": "$fecha_inicio"},
                "last_estado_id": {"$first": "$estado_id"},
                "total": {"$sum": 1},
            }           
        },
        {"$limit": int(limit)}
    ]

    rows = await coll.aggregate(pipeline).to_list(length=None)

    out: List[Dict[str, Any]] = []
    for r in rows:
        pid = r["_id"]
        profile = await get_paciente_profile_by_id(str(pid), tenant_id)
        estado = await get_estado_cita_by_id(int(r.get('last_estado_id', 0)), tenant_id)
        out.append({
            "paciente_id": str(pid),
            "nombre": f"{profile.user.name} {profile.user.lastname}" if profile and profile.user else None,
            "telefono": getattr(profile.user, "phone", None) if profile and profile.user else None,
            "last_cita": r.get("last_cita"),
            "last_estado": estado.nombre if estado else None,
            "total": int(r.get("total", 1)),            
        })
    
    return out

async def cancelar_citas(
    ids: List[str],
    motivo: str,
    tenant_id: str,
    by_user_id: Optional[str] = None,
    enviar_horarios: bool = True
) -> int:
    if not ids:
        return 0
    
    if not motivo:
        raise raise_duplicate_entity('Debe proporcionar un motivo para cancelar.')
    
    estado_cancel = await get_estado_cita_by_id(ESTADOS_CITA.cancelada.value, tenant_id)
    if not estado_cancel:
        raise raise_not_found(f'Estado de cita {ESTADOS_CITA.cancelada.value}')
    
    cancel_user = None
    if by_user_id:
        cancel_user = await get_user_by_id(by_user_id, tenant_id)
    else:
        cancel_user = await get_admin_user(tenant_id)

    actualizadas = 0
    for cid in ids:
        cita = await get_cita_by_id(cid, tenant_id)
        if not cita:
            continue
        if cita.estado_id == estado_cancel.estado_id:
            continue

        cita.estado_id = estado_cancel.estado_id
        cita.canceledBy = cancel_user.id if cancel_user else None
        cita.motivo_cancelacion = motivo
        await cita.save()
        actualizadas += 1

        if enviar_horarios:
            await _send_cita_email_cancelacion_inactividad(cita)
        else:
            await send_cita_email('cancelacion', cita)
    
    return actualizadas