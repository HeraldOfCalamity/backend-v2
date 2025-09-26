# notification_service.py
from typing import Literal
from app.application.websockets.manager import manager

async def notificar_evento_cita(
    tenant_id: str,
    action: Literal["created","confirmed","canceled","attended"],
    payload: dict,  # Idealmente CitaOut serializable
    especialista_id: str | None = None
):
    message = {
        "entity": "cita",
        "action": action,
        "data": payload
    }
    # broadcast a todo el tenant
    await manager.broadcast(f"tenant:{tenant_id}", message)
    # y también al canal del especialista (si aplica)
    if especialista_id:
        await manager.broadcast(f"tenant:{tenant_id}:esp:{especialista_id}", message)
