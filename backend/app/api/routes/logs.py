import logging
import uuid
from datetime import datetime, timezone
from typing import Annotated

from app.api.schemas.generic import SimpleResponseSchema
from app.api.utils.authentication import get_current_user, require_admin
from app.api.utils.filters import LogFilterParams
from app.api.utils.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
)
from app.config import settings
from app.db.crud import delete_logs_for_user
from app.db.deps import get_db
from app.db.models import Log, User
from app.api.schemas.logs import LogRead
from app.services.logging.file_helpers import prepare_logs_file
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, Response
from fastcrud import FastCRUD
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/logs", tags=["logs"])

logger = logging.getLogger(__name__)

logs_crud = FastCRUD(Log)
user_crud = FastCRUD(User)


@router.get(
    "",
    summary="Get logs with filtering and pagination",
    response_model=PaginatedResponse[LogRead],
)
async def get_logs(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends()],
    filters: Annotated[LogFilterParams, Depends()],
) -> PaginatedResponse[LogRead]:
    """
    Retrieve logs with optional filtering by date range and log type.
    Returns up to 100 logs by default with pagination support.
    """

    logger.info(
        f"Fetching logs for user {user.email} with filters: "
        f"from_date={filters.from_date} (type: {type(filters.from_date)}), "
        f"to_date={filters.to_date} (type: {type(filters.to_date)}), "
        f"type={filters.log_type} (type: {type(filters.log_type)}), "
        f"pagination offset={pagination.offset}, limit={pagination.limit}"
    )

    filter_kwargs = {"user_id": user.id}
    filter_kwargs.update(filters.to_dict())

    result = await logs_crud.get_multi(
        db=db,
        offset=pagination.offset,
        limit=pagination.limit,
        sort_columns=["created_at"],
        sort_orders=["desc"],
        schema_to_select=LogRead,
        return_as_model=True,
        **filter_kwargs,
    )

    logger.info(str(filter_kwargs))

    logger.info(
        f"Retrieved {len(result['data'])} logs for user {user.email} "
        f"(offset: {pagination.offset}, limit: {pagination.limit})"
        f" with filters: ",
    )

    return build_paginated_response(
        request=request,
        result=result,
        offset=pagination.offset,
        limit=pagination.limit,
        endpoint="/api/v1/logs/",
        response_class=LogRead,
        from_date=filters.from_date.isoformat() if filters.from_date else None,
        to_date=filters.to_date.isoformat() if filters.to_date else None,
        type=filters.log_type,
    )


@router.get(
    "/download",
    summary="Download logs as a file",
    response_class=Response,
)
async def download_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    filters: Annotated[LogFilterParams, Depends()],
    limit: int = Query(
        1000, ge=1, le=10000, description="Maximum number of logs to download"
    ),
) -> Response:
    """
    Download logs as a formatted text file with the same filtering options as the main logs endpoint.
    """
    logger.info(
        f"Preparing to download logs for user {user.email} with filters: "
        f"from_date={filters.from_date}, to_date={filters.to_date}, type={filters.log_type}, limit={limit}"
    )

    filter_kwargs = {"user_id": user.id}
    filter_kwargs.update(filters.to_dict())

    result = await logs_crud.get_multi(
        db=db,
        offset=0,
        limit=limit,
        sort_columns=["created_at"],
        sort_orders=["desc"],
        schema_to_select=LogRead,
        return_as_model=True,
        **filter_kwargs,
    )

    logs = result["data"]

    logger.info(
        f"Preparing log file download for user {user.email} with {len(logs)} logs"
    )

    file_content = prepare_logs_file(logs)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d at %H-%M-%S")
    filename = f"{settings.LOGFILE_NAME_PREFIX}_logs_{timestamp}"

    if filters.from_date:
        filename += f"_from_{filters.from_date.strftime('%Y%m%d')}"
    if filters.to_date:
        filename += f"_to_{filters.to_date.strftime('%Y%m%d')}"
    if filters.log_type:
        filename += f"_{filters.log_type.lower()}"

    filename += ".log"

    return Response(
        content=file_content,
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "text/plain; charset=utf-8",
        },
    )


@router.delete(
    "/delete-for-user/{user_id}",
    summary="Delete all logs for a specific user (Admin only)",
    response_model=SimpleResponseSchema,
)
async def delete_logs_for_user_endpoint(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin())],
) -> SimpleResponseSchema:
    """
    Delete all logs for a specific user. Admin access required.
    """
    try:
        # Check if the user exists
        user_to_check = await user_crud.get(db, id=user_id)
        logger.info(
            f"Admin {admin_user.email} requested log deletion for user ID {user_id}"
        )
        logger.info(f"User to check: {user_to_check}")
        if not user_to_check:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Delete all logs for the user
        deleted_count = await delete_logs_for_user(db, user_id)

        logger.info(
            f"Admin {admin_user.email} deleted {deleted_count} logs for user {user_id}"
        )

        return SimpleResponseSchema(
            message=f"Successfully deleted {deleted_count} logs for user {user_id}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete logs for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete logs for user: {str(e)}",
        )
