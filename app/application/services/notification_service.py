from enum import Enum
from typing import Literal

from app.infrastructure.notifiers.email_notifier import send_event_email
from app.infrastructure.notifiers.push_notifier import send_event_push


class NotificationType(str, Enum):
    EMAIL = 'email'
    PUSH = 'push'

async def notificar_evento_cita(
    evento: str,
    message: str,
    tipo: list[NotificationType] = [NotificationType.EMAIL, NotificationType.PUSH]
):
    if NotificationType.EMAIL in tipo:
        await send_event_email(evento, message)

    if NotificationType.PUSH in tipo:
        await send_event_push(evento, message)