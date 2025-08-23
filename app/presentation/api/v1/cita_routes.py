from fastapi import APIRouter, Depends

from app.core.auth_utils import get_user_and_tenant
from app.core.exceptions import raise_not_found
from app.core.security import require_permission
from app.domain.entities.cita_entity import CitaCreate, CitaOut
from app.infrastructure.repositories.cita_repo import cancel_cita, cita_to_out, confirm_cita, create_cita, get_citas_by_especialista_id, get_citas_by_paciente_id, get_citas_by_tenant_id, send_cita_email
from app.infrastructure.repositories.role_repo import get_role_by_id
from app.shared.dto.mailData_dto import MailData


router = APIRouter(prefix='/citas', tags=['Citas'])

@router.post('/', response_model=CitaOut, dependencies=[Depends(require_permission('create_appointments'))])
async def agendar_cita(data: CitaCreate, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    cita = await create_cita(data, tenant_id)
    cita_out = await cita_to_out(cita)
    # role = await get_role_by_id(str(user.role), tenant_id)
    await send_cita_email('reserva', cita)
    return cita_out

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

    return [await cita_to_out(c) for c in citas]

@router.get('/especialista/{especialista_id}', response_model=list[CitaOut])
async def listar_mis_citas(especialista_id: str, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    citas = await get_citas_by_especialista_id(especialista_id, tenant_id)

    return [await cita_to_out(c) for c in citas]

@router.get('/paciente/{paciente_id}', response_model=list[CitaOut])
async def listar_mis_citas(paciente_id: str, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    citas = await get_citas_by_paciente_id(paciente_id, tenant_id)

    return [await cita_to_out(c) for c in citas]

@router.get('/admin', response_model=list[CitaOut], dependencies=[Depends(require_permission('read_appointments'))])
async def listar_citas_todas_admin(ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx

    role = await get_role_by_id(str(user.role), tenant_id)
    if not role: 
        raise raise_not_found(f'Rol {user.role}')
    
    if role.name != 'admin':
        return []
    
    citas = await get_citas_by_tenant_id(tenant_id)
    return [await cita_to_out(c) for c in citas]

@router.put('/cancelar/{cita_id}', response_model=CitaOut, dependencies=[Depends(require_permission('cancel_appointments'))])
async def cancelar_cita(cita_id: str, ctx=Depends(get_user_and_tenant)):
    user, tenant_id=ctx
    canceled = await cancel_cita(cita_id, tenant_id, str(user.id))
    cita_out = await cita_to_out(canceled)
    await send_cita_email('cancelacion', canceled)
    return cita_out

@router.put('/confirmar/{cita_id}', response_model=CitaOut, dependencies=[Depends(require_permission('confirm_appointments'))])
async def cancelar_cita(cita_id: str, ctx=Depends(get_user_and_tenant)):
    user, tenant_id=ctx
    confirmed = await confirm_cita(cita_id, tenant_id)
    cita_out = await cita_to_out(confirmed)
    await send_cita_email('confirmacion', confirmed)
    return cita_out