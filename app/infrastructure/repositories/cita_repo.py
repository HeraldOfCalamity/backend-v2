from datetime import datetime, timedelta
from beanie import PydanticObjectId
from app.application.services.notification_service import notificar_evento_cita
from app.core.exceptions import raise_duplicate_entity, raise_not_found
from app.domain.entities.cita_entity import CitaCreate, CitaOut
from app.infrastructure.repositories.especialidad_repo import especialidad_to_out, get_especialidad_by_id
from app.infrastructure.repositories.especialista_repo import especialista_to_out, get_especialista_by_id
from app.infrastructure.repositories.estadoCita_repo import estado_cita_to_out, get_estado_cita_by_id, get_estado_cita_by_name
from app.infrastructure.repositories.officeConfig_repo import get_office_config_by_name
from app.infrastructure.repositories.paciente_repo import get_paciente_by_id, paciente_to_out
from app.infrastructure.schemas.cita import Cita
from beanie.operators import And, GTE, LTE, LT, GT

from app.infrastructure.schemas.estadoCita import ESTADOS_CITA

async def get_cita_by_id(cita_id: str, tenant_id: str) -> Cita:
    return await Cita.find_one(And(
        Cita.tenant_id == PydanticObjectId(tenant_id),
        Cita.id == PydanticObjectId(cita_id)
    ))

async def get_citas_by_paciente_id(paciente_id: str, tenant_id: str) -> list[Cita]:
    return await Cita.find(And(
        Cita.tenant_id == PydanticObjectId(tenant_id),
        Cita.paciente_id == PydanticObjectId(paciente_id)
    )).to_list()

async def get_citas_by_especialista_id(especialista_id: str, tenant_id: str) -> list[Cita]:
    return await Cita.find(And(
        Cita.tenant_id == PydanticObjectId(tenant_id),
        Cita.especialista_id == PydanticObjectId(especialista_id)
    )).to_list()

async def exists_cita_same_day(paciente_id: str, especialista_id: str, fecha: datetime, tenant_id: str) -> bool:
    inicio_dia=fecha.replace(hour=0, minute=0, second=0, microsecond=0)
    fin_dia=fecha.replace(hour=23, minute=59, second=59, microsecond=999999)

    return await Cita.find(And(
        Cita.tenant_id == PydanticObjectId(tenant_id),
        Cita.paciente_id == PydanticObjectId(paciente_id),
        Cita.especialista_id == PydanticObjectId(especialista_id),
        And(
            GTE(Cita.fecha_inicio, inicio_dia),
            LTE(Cita.fecha_inicio, fin_dia)
        )
    )).first_or_none() is not None

async def exists_solapamiento(especialista_id: str, fecha_inicio: datetime, fecha_fin: datetime, tenant_id: str) -> bool:
    return await Cita.find(And(
        Cita.tenant_id == PydanticObjectId(tenant_id),
        Cita.especialista_id == PydanticObjectId(especialista_id),
        LT(Cita.fecha_inicio, fecha_fin),
        GT(Cita.fecha_fin, fecha_inicio)
    )).first_or_none() is not None

async def create_cita(data: CitaCreate, tenant_id: str) -> Cita:
    duracion_parameter = await get_office_config_by_name('duracion_cita_minutos', tenant_id);
    duracion = timedelta(minutes=float(duracion_parameter.value))
    fecha_fin = data.fecha_inicio + duracion

    if not await get_paciente_by_id(data.paciente_id, tenant_id):
        raise_not_found('Paciente')

    if not await get_especialista_by_id(data.especialista_id, tenant_id):
        raise_not_found('Especialista')

    if not await get_especialidad_by_id(data.especialidad_id, tenant_id):
        raise_not_found('Especialidad')

    if await exists_solapamiento(data.especialista_id, data.fecha_inicio,fecha_fin, tenant_id):
        raise raise_duplicate_entity(f'Cita con la hora seleccionada para el especialista')
    
    if await exists_cita_same_day(data.paciente_id, data.especialista_id, data.fecha_inicio, tenant_id):
        raise raise_duplicate_entity('El paciente ya teiene una cita con este especilista el mismo dia')
    
    confirmacion_parameter = await get_office_config_by_name('confirmacion_automatica', tenant_id)

    estado_inicial = ESTADOS_CITA.confirmada if confirmacion_parameter.value else ESTADOS_CITA.pendiente

    estado = await get_estado_cita_by_id(estado_inicial.value, tenant_id)
    if not estado:
        raise raise_not_found(f'Estado de cita {estado_inicial}')
    
    cita = Cita(
        paciente_id=PydanticObjectId(data.paciente_id),
        especialista_id=PydanticObjectId(data.especialista_id),
        fecha_inicio=data.fecha_inicio,
        fecha_fin=fecha_fin,
        duration_minutes=int(duracion_parameter.value),
        motivo=data.motivo,
        estado_id=estado.estado_id,
        tenant_id=PydanticObjectId(tenant_id),
        especialidad_id=data.especialidad_id
    )

    cita_guardada = await cita.insert()

    await notificar_evento_cita('creada', f'{cita_guardada.id} {cita_guardada.fecha_inicio} {cita_guardada.fecha_fin}')

    return cita_guardada


async def cita_to_out(cita: Cita) -> CitaOut:
    paciente = await get_paciente_by_id(str(cita.paciente_id), str(cita.tenant_id))
    especialista = await get_especialista_by_id(str(cita.especialista_id), str(cita.tenant_id))
    especialidad = await get_especialidad_by_id(str(cita.especialidad_id), str(cita.tenant_id))
    estado = await get_estado_cita_by_id(cita.estado_id, str(cita.tenant_id))

    cita_out = CitaOut(
        id=str(cita.id),
        paciente=paciente_to_out(paciente) if paciente else None,
        duration_minutes=cita.duration_minutes,
        especialidad=especialidad_to_out(especialidad) if especialidad else None,
        especialista=especialista_to_out(especialista) if especialista else None,
        estado=estado_cita_to_out(estado) if estado else None,
        fecha_fin=cita.fecha_fin,
        fecha_inicio=cita.fecha_inicio,
        motivo=cita.motivo,
    )

    return cita_out

async def get_citas_by_tenant_id(tenant_id: str) -> list[Cita]:
    return await Cita.find(Cita.tenant_id == PydanticObjectId(tenant_id)).to_list()