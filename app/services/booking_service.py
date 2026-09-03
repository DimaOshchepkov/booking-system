from datetime import date, time

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import and_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BookingNotFoundError, SlotUnavailableError
from app.models.booking import Booking
from app.schemas.booking import BookingCreate


class BookingService:
    """Сервис для работы с бронированиями."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def is_slot_available(
        self,
        booking_date: date,
        booking_time: time,
    ) -> bool:
        """Проверяет, свободен ли слот."""
        query = select(Booking.id).where(
            and_(
                Booking.booking_date == booking_date,
                Booking.booking_time == booking_time,
                Booking.status == "active",
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is None

    async def create(self, data: BookingCreate) -> Booking:
        """
        Создаёт бронирование.

        Raises:
            SlotUnavailableError: Если время уже занято.
        """
        if not await self.is_slot_available(data.booking_date, data.booking_time):
            raise SlotUnavailableError()

        booking = Booking(
            name=data.name,
            phone=data.phone,
            booking_date=data.booking_date,
            booking_time=data.booking_time,
            guests=data.guests,
            status="active",
        )
        self.db.add(booking)

        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            raise SlotUnavailableError() from None

        return booking

    async def list(
        self,
        booking_date: date | None = None,
        page: int = 1,
        size: int = 50,
    ) -> Page[Booking]:
        """Возвращает список активных бронирований."""
        query = select(Booking).where(Booking.status == "active")

        if booking_date is not None:
            query = query.where(Booking.booking_date == booking_date)

        query = query.order_by(Booking.booking_date, Booking.booking_time)

        pagination_params = Params(page=page, size=size)

        return await paginate(self.db, query, params=pagination_params)


    async def get_by_id(self, booking_id: int) -> Booking:
        """
        Получает бронь по ID.

        Raises:
            BookingNotFoundError: Если бронь не найдена.
        """
        result = await self.db.execute(select(Booking).where(Booking.id == booking_id))
        booking = result.scalar_one_or_none()

        if booking is None:
            raise BookingNotFoundError(booking_id)

        return booking

    async def cancel(self, booking_id: int) -> Booking:
        """
        Отменяет бронь (меняет status на 'cancelled').

        Raises:
            BookingNotFoundError: Если бронь не найдена.
        """
        stmt = (
            update(Booking)
            .where(Booking.id == booking_id)
            .values(status="cancelled")
            .returning(Booking)
        )

        result = await self.db.execute(stmt)
        booking = result.scalar_one_or_none()

        if booking is None:
            raise BookingNotFoundError(booking_id)

        return booking
