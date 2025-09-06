from fastapi import APIRouter, Depends, Query

from app.core.auth_utils import get_user_and_tenant
from app.domain.entities.historial_entity import EntradaAdd, HistorialCreate, PresignReq, RegisterImageReq
from app.infrastructure.repositories.historial_repo import add_entrada, create_historial, presign_upload, register_image, signed_get


router = APIRouter(prefix='/historial', tags=['Historiales'])

@router.post('/upload/presign')
def historial_presign_upload(body: PresignReq):
    return presign_upload(body)

@router.post('/upload/register')
async def historial_register_image(body: RegisterImageReq, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    return await register_image(body, tenant_id)

@router.get('/images/signed-get')
def historial_signed_get(key: str = Query(...)):
    return signed_get(key)

@router.post('/')
async def crear_historial(body: HistorialCreate, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    return await create_historial(body, tenant_id)
    

@router.post('/{historial_id}/entradas')
async def historial_add_entrada(historial_id: str, body: EntradaAdd, ctx=Depends(get_user_and_tenant)):
    user, tenant_id = ctx
    return await add_entrada(historial_id, tenant_id)
    