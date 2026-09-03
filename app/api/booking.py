from datetime import date

from fastapi import APIRouter, Depends, Query, Request, Response

from app.dependencies import get_booking_service
from app.schemas.booking import BookingCreate, BookingOut
from app.services.booking_service import BookingService

router = APIRouter(
    prefix="/bookings",
    tags=["bookings"],
)


@router.get("/", response_model=list[BookingOut])
async def get_bookings(
    date: date | None = Query(
        default=None,
        description="Фильтр по дате бронирования (YYYY-MM-DD)",
        examples=["2026-09-10"],
    ),
    service: BookingService = Depends(get_booking_service),
):
    return await service.list(booking_date=date)


@router.post("/", response_model=BookingOut, status_code=201)
async def create_booking_endpoint(
    data: BookingCreate,
    request: Request,
    response: Response,
    service: BookingService = Depends(get_booking_service),
):
    booking = await service.create(data)

    location = request.url_for("get_booking", booking_id=booking.id)
    response.headers["Location"] = str(location)

    return booking


@router.get(
    "/{booking_id}",
    response_model=BookingOut,
    name="get_booking",
)
async def get_booking(
    booking_id: int,
    service: BookingService = Depends(get_booking_service),
):
    return await service.get_by_id(booking_id)


@router.delete(
    "/{booking_id}",
    response_model=BookingOut,
)
async def delete_booking(
    booking_id: int,
    service: BookingService = Depends(get_booking_service),
):
    return await service.cancel(booking_id)