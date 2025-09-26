from datetime import date
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query

from app.core.auth_utils import get_tenant, get_user_and_tenant
from app.core.security import require_permission
from app.infrastructure.repositories.reportes_citas_repo import overview_report

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
