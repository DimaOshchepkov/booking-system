import pytest
from datetime import date, time, timedelta
from pydantic import ValidationError

from app.schemas.booking import BookingCreate


class TestBookingCreateSchema:

    @pytest.fixture
    def valid_data(self) -> dict:
        return {
            "name": "Иван Петров",
            "phone": "+79991234567",
            "booking_date": (date.today() + timedelta(days=1)).isoformat(),
            "booking_time": "14:00",
            "guests": 4,
        }


    def test_name_with_hyphen(self, valid_data: dict):
        valid_data["name"] = "Анна-Мария"
        schema = BookingCreate(**valid_data)
        assert schema.name == "Анна-Мария"

    def test_name_too_short(self, valid_data: dict):
        valid_data["name"] = "Я"
        with pytest.raises(ValidationError):
            BookingCreate(**valid_data)

    def test_name_with_numbers(self, valid_data: dict):
        valid_data["name"] = "Иван123"
        with pytest.raises(ValidationError):
            BookingCreate(**valid_data)




    def test_invalid_phone_format(self, valid_data: dict):
        valid_data["phone"] = "+1234567890"
        with pytest.raises(ValidationError):
            BookingCreate(**valid_data)
            
    def test_invalid_phone_format_with_hyphen(self, valid_data: dict):
        valid_data["phone"] = "+723456-78-90"
        with pytest.raises(ValidationError):
            BookingCreate(**valid_data)
            
    def test_invalid_phone_format_with_brackets(self, valid_data: dict):
        valid_data["phone"] = "+7(234)567890"
        with pytest.raises(ValidationError):
            BookingCreate(**valid_data)
            
    def test_invalid_phone_format_less_digits(self, valid_data: dict):
        valid_data["phone"] = "+723456780"
        with pytest.raises(ValidationError):
            BookingCreate(**valid_data)
            
    def test_invalid_phone_format_not_star_with_plus(self, valid_data: dict):
        valid_data["phone"] = "7234567890"
        with pytest.raises(ValidationError):
            BookingCreate(**valid_data)



    def test_date_in_past(self, valid_data: dict):
        valid_data["booking_date"] = "2020-01-01"
        with pytest.raises(ValidationError):
            BookingCreate(**valid_data)

    def test_date_too_far(self, valid_data: dict):
        far_date = (date.today() + timedelta(days=100)).isoformat()
        valid_data["booking_date"] = far_date
        with pytest.raises(ValidationError):
            BookingCreate(**valid_data)


    def test_valid_time_slots(self, valid_data: dict):
        for hour in range(12, 23):
            valid_data["booking_time"] = f"{hour:02d}:00"
            schema = BookingCreate(**valid_data)
            assert schema.booking_time == time(hour, 0)

    def test_invalid_time_slot(self, valid_data: dict):
        valid_data["booking_time"] = "14:30"
        with pytest.raises(ValidationError):
            BookingCreate(**valid_data)

    def test_time_before_12(self, valid_data: dict):
        valid_data["booking_time"] = "11:00"
        with pytest.raises(ValidationError):
            BookingCreate(**valid_data)

    def test_time_after_22(self, valid_data: dict):
        valid_data["booking_time"] = "23:00"
        with pytest.raises(ValidationError):
            BookingCreate(**valid_data)


    def test_guests_too_few(self, valid_data: dict):
        valid_data["guests"] = 0
        with pytest.raises(ValidationError):
            BookingCreate(**valid_data)

    def test_guests_too_many(self, valid_data: dict):
        valid_data["guests"] = 13
        with pytest.raises(ValidationError):
            BookingCreate(**valid_data)