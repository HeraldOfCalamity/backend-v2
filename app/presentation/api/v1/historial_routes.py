from fastapi import APIRouter, Depends, Query

from app.core.auth_utils import get_tenant, get_user_and_tenant
from app.core.exceptions import raise_not_found
from app.domain.entities.historial_entity import EntradaAdd, HistorialCreate, PresignReq, RegisterImageReq
from app.infrastructure.repositories.historial_repo import add_entrada, create_historial, get_historial_by_paciente_id, presign_upload, register_image, signed_get


router = APIRouter(prefix='/historiales', tags=['Historiales'])

@router.post('/upload/presign')
def historial_presign_upload(body: PresignReq):
    return presign_upload(body)

@router.post('/upload/register')
async def historial_register_image(body: RegisterImageReq):
    # user, tenant_id = ctx
    tenant_id = await get_tenant()
    return await register_image(body, tenant_id)

@router.get('/images/signed-get')
def historial_signed_get(key: str = Query(...)):
    return signed_get(key)

@router.post('/')
async def crear_historial(body: HistorialCreate):
    # user, tenant_id = ctx
    tenant_id = await get_tenant()
    return await create_historial(body, tenant_id)
    

@router.post('/{historial_id}/entradas')
async def historial_add_entrada(historial_id: str, body: EntradaAdd):
    # user, tenant_id = ctx
    tenant_id = await get_tenant()
    return await add_entrada(historial_id, tenant_id, body)
    
@router.get('/{paciente_id}')
async def obtener_historial_by_paciente_id(paciente_id: str):
    tenant_id = await get_tenant()
    historial = await get_historial_by_paciente_id(paciente_id, tenant_id)
    return historial
