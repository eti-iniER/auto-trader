from pydantic import BaseModel


class NewWebhookSecretResponse(BaseModel):
    secret: str
