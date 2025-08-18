from fastapi import APIRouter, Depends, status

from app.core.auth_utils import get_user_and_tenant
from app.core.security import require_permission
from app.domain.entities.tratamiento_entity import TratamientoCreate, TratamientoOut, TratamientoUpdate
from app.infrastructure.repositories.office_repo import get_benedetta_office
from app.infrastructure.repositories.tratamiento_repo import create_tratamiento, delete_tratamiento, get_tratamientos_by_tenant, tratamiento_to_out, update_tratamiento


router = APIRouter(prefix='/tratamientos', tags=['Tratamientos'])

@router.post('/', response_model=TratamientoOut, dependencies=[Depends(require_permission('create_tratamientos'))])
async def crear_tratamiento(data: TratamientoCreate, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    created = await create_tratamiento(data, tenant_id)
    return tratamiento_to_out(created)

@router.get('/', response_model=list[TratamientoOut])
async def listar_tratamientos():
    office = await get_benedetta_office()
    tratamientos = await get_tratamientos_by_tenant(str(office.id))
    return [tratamiento_to_out(t) for t in tratamientos]

@router.put('/{tratamiento_id}', response_model=TratamientoOut, dependencies=[Depends(require_permission('update_tratamientos'))])
async def editar_tratamiento(tratamiento_id: str, data: TratamientoUpdate, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    tratamiento = await update_tratamiento(tratamiento_id, data, tenant_id)
    return tratamiento_to_out(tratamiento)

@router.delete('/{tratamiento_id}', status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission('delete_tratamientos'))])
async def eliminar_tratamiento(tratamiento_id: str, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    await delete_tratamiento(tratamiento_id, tenant_id)
    return None