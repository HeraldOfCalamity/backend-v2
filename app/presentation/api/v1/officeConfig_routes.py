from fastapi import APIRouter, Depends

from app.core.auth_utils import get_tenant, get_user_and_tenant
from app.core.security import require_permission
from app.domain.entities.officeConfig_entity import OfficeConfigOut, OfficeConfigUpdate
from app.infrastructure.repositories.officeConfig_repo import get_office_config, office_config_to_out, update_office_config
from app.infrastructure.repositories.office_repo import get_benedetta_office


router = APIRouter(prefix='/config', tags=['Configuracion'])


@router.get('/', response_model=list[OfficeConfigOut])
async def obtener_parametros(tenant_id=Depends(get_tenant)):
    config = await get_office_config(tenant_id)
    return [office_config_to_out(oc) for oc in config]

@router.put('/{config_id}', response_model=OfficeConfigOut, dependencies=[Depends(require_permission('update_office_config'))])
async def actualizar_parametro(config_id: str, data: OfficeConfigUpdate, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    updated = await update_office_config(config_id, data, tenant_id)
    return office_config_to_out(updated);