import csv
import io
import logging
import uuid
from decimal import Decimal
from typing import Annotated

from app.api.exceptions import APIException
from app.api.schemas.instruments import (
    DividendFetchResponse,
    InstrumentCreate,
    InstrumentRead,
    InstrumentUpdate,
    InstrumentUploadResponse,
)
from app.api.utils.authentication import get_current_user
from app.api.utils.caching import cache, cache_with_pagination
from app.api.utils.filters import InstrumentFilters
from app.api.utils.pagination import (
    PaginatedResponse,
    PaginationParams,
    SortingParams,
    build_paginated_response,
)
from app.db.deps import get_db
from app.db.models import Instrument, User
from app.db.crud import universal_search_instruments
from app.services.logging import log_message
from app.tasks import update_dividend_dates
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastcrud import FastCRUD
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/instruments", tags=["instruments"])

instrument_crud = FastCRUD(Instrument)

logger = logging.getLogger(__name__)


@router.get("/search", response_model=PaginatedResponse[InstrumentRead])
@cache_with_pagination(ttl=300, namespace="instrument_search")
async def search_instruments(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
    filters: Annotated[InstrumentFilters, Depends()],
    user: Annotated[User, Depends(get_current_user)],
) -> PaginatedResponse[InstrumentRead]:
    """
    Search instruments with filters.
    """
    try:
        # Handle universal search
        if filters.q:
            # Use the helper function from crud module
            result_data = await universal_search_instruments(
                db=db,
                user_id=user.id,
                query=filters.q,
                offset=pagination.offset,
                limit=pagination.limit,
            )

            # Convert to response format
            result_data = {
                "data": [
                    InstrumentRead.model_validate(instrument)
                    for instrument in result_data["data"]
                ],
                "total_count": result_data["total_count"],
            }
        else:
            # Use existing FastCRUD logic for specific field searches
            result_data = await instrument_crud.get_multi(
                db,
                offset=pagination.offset,
                limit=pagination.limit,
                schema_to_select=InstrumentRead,
                return_as_model=True,
                **filters.to_dict(),
                user_id=user.id,
            )

        return build_paginated_response(
            request=request,
            result=result_data,
            offset=pagination.offset,
            limit=pagination.limit,
            endpoint="/api/v1/instruments/search/",
            response_class=InstrumentRead,
            **filters.to_query_params(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search instruments: {str(e)}",
        )


@router.post(
    "/fetch-dividend-dates",
    response_model=DividendFetchResponse,
    status_code=status.HTTP_200_OK,
)
async def fetch_dividend_dates(
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
    user: Annotated[User, Depends(get_current_user)],
) -> DividendFetchResponse:
    """
    Trigger fetching and updating of dividend dates for all instruments with Yahoo symbols.
    This endpoint will fetch the latest dividend dates from Yahoo Finance and update the database.
    """
    try:
        background_tasks.add_task(update_dividend_dates.send)
        return DividendFetchResponse(
            message="Successfully updated dividend dates for all instruments",
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dividend dates: {str(e)}",
        )


@router.post(
    "/upload-csv",
    response_model=InstrumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_instruments_csv(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(..., description="CSV file containing instrument data"),
) -> InstrumentUploadResponse:
    """
    Upload a CSV file containing instrument data.
    This will replace ALL existing instruments with the new data from the CSV.

    Expected CSV format:
    Symbol,IG EPIC,Yahoo Symbol,ATR Stop Loss Period,ATR Stop Loss Multiple,ATR Profit Target Period,ATR Profit Multiple,Position Size Max GBP,Opening Price Multiple
    """

    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a CSV file"
        )

    try:
        content = await file.read()
        csv_content = content.decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(csv_content))

        header_mapping = {
            "Symbol": "market_and_symbol",
            "IG EPIC": "ig_epic",
            "Yahoo Symbol": "yahoo_symbol",
            "ATR Stop Loss Period": "atr_stop_loss_period",
            "ATR Stop Loss Multiple": "atr_stop_loss_multiple_percentage",
            "ATR Profit Target Period": "atr_profit_target_period",
            "ATR Profit Multiple": "atr_profit_multiple_percentage",
            "Position Size Max GBP": "max_position_size",
            "Opening Price Multiple": "opening_price_multiple_percentage",
            "TV Price Multiple": "trading_view_price_multiplier",
        }

        csv_headers = set(csv_reader.fieldnames or [])
        expected_headers = set(header_mapping.keys())

        logger.info(f"CSV Headers: {csv_headers}")
        logger.info(f"Expected Headers: {expected_headers}")

        if not expected_headers.issubset(csv_headers):
            missing_headers = expected_headers - csv_headers
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CSV is missing required headers: {', '.join(missing_headers)}",
            )

        instruments_data = []
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                instrument_data = {}

                for csv_field, model_field in header_mapping.items():
                    value = row[csv_field].strip() if row[csv_field] else None

                    if not value:
                        raise ValueError(f"Missing value for {csv_field}")

                    # Type conversion based on field
                    if model_field in [
                        "atr_stop_loss_period",
                        "atr_profit_target_period",
                        "max_position_size",
                    ]:
                        instrument_data[model_field] = int(value)
                    elif model_field in [
                        "atr_stop_loss_multiple_percentage",
                        "atr_profit_multiple_percentage",
                        "opening_price_multiple_percentage",
                        "trading_view_price_multiplier",
                    ]:
                        instrument_data[model_field] = Decimal(str(value))
                    else:
                        instrument_data[model_field] = value

                # Set default values for fields not in CSV
                instrument_data["position_size"] = 1  # Default value
                instrument_data["next_dividend_date"] = None  # Not in CSV

                instruments_data.append(
                    InstrumentCreate(**instrument_data, user_id=user.id)
                )

            except (ValueError, TypeError) as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid data in row {row_num}: {str(e)}",
                )

        if not instruments_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid instrument data found in CSV",
            )

        # this clears out all existing instruments for the user
        await db.execute(delete(Instrument).where(Instrument.user_id == user.id))

        created_instruments = []
        for instrument_create in instruments_data:
            new_instrument = await instrument_crud.create(db, instrument_create)
            created_instruments.append(new_instrument)

        await db.commit()
        await log_message(
            "Instruments uploaded via CSV",
            f"You uploaded {len(created_instruments)} instruments via CSV upload.",
            "instrument",
            user_id=user.id,
            identifier="instruments_csv_upload",
            extra={
                "instruments_created": len(created_instruments),
                "instruments": [
                    instrument.model_dump(mode="json")
                    for instrument in instruments_data
                ],
            },
        )

        return InstrumentUploadResponse(
            message=f"Successfully uploaded {len(created_instruments)} instruments",
            instruments_created=len(created_instruments),
        )

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File encoding error. Please ensure the file is UTF-8 encoded",
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process CSV file: {str(e)}",
        )


