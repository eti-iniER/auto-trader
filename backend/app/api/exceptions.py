from typing import Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse


class APIException(HTTPException):
    """
    Custom application-level HTTP exception.

    Args:
        message: Human-readable error message.
        code: Application-specific error code (string), not an HTTP status code.
        status_code: HTTP status code to return (defaults to 400).
        details: Optional JSON-serializable object with extra error context.
        headers: Optional HTTP headers to include in the response.
    """

    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = 400,
        details: Any | None = None,
        headers: dict | None = None,
    ):
        super().__init__(status_code=status_code, detail=message, headers=headers)
        self.message = message
        self.code = code
        self.details = details

    def to_dict(self) -> dict:
        return {"message": self.message, "code": self.code, "details": self.details}


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Return the configured status with the exact error shape: {message, code, details}."""
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


def register_exception_handlers(app: FastAPI) -> None:
    """Register APIException handler on the given FastAPI app."""
    app.add_exception_handler(APIException, api_exception_handler)
