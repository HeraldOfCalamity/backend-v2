from fastapi import APIRouter, Depends, status

from app.core.auth_utils import get_user_and_tenant
from app.core.security import require_permission
from app.domain.entities.especialidad_entity import EspecialidadCreate, EspecialidadOut, EspecialidadUpdate
from app.infrastructure.repositories.especialidad_repo import create_especialidad, delete_especialidad, especialidad_to_out, get_especialidades_by_tenant, update_especialidad
from app.infrastructure.repositories.office_repo import get_benedetta_office


router = APIRouter(prefix='/especialidades', tags=['Especialidades'])

@router.post('/', response_model=EspecialidadOut, dependencies=[Depends(require_permission('create_specialties'))])
async def crear_especialidad(data: EspecialidadCreate, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    created = await create_especialidad(data, tenant_id)
    return especialidad_to_out(created)

@router.get('/', response_model=list[EspecialidadOut])
async def listar_especialidades():
    office = await get_benedetta_office()
    especialidades = await get_especialidades_by_tenant(str(office.id))
    return [especialidad_to_out(e) for e in especialidades]

@router.put('/{especialidad_id}', response_model=EspecialidadOut, dependencies=[Depends(require_permission('update_specialties'))])
async def editar_especialidad(especialidad_id: str, data: EspecialidadUpdate, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    especialidad = await update_especialidad(especialidad_id, data, tenant_id)
    return especialidad_to_out(especialidad)

@router.delete('/{especialidad_id}', status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission('delete_specialties'))])
async def eliminar_especialidad(especialidad_id: str, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    await delete_especialidad(especialidad_id, tenant_id)
    return None