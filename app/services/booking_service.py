from datetime import date, time

from sqlalchemy import and_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BookingNotFoundError, SlotUnavailableError
from app.models.booking import Booking
from app.schemas.booking import BookingCreate


async def is_slot_available(
    db: AsyncSession,
    booking_date: date,
    booking_time: time,
) -> bool:
    query = select(Booking.id).where(
        and_(
            Booking.booking_date == booking_date,
            Booking.booking_time == booking_time,
            Booking.status == "active",
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none() is None


async def create_booking(db: AsyncSession, data: BookingCreate) -> Booking:
    """
    Raises:
        SlotUnavailableError:
        SlotUnavailableError:
    """
    if not await is_slot_available(db, data.booking_date, data.booking_time):
        raise SlotUnavailableError()

    booking = Booking(
        name=data.name,
        phone=data.phone,
        booking_date=data.booking_date,
        booking_time=data.booking_time,
        guests=data.guests,
        status="active",
    )
    db.add(booking)

    try:
        await db.flush()
    except (
        IntegrityError
    ):  # защита от гонок. Основано на ограничении uq_booking_active_slot
        await db.rollback()
        raise SlotUnavailableError() from None

    await db.refresh(booking)
    return booking


async def list_bookings(
    db: AsyncSession,
    booking_date: date | None = None,
) -> list[Booking]:

    query = select(Booking).where(Booking.status == "active")

    if booking_date is not None:
        query = query.where(Booking.booking_date == booking_date)

    query = query.order_by(Booking.booking_date, Booking.booking_time)

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_booking_by_id(db: AsyncSession, booking_id: int) -> Booking:
    """
    Raises:
        BookingNotFoundError:
    """
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()

    if booking is None:
        raise BookingNotFoundError(booking_id)

    return booking


async def cancel_booking(db: AsyncSession, booking_id: int) -> Booking:
    """
    Raises:
        BookingNotFoundError:
    """
    stmt = (
        update(Booking)
        .where(Booking.id == booking_id)
        .values(status="cancelled")
        .returning(Booking)
    )

    result = await db.execute(stmt)
    booking = result.scalar_one_or_none()

    if booking is None:
        raise BookingNotFoundError(booking_id)

    return booking
