"""
Utility functions for creating IG client instances based on user settings.
"""

from fastapi import HTTPException, status
from app.db.models import User
from app.db.enums import UserSettingsMode
from app.clients.ig.client import IGClient
from app.config import settings


def get_ig_client_for_user(user: User) -> IGClient:
    """
    Create IG client instance using user's mode-specific credentials.

    Args:
        user: The authenticated user with settings containing IG credentials

    Returns:
        IGClient: Configured IG client instance

    Raises:
        HTTPException: If user settings are missing or credentials are incomplete
    """
    if not user.settings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User settings not found. Please configure your IG credentials.",
        )

    if user.settings.mode == UserSettingsMode.DEMO:
        api_key = user.settings.demo_api_key
        username = user.settings.demo_username
        password = user.settings.demo_password
        base_url = settings.IG_DEMO_API_BASE_URL
    else:  # LIVE mode
        api_key = settings.live_api_key
        username = settings.live_username
        password = settings.live_password
        base_url = settings.IG_LIVE_API_BASE_URL

    if not all([api_key, username, password]):
        mode_str = user.settings.mode.value.lower()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing {mode_str} mode IG credentials. Please configure your {mode_str} API key, username, and password.",
        )

    return IGClient(
        username=username, password=password, api_key=api_key, base_url=base_url
    )
