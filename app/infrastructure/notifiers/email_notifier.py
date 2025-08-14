from app.core.config import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

async def send_event_email(event: str, message: str):
    print(f"[EMAIL] ✉️ Enviando email por evento '{event}' para cita: {message}")

async def send_sendgrid_email(to: str, subject: str, html: str):
    message = Mail(
        from_email=settings.SENDGRID_FROM_EMAIL,
        to_emails=to,
        subject=subject,
        html_content=html
    )

    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        print(f'Correo enviado ({response.status_code}) {response.body} a {to}')
    except Exception as e:
        print(f'Error al enviar correo: {e}')



    