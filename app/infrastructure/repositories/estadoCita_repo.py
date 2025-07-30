from beanie import PydanticObjectId
from app.infrastructure.schemas.estadoCita import EstadoCita
from beanie.operators import And


async def get_estado_cita_by_name(name: str, tenant_id: str) -> EstadoCita:
    return await EstadoCita.find_one(And(
        EstadoCita.tenant_id == PydanticObjectId(tenant_id),
        EstadoCita.nombre == name
    ))

async def get_estado_cita_by_id(estado_id: int, tenant_id: str) -> EstadoCita:
    return await EstadoCita.find_one(And(
        EstadoCita.tenant_id == PydanticObjectId(tenant_id),
        EstadoCita.estado_id == estado_id
    ))

def estado_cita_to_out(estado_cita: EstadoCita):
    estado_cita_dict = estado_cita.model_dump()
    estado_cita_dict['id'] = str(estado_cita.estado_id)

    return EstadoCita(**estado_cita_dict)