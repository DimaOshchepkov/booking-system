from contextlib import asynccontextmanager

from app.api import booking
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import BookingError, BookingNotFoundError, SlotUnavailableError
from app.database import engine
from app.schemas.health_check import HealthCheckResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.include_router(booking.router)


@app.exception_handler(BookingError)
async def booking_error_handler(request: Request, exc: BookingError):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "booking_error"

    if isinstance(exc, BookingNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
        error_code = "booking_not_found"
    elif isinstance(exc, SlotUnavailableError):
        status_code = status.HTTP_409_CONFLICT
        error_code = "slot_unavailable"

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": error_code,
                "field": exc.field,
                "message": exc.message,
            }
        },
    )

@app.get("/health", response_model=HealthCheckResponse, tags=["System"])
async def health_check():
    return {"status": "healthy"}