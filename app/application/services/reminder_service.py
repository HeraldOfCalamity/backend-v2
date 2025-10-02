# app/application/services/reminder_service.py
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from beanie.operators import And, GTE, LTE

from app.core.config import settings
from app.infrastructure.schemas.cita import Cita
from app.infrastructure.schemas.estadoCita import ESTADOS_CITA
from app.infrastructure.repositories.cita_repo import send_cita_email
from app.infrastructure.repositories.estadoCita_repo import get_estado_cita_by_id
from app.infrastructure.repositories.user_repo import get_admin_user
from app.infrastructure.repositories.officeConfig_repo import is_auto_cancel_enabled

# ---------- Logger ----------
logger = logging.getLogger("app.reminders")
# Si está activado DEBUG_REMINDERS, forzamos DEBUG para este logger (sin tocar el root)
if settings.DEBUG_REMINDERS and logger.level > logging.DEBUG:
    logger.setLevel(logging.DEBUG)

# ---------- Config de tiempo ----------
TEST_SPEEDUP = settings.REMINDERS_TEST_SPEEDUP
# 1 'hora' = 1 'minuto' en tests
HOUR_SECONDS = 60 if TEST_SPEEDUP else 60 * 60
SLEEP_SECONDS = settings.REMINDERS_SLEEP_SECONDS
TOLERANCE_SECONDS = settings.REMINDERS_TOLERANCE_SECONDS

# Marcadores de recordatorio: cada 2 h desde 24 hasta 8 (NO incluye 6)
REMINDER_MARKS_HOURS = [h for h in range(24, 7, -2)]  # [24,22,20,18,16,14,12,10,8]

def now_utc():
    return datetime.now(timezone.utc)

def window(center: datetime, tol_seconds: int):
    return (center - timedelta(seconds=tol_seconds),
            center + timedelta(seconds=tol_seconds))

async def _send_reminder(cita: Cita, mark_hour: int):
    try:
        await send_cita_email('recordatorio', cita)
        # idempotencia
        if mark_hour not in (cita.reminders_sent_marks or []):
            cita.reminders_sent_marks.append(mark_hour)
        cita.last_reminder_sent_at = now_utc()
        await cita.save()
        logger.info(
            "Recordatorio enviado | cita_id=%s paciente_id=%s mark=%sh fecha_inicio=%s",
            str(cita.id), str(cita.paciente_id), mark_hour, cita.fecha_inicio.isoformat()
        )
    except Exception:
        logger.exception(
            "Error enviando recordatorio | cita_id=%s mark=%sh",
            str(cita.id), mark_hour
        )

async def _auto_cancel(cita: Cita):
    # Flag de oficina
    enabled = await is_auto_cancel_enabled(str(cita.tenant_id))
    if not enabled:
        logger.debug(
            "Autocancel deshabilitada para tenant | tenant_id=%s cita_id=%s",
            str(cita.tenant_id), str(cita.id)
        )
        return

    estado_cancelada = await get_estado_cita_by_id(
        ESTADOS_CITA.cancelada.value, str(cita.tenant_id)
    )
    if not estado_cancelada:
        logger.warning(
            "No se encontró estado 'cancelada' para tenant | tenant_id=%s cita_id=%s",
            str(cita.tenant_id), str(cita.id)
        )
        return

    try:
        pre_estado = cita.estado_id
        cita.estado_id = estado_cancelada.estado_id
        cita.auto_canceled_at = now_utc()

        admin = await get_admin_user(str(cita.tenant_id))
        if admin:
            cita.canceledBy = admin.id

        await cita.save()
        await send_cita_email('cancelacion', cita)
        logger.info(
            "Cita autocancelada | cita_id=%s from_estado=%s to_estado=%s fecha_inicio=%s",
            str(cita.id), pre_estado, cita.estado_id, cita.fecha_inicio.isoformat()
        )
    except Exception:
        logger.exception("Error durante autocancelación | cita_id=%s", str(cita.id))

async def _process_reminder_mark(mark_hour: int):
    # Ventana objetivo (citas cuyo inicio ≈ now + mark_hour)
    now = now_utc()
    target = now + timedelta(seconds=HOUR_SECONDS * mark_hour)
    start, end = window(target, TOLERANCE_SECONDS)
    logger.debug(
        "Procesando marca | mark=%sh window=[%s .. %s]",
        mark_hour, start.isoformat(), end.isoformat()
    )

    pendientes = await Cita.find(And(
        Cita.estado_id == ESTADOS_CITA.pendiente.value,
        GTE(Cita.fecha_inicio, start),
        LTE(Cita.fecha_inicio, end),
    )).to_list()

    logger.debug("Citas pendientes encontradas | mark=%sh count=%d", mark_hour, len(pendientes))
    sent = 0
    skipped = 0

    for cita in pendientes:
        if mark_hour in (cita.reminders_sent_marks or []):
            skipped += 1
            logger.debug(
                "Recordatorio ya enviado previamente; se omite | cita_id=%s mark=%sh",
                str(cita.id), mark_hour
            )
            continue
        await _send_reminder(cita, mark_hour)
        sent += 1

    if sent or settings.DEBUG_REMINDERS:
        logger.info(
            "Resumen marca | mark=%sh enviados=%d omitidos=%d",
            mark_hour, sent, skipped
        )

async def _process_auto_cancel_6h():
    now = now_utc()
    target = now + timedelta(seconds=HOUR_SECONDS * 6)
    start, end = window(target, TOLERANCE_SECONDS)
    logger.debug(
        "Procesando autocancel (6h) | window=[%s .. %s]",
        start.isoformat(), end.isoformat()
    )

    pendientes = await Cita.find(And(
        Cita.estado_id == ESTADOS_CITA.pendiente.value,
        GTE(Cita.fecha_inicio, start),
        LTE(Cita.fecha_inicio, end),
    )).to_list()

    logger.debug("Citas pendientes en ventana 6h | count=%d", len(pendientes))
    for cita in pendientes:
        await _auto_cancel(cita)

async def process_windows_once():
    # Útil para endpoint /_debug/reminders/run-once
    for h in REMINDER_MARKS_HOURS:
        await _process_reminder_mark(h)
    await _process_auto_cancel_6h()
    logger.info("Ejecución manual única completada (process_windows_once)")

async def reminder_scheduler_loop():
    tick = 0
    # Log de arranque (una sola vez)
    logger.info(
        "Reminder scheduler iniciado | DEBUG_REMINDERS=%s TEST_SPEEDUP=%s HOUR_SECONDS=%s SLEEP_SECONDS=%s TOLERANCE_SECONDS=%s marks=%s",
        settings.DEBUG_REMINDERS, TEST_SPEEDUP, HOUR_SECONDS, SLEEP_SECONDS, TOLERANCE_SECONDS, REMINDER_MARKS_HOURS
    )

    while True:
        tick += 1
        try:
            logger.debug("Tick #%d start | now=%s", tick, now_utc().isoformat())
            for h in REMINDER_MARKS_HOURS:
                await _process_reminder_mark(h)
            await _process_auto_cancel_6h()
            logger.debug("Tick #%d end", tick)
        except Exception:
            logger.exception("Error no controlado en el scheduler (tick=%d)", tick)
        await asyncio.sleep(SLEEP_SECONDS)