@router.post("", response_model=InstrumentRead, status_code=status.HTTP_201_CREATED)
async def create_instrument(
    instrument: InstrumentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> InstrumentRead:
    """
    Create a new instrument.
    """
    try:
        new_instrument = await instrument_crud.create(db, instrument)
        await db.refresh(new_instrument)
        return InstrumentRead.model_validate(new_instrument)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create instrument: {str(e)}",
        )


@router.get("", response_model=PaginatedResponse[InstrumentRead])
@cache_with_pagination(ttl=300, namespace="instruments")
async def list_instruments(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
    sorting: Annotated[SortingParams, Depends()],
    user: Annotated[User, Depends(get_current_user)],
) -> PaginatedResponse[InstrumentRead]:
    """
    Get a list of instruments with pagination and sorting.

    Returns:
        PaginatedResponse: Contains 'data' (list of instruments), 'count', 'next', and 'previous' URLs
    """
    try:
        result = await instrument_crud.get_multi(
            db,
            offset=pagination.offset,
            limit=pagination.limit,
            sort_columns=sorting.sort_columns,
            sort_orders=sorting.sort_orders,
            schema_to_select=InstrumentRead,
            return_as_model=True,
            user_id=user.id,
        )

        return build_paginated_response(
            request=request,
            result=result,
            offset=pagination.offset,
            limit=pagination.limit,
            endpoint="/api/v1/instruments/",
            response_class=InstrumentRead,
            sort_by=sorting.sort_by,
            sort_order=sorting.sort_order,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve instruments: {str(e)}",
        )


@router.get("/{id}", response_model=InstrumentRead)
@cache(ttl=300, namespace="instruments")
async def get_instrument(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> InstrumentRead:
    """
    Get a specific instrument by ID.
    """
    try:
        instrument = await instrument_crud.get(
            db,
            schema_to_select=InstrumentRead,
            return_as_model=True,
            id=id,
            user_id=user.id,
        )

        if not instrument:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=f"Instrument not found",
                code="INSTRUMENT_NOT_FOUND",
            )

        return instrument
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to retrieve instrument: {str(e)}",
            code="INTERNAL_SERVER_ERROR",
        )


@router.put("/{id}", response_model=InstrumentRead)
async def update_instrument(
    id: uuid.UUID,
    instrument_update: InstrumentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> InstrumentRead:
    """
    Update an existing instrument.
    """
    try:
        existing_instrument = await instrument_crud.exists(db, id=id, user_id=user.id)
        if not existing_instrument:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Instrument with ID {id} for user {user.email} not found",
            )

        update_data = instrument_update.model_dump(
            exclude_unset=True, exclude_none=True
        )

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields provided for update",
            )

        updated_instrument = await instrument_crud.update(
            db,
            update_data,
            schema_to_select=InstrumentRead,
            return_as_model=True,
            id=id,
        )

        return updated_instrument
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update instrument: {str(e)}",
        )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_instrument(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    """
    Delete an instrument by ID.
    """
    try:
        existing_instrument = await instrument_crud.exists(db, id=id, user_id=user.id)
        if not existing_instrument:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=f"Instrument not found",
                code="INSTRUMENT_NOT_FOUND",
            )

        await instrument_crud.delete(db, id=id)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to delete instrument",
            code="INTERNAL_SERVER_ERROR",
            details={
                "error": str(e),
                "instrument_id": str(id),
            },
        )
