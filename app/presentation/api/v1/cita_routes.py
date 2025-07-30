from fastapi import APIRouter, Depends

from app.core.auth_utils import get_user_and_tenant
from app.core.exceptions import raise_not_found
from app.core.security import require_permission
from app.domain.entities.cita_entity import CitaCreate, CitaOut
from app.infrastructure.repositories.cita_repo import cita_to_out, create_cita, get_citas_by_especialista_id, get_citas_by_paciente_id, get_citas_by_tenant_id
from app.infrastructure.repositories.role_repo import get_role_by_id


router = APIRouter(prefix='/citas', tags=['Citas'])

@router.post('/', response_model=CitaOut, dependencies=[Depends(require_permission('create_appointments'))])
async def agendar_cita(data: CitaCreate, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    cita = await create_cita(data, tenant_id)
    return cita_to_out(cita)

@router.get('/mis-citas', response_model=list[CitaOut])
async def listar_mis_citas(ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    role = await get_role_by_id(str(user.role), tenant_id)
    if not role: 
        raise raise_not_found(f'Rol {user.role}')

    citas = []
    if role.name == 'paciente':
        citas = await get_citas_by_paciente_id(user.id, tenant_id)

    if role.name == 'especialista':
        citas = await get_citas_by_especialista_id(user.id, tenant_id)

    return [cita_to_out(c) for c in citas]

@router.get('/especialista/{especialista_id}', response_model=list[CitaOut])
async def listar_mis_citas(ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    role = await get_role_by_id(str(user.role), tenant_id)
    if not role: 
        raise raise_not_found(f'Rol {user.role}')

    citas = []
    if role.name == 'especialista':
        citas = await get_citas_by_especialista_id(user.id, tenant_id)

    return [cita_to_out(c) for c in citas]

@router.get('/paciente/{paciente_id}', response_model=list[CitaOut])
async def listar_mis_citas(ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    role = await get_role_by_id(str(user.role), tenant_id)
    if not role: 
        raise raise_not_found(f'Rol {user.role}')

    citas = []
    if role.name == 'paciente':
        citas = await get_citas_by_paciente_id(user.id, tenant_id)

    return [cita_to_out(c) for c in citas]

@router.get('/admin', response_model=list[CitaOut], dependencies=[Depends(require_permission('read_appointments'))])
async def listar_citas_todas_admin(ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx

    role = await get_role_by_id(str(user.role), tenant_id)
    if not role: 
        raise raise_not_found(f'Rol {user.role}')
    
    if role.name != 'admin':
        return []
    
    citas = await get_citas_by_tenant_id(tenant_id)
    return [cita_to_out(c) for c in citas]