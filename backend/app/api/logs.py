import logging
from datetime import datetime
from typing import Annotated, List, Optional

from app.api.utils.authentication import get_current_user
from app.api.utils.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
)
from app.db.deps import get_db
from app.db.enums import LogType
from app.db.models import Log, User
from app.schemas.logs import LogRead, LogFilters
from app.services.logging.file_helpers import prepare_logs_file
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response
from fastcrud import FastCRUD
from sqlalchemy import and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/logs", tags=["logs"])

logger = logging.getLogger(__name__)

logs_crud = FastCRUD(Log)


@router.get(
    "/",
    summary="Get logs with filtering and pagination",
    response_model=PaginatedResponse[LogRead],
)
async def get_logs(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends()],
    from_date: Optional[datetime] = Query(
        None, description="Filter logs from this date"
    ),
    to_date: Optional[datetime] = Query(
        None, description="Filter logs until this date"
    ),
    log_type: Optional[LogType] = Query(None, description="Filter logs by type"),
) -> PaginatedResponse[LogRead]:
    """
    Retrieve logs with optional filtering by date range and log type.
    Returns up to 100 logs by default with pagination support.
    """
    # Build filters
    filters = []

    if from_date:
        filters.append(Log.created_at >= from_date)

    if to_date:
        filters.append(Log.created_at <= to_date)

    if log_type:
        filters.append(Log.type == log_type)

    # Combine filters
    where_clause = and_(*filters) if filters else None

    # Get logs with pagination, ordered by created_at descending (newest first)
    result = await logs_crud.get_multi(
        db=db,
        offset=pagination.offset,
        limit=pagination.limit,
        where=where_clause,
        order_by=[desc(Log.created_at)],
    )

    logger.info(
        f"Retrieved {len(result['data'])} logs for user {user.email} "
        f"(offset: {pagination.offset}, limit: {pagination.limit})"
    )

    # Build paginated response
    return build_paginated_response(
        request=request,
        result=result,
        offset=pagination.offset,
        limit=pagination.limit,
        endpoint="/api/v1/logs/",
        response_class=LogRead,
        from_date=from_date.isoformat() if from_date else None,
        to_date=to_date.isoformat() if to_date else None,
        log_type=log_type.value if log_type else None,
    )


@router.get(
    "/download",
    summary="Download logs as a file",
    response_class=Response,
)
async def download_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    from_date: Optional[datetime] = Query(
        None, description="Filter logs from this date"
    ),
    to_date: Optional[datetime] = Query(
        None, description="Filter logs until this date"
    ),
    log_type: Optional[LogType] = Query(None, description="Filter logs by type"),
    limit: int = Query(
        1000, ge=1, le=10000, description="Maximum number of logs to download"
    ),
) -> Response:
    """
    Download logs as a formatted text file with the same filtering options as the main logs endpoint.
    """
    # Build filters (same as get_logs endpoint)
    filters = []

    if from_date:
        filters.append(Log.created_at >= from_date)

    if to_date:
        filters.append(Log.created_at <= to_date)

    if log_type:
        filters.append(Log.type == log_type)

    # Combine filters
    where_clause = and_(*filters) if filters else None

    # Get logs without pagination but with a reasonable limit for file download
    result = await logs_crud.get_multi(
        db=db,
        offset=0,
        limit=limit,
        where=where_clause,
        order_by=[desc(Log.created_at)],
    )

    logs = result["data"]

    logger.info(
        f"Preparing log file download for user {user.email} " f"with {len(logs)} logs"
    )

    # Prepare file content using the helper function
    file_content = prepare_logs_file(logs)

    # Generate filename with timestamp and filters
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"logs_{timestamp}"

    if from_date:
        filename += f"_from_{from_date.strftime('%Y%m%d')}"
    if to_date:
        filename += f"_to_{to_date.strftime('%Y%m%d')}"
    if log_type:
        filename += f"_{log_type.value.lower()}"

    filename += ".txt"

    # Return file as download
    return Response(
        content=file_content,
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "text/plain; charset=utf-8",
        },
    )
