import secrets
import string

from app.config import settings


def generate_webhook_secret(length: int = settings.WEBHOOK_SECRET_LENGTH) -> str:
    """Generate a secure random variable-length string for webhook secrets."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_deal_reference(length: int = 16) -> str:
    """Generate a secure random variable-length string for deal references."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))
