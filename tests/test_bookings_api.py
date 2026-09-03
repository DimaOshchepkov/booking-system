from datetime import date, time
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.exceptions import BookingNotFoundError, SlotUnavailableError
from app.dependencies import get_booking_service
from app.main import app
from app.models.booking import Booking
from app.services.booking_service import BookingService


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock(spec=BookingService)


@pytest.fixture
async def client(mock_service: AsyncMock):
    app.dependency_overrides[get_booking_service] = lambda: mock_service

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()



@pytest.fixture
def sample_booking() -> Booking:
    return Booking(
        id=1,
        name="Иван Петров",
        phone="+79991234567",
        booking_date=date(2026, 9, 10),
        booking_time=time(14, 0),
        guests=4,
        status="active",
    )


class TestBookingsAPI:

    async def test_create_booking_success(
        self,
        client: AsyncClient,
        mock_service: AsyncMock,
        valid_payload: dict,
        sample_booking: Booking,
    ):
        mock_service.create.return_value = sample_booking

        response = await client.post("/bookings/", json=valid_payload)

        assert response.status_code == 201
        assert "/bookings/1" in response.headers["Location"]

    async def test_create_booking_slot_unavailable(
        self,
        client: AsyncClient,
        mock_service: AsyncMock,
        valid_payload: dict,
    ):
        mock_service.create.side_effect = SlotUnavailableError()

        response = await client.post("/bookings/", json=valid_payload)

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "slot_unavailable"

    async def test_create_booking_validation_error(
        self, client: AsyncClient, valid_payload: dict
    ):
        valid_payload["name"] = "A"

        response = await client.post("/bookings/", json=valid_payload)

        assert response.status_code == 422

    async def test_list_bookings_empty(
        self, client: AsyncClient, mock_service: AsyncMock
    ):
        mock_service.list.return_value = []

        response = await client.get("/bookings/")

        assert response.status_code == 200
        assert response.json() == []
        mock_service.list.assert_awaited_once_with(booking_date=None)

    async def test_list_bookings_with_date_filter(
        self, client: AsyncClient, mock_service: AsyncMock
    ):
        mock_service.list.return_value = []

        response = await client.get("/bookings/?date=2026-09-10")

        assert response.status_code == 200
        mock_service.list.assert_awaited_once_with(booking_date=date(2026, 9, 10))

    async def test_list_bookings_with_data(
        self,
        client: AsyncClient,
        mock_service: AsyncMock,
        sample_booking: Booking,
    ):
        mock_service.list.return_value = [sample_booking]

        response = await client.get("/bookings/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == 1

    async def test_get_booking_success(
        self,
        client: AsyncClient,
        mock_service: AsyncMock,
        sample_booking: Booking,
    ):
        mock_service.get_by_id.return_value = sample_booking

        response = await client.get("/bookings/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1
        mock_service.get_by_id.assert_awaited_once_with(1)

    async def test_get_booking_not_found(
        self, client: AsyncClient, mock_service: AsyncMock
    ):
        mock_service.get_by_id.side_effect = BookingNotFoundError(999)

        response = await client.get("/bookings/999")

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "booking_not_found"

    async def test_cancel_booking_success(
        self,
        client: AsyncClient,
        mock_service: AsyncMock,
        sample_booking: Booking,
    ):
        cancelled = Booking(
            id=1,
            name=sample_booking.name,
            phone=sample_booking.phone,
            booking_date=sample_booking.booking_date,
            booking_time=sample_booking.booking_time,
            guests=sample_booking.guests,
            status="cancelled",
        )
        mock_service.cancel.return_value = cancelled

        response = await client.delete("/bookings/1")

        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"
        mock_service.cancel.assert_awaited_once_with(1)

    async def test_cancel_booking_not_found(
        self, client: AsyncClient, mock_service: AsyncMock
    ):
        mock_service.cancel.side_effect = BookingNotFoundError(999)

        response = await client.delete("/bookings/999")

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "booking_not_found"
