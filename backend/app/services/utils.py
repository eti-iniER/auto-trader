import secrets
import string


def generate_webhook_secret() -> str:
    """Generate a secure random 32-character string for webhook secrets."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(32))
