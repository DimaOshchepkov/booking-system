from datetime import date, time

import pytest

from app.core.exceptions import BookingNotFoundError, SlotUnavailableError
from app.schemas.booking import BookingCreate
from app.services.booking_service import BookingService


class TestBookingService:

    @pytest.fixture
    def booking_data(self) -> BookingCreate:
        """Тестовые данные для брони."""
        return BookingCreate(
            name="Иван Петров",
            phone="+79991234567",
            booking_date=date(2026, 9, 10),
            booking_time=time(14, 0),
            guests=4,
        )

    async def test_is_slot_unavailable_after_create(
        self, booking_service: BookingService, booking_data: BookingCreate
    ):
        await booking_service.create(booking_data)

        assert (
            await booking_service.is_slot_available(date(2026, 9, 10), time(14, 0))
            is False
        )

    async def test_is_slot_available_different_time(
        self, booking_service: BookingService, booking_data: BookingCreate
    ):
        await booking_service.create(booking_data)

        assert (
            await booking_service.is_slot_available(date(2026, 9, 10), time(15, 0))
            is True
        )

    async def test_is_slot_available_different_date(
        self, booking_service: BookingService, booking_data: BookingCreate
    ):
        await booking_service.create(booking_data)

        assert (
            await booking_service.is_slot_available(date(2026, 9, 11), time(14, 0))
            is True
        )

    async def test_is_slot_available_after_cancel(
        self, booking_service: BookingService, booking_data: BookingCreate
    ):
        booking = await booking_service.create(booking_data)
        await booking_service.cancel(booking.id)

        assert (
            await booking_service.is_slot_available(date(2026, 9, 10), time(14, 0))
            is True
        )

    async def test_create_booking_success(
        self, booking_service: BookingService, booking_data: BookingCreate
    ):
        booking = await booking_service.create(booking_data)

        assert booking.id is not None
        assert booking.name == "Иван Петров"
        assert booking.phone == "+79991234567"
        assert booking.booking_date == date(2026, 9, 10)
        assert booking.booking_time == time(14, 0)
        assert booking.guests == 4
        assert booking.status == "active"

    async def test_create_booking_slot_unavailable(
        self, booking_service: BookingService, booking_data: BookingCreate
    ):
        await booking_service.create(booking_data)

        with pytest.raises(SlotUnavailableError):
            await booking_service.create(booking_data)

    async def test_list_bookings_returns_active_only(
        self, booking_service: BookingService, booking_data: BookingCreate
    ):
        booking1 = await booking_service.create(booking_data)

        booking_data2 = booking_data.model_copy(update={"booking_time": time(15, 0)})
        await booking_service.create(booking_data2)

        await booking_service.cancel(booking1.id)

        bookings = await booking_service.list()
        assert len(bookings) == 1
        assert bookings[0].id != booking1.id

    async def test_list_bookings_filter_by_date(
        self, booking_service: BookingService, booking_data: BookingCreate
    ):
        await booking_service.create(booking_data)

        booking_data2 = booking_data.model_copy(
            update={"booking_date": date(2026, 9, 11)}
        )
        await booking_service.create(booking_data2)

        bookings = await booking_service.list(booking_date=date(2026, 9, 10))
        assert len(bookings) == 1
        assert bookings[0].booking_date == date(2026, 9, 10)

    async def test_list_bookings_sorted(
        self, booking_service: BookingService, booking_data: BookingCreate
    ):
        data2 = booking_data.model_copy(
            update={"booking_date": date(2026, 9, 11), "booking_time": time(12, 0)}
        )
        await booking_service.create(data2)

        data3 = booking_data.model_copy(
            update={"booking_date": date(2026, 9, 11), "booking_time": time(13, 0)}
        )
        await booking_service.create(data3)

        await booking_service.create(booking_data)

        bookings = await booking_service.list()
        assert len(bookings) == 3
        assert bookings[0].booking_date == date(2026, 9, 10)
        assert bookings[1].booking_time == time(12, 0)
        assert bookings[2].booking_time == time(13, 0)

    async def test_get_by_id_not_found(self, booking_service: BookingService):
        with pytest.raises(BookingNotFoundError) as exc_info:
            await booking_service.get_by_id(999)

        assert exc_info.value.field == "booking_id"

    async def test_get_by_id_returns_cancelled(
        self, booking_service: BookingService, booking_data: BookingCreate
    ):
        booking = await booking_service.create(booking_data)
        await booking_service.cancel(booking.id)

        result = await booking_service.get_by_id(booking.id)
        assert result.status == "cancelled"

    async def test_cancel_booking_idempotent(
        self, booking_service: BookingService, booking_data: BookingCreate
    ):
        booking = await booking_service.create(booking_data)

        await booking_service.cancel(booking.id)
        cancelled_again = await booking_service.cancel(booking.id)

        assert cancelled_again.status == "cancelled"

    async def test_cancel_booking_not_found(self, booking_service: BookingService):
        with pytest.raises(BookingNotFoundError):
            await booking_service.cancel(999)

    async def test_cancel_frees_slot(
        self, booking_service: BookingService, booking_data: BookingCreate
    ):
        booking = await booking_service.create(booking_data)
        await booking_service.cancel(booking.id)

        new_booking = await booking_service.create(booking_data)
        assert new_booking.status == "active"
        assert new_booking.id != booking.id
