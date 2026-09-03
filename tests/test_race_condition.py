from httpx import AsyncClient

from tests.utils import run_concurrently

class TestCreate:
    async def test_concurrent_booking_same_slot(
        self, client: AsyncClient, valid_payload: dict
    ):
        async def try_create() -> int:
            response = await client.post("/bookings/", json=valid_payload)
            return response.status_code
        
        COUNT_RESPONSE = 50
        status_codes = await run_concurrently(50, try_create)
        
        assert status_codes.count(201) == 1
        assert status_codes.count(409) == COUNT_RESPONSE - 1