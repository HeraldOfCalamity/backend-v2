from datetime import date
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query

from app.core.auth_utils import get_tenant, get_user_and_tenant
from app.core.security import require_permission
from app.infrastructure.repositories.reportes_citas_repo import overview_report, por_estado_de_especialidad, por_estado_de_especialista

router = APIRouter(prefix="/reportes/citas", tags=["Reportes de Citas"])

@router.get(
    "/overview"
)
async def reportes_overview(
    from_date: date | None = Query(None, description="YYYY-MM-DD"),
    to_date: date | None = Query(None, description="YYYY-MM-DD"),
    # ctx=Depends(get_user_and_tenant),
) -> Dict[str, Any]:
    tenant_id = await get_tenant()
    return await overview_report(tenant_id, from_date, to_date)

@router.get('/por-estado-especialista')
async def reportes_por_estado_especialista(
    especialista: str = Query(..., description='Nombre visible del especialista'),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None)
) -> List[Dict[str, Any]]:
    tenant_id = await get_tenant()
    return await por_estado_de_especialista(tenant_id, from_date, to_date, especialista)

@router.get('/por-estado-especialidad')
async def reportes_por_estado_especialidad(
    especialidad: str = Query(..., description='Nombre visible de la especialidad'),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None)
) -> List[Dict[str, Any]]:
    tenant_id = await get_tenant()
    return await por_estado_de_especialidad(tenant_id, from_date, to_date, especialidad)