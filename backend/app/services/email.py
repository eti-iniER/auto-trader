from app.config import settings
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from jinja2 import Environment, FileSystemLoader
import os

templates_dir = os.path.join(settings.BASE_DIR, "templates")

environment = Environment(
    loader=FileSystemLoader(templates_dir),
    autoescape=True,
)

reset_password_template = environment.get_template("reset_password.html")

config = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USERNAME,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.FROM_EMAIL,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_STARTTLS=True,
    USE_CREDENTIALS=True,
    MAIL_SSL_TLS=False,
)


fast_mail = FastMail(config)


async def send_reset_password_email(email: str, first_name: str, reset_link: str):
    message = MessageSchema(
        subject=f"{first_name}, reset your AutoTrader password",
        recipients=[email],
        body=reset_password_template.render(
            first_name=first_name, reset_link=reset_link
        ),
        subtype=MessageType.html,
    )
    await fast_mail.send_message(message)
