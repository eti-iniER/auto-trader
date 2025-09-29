"""Custom exceptions for IG API client."""


class IGClientError(Exception):
    """Base exception for IG client errors."""

    def __init__(self, message: str, status_code: int = None, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)


class IGAuthenticationError(IGClientError):
    """Exception raised when authentication fails."""

    pass


class IGAPIError(IGClientError):
    """Exception raised when API returns an error response."""

    pass


class MissingCredentialsError(IGClientError):
    """Exception raised when required credentials are missing."""

    def __init__(
        self,
        message: str = "Missing required credentials",
        status_code: int = 400,
        error_code: str = "missing_credentials",
    ):
        super().__init__(message, status_code, error_code)
