from datetime import date

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.booking import BookingCreate, BookingOut
from app.services.booking_service import (
    cancel_booking,
    create_booking,
    get_booking_by_id,
    list_bookings,
)

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
    db: AsyncSession = Depends(get_db),
):
    return await list_bookings(db, booking_date=date)


@router.post("/", response_model=BookingOut, status_code=201)
async def create_booking_endpoint(
    data: BookingCreate,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    booking = await create_booking(db, data)

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
    db: AsyncSession = Depends(get_db),
):
    return await get_booking_by_id(db, booking_id)


@router.delete(
    "/{booking_id}",
    response_model=BookingOut,
)
async def delete_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await cancel_booking(db, booking_id)
