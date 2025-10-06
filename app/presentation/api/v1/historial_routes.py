from fastapi import APIRouter, Depends, Query

from app.core.auth_utils import get_tenant, get_user_and_tenant
from app.core.exceptions import raise_not_found
from app.domain.entities.historial_entity import EntradaAdd, HistorialCreate, PresignReq, RecomendacionesUpdate, RegisterImageReq, TratamientoAdd, UpdateHistorial
from app.infrastructure.repositories.historial_repo import add_entrada, add_tratamiento, create_historial, get_historial_by_paciente_id, presign_upload, register_attachment, register_image, set_anamnesis_once, set_recomendaciones, signed_get, update_historial_anamnesis


router = APIRouter(prefix='/historiales', tags=['Historiales'])

@router.post('/upload/presign')
def historial_presign_upload(body: PresignReq):
    return presign_upload(body)

@router.post('/upload/register')
async def historial_register_image(body: RegisterImageReq):
    # user, tenant_id = ctx
    tenant_id = await get_tenant()
    return await register_image(body, tenant_id)

@router.post('/upload/register-attach')
async def historial_register_attachment(body: RegisterImageReq):
    tenant_id = await get_tenant()
    return await register_attachment(body, tenant_id)

@router.get('/images/signed-get')
def historial_signed_get(key: str = Query(...)):
    return signed_get(key)

@router.post('/')
async def crear_historial(body: HistorialCreate):
    # user, tenant_id = ctx
    tenant_id = await get_tenant()
    return await create_historial(body, tenant_id)
    

@router.post('/{historial_id}/entradas/{tratamiento_id}')
async def historial_add_entrada(historial_id: str, tratamiento_id: str, body: EntradaAdd):
    # user, tenant_id = ctx
    tenant_id = await get_tenant()
    return await add_entrada(historial_id, tratamiento_id, tenant_id, body)
    
@router.put('/{historial_id}/anamnesis')
async def update_anamnesis(historial_id: str, body: UpdateHistorial):
    tenant_id = await get_tenant()
    return await update_historial_anamnesis(body, tenant_id, historial_id)


@router.get('/{paciente_id}')
async def obtener_historial_by_paciente_id(paciente_id: str):
    tenant_id = await get_tenant()
    historial = await get_historial_by_paciente_id(paciente_id, tenant_id)
    return historial

@router.post('/{historial_id}/tratamientos')
async def historial_add_tratamiento(historial_id: str, body: TratamientoAdd):
    tenant_id = await get_tenant()
    return await add_tratamiento(historial_id,tenant_id, body)

@router.post('/{historial_id}/tratamientos/{tratamiento_id}/anamnesis:set-once')
async def set_anamnesis_once_route(historial_id: str, tratamiento_id: str, body: TratamientoAdd):
    tenant_id = await get_tenant()
    return await set_anamnesis_once(historial_id, tratamiento_id, tenant_id, body)

@router.put("/{historial_id}/tratamientos/{tratamiento_id}/entradas/{entrada_id}/recomendaciones")
async def put_recomendaciones(historial_id: str, tratamiento_id: str, entrada_id: str, body: RecomendacionesUpdate):
    tenant_id = await get_tenant()
    return await set_recomendaciones(historial_id, tratamiento_id, entrada_id, body.recomendaciones, tenant_id)