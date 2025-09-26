# app/application/websockets/routes.py
# app/application/websockets/routes.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.application.websockets.manager import manager
from app.core.security import decode_access_token  # tu helper real
import logging

ws_router = APIRouter()
log = logging.getLogger("ws")

async def _auth_from_ws(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        auth = websocket.headers.get("authorization") or websocket.headers.get("Authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1]

    if not token:
        log.warning("WS reject: no token")
        await websocket.close(code=4401)  # Unauthorized
        return None, None

    try:
        payload = decode_access_token(token)
        log.info("WS token payload: %s", payload)  # <-- LOGEAMOS para ver claims
        tenant_id = payload.get("tenant_id")
        user_id = payload.get("sub") or payload.get("user_id")
        if not tenant_id or not user_id:
            log.warning("WS reject: missing claims (tenant_id/user_id)")
            await websocket.close(code=4401)
            return None, None
        return {"id": user_id}, str(tenant_id)
    except Exception:
        log.exception("WS reject: invalid token")
        await websocket.close(code=4401)
        return None, None

@ws_router.websocket("/ws/citas")
async def ws_citas(websocket: WebSocket, especialista_id: str | None = Query(default=None)):
    try:
        user, tenant_id = await _auth_from_ws(websocket)
        if not user:
            return  # ya cerró con 4401

        await websocket.accept()  # ACEPTAR **UNA VEZ**
        log.info("WS accepted: user=%s tenant=%s esp=%s", user["id"], tenant_id, especialista_id)

        room_tenant = f"tenant:{tenant_id}"
        room_especialista = f"tenant:{tenant_id}:esp:{especialista_id}" if especialista_id else None
        await manager.connect(room_tenant, websocket)
        if room_especialista:
            await manager.connect(room_especialista, websocket)

        while True:
            try:
                await websocket.receive_text()  # keepalive
            except WebSocketDisconnect:
                log.info("WS disconnected: user=%s tenant=%s esp=%s", user["id"], tenant_id, especialista_id)
                manager.disconnect(room_tenant, websocket)
                if room_especialista:
                    manager.disconnect(room_especialista, websocket)
                break
            except Exception:
                log.exception("WS receive error")
                await websocket.close(code=1011)  # internal error
                manager.disconnect(room_tenant, websocket)
                if room_especialista:
                    manager.disconnect(room_especialista, websocket)
                break
    except Exception:
        log.exception("WS handler fatal")
        try:
            await websocket.close(code=1011)
        except Exception:
            pass


@ws_router.websocket("/ws/ping")
async def ws_ping(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("pong")
    await websocket.close()